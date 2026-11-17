from datetime import timedelta

import gymnasium as gym
from gymnasium import ActionWrapper
import numpy as np

import pcse

import pcse_gym.envs.sb3


class ActionConstrainer(ActionWrapper):
    """
    Action Wrapper to limit fertilization actions
    """
    def __init__(self, env, action_limit=0, n_budget=0, temporal=False):
        super(ActionConstrainer, self).__init__(env)
        self.counter = 0
        self.action_limit = action_limit
        self.n_counter = 0
        self.temporal = temporal
        self.n_budget = n_budget

    def action(self, action):
        if self.action_limit > 0:
            if isinstance(self.action_space, gym.spaces.Discrete):
                action = self.freq_limiter_discrete(action)
            elif isinstance(self.action_space, gym.spaces.MultiDiscrete):
                action = self.freq_limiter_multi_discrete(action)
        if self.n_budget > 0:
            if isinstance(self.action_space, gym.spaces.Discrete):
                action = self.discrete_n_budget(action)
            elif isinstance(self.action_space, gym.spaces.MultiDiscrete):
                action = self.multi_discrete_n_budget(action)
        if self.temporal is not False:
            if isinstance(self.action_space, gym.spaces.Discrete):
                action = self.discrete_temporal_constraint(action)
            if isinstance(self.action_space, gym.spaces.MultiDiscrete):
                action = self.multi_discrete_temporal_constraint(action)
        return action

    def discrete_temporal_constraint(self, action):
        if self.sb3_env.dvs < 0.01:
            action = 0
            return action
        if self.sb3_env.dvs > 1:
            action = 0
            return action
        return action

    def multi_discrete_temporal_constraint(self, action):
        if self.sb3_env.dvs < 0.01:
            action[0] = 0
            return action
        if self.sb3_env.dvs > 1:
            action[0] = 0
            return action
        return action

    def discrete_n_budget(self, action):
        if self.n_counter == self.n_budget:
            action = 0
            return action
        self.n_counter += action * 10
        if self.n_counter > self.n_budget:
            action = ((self.n_budget + action * 10) - self.n_counter) / 10
            self.n_counter = self.n_budget
        return action

    def multi_discrete_n_budget(self, action):
        if self.n_counter == self.n_budget:
            action = action.copy()  # Needed for RLlib VecEnvs
            action[0] = 0
            return action
        self.n_counter += action[0] * 10
        if self.n_counter > self.n_budget:
            action = action.copy()
            action[0] = ((self.n_budget + action[0] * 10) - self.n_counter) / 10
            self.n_counter = self.n_budget
        return action

    def freq_limiter_discrete(self, action):
        if action != 0:  # if there's an action, increase the counter
            self.counter += 1
        if self.counter > self.action_limit:  # return 0 if the action exceeds limit
            action = 0
        return action

    def freq_limiter_multi_discrete(self, action):
        if action[0] != 0:
            self.counter += 1
        if self.counter > self.action_limit:
            action = action.copy()
            action[0] = 0
        return action

    def reset(self, **kwargs):
        self.counter = 0
        self.n_counter = 0
        return self.env.reset(**kwargs)


def ratio_rescale(value, old_max=None, old_min=None, new_max=None, new_min=None):
    new_value = (((value - old_min) * (new_max - new_min)) / (old_max - old_min)) + new_min
    return new_value


def non_linear_ratio_rescale(value, old_max=None, old_min=None, new_max=None, new_min=None):
    # Normalize the input value to [0, 1]
    normalized_value = (value - old_min) / (old_max - old_min)

    # Determine which segment we are in based on the normalized value
    if normalized_value <= 0.5:
        # Scale sine to [0, 1] and then rescale to [0.3, 0.55]
        return 0.3 + 0.25 * np.sin(np.pi * normalized_value)
    else:
        # Scale sine to [0, 1] and then rescale to [0.55, 0.8]
        return 0.55 + 0.25 * np.sin(np.pi * (normalized_value - 0.5))


