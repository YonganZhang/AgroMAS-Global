"""Summarize frozen source/engineering gates without selecting on yields or Dev."""
from pathlib import Path
import json,hashlib
import numpy as np
R=Path(__file__).resolve().parents[1];P=R/'reports/phase5'
def rows(name):return [json.loads(x) for x in (P/name).read_text().splitlines()]
def summary(v):
    ok=[r for r in v if r['status']=='completed']
    a=np.array([r['outcome'] for r in ok])
    return dict(total=len(v),completed=len(ok),mean_yield_dm_t_ha=float(a[:,0].mean()),
        mean_NUE=float(a[:,3].mean()),mean_surplus_kg_ha=float(a[:,2].mean()),mean_fert_kg_ha=float(a[:,4].mean()),
        joint_40_fraction=float(np.mean((a[:,3]>=.5)&(a[:,3]<=.9)&(a[:,2]<=40))),
        NUE_above1_fraction=float(np.mean(a[:,3]>1)),negative_surplus_fraction=float(np.mean(a[:,2]<0)),
        three_positive_stage_fraction=float(np.mean([sum(e['dose']>0 for e in r['events'])==3 for r in ok])))
if __name__=='__main__':
    f=json.loads((P/'regional-phenology-train-freeze-v2.json').read_text())
    train=rows('regional-train-phenology-v2.jsonl');dev=rows('regional-dev-frozen-check-v2.jsonl');diag=rows('regional-train-diagnostics-v2.jsonl')
    report=dict(status='engineering_gate_passed_with_agronomic_source_limitations',all_train_candidates=1512,
         train_failed=sum(r['status']!='completed' for r in train),dev_cumulative_check=2,dev_reselected=False,
         heldout_unlocked=False,regions={},
         claim_ceiling='Real gridded weather plus registered arable/SoilGrids priors, unvalidated field inputs; no field-validity or policy superiority claim',
         source_limitations=['Foreign initial mineral N and24year age remain native priors','Grid points have no verified field landcover',
         'Zero wet deposition is common experimental control','China171basal with220total leaves49topdress; zero-topdress is notN0',
         'France soil-stock N can drive NUE>1; native NUE denominator excludes initial soil stocks','Idealized warming/CO2 is not actualCMIP6'])
    for n,s in f['selected'].items():
        t=[r for r in train if r['region_id']==n and r['cultivar']==s['cultivar'] and r['thermal_scale']==s['thermal_scale']]
        d=[r for r in dev if r['region_id']==n]
        z=[r for r in diag if r['region_id']==n and r['diagnostic']=='zero_topdress']
        depth=[r for r in diag if r['region_id']==n and r['diagnostic']=='root100']
        report['regions'][n]=dict(selected=s,Train=summary(t),Dev_check2=summary(d),zero_topdress=summary(z),root100=summary(depth))
        report['regions'][n]['fertilizer_response_dm_t_ha']=summary(t)['mean_yield_dm_t_ha']-summary(z)['mean_yield_dm_t_ha']
    path=P/'regional-validity-gate-v2.json'
    with path.open('x') as out:json.dump(report,out,indent=2)
    path.chmod(0o444)
    lines=['# v2区域校准：工程门槛通过，田间与农艺局限保留','',
      '1512个训练候选季全部完成。按预注册成熟规则冻结五区选择；25个开发季为累计检查#2，未据此重选。独立52季仍锁定。',
      '', '|区域|Train产量tDM/ha|Train NUE|盈余kgN/ha|相对零追肥增产tDM/ha|Dev产量tDM/ha|','|---|---:|---:|---:|---:|---:|']
    for n,x in report['regions'].items():
        t=x['Train'];d=x['Dev_check2']
        lines.append(f"|{n}|{t['mean_yield_dm_t_ha']:.3f}|{t['mean_NUE']:.3f}|{t['mean_surplus_kg_ha']:.2f}|{x['fertilizer_response_dm_t_ha']:.3f}|{d['mean_yield_dm_t_ha']:.3f}|")
    lines+=['','这里是参考施肥方案的模型诊断，不是智能体对比。栾城零追肥仍含171kgN/ha底肥；其他地区零追肥才是化肥N0。初始有机氮/矿质氮不进入原生NUE分母，因此NUE>1和负盈余均原样保留，不反推库存求合规。',
      '', '根深100cm结果是敏感性证据，未用于挑选更好产量/响应。所有缺少田间来源的背景仍明确列为先验。v1原始档案、失败结果和第一次Dev检查不改写。工程完成不等于五区田间有效性已验证；模型训练和最终实验尚待完成。']
    (P/'STAGE5C_V2_VALIDITY.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(report['regions'],indent=2))
