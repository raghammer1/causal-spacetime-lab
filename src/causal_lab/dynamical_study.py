"""Frozen Experiment 7: exact quantum links, operational interventions and controls."""
from __future__ import annotations
import argparse
from dataclasses import asdict, replace
import hashlib
import gzip
import io
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import signal
import tempfile
import time
import numpy as np
import scipy
from scipy.linalg import eigh
from .dynamical_core import (Parameters,build_hamiltonian,product_state,evolve_state,
    evolve_trajectory,born_probabilities,matter_bloch,response_trajectories,
    direct_response_slopes,ground_state,state_diagnostics)
from .dynamical_graphs import GraphCatalog,FrozenGraphResponse,static_controls,classical_degree_two_degeneracy,degree_connectivity_identifiability
from .dynamical_statistics import assess_unit,summarize,calibrate_cp,top_two

AGES=(0.,.5,1.,2.,3.,4.)
DELAYS=(0.,.05,.1,.25,.5,1.,2.)
CELLS=tuple((mu,gamma) for mu in (2.,.1,-2.) for gamma in (.25,1.))
STREAMS={'smoke':1,'calibration':2,'pilot':3,'primary':4,'audit':5}
PROTOCOL_COMMIT='5b71924'
BASELINE_COMMIT='73baea299fb07d608bade8364d6cf66443e23166'
PLANNING_BUDGET_SECONDS=1800.  # Resource-only amendment A1 before primary data.


def plain(x):
    if isinstance(x,np.ndarray):
        if np.iscomplexobj(x):return {'real':plain(x.real),'imag':plain(x.imag)}
        return plain(x.tolist())
    if isinstance(x,(np.integer,np.floating,np.bool_)):return plain(x.item())
    if isinstance(x,float) and not np.isfinite(x):return None
    if isinstance(x,dict):return {str(k):plain(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)):return [plain(v) for v in x]
    return x


def write_json(path,obj):
    Path(path).write_text(json.dumps(plain(obj),sort_keys=True,indent=2,allow_nan=False)+'\n')


def rng_for(stream,n,cell,batch,rep,purpose):
    return np.random.default_rng(np.random.SeedSequence([20261025,7,STREAMS[stream],n,cell,batch,rep,purpose]))


def initial_factors(n,preparation,rng):
    m=n*(n-1)//2
    if preparation=='E':return rng.uniform(.25,.75,m),rng.uniform(0,2*np.pi,m)
    if preparation=='Splus':return np.full(m,.5),np.zeros(m)
    if preparation=='Sempty':return np.zeros(m),np.zeros(m)
    raise ValueError('unknown preparation')


def parameters(n,cell):
    mu,gamma=CELLS[cell]
    return Parameters(N=n,h=1.,g=1.,Gamma=gamma,mu=mu,U=1.)


def peak_bytes():
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(rss if sys.platform=='darwin' else rss*1024)


