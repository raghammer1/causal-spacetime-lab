"""Prespecified finite-system necessary conditions; no fitted classifier."""
from __future__ import annotations
import numpy as np
from scipy.stats import beta, binom


def top_two(response, tolerance=1e-10):
    """Fractional boundary ties; diagonal excluded. Undefined rows stay NaN."""
    a=np.asarray(response,float)
    if a.ndim!=2 or a.shape[0]!=a.shape[1] or len(a)<4:
        raise ValueError('response must be square with N>=4')
    n=len(a); weights=np.zeros_like(a); capture=np.full(n,np.nan)
    for i in range(n):
        js=np.flatnonzero(np.arange(n)!=i); values=a[i,js]
        if not np.all(np.isfinite(values)) or np.any(values < -tolerance): continue
        threshold=np.sort(values)[-2]
        above=values>threshold+tolerance
        tied=np.abs(values-threshold)<=tolerance
        weights[i,js[above]]=1
        weights[i,js[tied]]=(2-int(above.sum()))/int(tied.sum())
        total=values.sum()
        if total>tolerance: capture[i]=np.dot(weights[i,js],values)/total
    f=float(np.mean(capture))
    return dict(weights=weights, per_source=capture, F=f,
                normalized_excess=(f-2/(n-1))/(1-2/(n-1)),
                mean_response=float(a[~np.eye(n,dtype=bool)].mean()))


def cp_interval(successes, trials, family=1, alpha=.05):
    if not 0<=successes<=trials or trials<1 or family<1:
        raise ValueError('invalid binomial counts or family size')
    tail=alpha/(2*family)
    return [0. if successes==0 else float(beta.ppf(tail,successes,trials-successes+1)),
            1. if successes==trials else float(beta.ppf(1-tail,successes+1,trials-successes))]


def assess_unit(born, connectivity, response, perturbed, initial_frozen, delays):
    """One independent preparation, all dependent pairs/times inside its event."""
    p=np.asarray(born); connected=p@np.asarray(connectivity)
    tvs=np.array([.5*np.abs(p[3]-p[4]).sum(),.5*np.abs(p[4]-p[5]).sum()])
    details=[]
    for delay in (.25,.5):
        k=list(delays).index(delay)
        full=top_two(response[k]); pert=top_two(perturbed[k]); frozen=top_two(initial_frozen[k])
        overlap=float(np.minimum(full['weights'],pert['weights']).sum()/ (2*len(response[k])))
        details.append(dict(delay=delay,F=full['F'],normalized_excess=full['normalized_excess'],
            response_mean=full['mean_response'],perturbed_F=pert['F'],
            perturbed_response_mean=pert['mean_response'],frozen_F=frozen['F'],
            overlap=overlap,dynamic_gain=full['F']-frozen['F']))
    C=bool(np.all(connected[3:6]>=.8))
    L=all(d['F']>=.8 and d['response_mean']>=.01 for d in details)
    T=bool(np.all(tvs<=.1) and all(d['overlap']>=.8 and d['perturbed_F']>=.8
          and d['perturbed_response_mean']>=.01 for d in details))
    D=all(np.isfinite(d['frozen_F']) and d['dynamic_gain']>=.1 for d in details)
    return dict(C=C,L=L,T=T,D=D,joint=C and L and T and D,
        late_connectivity=connected[3:6].tolist(),late_tv=tvs.tolist(),response_details=details)


def summarize(rows, sizes, cells=6, expected_per_cell=None):
    family=len(sizes)*cells; table=[]
    for n in sizes:
        for cell in range(cells):
            selected=[r for r in rows if r['N']==n and r['cell']==cell and r['preparation']=='E']
            total=len(selected)
            if not total: continue
            valid=[r for r in selected if r.get('status')=='ok']
            successes=sum(r['gate']['joint'] for r in valid)
            structural=sum(bool(r.get('degree_null_event',False)) for r in valid)
            complete=expected_per_cell is None or total==expected_per_cell
            if expected_per_cell is not None:
                actual=[(r.get('batch'),r.get('replicate')) for r in selected]
                expected={(0,0)} if expected_per_cell==1 else {(b,r) for b in range(3) for r in range(expected_per_cell//3)}
                complete=complete and len(set(actual))==total and set(actual)==expected
            bounds=cp_interval(successes,total,family)
            table.append(dict(N=n,cell=cell,attempted=total,valid=len(valid),successes=successes,
                component_successes={k:sum(r['gate'][k] for r in valid) for k in ('C','L','T','D')},
                cp_family_bounds=bounds,cp_go_bounds=cp_interval(successes,total,2*family),
                degree_null_successes=structural,degree_null_go_bounds=cp_interval(structural,total,2*family),
                cohort_complete=complete,
                assessment='fails' if bounds[1]<.8 else 'passes necessary screen' if bounds[0]>.8 else 'unresolved'))
    eliminated=[c for c in range(cells) if any(x['cell']==c and x['assessment']=='fails' for x in table)]
    valid_all=all(r.get('status')=='ok' for r in rows)
    complete_all=len(table)==family and all(r['cohort_complete'] for r in table)
    eligible=[c for c in range(cells) if all(any(r['N']==n and r['cell']==c and r['cp_go_bounds'][0]>.8
        and (n<5 or r['degree_null_go_bounds'][0]>.8) for r in table) for n in sizes)]
    decision='NO-GO' if len(eliminated)==cells and valid_all and complete_all else 'INCONCLUSIVE'
    return dict(decision=decision,scope='registered finite unconditioned dynamically organized locality',
        geometry_beyond_graph='UNRESOLVED at these sizes',family_size=family,
        alpha=.05,target_joint_probability=.8,cells=table,eliminated_parameter_settings=eliminated,
        complete_expected_cohorts=complete_all,statistically_eligible_parameter_settings=eligible,
        limited_go_requires_independently_verified_mechanism=True,
        limitation='A necessary screen cannot establish LIMITED GO without the separate mechanism and null requirements.')


def calibrate_cp(rng, trials=(12,24,36), families=(12,18,24,36)):
    """Exact binomial coverage, plus an independently seeded numerical cross-check."""
    rows=[]
    for n in trials:
        for family in families:
            intervals=np.array([cp_interval(k,n,family) for k in range(n+1)])
            ps=np.unique(np.r_[np.linspace(0,1,1001),intervals.ravel()])
            coverage=[]
            for p in ps:
                inside=(intervals[:,0]<=p+1e-14)&(intervals[:,1]>=p-1e-14)
                coverage.append(float(binom.pmf(np.arange(n+1),n,p)@inside))
            testp=.37; draws=rng.binomial(n,testp,size=10000)
            hit=(intervals[draws,0]<=testp)&(intervals[draws,1]>=testp)
            rows.append(dict(trials=n,family=family,minimum_enumerated_coverage=min(coverage),
                required_marginal_coverage=1-.05/family,grid_points=len(ps),
                simulation_probability=testp,simulation_covered=int(hit.sum()),simulation_trials=len(hit),
                passed=min(coverage)>=1-.05/family-1e-12))
    return dict(method='exact binomial enumeration; grid includes all CI endpoints',
        rows=rows,passed=all(r['passed'] for r in rows))
