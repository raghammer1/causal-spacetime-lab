#!/usr/bin/env python3
"""Secondary graph-conditioned response summaries; never changes the registered decision.

Uses only archived, independently audited frozen-graph probe arrays. These controls
reset matter to the fixed tilted product, freeze the measured graph, and distinguish
an accessible graph record from an unobserved mixture. No new quantum run or fit.
"""
from __future__ import annotations
import argparse
from collections import defaultdict,deque
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import numpy as np

TOL=1e-10


def concentration(matrix):
    """Registered fractional-top-two convention, independently implemented."""
    n=len(matrix);fractions=[];totals=[]
    for source in range(n):
        values=np.delete(np.asarray(matrix[source],float),source)
        total=float(values.sum());totals.append(total)
        if total<=TOL:fractions.append(np.nan);continue
        second=sorted(values,reverse=True)[1]
        strict=values>second+TOL;tied=np.abs(values-second)<=TOL
        leftover=2-int(strict.sum())
        kept=float(values[strict].sum()+leftover*values[tied].mean())
        fractions.append(kept/total)
    valid=bool(np.all(np.isfinite(fractions)))
    return (float(np.mean(fractions)) if valid else None),np.asarray(totals)


def graphs(n):
    edges=list(combinations(range(n),2));G=1<<len(edges)
    bits=np.array([[int(ch) for ch in f'{g:0{len(edges)}b}'] for g in range(G)],int)
    degrees=np.zeros((G,n),int);connected=np.zeros(G,bool)
    classes=defaultdict(list)
    for g,mask in enumerate(bits):
        neighbors=[set() for _ in range(n)]
        for value,(i,j) in zip(mask,edges):
            if value:degrees[g,i]+=1;degrees[g,j]+=1;neighbors[i].add(j);neighbors[j].add(i)
        seen={0};queue=deque([0])
        while queue:
            for target in neighbors[queue.popleft()]-seen:seen.add(target);queue.append(target)
        connected[g]=len(seen)==n;classes[tuple(degrees[g])].append(g)
    return bits,connected,list(classes.values())


def laws(probability,bits,degree_classes):
    p=np.asarray(probability,float);p=p/p.sum()
    density=float(sum(p@bits)/bits.shape[1])
    edgecount=bits.sum(1)
    qdensity=density**edgecount*(1-density)**(bits.shape[1]-edgecount)
    qdegree=np.empty_like(p)
    for group in degree_classes:qdegree[group]=sum(p[group])/len(group)
    return dict(Born=p,density=qdensity,degree=qdegree)


def aggregate(units):
    groups=defaultdict(list)
    for unit in units:groups[(unit['N'],unit['cell'],unit['preparation'],unit['law'],unit['delay'])].append(unit)
    output=[]
    names=['valid_graph_F_probability','undefined_graph_F_probability','zero_total_response_probability',
           'partial_zero_source_probability','mean_graph_conditioned_F_given_valid','F_of_average_conditional_response',
           'F_of_unobserved_mixture_response','connected_probability','valid_and_connected_probability']
    for (n,cell,prep,law,delay),rows in sorted(groups.items()):
        result=dict(N=n,cell=cell,preparation=prep,law=law,delay=delay,preparation_units=len(rows),metrics={})
        for name in names:
            values=[r[name] for r in rows if r[name] is not None]
            result['metrics'][name]=dict(mean=float(np.mean(values)) if values else None,
                minimum=min(values) if values else None,maximum=max(values) if values else None,
                sd=float(np.std(values,ddof=1)) if len(values)>1 else None,
                defined_units=len(values),undefined_units=len(rows)-len(values))
        valid_mass=sum(r['valid_graph_F_probability'] for r in rows)
        numerator=sum(r['graph_F_mass_weighted_sum'] for r in rows)
        result['pooled_graph_conditioned_F_given_valid']=numerator/valid_mass if valid_mass else None
        output.append(result)
    return output