class VariableRecoveryRate(pcse_gym.envs.sb3.StableBaselinesWrapper):
    def __init__(self, env):
        super().__init__()
        self.__dict__.update(env.__dict__)

    def _apply_action(self, action) -> None:
        amount = action * self.action_multiplier
        recovery_rate = self.recovery_penalty()
        self._model._send_signal(signal=pcse.signals.apply_n, N_amount=amount * 10, N_recovery=recovery_rate,
                                 amount=amount, recovery=recovery_rate)

    def recovery_penalty(self):
        """
        estimation function due to static recovery rate of WOFOST/LINTUL
        Potentially enforcing the agent not to dump everything at the start
        Not to be used with CERES 'start-dump'
        Adapted, based on the findings of Raun, W.R. and Johnson, G.V. (1999)
        """
        date_now = self.date - self.start_date
        date_end = self.end_date - self.start_date  # TODO end on flowering?
        recovery = ratio_rescale(date_now / timedelta(days=1),
                                 old_max=date_end / timedelta(days=1), old_min=0.0, new_max=0.8, new_min=0.3)
        return recovery


def generate_combinations(elements):
    from itertools import combinations
    all_combinations = []

    for x in range(1, len(elements) + 1):
        all_combinations.extend(combinations(elements, x))

    return all_combinations


def corrected_fertilization_action_constraint(actions, episodic_step, non_zero_action_counter,
        last_non_zero_action_step, dvs, nitrogen_efficiency, nitrogen_surplus, end_of_episode_mask,
        max_non_zero_actions=4, min_steps_between_actions=2, start_step=.01, end_step=1.,
        time_weight=50., n_weight=5., con_weight=3., nue_threshold=(.5,.9), n_surplus_threshold=(0.,40.)):
    """Costs use PRE-action counts/timing and per-environment TRUE terminal flags."""
    # Supports both NumPy buffer collection and torch diagnostic minibatches.
    import torch
    is_tensor = isinstance(actions, torch.Tensor)
    if is_tensor:
        logical_and = torch.logical_and
        positive = torch.clamp(non_zero_action_counter + (actions > 0) - max_non_zero_actions, min=0)
    else:
        logical_and = np.logical_and
        positive = np.maximum(non_zero_action_counter + (actions > 0) - max_non_zero_actions, 0)
    nz = actions > 0
    invalid = (dvs < start_step) | (dvs > end_step)
    spacing = logical_and(nz, episodic_step - last_non_zero_action_step < min_steps_between_actions)
    nue = logical_and(end_of_episode_mask, (nitrogen_efficiency < nue_threshold[0]) | (nitrogen_efficiency > nue_threshold[1]))
    surplus = logical_and(end_of_episode_mask, (nitrogen_surplus < n_surplus_threshold[0]) | (nitrogen_surplus > n_surplus_threshold[1]))
    return positive*n_weight, logical_and(nz, invalid)*time_weight, spacing*con_weight, nue*1., surplus*1.


def fertilization_action_constraint(*args, constraint_mode="raw", **kwargs):
    """Public explicit mode selector; original published implementation remains unchanged."""
    if constraint_mode == "raw":
        from pcse_gym.agent.ppo_mod import fertilization_action_constraint as raw
        return raw(*args, **kwargs)
    if constraint_mode == "corrected":
        return corrected_fertilization_action_constraint(*args, **kwargs)
    raise ValueError(constraint_mode)


