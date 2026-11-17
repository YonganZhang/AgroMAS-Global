"""Freeze discrete regional/scenario subsidy choices using TRAIN only."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import json,hashlib,logging,multiprocessing
import numpy as np
from pcse_gym.agromas.replay import replay_book
R=Path(__file__).resolve().parents[1];P=R/'reports/phase5'
BOOKS={};BETA=None

def evaluate(key):
    name,year,climate=key;book=BOOKS[key];rows=[]
    for zone in ('strict_25','buffer_35','outer_50'):
        for price in (1.,2.):
            ref=replay_book(str(R),book,year=year,climate=climate,zone=zone,price_multiplier=price,subsidy=0.,beta=0.,variant='LOAO-eco')
            for subsidy in (0.,50.,100.,150.,200.):
                row=replay_book(str(R),book,year=year,climate=climate,zone=zone,price_multiplier=price,subsidy=subsidy,beta=BETA)
                row['reference_partial_profit']=ref['partial_profit'];row['paired_partial_profit_difference']=row['partial_profit']-ref['partial_profit']
                rows.append(row)
    return rows

if __name__=='__main__':
    logging.disable(logging.CRITICAL)
    protocol=dict(status='registered_before_subsidy_control_replay',grid=[0,50,100,150,200],
      grouping='Region×climate×researchcap×price;15TRAINharvestyears1995..2009 pergroup',
      reference='FrozenretrainedLOAO-eco(nohardecofilter),zero subsidy,beta0,partialprofitobjective,sharedphysicalbudget',
      criterion='Firstregisteredsubsidywithmeanpairedpartialprofitdifference>=0ANDALL15TRAINseasonsactualS<=cap',
      target_scope='ZeroNsurplusproxyviolationsonTRAIN,notlegalnitratewatercomplianceorfieldguarantee',
      in_sample_selection='FinalTRAINfittedsurrogatesonTRAINinterventionbooks;independentHeld-Outconfirmsonefixedchoice',
      no_solution='Explicitnosolutionwithin0..200;registersigma0asnonconfirmatoryfallback,neverpickbestHeld-Outgridpoint',
      final_grid='Full5levelHeld-Outcurveisprespecifieddescriptive;confirmedthresholdanalysisusesTRAINchoiceonly',
      tipping_resolution='Discretebracketbetweensuccessivegridlevels,neverexactcontinuoustippingpoint',
      replay_firewall='ControlleronlygetscurrentDVS/LAI/SM/cumN/cropN;nodataframefutureterminaloutcomeinput')
    pp=P/'green-subsidy-selection-protocol-v2.json'
    with pp.open('x') as f:json.dump(protocol,f,indent=2)
    pp.chmod(0o444)
    registry=json.loads((P/'teacher-book-receipt-v2.json').read_text());assert registry['failed']==0
    BETA=json.loads((P/'policy-train-freeze-v2.json').read_text())['selected_beta']
    for entry in registry['files']:
        path=R/entry['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256']
        v=[json.loads(line) for line in path.read_text().splitlines()];r=v[0]
        BOOKS[(r['region_id'],r['harvest_year'],r['climate'])]={tuple(row['plan']):row for row in v}
    rows=[];path=P/'green-subsidy-TRAIN-replay-v2.jsonl'
    with path.open('x') as log:
        with ProcessPoolExecutor(max_workers=8,mp_context=multiprocessing.get_context('fork')) as pool:
            for future in as_completed([pool.submit(evaluate,k) for k in BOOKS]):
                result=future.result();rows.extend(result)
                for row in result:log.write(json.dumps(row)+'\n')
                log.flush()
    path.chmod(0o444)
    thresholds=[]
    groups=sorted({(r['region_id'],r['climate'],r['zone'],r['price_multiplier']) for r in rows})
    for name,climate,zone,price in groups:
        grid=[]
        for subsidy in protocol['grid']:
            v=[r for r in rows if (r['region_id'],r['climate'],r['zone'],r['price_multiplier'],r['subsidy'])==(name,climate,zone,price,subsidy)]
            assert len(v)==15
            diff=float(np.mean([r['paired_partial_profit_difference'] for r in v]));violations=sum(r['outcome'][2]>r['cap'] for r in v)
            grid.append(dict(subsidy=subsidy,paired_mean_profit_difference=diff,actual_surplus_violations=violations,
                mean_joint=float(np.mean([r['joint'] for r in v])),qualifies=diff>=0 and violations==0))
        eligible=[g for g in grid if g['qualifies']];chosen=eligible[0]['subsidy'] if eligible else None
        thresholds.append(dict(region_id=name,climate=climate,zone=zone,price_multiplier=price,
            selected_subsidy=chosen,grid=grid,confirmation_subsidy=chosen if chosen is not None else 0,
            status='TRAIN_selected' if chosen is not None else 'No_solution_in_registered_grid',
            bracket=None if chosen is None else [None if chosen==0 else protocol['grid'][protocol['grid'].index(chosen)-1],chosen]))
    result=dict(status='TRAIN_frozen',groups=thresholds,dev_used=False,heldout_used=False,
        protocol_sha256=hashlib.sha256(pp.read_bytes()).hexdigest(),replay_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    out=P/'green-subsidy-TRAIN-freeze-v2.json'
    with out.open('x') as f:json.dump(result,f,indent=2)
    out.chmod(0o444)
    print(json.dumps(dict(groups=len(groups),selected=sum(g['selected_subsidy'] is not None for g in thresholds),nosolution=sum(g['selected_subsidy'] is None for g in thresholds))),flush=True)
