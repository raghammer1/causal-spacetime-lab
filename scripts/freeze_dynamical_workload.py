"""Resource-only A2: conservative reuse of complete pilots, fresh N6 censor."""
import argparse
import json
from pathlib import Path
import signal
import time
import numpy as np
from causal_lab.dynamical_study import bundle,source_metadata,write_json,peak_bytes,PLANNING_BUDGET_SECONDS
from causal_lab.dynamical_graphs import GraphCatalog


def combine(records):
    maxima={};fixed={}
    for n in (4,5):
        for record in records:
            cases={(x['cell'],x['preparation']) for x in record['measurements'] if x['N']==n and not x.get('censored',False)}
            expected={(c,p) for c in range(6) for p in ('Splus','Sempty','E')}
            if cases!=expected or not all(x.get('valid',True) for x in record['measurements'] if x['N']==n):
                raise ValueError('incomplete or numerically invalid pilot')
        maxima[n]=max(record['maxima'][str(n)] for record in records)
        fixed[n]=max(record['fixed_seconds'][str(n)] for record in records)
    overhead=max(r.get('postprocessing_seconds_largest_candidate',0.) for r in records)
    choices=[dict(repeats_per_batch=r,mandatory_projection_seconds=2*(sum(maxima[n]*6*(3*r+2)+fixed[n] for n in (4,5))+overhead)) for r in (12,8,4)]
    feasible=[r for r in choices if r['mandatory_projection_seconds']<=PLANNING_BUDGET_SECONDS]
    if not feasible:raise RuntimeError('minimum complete cohort infeasible under final A2 limit')
    return maxima,fixed,overhead,choices,feasible[0]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    files=[root/f'docs/experiments/dynamical-locality-pilot-attempt{k}.json' for k in (1,2,3)]
    records=[json.loads(p.read_text()) for p in files]
    maxima,fixed,overhead,choices,selected=combine(records)
    source=source_metadata();catalog=GraphCatalog(6)
    limit=PLANNING_BUDGET_SECONDS/(2*84)+.05
    def timeout(signum,frame):raise TimeoutError('censored N6 feasibility lower bound')
    old=signal.signal(signal.SIGALRM,timeout);tick=time.monotonic();censored=False
    try:
        signal.setitimer(signal.ITIMER_REAL,limit)
        bundle(6,0,'Splus','pilot',0,0,catalog,checkpoint=True)
    except TimeoutError:
        censored=True
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,old)
    elapsed=time.monotonic()-tick
    # A completed early pilot is not sufficient for admission, and there is no partial primary cohort.
    reason='censored lower-bound projection exceeds planning limit' if censored else 'not admitted: complete optional-size feasibility cohort unavailable'
    if source['sha256']!=source_metadata()['sha256']:raise RuntimeError('source changed during final resource check')
    if peak_bytes()>2*1024**3:raise RuntimeError('resource check memory cap exceeded')
    result=dict(sizes=[4,5],repeats_per_batch=selected['repeats_per_batch'],source=source,
        resource_amendment='A2',prior_pilots=[p.name for p in files],max_bundle_seconds=maxima,
        fixed_seconds=fixed,postprocessing_seconds_largest_candidate=overhead,choices=choices,
        projected_seconds=selected['mandatory_projection_seconds'],primary_budget_seconds=PLANNING_BUDGET_SECONDS,
        safety_factor=2.,hard_cap_seconds=2700,peak_rss_bytes=peak_bytes(),
        N6=dict(admitted=False,reason=reason,censored=censored,elapsed_lower_bound_seconds=elapsed,
            censor_seconds=limit,minimum_cohort_bundle_count=84,projection_lower_bound_seconds=2*84*elapsed),
        selection_uses='worst complete-pilot timing and memory only; no primary outcomes existed')
    write_json(args.output,result)
    print(json.dumps({k:result[k] for k in ('sizes','repeats_per_batch','projected_seconds','N6')}),flush=True)

if __name__=='__main__':main()