class AgronomicShield(ActionConstrainer):
    """Pre-execution deterministic shield. No future weather or soil truth is read."""
    def __init__(self, env, enabled=True, n_budget=0, max_applications=4, min_days=14):
        super().__init__(env, n_budget=n_budget)
        self.enabled = enabled
        self.max_applications = max_applications
        self.min_days = min_days
        self.day = 0
        self.last_day = -10000
        self.total_steps = self.proposed_violations = self.executed_violations = 0
        self.current_dvs = 0.

    def reset(self, **kwargs):
        self.day = 0
        self.last_day = -10000
        self.total_steps = self.proposed_violations = self.executed_violations = 0
        obs, info = super().reset(**kwargs)
        self.current_dvs = float(np.asarray(obs).flat[0])
        return obs, info

    def get_action_mask(self, obs_state=None, info=None):
        """Conservative causal subset; execution-day projection remains authoritative.

        The .12 DVS margin is an engineering safety margin, not a proven
        all-weather upper bound. Interceptions are measured separately.
        """
        state = {} if info is None else info
        dvs = self.current_dvs if obs_state is None else float(np.asarray(obs_state).flat[0])
        remaining = state.get('remaining_budget', self.n_budget-self.n_counter if self.n_budget else 1e9)
        since = state.get('days_since_last', self.day-self.last_day)
        count = state.get('fert_count', self.counter)
        mask = np.zeros(9, dtype=bool)
        mask[0] = True
        if .01 <= dvs <= .88 and since >= self.min_days and count < self.max_applications:
            mask[1:] = np.arange(1,9)*10 <= remaining + 1e-6
        return mask

    def violations(self, action):
        reasons = []
        if not np.isfinite(action) or not 0 <= action <= 8 or action != int(action):
            return ["action_domain"]
        if action > 0:
            if self.counter >= self.max_applications: reasons.append("application_frequency")
            if self.day - self.last_day < self.min_days: reasons.append("minimum_spacing")
            if not .01 <= self.current_dvs <= 1.: reasons.append("phenology_window")
            if self.n_budget > 0 and self.n_counter + action*10 > self.n_budget: reasons.append("seasonal_budget")
        return reasons

    def step(self, action):
        proposed = float(np.asarray(action).item())
        proposal_dvs = self.current_dvs
        engine = getattr(getattr(self.env.unwrapped, "sb3_env", None), "model", None)
        state = {}
        def project(candidate, dvs, execution_day):
            self.current_dvs = float(dvs)
            reasons = self.violations(proposed)
            if engine is not None and getattr(engine, 'flag_terminate', False) and proposed>0:
                reasons.append('season_ended')
            executed = candidate
            if self.enabled:
                if any(r != "seasonal_budget" for r in reasons): executed = 0
                elif "seasonal_budget" in reasons:
                    executed = max(0, min(candidate, (self.n_budget-self.n_counter)//10))
            state.update(reasons=reasons, executed=int(executed), dvs=float(dvs), day=str(execution_day))
            return executed
        if engine is not None:
            # Domain projection must precede indexing the native discrete-action table.
            candidate = 0 if self.enabled and "action_domain" in self.violations(proposed) else proposed
            engine._guard_updates_accounting = self.enabled
            engine._action_guard = lambda amount, dvs, day: project(amount/10, dvs, day)*10
        else:
            candidate = project(proposed, self.current_dvs, self.day)
        obs, reward, term, trunc, info = self.env.step(int(candidate))
        if engine is not None and not state:
            # Crop terminated before the planned application day: no fertilizer signal was sent.
            state.update(reasons=["season_ended"] if proposed>0 else [], executed=0,
                         dvs=float(np.asarray(obs).flat[0]), day=str(getattr(self.env.unwrapped,"date",self.day)))
        executed = state['executed']
        reasons = state['reasons']
        self.current_dvs = state['dvs']
        execution_reasons = self.violations(executed)
        if executed > 0:
            self.counter += 1
            self.n_counter += executed*10
            self.last_day = self.day
        self.day += 7
        self.total_steps += 1
        self.proposed_violations += bool(reasons)
        self.executed_violations += bool(execution_reasons)
        info.update(proposed_action=proposed, executed_action=int(executed),
                    shield_triggered=bool(self.enabled and proposed != executed), shield_reason=reasons,
                    executed_violation_reasons=execution_reasons, proposal_dvs=proposal_dvs,
                    decision_dvs=state['dvs'], application_dvs=state['dvs'], application_date=state['day'],
                    proposed_violation_rate=self.proposed_violations/self.total_steps,
                    executed_violation_rate=self.executed_violations/self.total_steps)
        self.current_dvs = float(np.asarray(obs).flat[0])
        return obs, reward, term, trunc, info


def upper_surplus_constraint(*args, **kwargs):
    """Version3: retain step safety costs; dual endpoint cost only penalizes excess surplus."""
    result=list(corrected_fertilization_action_constraint(*args, **kwargs))
    import torch
    surplus=args[6];done=args[7]
    if isinstance(surplus,torch.Tensor):
        result[3]=torch.zeros_like(surplus);result[4]=torch.clamp((surplus-40)/20,min=0)*done
    else:
        result[3]=np.zeros_like(surplus,dtype=float);result[4]=np.maximum((np.asarray(surplus)-40)/20,0)*done
    return tuple(result)
