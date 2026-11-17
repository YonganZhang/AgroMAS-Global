"""LightningModule wrapper. Model/loss/metric are injected; the loop is fixed."""
from __future__ import annotations

import math
from typing import Callable

import lightning as L
import torch
from torch import nn


def _build_scheduler(
    optimizer: torch.optim.Optimizer,
    scheduler_cfg: dict | None,
    trainer: L.Trainer | None,
    max_lr: float,
) -> dict | torch.optim.Optimizer:
    if not scheduler_cfg:
        return optimizer
    name = scheduler_cfg.get("name", "step")
    if name == "step":
        scheduler = torch.optim.lr_scheduler.StepLR(
            optimizer,
            step_size=int(scheduler_cfg.get("step_size", 1000)),
            gamma=float(scheduler_cfg.get("gamma", 0.1)),
        )
    elif name in {"cosine", "onecycle"}:
        est = getattr(trainer, "estimated_stepping_batches", None) if trainer is not None else None
        default_steps = int(est) if (est is not None and math.isfinite(float(est)) and float(est) > 0) else 1000
        total_steps = max(int(scheduler_cfg.get("total_steps") or default_steps), 1)
        if name == "cosine":
            scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
                optimizer,
                T_max=total_steps,
                eta_min=float(scheduler_cfg.get("eta_min", 0.0)),
            )
        else:
            scheduler = torch.optim.lr_scheduler.OneCycleLR(
                optimizer,
                max_lr=float(scheduler_cfg.get("max_lr", max_lr)),
                total_steps=total_steps,
                pct_start=float(scheduler_cfg.get("pct_start", 0.1)),
            )
    else:
        raise ValueError(f"unsupported scheduler {name!r}; expected 'step', 'cosine', or 'onecycle'")
    return {"optimizer": optimizer, "lr_scheduler": {"scheduler": scheduler, "interval": "step"}}


def _build_param_groups(module: nn.Module, weight_decay: float) -> list[dict]:
    """Split trainable parameters into decay (ndim >= 2) and no-decay (biases, norms, 1D gates)."""
    decay = [p for p in module.parameters() if p.requires_grad and p.ndim >= 2]
    no_decay = [p for p in module.parameters() if p.requires_grad and p.ndim < 2]
    groups: list[dict] = []
    if decay:
        groups.append({"params": decay, "weight_decay": float(weight_decay)})
    if no_decay:
        groups.append({"params": no_decay, "weight_decay": 0.0})
    return groups or [{"params": list(module.parameters()), "weight_decay": float(weight_decay)}]



class SupervisedModule(L.LightningModule):
    def __init__(
        self,
        model: nn.Module,
        loss_fn: Callable[[torch.Tensor, torch.Tensor], torch.Tensor],
        metrics: dict[str, Callable[[torch.Tensor, torch.Tensor], torch.Tensor]] | None = None,
        lr: float = 1e-3,
        weight_decay: float = 0.0,
        scheduler: dict | None = None,
    ) -> None:
        super().__init__()
        self.save_hyperparameters(ignore=["model", "loss_fn", "metrics"])
        self.model = model
        self.loss_fn = loss_fn
        self.metrics = metrics or {}
        self.lr = lr
        self.weight_decay = weight_decay
        self.scheduler_cfg = scheduler

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)

    def _shared_step(self, batch: dict, stage: str) -> torch.Tensor:
        pred = self(batch["x"])
        target = batch["y"]
        loss = self.loss_fn(pred, target)
        if stage == "train" and hasattr(self.model, "aux_loss") and callable(self.model.aux_loss):
            aux = self.model.aux_loss()
            if aux is not None:
                loss = loss + aux
        if not torch.isfinite(loss).all():
            raise ValueError(f"non-finite {stage} loss: {loss}")
        batch_size = batch["x"].shape[0]
        self.log(
            f"{stage}/loss",
            loss,
            on_step=(stage == "train"),
            on_epoch=True,
            prog_bar=True,
            batch_size=batch_size,
            sync_dist=(stage == "val"),
        )
        for name, fn in self.metrics.items():
            value = fn(pred.detach(), target.detach())
            self.log(
                f"{stage}/{name}",
                value,
                on_step=False,
                on_epoch=True,
                prog_bar=False,
                batch_size=batch_size,
                sync_dist=(stage == "val"),
            )
        return loss

    def training_step(self, batch: dict, batch_idx: int) -> torch.Tensor:
        return self._shared_step(batch, "train")

    def validation_step(self, batch: dict, batch_idx: int) -> torch.Tensor:
        return self._shared_step(batch, "val")

    def test_step(self, batch: dict, batch_idx: int) -> torch.Tensor:
        return self._shared_step(batch, "test")

    def predict_step(self, batch: dict, batch_idx: int, dataloader_idx: int = 0) -> dict:
        return {"pred": self(batch["x"]), "sample_id": batch["sample_id"]}

    def configure_optimizers(self):
        optimizer = torch.optim.AdamW(
            _build_param_groups(self, self.weight_decay),
            lr=self.lr,
            weight_decay=self.weight_decay,
        )
        return _build_scheduler(optimizer, self.scheduler_cfg, getattr(self, "_trainer", None), self.lr)