def calculate(root):
    root=Path(root);manifest=json.loads((root/'manifest.json').read_text())
    for name,expected in manifest['sha256'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts:raise ValueError('external archive path')
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:raise ValueError('archive hash mismatch: '+name)
    digest=hashlib.sha256()
    for name in manifest['scientific_files']:
        if name not in manifest['sha256']:raise ValueError('unlisted scientific artifact')
        digest.update(name.encode());digest.update((root/name).read_bytes())
    if digest.hexdigest()!=manifest['scientific_digest']:raise ValueError('scientific digest mismatch')
    rows=json.loads(gzip.decompress((root/'raw.json.gz').read_bytes()))
    unitrows=[];validation=[];cache={};maximum_convexity_error=0.
    for n in sorted({r['N'] for r in rows}):
        bits,connected,groups=graphs(n)
        static=np.load(root/'arrays'/f'static_N{n}.npz',allow_pickle=False)
        delayed={}
        times=json.loads((root/'metadata.json').read_text())['delays']
        for delay in (.25,.5):
            t=times.index(delay);response=static['response'][:,t]
            scores=[];total_rows=[]
            for matrix in response:
                value,total=concentration(matrix);scores.append(np.nan if value is None else value);total_rows.append(total)
            scores=np.array(scores);total_rows=np.array(total_rows)
            delayed[delay]=dict(t=t,response=response,scores=scores,valid=np.isfinite(scores),
                all_zero=np.all(total_rows<=TOL,axis=1),any_zero=np.any(total_rows<=TOL,axis=1))
        cache[n]=(bits,connected,groups,static,delayed)
    for row in rows:
        if row['status']!='ok':raise ValueError('secondary summary cannot silently omit failed primary units')
        n=row['N'];bits,connected,groups,static,delayed=cache[n]
        a=np.load(root/row['array_file'],allow_pickle=False)
        for name,p in laws(a['full_born'][3],bits,groups).items():
            for delay,d in delayed.items():
                valid=d['valid'];valid_mass=float(sum(p[valid]));numerator=float(sum(p[valid]*d['scores'][valid]))
                conditional=np.einsum('g,gij->ij',p,d['response'])
                baseline=np.einsum('g,gic->ic',p,static['baseline_bloch'][:,d['t']])
                probe=np.einsum('g,gsic->sic',p,static['probe_bloch'][:,d['t']])
                mixture=np.linalg.norm(probe-baseline[None,:,:],axis=-1)/2;np.fill_diagonal(mixture,0)
                f_cond,_=concentration(conditional);f_mix,_=concentration(mixture)
                maximum_convexity_error=max(maximum_convexity_error,float(np.max(mixture-conditional)))
                unitrows.append(dict(N=n,cell=row['cell'],preparation=row['preparation'],batch=row['batch'],
                    replicate=row['replicate'],law=name,delay=delay,
                    valid_graph_F_probability=valid_mass,undefined_graph_F_probability=1-valid_mass,
                    zero_total_response_probability=float(sum(p[d['all_zero']])),
                    partial_zero_source_probability=float(sum(p[d['any_zero']&~d['all_zero']])),
                    mean_graph_conditioned_F_given_valid=numerator/valid_mass if valid_mass else None,
                    graph_F_mass_weighted_sum=numerator,F_of_average_conditional_response=f_cond,
                    F_of_unobserved_mixture_response=f_mix,connected_probability=float(sum(p[connected])),
                    valid_and_connected_probability=float(sum(p[valid&connected]))))
    if maximum_convexity_error>2e-8:raise ArithmeticError('trace-distance convexity failed')
    return dict(status='SECONDARY DESCRIPTIVE; does not alter the registered decision',
        source_scientific_digest=manifest['scientific_digest'],
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        protocol='Age2 Born law or exact density/degree null; fresh tilted matter; frozen graph TFIM h=g=1; Pauli-Y probe',
        definitions=dict(valid_graph_F='Every source has nonzero total off-diagonal response above1e-10; undefined source rows are not omitted',
            zero_total_response='All source rows have total off-diagonal response at most1e-10',
            partial_zero_source='At least one but not every source row has zero response; whole-graph F remains undefined',
            graph_conditioned_F='Compute F separately within each known graph, then average over valid graphs; validity mass reported',
            averaged_conditional_F='Take F of the graph-weighted mean target trace-distance matrix; differs from average graph-conditioned F',
            unobserved_mixture_F='Average target density matrices first, then take target trace distances and F',
            E_aggregation='Unweighted means/ranges of independent preparation-level quantities; pooled ratio also reported; no confidence claims',
            connectivity='Reported mass, never a selection filter; disconnected graphs can have a high conditioned F',
            limits='Graph-adapted target choice is a different conditional protocol from the primary unconditioned labeled assay; these are supplied static controls'),
        maximum_trace_distance_convexity_error=maximum_convexity_error,
        preparation_records=len(rows),stochastic_E_preparation_records=sum(r['preparation']=='E' for r in rows),
        deterministic_symmetric_preparation_records=sum(r['preparation']!='E' for r in rows),secondary_unit_rows=len(unitrows),aggregates=aggregate(unitrows),units=unitrows)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('archive',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=calculate(args.archive)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','preparation_records','stochastic_E_preparation_records','deterministic_symmetric_preparation_records','secondary_unit_rows','maximum_trace_distance_convexity_error')}))

if __name__=='__main__':main()
