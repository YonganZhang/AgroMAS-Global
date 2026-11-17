"""Outer-loop trajectory lookup; no physical labels enter the controller API."""
from pathlib import Path
from itertools import product
import hashlib,json
import numpy as np
from .core import GRID
PLANS=np.array(list(product(GRID,repeat=3)))
FACTORS=np.array([49,7,1])

class DenseBooks:
    def __init__(self,keys,features,available,outcomes):
        self.keys=keys;self.features=np.asarray(features,float);self.available=np.asarray(available,bool);self.outcomes=np.asarray(outcomes,float)
        if self.features.shape!=(len(keys),3,343,22) or self.outcomes.shape!=(len(keys),343,6):raise ValueError('Invalidbookshape')
        if not np.isfinite(self.features).all() or not np.isfinite(self.outcomes).all():raise ValueError('Nonfinitebook')
        self.check_prefix_causality()
    def check_prefix_causality(self):
        for stage in range(3):
            suffix=7**(3-stage)
            for start in range(0,343,suffix):
                a=self.available[:,stage,start:start+suffix]
                f=self.features[:,stage,start:start+suffix]
                if np.any(a!=a[:,:1]) or not np.allclose(f,f[:,:1],rtol=0,atol=1e-10):raise ValueError('Observableprefixdependsunexecutedfutureaction')
    def cases(self,worlds,stage):
        w=np.repeat(np.asarray(worlds),7**stage);ix=np.tile(np.arange(0,343,7**(3-stage)),len(worlds))
        legal=self.available[w,stage-1,ix].copy()
        for previous in range(stage-1):
            doses=PLANS[ix,previous];seen=self.available[w,previous,ix];cumulative=self.features[w,previous,ix,3]
            legal&=(seen| (doses==0))&((~seen)|(cumulative+doses<=220+1e-8))
        legal&=self.features[w,stage-1,ix,3]+PLANS[ix,stage-1]<=220+1e-8
        return w[legal],ix[legal]
    def candidate_inputs(self,w,ix,stage):
        base=self.features[w,stage-1,ix];seen=self.available[w,stage-1,ix]
        x=np.concatenate([np.repeat(base[:,None,:],7,axis=1),np.broadcast_to(GRID,(len(w),7))[...,None]],axis=-1)
        legal=seen[:,None]&(base[:,3,None]+GRID<=220+1e-8)
        return x,legal

def load_train(root):
    root=Path(root);registry=json.loads((root/'reports/phase5/teacher-book-receipt-v2.json').read_text());keys=[];features=[];available=[];outcomes=[]
    for entry in sorted(registry['files'],key=lambda v:v['path']):
        p=root/entry['path']
        if hashlib.sha256(p.read_bytes()).hexdigest()!=entry['sha256']:raise ValueError('TeacherSHAchanged')
        rows={tuple(row['plan']):row for row in map(json.loads,p.read_text().splitlines())};first=rows[(0,0,0)]
        if len(rows)!=343 or first['role']!='Train' or not 1995<=first['harvest_year']<=2009:raise ValueError('TRAINonlybooksrequired')
        f=np.zeros((3,343,22));a=np.zeros((3,343),bool);y=[]
        for i,plan in enumerate(PLANS):
            row=rows[tuple(plan)]
            if row['status']!='completed':raise ValueError('Failedteacherrow')
            y.append(row['outcome'])
            for s,base in row['features'].items():f[int(s)-1,i]=base;a[int(s)-1,i]=True
        keys.append((first['region_id'],int(first['harvest_year']),first['climate']));features.append(f);available.append(a);outcomes.append(y)
    return DenseBooks(keys,features,available,outcomes)