class MultiTaskModule(L.LightningModule):
    """Shared backbone with one head, loss and metric set per task.

    The template selects the lowest weighted ``val/loss`` for every run. That
    is a declared common compromise, not each task's independently best step.
    """

    def __init__(
        self,
        backbone: nn.Module,
        heads: dict[str, nn.Module],
        losses: dict[str, Callable[[torch.Tensor, torch.Tensor], torch.Tensor]],
        loss_weights: dict[str, float],
        metrics: dict[str, dict[str, Callable[[torch.Tensor, torch.Tensor], torch.Tensor]]] | None = None,
        lr: float = 1e-3,
        weight_decay: float = 0.0,
        scheduler: dict | None = None,
    ) -> None:
        super().__init__()
        if not heads:
            raise ValueError("multi-task module needs at least one head")
        if set(heads) != set(losses) or set(heads) != set(loss_weights):
            raise ValueError("heads, losses and loss_weights must have identical task keys")
        for task, weight in loss_weights.items():
            if not math.isfinite(float(weight)) or float(weight) < 0:
                raise ValueError(f"loss weight for {task!r} must be finite and >= 0")
        if sum(float(v) for v in loss_weights.values()) <= 0:
            raise ValueError("at least one loss weight must be positive")
        self.save_hyperparameters(ignore=["backbone", "heads", "losses", "metrics"])
        self.backbone = backbone
        self.heads = nn.ModuleDict(heads)
        self.losses = losses
        self.loss_weights = {k: float(v) for k, v in loss_weights.items()}
        self.metrics = metrics or {}
        unknown_metrics = set(self.metrics) - set(heads)
        if unknown_metrics:
            raise ValueError(f"metrics for unknown tasks: {sorted(unknown_metrics)}")
        self.lr = lr
        self.weight_decay = weight_decay
        self.scheduler_cfg = scheduler

    def forward(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        features = self.backbone(x)
        return {task: head(features) for task, head in self.heads.items()}

    def _shared_step(self, batch: dict, stage: str) -> torch.Tensor:
        prediction = self(batch["x"])
        target = batch["y"]
        if set(prediction) != set(target):
            raise ValueError(
                f"prediction/target task mismatch: {sorted(prediction)} != {sorted(target)}"
            )
        if set(prediction) != set(self.losses):
            raise ValueError(
                f"prediction/loss task mismatch: {sorted(prediction)} != {sorted(self.losses)}"
            )
        task_losses = {
            task: self.losses[task](prediction[task], target[task]) for task in prediction
        }
        for task, value in task_losses.items():
            if not torch.isfinite(value):
                raise ValueError(f"non-finite loss for task {task!r}: {value}")
        total = sum(self.loss_weights[task] * task_losses[task] for task in task_losses)
        if stage == "train" and hasattr(self.backbone, "aux_loss") and callable(self.backbone.aux_loss):
            aux = self.backbone.aux_loss()
            if aux is not None:
                total = total + aux
        batch_size = batch["x"].shape[0]
        self.log(
            f"{stage}/loss",
            total,
            on_step=(stage == "train"),
            on_epoch=True,
            prog_bar=True,
            batch_size=batch_size,
            sync_dist=(stage == "val"),
        )
        for task, value in task_losses.items():
            self.log(
                f"{stage}/{task}_loss",
                value,
                on_step=(stage == "train"),
                on_epoch=True,
                prog_bar=False,
                batch_size=batch_size,
                sync_dist=(stage == "val"),
            )
            for name, fn in self.metrics.get(task, {}).items():
                metric_value = fn(prediction[task].detach(), target[task].detach())
                self.log(
                    f"{stage}/{task}_{name}",
                    metric_value,
                    on_step=False,
                    on_epoch=True,
                    prog_bar=False,
                    batch_size=batch_size,
                    sync_dist=(stage == "val"),
                )
        return total

    def training_step(self, batch: dict, batch_idx: int) -> torch.Tensor:
        return self._shared_step(batch, "train")

    def validation_step(self, batch: dict, batch_idx: int) -> torch.Tensor:
        return self._shared_step(batch, "val")

    def test_step(self, batch: dict, batch_idx: int) -> torch.Tensor:
        return self._shared_step(batch, "test")

    def predict_step(self, batch: dict, batch_idx: int, dataloader_idx: int = 0) -> dict:
        return {"pred": self(batch["x"]), "sample_id": batch["sample_id"]}

    def configure_optimizers(self):
        optimizer = torch.optim.AdamW(
            _build_param_groups(self, self.weight_decay),
            lr=self.lr,
            weight_decay=self.weight_decay,
        )
        return _build_scheduler(optimizer, self.scheduler_cfg, getattr(self, "_trainer", None), self.lr)



class StructuredAutoResearchModule(SupervisedModule):
    """4-Slot PyTorch Lightning Container with NaN-safe numerator/denominator per-slice aggregation.

    Accepts either:
    - ``model(batch["x"]) -> Tensor`` (standard template contract), or
    - ``model(batch) -> {"pred": Tensor, "aux_loss": Tensor}`` (4-slot dict contract).
    """

    def __init__(
        self,
        model: nn.Module,
        loss_fn: Callable,
        slice_names: tuple[str, ...] = ("clean", "boundary", "missing_interior", "extreme_noise"),
        metrics: dict[str, Callable[[torch.Tensor, torch.Tensor], torch.Tensor]] | None = None,
        lr: float = 5e-4,
        weight_decay: float = 1e-4,
        scheduler: dict | None = None,
    ) -> None:
        super().__init__(
            model=model,
            loss_fn=loss_fn,
            metrics=metrics,
            lr=lr,
            weight_decay=weight_decay,
            scheduler=scheduler,
        )
        self.slice_names = tuple(slice_names)
        self.register_buffer("_val_num", torch.zeros(len(self.slice_names), dtype=torch.float64), persistent=False)
        self.register_buffer("_val_den", torch.zeros(len(self.slice_names), dtype=torch.float64), persistent=False)

    def _forward_and_target(self, batch: dict) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor | None]:
        out = self.model(batch["x"]) if "x" in batch else self.model(batch)
        if isinstance(out, dict):
            pred = out["pred"]
            aux = out.get("aux_loss")
        else:
            pred = out
            aux = self.model.aux_loss() if (hasattr(self.model, "aux_loss") and callable(self.model.aux_loss)) else None
        target = batch["y"] if "y" in batch else batch["target"]
        return pred, target, aux

    def training_step(self, batch: dict, batch_idx: int) -> torch.Tensor:
        if "x" in batch and "y" in batch and not isinstance(self.model(batch["x"]), dict):
            return super().training_step(batch, batch_idx)
        pred, target, aux = self._forward_and_target(batch)
        loss = self.loss_fn(pred, target)
        if aux is not None:
            loss = loss + aux
        if not torch.isfinite(loss).all():
            raise ValueError(f"non-finite train loss: {loss}")
        self.log("train/loss", loss, on_step=True, on_epoch=True, prog_bar=True, batch_size=pred.shape[0])
        return loss

    def on_validation_epoch_start(self) -> None:
        self._val_num.zero_()
        self._val_den.zero_()

    def validation_step(self, batch: dict, batch_idx: int) -> torch.Tensor:
        loss = super().validation_step(batch, batch_idx) if ("x" in batch and "y" in batch) else self.training_step(batch, batch_idx)
        pred, target, _ = self._forward_and_target(batch)
        raw_diff = pred.detach().to(torch.float64) - target.detach().to(torch.float64)
        finite_target = torch.isfinite(target)
        err2 = torch.where(finite_target, raw_diff.pow(2), torch.zeros_like(raw_diff))
        slice_masks = batch.get("slice_masks", {})
        for i, name in enumerate(self.slice_names):
            mask = slice_masks.get(name)
            if mask is None:
                valid = finite_target
            else:
                valid = finite_target & (mask.to(dtype=torch.bool, device=err2.device))
            valid_f = valid.expand_as(err2).to(torch.float64)
            self._val_num[i] += torch.where(valid.expand_as(err2), err2, torch.zeros_like(err2)).sum()
            self._val_den[i] += valid_f.sum()
        return loss

    def on_validation_epoch_end(self) -> None:
        num = self.all_gather(self._val_num).sum(0) if self.trainer.world_size > 1 else self._val_num
        den = self.all_gather(self._val_den).sum(0) if self.trainer.world_size > 1 else self._val_den
        slice_rmses: list[torch.Tensor] = []
        for i, name in enumerate(self.slice_names):
            count = float(den[i].item())
            self.log(f"val/slice_{name}_count", float(count), prog_bar=False, sync_dist=False)
            if count > 0.0:
                rmse = torch.sqrt(num[i] / den[i]).to(torch.float32)
                self.log(f"val/slice_{name}", rmse, prog_bar=(i == 0), sync_dist=False)
                slice_rmses.append(rmse)
            else:
                self.log(f"val/slice_{name}", float("nan"), prog_bar=False, sync_dist=False)
        if slice_rmses:
            self.log("val/primary_mean", torch.stack(slice_rmses).mean(), prog_bar=True, sync_dist=False)