def source_metadata():
    root=Path(__file__).resolve().parents[2]
    paths=sorted((root/'src/causal_lab').glob('dynamical_*.py'))
    paths += [root/'docs/DYNAMICAL_LOCALITY_PROTOCOL.md',root/'docs/DYNAMICAL_LOCALITY_THEORY.md',root/'docs/DYNAMICAL_LOCALITY_COMPUTATIONAL_PLAN.md']
    hashes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    return dict(commit=rev,sha256=hashes,protocol_commit=PROTOCOL_COMMIT,baseline_commit=BASELINE_COMMIT,
        python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,platform=platform.system(),
        machine=platform.machine(),threads={k:os.getenv(k) for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS']})


def require_clean():
    root=Path(__file__).resolve().parents[2]
    dirty=subprocess.check_output(['git','status','--porcelain','--untracked-files=normal'],cwd=root,text=True)
    if dirty.strip():raise RuntimeError('primary requires a clean committed source tree')


def _response_arrays(prefix,result,arrays):
    for key in ('baseline_bloch','probe_bloch','response','global_source_distance'):
        arrays[f'{prefix}_{key}']=result[key]


def bundle(n,cell,preparation,stream,batch,rep,catalog,models=None,checkpoint=False):
    params=parameters(n,cell)
    if models is None:
        models={name:build_hamiltonian(p) for name,p in (
            ('full',params),('perturbed',replace(params,Gamma=1.05*params.Gamma)),
            ('frozen',replace(params,Gamma=0.)))}
    p,phase=initial_factors(n,preparation,rng_for(stream,n,cell,batch,rep,1))
    psi=product_state(n,np.pi/4,p,phase)
    arrays={'initial_link_probabilities':p,'initial_link_phases':phase,'ages':np.array(AGES),
            'delays':np.array(DELAYS)}
    diagnostics={};aged={}
    for name in ('full','perturbed'):
        born=[];checks=[]
        for item in evolve_trajectory(models[name],psi,AGES):
            born.append(born_probabilities(item['state'],n))
            checks.append({k:v for k,v in item.items() if k!='state'})
            if item['time']==2.:aged[name]=item['state'].copy()
        arrays[f'{name}_born']=np.array(born);diagnostics[f'{name}_structure']=checks
    aged['initial_frozen']=evolve_state(models['frozen'],psi,2.)
    arrays['initial_frozen_born']=born_probabilities(aged['initial_frozen'],n)
    diagnostics['initial_frozen_age']=state_diagnostics(models['frozen'],aged['initial_frozen'],state_diagnostics(models['frozen'],psi))
    for name,model,state in (
        ('full',models['full'],aged['full']),('perturbed',models['perturbed'],aged['perturbed']),
        ('initial_frozen',models['frozen'],aged['initial_frozen']),('probe_frozen',models['frozen'],aged['full'])):
        response=response_trajectories(model,state,DELAYS)
        _response_arrays(name,response,arrays)
        diagnostics[name+'_response']={**response['diagnostics'],'baseline':response['baseline_diagnostics'],'probes':response['probe_diagnostics']}
    slopes=direct_response_slopes(models['full'],aged['full'])
    arrays.update({'direct_'+k:v for k,v in slopes.items()})
    arrays['full_age2_bloch']=matter_bloch(aged['full'],n)
    if checkpoint:arrays['checkpoint_age2_state']=aged['full']
    born=arrays['full_born']; metrics=[]
    for age,law in zip(AGES,born):
        nulls=catalog.nulls(law)
        metrics.append(dict(age=age,observed=catalog.summarize(law),
            nulls={k:dict(properties={key:value for key,value in catalog.summarize(q).items() if key in
                ('connected_probability','expected_edge_count','expected_components','largest_component_fraction',
                 'expected_triangles','expected_clustering','connected_mean_diameter')},
                tv=float(.5*np.abs(law-q).sum())) for k,q in nulls.items()}))
    samples=np.array([rng_for(stream,n,cell,batch,rep,100+a).choice(len(law),size=8,p=law/law.sum()) for a,law in enumerate(born)])
    arrays['born_draws']=samples
    arrays['perturbed_born_draws']=np.array([rng_for(stream,n,cell,batch,rep,200+a).choice(len(law),size=8,p=law/law.sum())
        for a,law in enumerate(arrays['perturbed_born'])])
    gate=assess_unit(born,catalog.connected,arrays['full_response'],arrays['perturbed_response'],
        arrays['initial_frozen_response'],DELAYS)
    degree=metrics[3]['nulls']['degree']
    degree_event=degree['tv']>=.1 and metrics[3]['observed']['connected_probability']-degree['properties']['connected_probability']>=.1
    symmetry=None
    if preparation in ('Splus','Sempty'):
        off=~np.eye(n,dtype=bool)
        symmetry=dict(max_occupation_range=max(x['observed']['occupation_contrast'] for x in metrics),
            max_response_range=float(np.ptp(arrays['full_response'][:,off],axis=1).max()))
        symmetry['passed']=max(symmetry.values())<2e-8
    row=dict(N=n,cell=cell,preparation=preparation,batch=batch,replicate=rep,stream=stream,
        parameters=asdict(params),initial_matter_theta=float(np.pi/4),status='ok',gate=gate,
        diagnostics=diagnostics,structure=metrics,degree_null_event=bool(degree_event),symmetry=symmetry,
        age2_state_sha256=hashlib.sha256(aged['full'].tobytes()).hexdigest())
    # Numerical validity is a property of all branches, not a filter on favorable results.
    def valid(x):
        if isinstance(x,dict):return bool(x.get('valid',True)) and all(valid(v) for v in x.values())
        if isinstance(x,(list,tuple)):return all(valid(v) for v in x)
        return True
    if not valid(diagnostics) or (symmetry is not None and not symmetry['passed']):row['status']='failed';row['failure']='numerical tolerance'
    return row,arrays,aged['full']


def static_weighted(cache,law):
    out=cache.weighted(law)
    return {k:np.asarray(v) for k,v in out.items() if isinstance(v,(np.ndarray,list,tuple))}


def measurement_backaction(model,aged,n):
    matrix=aged.reshape(2**n,-1);law=np.sum(np.abs(matrix)**2,axis=0)
    future=np.zeros_like(law);checks=[]
    for graph,p in enumerate(law):
        if p==0:continue
        projected=np.zeros_like(matrix);projected[:,graph]=matrix[:,graph]/np.sqrt(p)
        reference=state_diagnostics(model,projected.ravel())
        state=evolve_state(model,projected.ravel(),1.)
        checks.append(state_diagnostics(model,state,reference))
        future+=p*born_probabilities(state,n)
    unmeasured=born_probabilities(evolve_state(model,aged,1.),n)
    return dict(measured_future_born=future,unmeasured_future_born=unmeasured,
        measurement_born=law,tv=float(.5*np.abs(future-unmeasured).sum()),diagnostics=checks)


def equilibrium(n,cell,catalog,stream):
    model=build_hamiltonian(parameters(n,cell))
    solved=ground_state(model,rng_for(stream,n,cell,0,0,3));state=solved.pop('state')
    response=response_trajectories(model,state,DELAYS)
    arrays={'ground_state':state,'ground_born':born_probabilities(state,n)}
    arrays['ground_born_draws']=catalog.sample(arrays['ground_born'],rng_for(stream,n,cell,0,0,400))
    _response_arrays('ground',response,arrays)
    row=dict(N=n,cell=cell,solver=solved,properties=catalog.summarize(arrays['ground_born']),
        response_diagnostics=response['diagnostics'],
        max_response_symmetry_error=float(np.ptp(response['response'][:,~np.eye(n,dtype=bool)],axis=1).max()),
        occupation_symmetry_error=float(catalog.summarize(arrays['ground_born'])['occupation_contrast']))
    if n==4:
        values,vectors=eigh(model.operator.toarray())
        arrays['thermal_eigenvalues']=values;rows=[]
        for beta in (.5,2.):
            weights=np.exp(-beta*(values-values[0]));weights/=weights.sum()
            diagonal=np.abs(vectors)**2@weights
            born=diagonal.reshape(2**n,-1).sum(0)
            arrays[f'thermal_born_beta{beta}']=born
            arrays[f'thermal_born_draws_beta{beta}']=catalog.sample(born,rng_for(stream,n,cell,0,0,401+int(beta)))
            rows.append(dict(beta=beta,energy=float(values@weights),
                entropy_nats=float(-np.sum(weights[weights>0]*np.log(weights[weights>0]))),
                properties=catalog.summarize(born)))
        row['thermal']=rows;row['dense_ground_difference']=float(abs(values[0]-solved['energy']))
    row['passed']=solved['valid'] and max(row['max_response_symmetry_error'],row['occupation_symmetry_error'],
        row.get('dense_ground_difference',0.))<2e-8
    return row,arrays


def independent_control(n,cell,preparation,catalog,stream):
    params=replace(parameters(n,cell),g=0.,U=0.)
    model=build_hamiltonian(params)
    p,phase=initial_factors(n,preparation,rng_for(stream,n,cell,0,0,31))
    psi=product_state(n,np.pi/4,p,phase)
    states=list(evolve_trajectory(model,psi,AGES));born=np.array([born_probabilities(x['state'],n) for x in states])
    aged=states[3]['state'];resp=response_trajectories(model,aged,DELAYS)
    arrays=dict(born=born,initial_link_probabilities=p,initial_link_phases=phase)
    _response_arrays('independent',resp,arrays)
    maximum=float(np.max(resp['response'][:,~np.eye(n,dtype=bool)]))
    tv=max(float(.5*np.abs(law-catalog.nulls(law)['product']).sum()) for law in born)
    return dict(N=n,cell=cell,preparation=preparation,maximum_cross_response=maximum,
                maximum_product_tv=tv,passed=maximum<2e-8 and tv<2e-8,
                diagnostics=resp['diagnostics']),arrays


def validate_static(catalog,cache,stream):
    controls=static_controls(catalog);n=catalog.n
    permutation=rng_for(stream,n,0,0,0,77).permutation(n)
    graph=catalog.permute_index(controls['chain'],permutation)
    distance=catalog.distance[graph];response=cache.response[graph]
    off=~np.eye(n,dtype=bool)
    complete=cache.response[controls['complete']][:,off]
    matching=controls['matching'];unreachable=catalog.distance[matching]<0
    means=[float(response[2][distance==d].mean()) for d in range(1,n)]
    no_signal=max(float(response[0][off].max()),float(cache.response[matching][:,unreachable].max()))
    uniform_error=float(np.ptp(complete,axis=1).max())
    passed=no_signal<2e-8 and uniform_error<2e-8 and all(a>b for a,b in zip(means,means[1:])) and means[0]>.01
    return dict(N=n,chain_permutation=permutation,chain_graph_index=graph,
        chain_mean_responses_at_delay_point1_by_distance=means,
        maximum_no_signalling_error=no_signal,maximum_complete_response_range=uniform_error,
        disconnected_connectivity=bool(catalog.connected[matching]),passed=passed,
        control_graphs=controls,interpretation='locality and graph distance supplied by static controls')


def write_raw(path,rows):
    with Path(path).open('wb') as raw:
        with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as compressed:
            compressed.write(json.dumps(plain(rows),sort_keys=True,separators=(',',':'),allow_nan=False).encode())


def write_npz(path,arrays):
    np.savez_compressed(path,**arrays)


def catalog_arrays(catalog):
    return {k:v for k,v in vars(catalog).items() if isinstance(v,np.ndarray)}


def archive_manifest(out):
    out=Path(out)
    files={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(out.rglob('*')) if p.is_file() and p.name!='manifest.json'}
    scientific=[name for name in files if name not in ('metadata.json','timing.json')]
    digest=hashlib.sha256()
    for name in scientific:digest.update(name.encode());digest.update((out/name).read_bytes())
    manifest=dict(sha256=files,scientific_files=scientific,scientific_digest=digest.hexdigest())
    write_json(out/'manifest.json',manifest);return manifest


def verify_manifest(out):
    out=Path(out);manifest=json.loads((out/'manifest.json').read_text());digest=hashlib.sha256()
    for name,value in manifest['sha256'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts:raise ValueError('external artifact path')
        if hashlib.sha256((out/name).read_bytes()).hexdigest()!=value:raise ValueError(f'hash mismatch: {name}')
    for name in manifest['scientific_files']:
        if name not in manifest['sha256'] or Path(name).is_absolute() or '..' in Path(name).parts:raise ValueError('external scientific path')
        digest.update(name.encode());digest.update((out/name).read_bytes())
    if digest.hexdigest()!=manifest['scientific_digest']:raise ValueError('scientific digest mismatch')
    return digest.hexdigest()


def run(out,mode='smoke',sizes=(4,5),repeats=4,cells=range(6),freeze=None):
    out=Path(out)
    if out.exists() and any(out.iterdir()):raise ValueError('output directory must be new or empty')
    out.mkdir(parents=True,exist_ok=True);(out/'arrays').mkdir()
    if mode=='primary':
        require_clean()
        if freeze is None:raise ValueError('primary needs the committed pilot freeze')
        root=Path(__file__).resolve().parents[2]
        relative_freeze=Path(freeze).resolve().relative_to(root)
        subprocess.run(['git','ls-files','--error-unmatch',str(relative_freeze)],cwd=root,check=True,capture_output=True)
        frozen=json.loads(Path(freeze).read_text())
        sizes=tuple(frozen['sizes']);repeats=frozen['repeats_per_batch'];cells=range(6)
        if source_metadata()['sha256']!=frozen['source']['sha256']:
            raise RuntimeError('source differs from the committed timing freeze')
        if any(os.getenv(k)!='1' for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS')):
            raise RuntimeError('primary requires the registered single-thread environment')
    start=time.monotonic();rows=[];eqrows=[];indrows=[];timings=[];failures=[];staticrows=[]
    meta=source_metadata();meta.update(mode=mode,sizes=sizes,cells=list(cells),repeats_per_batch=repeats,
        ages=AGES,delays=DELAYS,seed_entropy_prefix=[20261025,7],streams=STREAMS,
        freeze_sha256=hashlib.sha256(Path(freeze).read_bytes()).hexdigest() if freeze else None)
    write_json(out/'metadata.json',meta)
    calibration=calibrate_cp(rng_for('calibration',0,0,0,0,0));write_json(out/'calibration.json',calibration)
    for n in sizes:
        catalog=GraphCatalog(n);write_npz(out/'arrays'/f'catalog_N{n}.npz',catalog_arrays(catalog))
        cache=FrozenGraphResponse(catalog,times=DELAYS)
        staticrows.append(validate_static(catalog,cache,mode))
        write_npz(out/'arrays'/f'static_N{n}.npz',dict(baseline_bloch=cache.baseline_bloch,
            probe_bloch=cache.probe_bloch,response=cache.response,norm_error=cache.norm_error,
            energy_drift=cache.energy_drift,parity_drift=cache.parity_drift,initial_energy=cache.initial_energy,initial_parity=cache.initial_parity))
        for cell in cells:
            params=parameters(n,cell)
            models={name:build_hamiltonian(p) for name,p in (
                ('full',params),('perturbed',replace(params,Gamma=1.05*params.Gamma)),
                ('frozen',replace(params,Gamma=0.)))}
            e,a=equilibrium(n,cell,catalog,mode);eqrows.append(e)
            write_npz(out/'arrays'/f'equilibrium_N{n}_c{cell}.npz',a)
            for preparation in ('Splus','Sempty','E'):
                row,a=independent_control(n,cell,preparation,catalog,mode);indrows.append(row)
                write_npz(out/'arrays'/f'independent_N{n}_c{cell}_{preparation}.npz',a)
            units=[('Splus',0,0),('Sempty',0,0)]+[('E',b,r) for b in range(3) for r in range(repeats)]
            if mode=='smoke':units=[('Splus',0,0),('Sempty',0,0),('E',0,0)]
            for prep,batch,rep in units:
                tick=time.monotonic();uid=f'N{n}_c{cell}_{prep}_b{batch}_r{rep}'
                try:
                    row,a,aged=bundle(n,cell,prep,mode,batch,rep,catalog,models,checkpoint=prep!='E' or rep==0)
                    law=a['full_born'][3]
                    for name,p in {'born':law,**catalog.nulls(law)}.items():
                        for key,value in static_weighted(cache,p).items():a[f'static_{name}_{key}']=value
                    from .dynamical_diagnostics import analyze
                    row['additional_diagnostics']=analyze(a,catalog)
                    if n==4 and prep=='E' and batch==rep==0:
                        back=measurement_backaction(models['full'],aged,n)
                        row['nonselective_measurement_tv']=back.pop('tv')
                        row['measurement_branch_diagnostics']=back.pop('diagnostics')
                        a.update({'measurement_'+k:v for k,v in back.items()})
                    write_npz(out/'arrays'/f'{uid}.npz',a)
                    row['array_file']=f'arrays/{uid}.npz';rows.append(row)
                except Exception as exc:
                    failure=dict(N=n,cell=cell,preparation=prep,batch=batch,replicate=rep,status='failed',
                        failure_type=type(exc).__name__,failure=str(exc),unit=uid)
                    failures.append(failure);rows.append(failure)
                    write_raw(out/'raw.json.gz',rows)
                    write_json(out/'failures.json',failures)
                    raise
                timings.append(dict(unit=uid,seconds=time.monotonic()-tick,peak_rss_bytes=peak_bytes()))
                print(f'{uid}: {timings[-1]["seconds"]:.3f}s',flush=True)
                if mode=='primary' and time.monotonic()-start>2700:raise RuntimeError('registered primary hard cap exceeded')
                if peak_bytes()>2*1024**3:raise RuntimeError('registered memory cap exceeded')
    summary=summarize(rows,list(sizes),len(list(cells)),expected_per_cell=3*repeats if mode=='primary' else 1)
    controls_pass=calibration['passed'] and all(r['passed'] for r in indrows+staticrows+eqrows)
    if not controls_pass:summary['decision']='INCONCLUSIVE'
    summary['independent_control_validation_passed']=controls_pass
    write_raw(out/'raw.json.gz',rows);write_json(out/'equilibrium.json',eqrows)
    write_json(out/'independent_controls.json',indrows);write_json(out/'static_controls.json',staticrows);
    write_json(out/'classical_degeneracy.json',classical_degree_two_degeneracy());
    write_json(out/'degree_identifiability.json',[degree_connectivity_identifiability(n) for n in sizes if n<=5]);write_json(out/'summary.json',summary)
    write_json(out/'failures.json',failures)
    from .dynamical_artifacts import write_figures,write_tables
    write_tables(out,rows,summary);write_figures(out,rows,eqrows,summary)
    write_json(out/'timing.json',dict(total_seconds=time.monotonic()-start,peak_rss_bytes=peak_bytes(),bundles=timings))
    if mode=='primary' and (time.monotonic()-start>2700 or peak_bytes()>2*1024**3):
        raise RuntimeError('registered total resource cap exceeded')
    result=archive_manifest(out);print(json.dumps(dict(decision=summary['decision'],scientific_digest=result['scientific_digest'])),flush=True)
    return summary


def pilot(out):
    """Timing only: ephemeral scientific arrays are deleted, never ranked."""
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    start=time.monotonic();initial_source=source_metadata();measurements=[];maxima={};fixed={};sizes=[4,5];decision={}
    pilotrows=[];eqrows=[];overhead=0.
    def checkpoint():
        write_json(out/'pilot.json',dict(measurements=measurements,maxima=maxima,fixed_seconds=fixed,
            decisions=decision,pilot_elapsed_seconds=time.monotonic()-start))
        if peak_bytes()>2*1024**3:raise RuntimeError('pilot memory cap exceeded')
        if time.monotonic()-start>1200:raise RuntimeError('pilot hard cap exceeded')
    with tempfile.TemporaryDirectory(prefix='causal-dynamical-timing-') as temp:
        tmp=Path(temp);(tmp/'arrays').mkdir()
        for n in (4,5,6):
            tick=time.monotonic();catalog=GraphCatalog(n);maxima[n]=0.;fixed[n]=time.monotonic()-tick
            # Before any costly N6 fixed controls, test a rigorous lower bound on bundle cost.
            if n==6:
                limit=PLANNING_BUDGET_SECONDS/(2*6*(3*4+2))+.05
                def timeout(signum,frame):raise TimeoutError('N6 censored timing lower bound exceeds admission inequality')
                old=signal.signal(signal.SIGALRM,timeout);tick=time.monotonic()
                try:
                    signal.setitimer(signal.ITIMER_REAL,limit)
                    row,arrays,_=bundle(n,0,'Splus','pilot',0,0,catalog,checkpoint=True)
                    buffer=io.BytesIO();np.savez_compressed(buffer,**arrays)
                    elapsed=time.monotonic()-tick
                    del row,arrays,buffer
                    measurements.append(dict(N=n,cell=0,preparation='Splus',seconds=elapsed,
                        censored=False,lower_bound_only=True,stage='quantum bundle without fixed graph-cache reductions'))
                    maxima[n]=elapsed
                except TimeoutError:
                    elapsed=time.monotonic()-tick;maxima[n]=elapsed
                    measurements.append(dict(N=n,cell=0,preparation='Splus',elapsed_lower_bound_seconds=elapsed,
                        censored=True,lower_bound_only=True,peak_rss_bytes=peak_bytes()))
                    decision['N6']='excluded: censored quantum-bundle cost already fails conservative complete minimum-cohort inequality'
                finally:
                    signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,old)
                if 2*maxima[n]*84>PLANNING_BUDGET_SECONDS:decision['N6']='excluded: quantum-bundle lower bound already fails conservative complete minimum-cohort inequality'
                checkpoint()
                if 'N6' in decision:continue
            tick=time.monotonic();cache=FrozenGraphResponse(catalog,times=DELAYS)
            write_npz(tmp/'arrays'/f'static_N{n}.npz',dict(response=cache.response))
            fixed[n]+=time.monotonic()-tick
            for cell in range(6):
                for prep in ('Splus','Sempty','E'):
                    tick=time.monotonic()
                    row,arrays,_=bundle(n,cell,prep,'pilot',0,0,catalog,checkpoint=True)
                    law=arrays['full_born'][3]
                    for name,p in {'born':law,**catalog.nulls(law)}.items():
                        for key,value in static_weighted(cache,p).items():arrays[f'static_{name}_{key}']=value
                    from .dynamical_diagnostics import analyze
                    row['additional_diagnostics']=analyze(arrays,catalog)
                    uid=f'N{n}_c{cell}_{prep}'
                    row['array_file']=f'arrays/{uid}.npz';write_npz(tmp/row['array_file'],arrays)
                    # Include JSON/gzip serialization in the timed complete bundle.
                    write_raw(tmp/'one-row.json.gz',[row])
                    seconds=time.monotonic()-tick
                    measurements.append(dict(N=n,cell=cell,preparation=prep,seconds=seconds,censored=False,
                        peak_rss_bytes=peak_bytes(),serialized_bytes=(tmp/row['array_file']).stat().st_size,valid=row['status']=='ok'))
                    maxima[n]=max(maxima[n],seconds);pilotrows.append(row);del arrays
                    print(f'pilot N{n} c{cell} {prep}: {seconds:.3f}s',flush=True)
                    checkpoint()
                tick=time.monotonic()
                eq,a=equilibrium(n,cell,catalog,'pilot');eqrows.append(eq)
                write_npz(tmp/'arrays'/f'equilibrium_N{n}_c{cell}.npz',a)
                for prep in ('Splus','Sempty','E'):
                    control,a=independent_control(n,cell,prep,catalog,'pilot')
                    write_npz(tmp/'arrays'/f'independent_N{n}_c{cell}_{prep}.npz',a)
                if n==4:
                    params=parameters(n,cell);model=build_hamiltonian(params)
                    p,phase=initial_factors(n,'E',rng_for('pilot',n,cell,0,0,1))
                    aged=evolve_state(model,product_state(n,np.pi/4,p,phase),2.)
                    back=measurement_backaction(model,aged,n)
                    pilotrows[-1]['nonselective_measurement_tv']=back['tv']
                fixed[n]+=time.monotonic()-tick;checkpoint()
            del cache
        tick=time.monotonic()
        calibrate_cp(rng_for('calibration',0,0,0,0,0))
        from .dynamical_artifacts import write_figures,write_tables
        # Repeated placeholders time largest-candidate serialization only; they are not evidence.
        expanded=[]
        for row in pilotrows:expanded.extend([row]*(36 if row['preparation']=='E' else 1))
        write_raw(tmp/'raw.json.gz',expanded)
        summary=summarize(pilotrows,[4,5]+([6] if 'N6' not in decision else []))
        write_tables(tmp,expanded,summary);write_figures(tmp,pilotrows,eqrows,summary)
        archive_manifest(tmp)
        overhead=time.monotonic()-tick
    choices=[]
    for r in (12,8,4):
        projection=2*(sum(maxima[n]*6*(3*r+2)+fixed[n] for n in (4,5))+overhead)
        choices.append(dict(repeats_per_batch=r,mandatory_projection_seconds=projection))
        if projection<=PLANNING_BUDGET_SECONDS:chosen=r;break
    else:
        checkpoint()
        write_json(out/'pilot.json',dict(status='infeasible',source=initial_source,measurements=measurements,
            maxima=maxima,fixed_seconds=fixed,decisions=decision,choices=choices,
            postprocessing_seconds_largest_candidate=overhead,pilot_elapsed_seconds=time.monotonic()-start,
            peak_rss_bytes=peak_bytes()))
        raise RuntimeError('mandatory minimum cohort does not fit; pre-primary computational amendment required')
    if 'N6' not in decision:
        allcost=2*(sum(maxima[n]*6*(3*chosen+2)+fixed[n] for n in (4,5,6))+overhead)
        if allcost<=PLANNING_BUDGET_SECONDS:sizes.append(6);decision['N6']='admitted complete cohort'
        else:decision['N6']='excluded: complete same-R cohort exceeds budget'
    if initial_source['sha256']!=source_metadata()['sha256']:raise RuntimeError('source changed during pilot; repeat timing before freeze')
    result=dict(sizes=sizes,repeats_per_batch=chosen,max_bundle_seconds=maxima,fixed_seconds=fixed,
        postprocessing_seconds_largest_candidate=overhead,choices=choices,N6=decision['N6'],measurements=measurements,source=initial_source,
        projected_seconds=2*(sum(maxima[n]*6*(3*chosen+2)+fixed[n] for n in sizes)+overhead),
        safety_factor=2.,primary_budget_seconds=PLANNING_BUDGET_SECONDS,hard_cap_seconds=2700,
        pilot_elapsed_seconds=time.monotonic()-start,peak_rss_bytes=peak_bytes(),
        selection_uses='timing, memory and numerical validity only; all pilot scientific arrays discarded')
    write_json(out/'pilot.json',result);print(json.dumps(dict(sizes=sizes,repeats=chosen)),flush=True)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=('smoke','pilot','primary'),default='smoke')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--freeze',type=Path)
    args=parser.parse_args()
    if args.mode=='pilot':pilot(args.output)
    elif args.mode=='smoke':run(args.output,mode='smoke',sizes=(4,),repeats=1,cells=(0,))
    else:
        def deadline(signum,frame):raise TimeoutError('registered 45-minute primary hard cap exceeded')
        old=signal.signal(signal.SIGALRM,deadline)
        try:
            signal.setitimer(signal.ITIMER_REAL,2700)
            run(args.output,mode='primary',freeze=args.freeze)
        finally:
            signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,old)

if __name__=='__main__':main()
