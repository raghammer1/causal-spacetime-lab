"""Independently verify the registered full Experiment 3 archive.

Usage: python scripts/audit_adversarial.py [path/to/full/archive]
The fixed-grid assertions intentionally reject smoke/reduced studies.
"""
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys
from time import perf_counter

import numpy as np

from causal_lab.adversarial_detectors import fit_model, score_detectors
from causal_lab.dimension import invert_ordering_fraction
from causal_lab.dimension_study import _scores as old_scores

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'docs/experiments/adversarial-geometry-v1'
DETECTORS='ABCDEF'
TARGETS=(.9,.95,.975)
EXACT={'total','antichain'}
POSITIVE={'genuine','rank_overlap'}
start=perf_counter()

def load_json(name):
    return json.loads((OUT/name).read_text())

def load_lines(name):
    with gzip.open(OUT/name,'rt') as stream:return [json.loads(line) for line in stream]

def canon(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')

def same(actual,expected,context):
    assert actual==expected, (context,actual,expected)

def close(actual,expected,context):
    if actual is None or expected is None:same(actual,expected,context)
    else:assert math.isclose(actual,expected,rel_tol=1e-13,abs_tol=2e-15),(context,actual,expected)

def wilson(k,n):
    if n==0:return None,None
    z=1.959963984540054
    p=k/n; den=1+z*z/n
    midpoint=(p+z*z/(2*n))/den
    width=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return (0. if k==0 else midpoint-width,1. if k==n else midpoint+width)

def class_label(value):
    return 'unclassified' if value is None or not 1.5<=value<=4.5 else str(min((2,3,4),key=lambda d:(abs(d-value),d)))

def key(row):return row['family'],row['dimension_label'],row['count']

def bootstrap_bounds(arrays,family,d,n,repeat,parameter):
    # Independent reconstruction of the registered hierarchical empirical law.
    payload=['adversarial-v1',metadata['config']['seed'],0,'bootstrap',family,d,n,repeat,parameter]
    seed=int(hashlib.sha256(json.dumps(payload,separators=(',',':'),ensure_ascii=True).encode('ascii')).hexdigest(),16)
    rng=np.random.Generator(np.random.PCG64(seed)); size=metadata['config']['bootstrap']; k=len(arrays)
    selected=rng.integers(k,size=(size,k)); simulated=np.zeros((size,k))
    for i,values in enumerate(arrays):
        possible,counts=np.unique(values,return_counts=True); mask=selected==i
        draws=rng.multinomial(len(values),counts/len(values),size=int(mask.sum()))
        simulated[mask]=draws@possible/len(values)
    return np.quantile(simulated.mean(axis=1),[.025,.975])

metadata=load_json('metadata.json')
raw=load_lines('raw.jsonl.gz'); searches=load_lines('searches.jsonl.gz'); paired=load_lines('paired.jsonl.gz')
models=load_json('models.json'); summary=load_json('summary.json'); examples=load_json('examples.json')
effects=load_json('search_effects.json'); advancement=load_json('advancement.json')
with (OUT/'classification.csv').open() as stream:
    classification=[{k:int(v) if k!='classification' and k!='family' else v for k,v in row.items()}
                    for row in csv.DictReader(stream)]
with (OUT/'rates.csv').open() as stream:rates=list(csv.DictReader(stream))
same(len(raw),52218,'recorded count'); same(len(searches),5400,'independent searches')
same(sum(row['evaluations'] for row in searches),345600,'candidate evaluations')
same(len(summary),1350,'summary count'); same(len(paired),3150,'paired count')
same(len(classification),900,'classification count'); same(len(effects),162,'stage comparison count')
same(len(rates),4050,'per-fit CSV rows')

sample_ids=[row['sample_id'] for row in raw]
same(len(set(sample_ids)),len(raw),'unique IDs across every split and fit')
by_id={row['sample_id']:row for row in raw}
splits=defaultdict(list); groups=defaultdict(lambda:defaultdict(list))
for row in raw:
    payload=['adversarial-v1',metadata['config']['seed'],row['fit'],row['phase'],row['family'],
             row['dimension_label'],row['count'],row['repeat'],row['parameter']]
    expected_id=hashlib.sha256(json.dumps(payload,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')).hexdigest()
    same(row['sample_id'],expected_id,'sample identity')
    splits[row['fit'],row['count'],row['phase']].append(row)
    if row['phase']=='test':groups[key(row)][row['fit']].append(row)
    n=row['count']; hist=row['interval_histogram']; relations=row['relations']; pairs=n*(n-1)//2
    same(len(hist),n-1,'histogram length'); same(sum(hist),relations,'relation histogram sum')
    same(hist[0],row['link_count'],'link abundance'); same(relations/pairs,row['ordering_fraction'],'ordering fraction')
    same(row['longest_chain']/n,row['chain_fraction'],'height fraction')
    abundance=[(pairs-relations)/pairs]+[sum(hist[lo:hi])/pairs for lo,hi in
                  ((0,1),(1,2),(2,3),(3,4),(4,8),(8,16),(16,32),(32,64),(64,len(hist)))]
    same(abundance,row['abundance_vector'],'ten abundance bins')
    if relations:
        close(hist[0]/relations,row['link_fraction'],'link fraction')
        mean=sum(k*number for k,number in enumerate(hist))/relations
        close(mean,row['interval_mean'],'mean interval')
        close(mean/max(n-2,1),row['interval_mean_fraction'],'normalized mean interval')
        close(sum(hist[4:])/relations,row['interval_ge4_fraction'],'interval >=4')
    else:
        for name in ('link_fraction','interval_mean','interval_mean_fraction','interval_ge4_fraction'):
            same(row[name],None,'undefined conditional feature')
    try:estimate=invert_ordering_fraction(relations/pairs); status='ok'
    except ValueError:estimate=None; status='out_of_domain'
    same(estimate,row['estimated_dimension'],'MM estimate'); same(status,row['estimate_status'],'MM status')
    same(class_label(estimate),row['classification'],'separate classification')

for fit in range(3):
    for n in (64,128,256):
        for phase,expected in (('calibration',300),('development',300),('validation',600),('test',4602)):
            same(len(splits[fit,n,phase]),expected,'partition size')
        rebuilt=fit_model(splits[fit,n,'calibration'],splits[fit,n,'validation'])
        stored=models[str(fit)][str(n)]
        same(rebuilt,{k:v for k,v in stored.items() if k!='adversary_parameters'},'model refit')
        for param in stored['adversary_parameters']:
            d=param['dimension']; donors=[r for r in splits[fit,n,'development'] if r['true_dimension']==d]
            q=sum(r['ordering_fraction'] for r in donors)/len(donors)*n*(n-1)/2/((n//2)*(n-n//2))
            close(q,param['raw_q'],'raw fitted bipartite q')
            close(min(1,max(0,q)),param['q'],'bounded fitted bipartite q')
            same(param['saturated'],q<0 or q>1,'saturation flag')

score_count=0
for row in raw:
    if row['phase']!='test':continue
    model=models[str(row['fit'])][str(row['count'])]
    replay=score_detectors({**row,'true_dimension':999,'dimension_label':-999,'family':'metadata poison'},model)
    same([replay[d]['score'] for d in DETECTORS],row['scores'],'all actual detector scores')
    same([replay[d]['candidate_dimension'] for d in DETECTORS],row['candidate_dimensions'],'candidate labels')
    old_a,old_d=old_scores(row,model)
    same(old_a,row['scores'][0],'historical A math');same(old_d,row['scores'][3],'historical D math')
    for target in TARGETS:
        expected=[replay[d]['score'] is not None and replay[d]['score']<=model['thresholds'][str(target)][d] for d in DETECTORS]
        same(expected,row['accepted'][str(target)],'six decisions at each target')
        score_count+=len(DETECTORS)
    same([d for d in DETECTORS if replay[d]['score'] is None],row['undefined_detectors'],'undefined bookkeeping')

for search in searches:
    donor=by_id[search['target_sample_id']]
    same((donor['phase'],donor['fit'],donor['count'],donor['true_dimension']),
         ('development',search['fit'],search['count'],search['dimension']),'donor isolation')
    payload=['adversarial-v1',metadata['config']['seed'],search['fit'],'test','search',search['dimension'],search['count'],search['repeat'],None]
    same(hashlib.sha256(json.dumps(payload,separators=(',',':'),ensure_ascii=True).encode('ascii')).hexdigest(),search['search_id'],'search identity')
search_rows=defaultdict(list)
for row in raw:
    if 'search_id' in row:search_rows[row['search_id']].append(row)
for search in searches:
    checkpoints=search_rows[search['search_id']]
    same({r['family'] for r in checkpoints},{'height_matched','multi_matched'},'paired checkpoints')
    same(len(checkpoints),2,'checkpoint count')
    for row in checkpoints:
        same(row['target_sample_id'],search['target_sample_id'],'checkpoint donor')
        same(row['longest_chain'],by_id[search['target_sample_id']]['longest_chain'],'exact protected height')

summary_index={}
for s in summary:
    g=groups[key(s)]; index=DETECTORS.index(s['detector']); actual_rates=[]
    summary_index[(*key(s),s['target'],s['detector'])]=s
    for f in s['per_fit']:
        rows=g[f['fit']]; accepts=sum(r['accepted'][str(s['target'])][index] for r in rows)
        same(f['n'],len(rows),'summary denominator');same(f['accepted'],accepts,'summary numerator')
        same(f['rate'],accepts/len(rows),'summary per-fit rate');actual_rates.append(f['rate'])
        lo,hi=(None,None) if s['family'] in EXACT else wilson(accepts,len(rows))
        close(f['wilson_low'],lo,'independent Wilson low');close(f['wilson_high'],hi,'independent Wilson high')
        unclassified=next(r for r in s['accepted_unclassified_per_fit'] if r['fit']==f['fit'])
        same(unclassified['count'],sum(r['classification']=='unclassified' and r['accepted'][str(s['target'])][index] for r in rows),'accepted unclassified')
    close(s['mean_acceptance'],np.mean(actual_rates),'equal-fit rate')
    close(s['between_fit_sd'],np.std(actual_rates,ddof=1),'between-fit SD')
    same(s['min_acceptance'],min(actual_rates),'fit minimum');same(s['max_acceptance'],max(actual_rates),'fit maximum')
    assert 'wilson_low' not in s and 'wilson_high' not in s,'no pooled binomial interval'
    arrays=[np.array([r['accepted'][str(s['target'])][index] for r in g[fit]],dtype=float) for fit in sorted(g)]
    lo,hi=bootstrap_bounds(arrays,s['family'],s['dimension_label'],s['count'],index,str(s['target']))
    same(s['hierarchical_ci_low'],float(lo),'hierarchical summary lower bound')
    same(s['hierarchical_ci_high'],float(hi),'hierarchical summary upper bound')

for row in rates:
    s=summary_index[row['family'],int(row['dimension_label']),int(row['count']),float(row['target']),row['detector']]
    f=next(f for f in s['per_fit'] if f['fit']==int(row['fit']))
    for name in ('n','accepted'):same(int(row[name]),f[name],'rates CSV integer')
    for name in ('rate','wilson_low','wilson_high'):
        close(float(row[name]) if row[name] else None,f[name],'rates CSV float')
    fr=1-f['rate'] if s['family'] in POSITIVE else None
    fa=f['rate'] if s['family'] not in POSITIVE|{'box'} else None
    close(float(row['false_rejection']) if row['false_rejection'] else None,fr,'false rejection')
    close(float(row['false_acceptance']) if row['false_acceptance'] else None,fa,'false acceptance')

def audit_pair(p, left_group, right_group, left_detector, right_detector, search_pair=False):
    mean=[]; arrays=[]
    for f in p['per_fit']:
        left=left_group[f['fit']];right=right_group[f['fit']]
        if search_pair:
            by_search={r['search_id']:r for r in right};right=[by_search[r['search_id']] for r in left]
        else:same([r['sample_id'] for r in left],[r['sample_id'] for r in right],'paired identical orders')
        a=[r['accepted'][str(p['target'])][left_detector] for r in left]
        b=[r['accepted'][str(p['target'])][right_detector] for r in right]
        cells=[sum(x and y for x,y in zip(a,b)),sum(x and not y for x,y in zip(a,b)),
               sum(not x and y for x,y in zip(a,b)),sum(not x and not y for x,y in zip(a,b))]
        same(cells,[f[k] for k in ('both_accepted','left_only','right_only','both_rejected')],'paired contingency')
        same(f['n'],len(a),'paired denominator')
        close(f['mean_difference'],(cells[1]-cells[2])/len(a),'paired fit difference')
        mean.append(f['mean_difference'])
        arrays.append(np.array(a,dtype=float)-np.array(b,dtype=float))
    close(p['mean_difference'],np.mean(mean),'paired equal-fit difference')
    if search_pair:
        lo,hi=bootstrap_bounds(arrays,'search_effect',p['dimension_label'],p['count'],left_detector,str(p['target']))
    else:
        lo,hi=bootstrap_bounds(arrays,p['family'],p['dimension_label'],p['count'],0,f"{p['target']}:{p['left']}:{p['right']}")
    same(p['ci_low'],float(lo),'hierarchical paired lower bound')
    same(p['ci_high'],float(hi),'hierarchical paired upper bound')

for p in paired:
    audit_pair(p,groups[key(p)],groups[key(p)],DETECTORS.index(p['left']),DETECTORS.index(p['right']))
for p in effects:
    left=groups['height_matched',p['dimension_label'],p['count']]
    right=groups['multi_matched',p['dimension_label'],p['count']]
    audit_pair(p,left,right,DETECTORS.index(p['detector']),DETECTORS.index(p['detector']),True)
for row in classification:
    rows=groups[key(row)][row['fit']]
    same(row['orders'],sum(r['classification']==row['classification'] for r in rows),'classification count')
    same(row['out_of_domain'],sum(r['classification']==row['classification'] and r['estimate_status']!='ok' for r in rows),'out-of-domain count')

# Independently classify every advancement cell from interval endpoints.
for detector,decision in advancement['primary'].items():
    states=[]
    for cell in decision['cells']:
        s=summary_index[(*key(cell),.95,detector)]
        if cell['family'] in EXACT:state='supported' if s['max_acceptance']==0 else 'failed'
        elif cell['family'] in POSITIVE:
            state='supported' if all(f['wilson_low']>=.9 for f in s['per_fit']) else 'failed' if any(f['wilson_high']<.9 for f in s['per_fit']) else 'inconclusive'
        else:
            state='supported' if all(f['wilson_high']<=.05 for f in s['per_fit']) else 'failed' if any(f['wilson_low']>.05 for f in s['per_fit']) else 'inconclusive'
        same(cell['status'],state,'cell advancement');states.append(state)
    aggregate='supported' if all(s=='supported' for s in states) else 'failed' if 'failed' in states else 'inconclusive'
    same(decision['status'],aggregate,'detector advancement')

# Scientific digest reconstruction uses archive contents, not the package digest helper.
digest=hashlib.sha256()
config={k:v for k,v in metadata['config'].items() if k!='workers'}
content=dict(config=config,raw=raw,searches=searches,models=models,examples=examples,summary=summary,
             paired=paired,classification=classification,search_effects=effects,advancement=advancement)
for name in ('config','raw','searches','models','examples','summary','paired','classification','search_effects','advancement'):
    digest.update(name.encode('ascii')+b'\n'); value=content[name]
    if isinstance(value,list):
        for row in value:digest.update(canon(row)+b'\n')
    else:digest.update(canon(value)+b'\n')
same(digest.hexdigest(),metadata['scientific_sha256'],'independently reconstructed scientific digest')
for name,expected in metadata['source_sha256'].items():
    same(hashlib.sha256((ROOT/'src/causal_lab'/name).read_bytes()).hexdigest(),expected,'source hash '+name)
same(hashlib.sha256((ROOT/'docs/ADVERSARIAL_GEOMETRY_PROTOCOL.md').read_bytes()).hexdigest(),metadata['protocol_sha256'],'protocol hash')
for name,expected in metadata['artifact_sha256'].items():
    same(hashlib.sha256((OUT/name).read_bytes()).hexdigest(),expected,'artifact hash '+name)

primary=[s for s in summary if s['target']==.95]
compact=[]
for detector in DETECTORS:
    genuine=[s for s in primary if s['detector']==detector and s['family']=='genuine']
    negative=[s for s in primary if s['detector']==detector and s['family'] not in POSITIVE|{'box'}]
    compact.append(dict(detector=detector,status=advancement['primary'][detector]['status'],
                        genuine_fit_min=min(f['rate'] for s in genuine for f in s['per_fit']),
                        genuine_fit_max=max(f['rate'] for s in genuine for f in s['per_fit']),
                        worst_negative_mean=max(s['mean_acceptance'] for s in negative),
                        genuine_supported=sum(s['all_lower_at_least_0_90'] for s in genuine),
                        cell_statuses=dict(Counter(c['status'] for c in advancement['primary'][detector]['cells']))))
family_table=[]
for family,d,n in sorted(groups):
    family_table.append(dict(family=family,dimension=d,count=n,
                            means={name:summary_index[family,d,n,.95,name]['mean_acceptance'] for name in DETECTORS},
                            fit_ranges={name:[summary_index[family,d,n,.95,name]['min_acceptance'],summary_index[family,d,n,.95,name]['max_acceptance']] for name in DETECTORS}))
report=dict(status='passed',recorded_orders=len(raw),decisions_replayed=score_count,
            independent_searches=len(searches),models_refit=9,summary_cells_checked=len(summary),
            paired_tables_checked=sum(len(p['per_fit']) for p in paired),stage_tables_checked=sum(len(p['per_fit']) for p in effects),
            scientific_sha256=digest.hexdigest(),elapsed_seconds=perf_counter()-start,
            detector_overview=compact,primary_family_table=family_table,
            local_gains=[p for p in advancement['paired_gains'] if p['meaningful_local_gain']],
            supported_regressions=[p for p in advancement['paired_gains'] if p['supported_adverse_regression']])
destination=ROOT/'results/adversarial_primary_independent_audit.json'
destination.parent.mkdir(parents=True,exist_ok=True)
destination.write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('primary_family_table','local_gains','supported_regressions')},indent=2))
print('Local meaningful gains:',len(report['local_gains']),'supported regressions:',len(report['supported_regressions']))
print('Full audit report:',destination)
