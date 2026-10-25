#!/usr/bin/env python3
"""Independent graph and frozen-probe audit for Experiment 7.

Imports no causal_lab code. Graphs are rebuilt from binary strings and BFS;
small matter Hamiltonians use dense Kronecker matrices; reduced density matrices
and their eigenvalue trace norms are assembled independently of production code.
"""
from __future__ import annotations
import argparse
from collections import defaultdict, deque
import gzip
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import time
import numpy as np

GRAPH_TOL=2e-10
RESPONSE_TOL=2e-8
PAULI=(np.array([[0,1],[1,0]],complex),np.array([[0,-1j],[1j,0]],complex),np.diag([1.,-1.]))

class Checks:
    def __init__(self):
        self.scalar_comparisons=0;self.checks=0;self.failures=[];self.max_errors={}
    def equal(self,label,got,expected,tolerance=GRAPH_TOL):
        self.checks+=1
        if got is None or expected is None:
            self.scalar_comparisons+=1
            if got is not None or expected is not None:self.fail(label,'None mismatch')
            return
        a=np.asarray(got);b=np.asarray(expected)
        if a.shape!=b.shape:
            self.fail(label,f'shape {a.shape} != {b.shape}');return
        self.scalar_comparisons+=a.size
        if a.dtype.kind in 'bui' and b.dtype.kind in 'bui':
            error=float(np.max(a!=b,initial=False))
        else:
            if not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
                self.fail(label,'nonfinite values');return
            error=float(np.max(np.abs(a-b),initial=0.))
        family=label.split(':',1)[0]
        self.max_errors[family]=max(error,self.max_errors.get(family,0.))
        if error>tolerance:self.fail(label,f'maximum absolute error {error:.16g} > {tolerance:g}')
    def require(self,label,condition):
        self.checks+=1;self.scalar_comparisons+=1
        if not condition:self.fail(label,'condition false')
    def fail(self,label,reason):
        self.failures.append(dict(label=label,reason=reason))


def decode(n,integer):
    edges=list(combinations(range(n),2));bits=np.array([int(c) for c in f'{integer:0{len(edges)}b}'],dtype=int)
    a=np.zeros((n,n),int)
    for bit,(i,j) in zip(bits,edges):a[i,j]=a[j,i]=bit
    return edges,bits,a


def bfs_properties(a):
    n=len(a);distance=np.full((n,n),-1,int)
    for source in range(n):
        q=deque([source]);distance[source,source]=0
        while q:
            u=q.popleft()
            for v in range(n):
                if a[u,v] and distance[source,v]<0:
                    distance[source,v]=distance[source,u]+1;q.append(v)
    sizes=[];remaining=set(range(n))
    while remaining:
        v=min(remaining);component={j for j in range(n) if distance[v,j]>=0}
        sizes.append(len(component));remaining-=component
    sizes=sorted(sizes,reverse=True)+[0]*(n-len(sizes))
    degree=np.array([sum(a[i,j] for j in range(n)) for i in range(n)])
    local=np.zeros(n);triangles=0
    for i,j,k in combinations(range(n),3):
        if a[i,j] and a[i,k] and a[j,k]:
            triangles+=1;local[[i,j,k]]+=1
    wedges=np.array([math.comb(int(d),2) for d in degree])
    clustering=np.array([local[i]/wedges[i] if wedges[i] else 0. for i in range(n)])
    components=sum(s>0 for s in sizes)
    return dict(degrees=degree,edge_count=int(degree.sum()//2),distance=distance,
        component_sizes=np.array(sizes),components=components,connected=components==1,
        largest_component_fraction=max(sizes)/n,isolated_vertices=int(sum(degree==0)),
        maximum_degree=int(max(degree)),universal_vertices=int(sum(degree==n-1)),
        diameter=int(distance.max()) if components==1 else -1,
        ball_sizes=np.array([[sum(0<=distance[i,j]<=r for j in range(n)) for r in range(n)] for i in range(n)]),
        triangles=triangles,local_clustering=clustering,clustering=float(clustering.mean()),
        transitivity=3*triangles/sum(wedges) if sum(wedges) else 0.,
        laplacian_spectra=np.linalg.eigvalsh(np.diag(degree)-a))


def catalogue(n):
    storage=defaultdict(list);edges=None
    for integer in range(1<<(n*(n-1)//2)):
        edges,bits,a=decode(n,integer)
        storage['graph_bits'].append(bits);storage['adjacency'].append(a)
        for key,value in bfs_properties(a).items():storage[key].append(value)
    answer={key:np.array(value) for key,value in storage.items()};answer['edges']=np.array(edges)
    return answer


def groups_for(catalog):
    counts=defaultdict(list);degrees=defaultdict(list)
    for index,(count,degree) in enumerate(zip(catalog['edge_count'],catalog['degrees'])):
        counts[int(count)].append(index);degrees[tuple(degree)].append(index)
    return list(counts.values()),list(degrees.values())


def null_laws(p,catalog,groups):
    p=np.asarray(p,float)/sum(p);bits=catalog['graph_bits'];occupations=np.array([sum(p[bits[:,e]==1]) for e in range(bits.shape[1])])
    density=sum(occupations)/len(occupations)
    qdensity=np.ones(len(p));qproduct=np.ones(len(p))
    for e in range(bits.shape[1]):
        qdensity*=np.where(bits[:,e],density,1-density)
        qproduct*=np.where(bits[:,e],occupations[e],1-occupations[e])
    result=dict(density=qdensity,product=qproduct)
    for name,classes in zip(('count','degree'),groups):
        q=np.empty_like(p)
        for indices in classes:q[indices]=sum(p[indices])/len(indices)
        result[name]=q
    return result


def properties(p,c):
    p=np.asarray(p,float)/sum(p);n=c['degrees'].shape[1];m=c['graph_bits'].shape[1]
    occ=np.array([sum(p[c['graph_bits'][:,i]==1]) for i in range(m)])
    joint=np.array([[sum(p[(c['graph_bits'][:,i]==1)&(c['graph_bits'][:,j]==1)]) for j in range(m)] for i in range(m)])
    mean=float(sum(p*c['edge_count']));connected=float(sum(p[c['connected']]))
    hist=lambda values,length:np.array([sum(p[values==k]) for k in range(length)])
    degree_hist=np.array([sum(p*np.sum(c['degrees']==k,axis=1))/n for k in range(n)])
    return dict(occupation=occ,occupation_variance=occ*(1-occ),occupation_covariance=joint-np.outer(occ,occ),
        occupation_contrast=float(max(occ)-min(occ)),expected_edge_count=mean,
        edge_count_variance=float(sum(p*(c['edge_count']-mean)**2)),edge_count_distribution=hist(c['edge_count'],m+1),
        expected_degrees=np.einsum('g,gi->i',p,c['degrees']),degree_distribution=degree_hist,
        connected_probability=connected,expected_components=float(sum(p*c['components'])),
        component_count_distribution=hist(c['components'],n+1),expected_sorted_component_sizes=np.einsum('g,gi->i',p,c['component_sizes']),
        largest_component_fraction=float(sum(p*c['largest_component_fraction'])),
        largest_component_size_distribution=hist(c['component_sizes'][:,0],n+1),
        expected_isolated_vertices=float(sum(p*c['isolated_vertices'])),probability_any_isolated=float(sum(p[c['isolated_vertices']>0])),
        expected_maximum_degree=float(sum(p*c['maximum_degree'])),expected_universal_vertices=float(sum(p*c['universal_vertices'])),
        expected_triangles=float(sum(p*c['triangles'])),expected_clustering=float(sum(p*c['clustering'])),
        expected_transitivity=float(sum(p*c['transitivity'])),
        connected_mean_diameter=float(sum(p[c['connected']]*c['diameter'][c['connected']])/connected) if connected else None,
        connected_diameter_distribution=np.array([sum(p[c['diameter']==k]) for k in range(n)]),
        expected_ball_sizes=np.einsum('g,gir->ir',p,c['ball_sizes']),
        mean_sorted_laplacian_eigenvalues=np.einsum('g,gi->i',p,c['laplacian_spectra']))


def tensor_operator(n,site,operator):
    result=np.array([[1.]],complex)
    for i in range(n):result=np.kron(result,operator if i==site else np.eye(2))
    return result


def reduce_site(states,n,site):
    # states[time,branch,basis] -> independent partial trace of all other matter.
    tensor=states.reshape(states.shape[:2]+(2,)*n)
    matrix=np.moveaxis(tensor,2+site,2).reshape(states.shape[:2]+(2,-1))
    return np.einsum('tbik,tbjk->tbij',matrix,matrix.conj())


def independent_static(catalog,times):
    n=catalog['degrees'].shape[1];G=len(catalog['adjacency']);T=len(times)
    x=[tensor_operator(n,i,PAULI[0]) for i in range(n)]
    y=[tensor_operator(n,i,PAULI[1]) for i in range(n)]
    z=[tensor_operator(n,i,PAULI[2]) for i in range(n)]
    base=np.array([1.],complex)
    for _ in range(n):base=np.kron(base,[math.cos(math.pi/8),math.sin(math.pi/8)])
    initial=np.array([base]+[operator@base for operator in y])
    bloch=np.empty((G,T,n+1,n,3));response=np.zeros((G,T,n,n))
    norms_saved=np.empty((G,T,n+1));energy_saved=np.empty_like(norms_saved);parity_saved=np.empty_like(norms_saved)
    energy_initial_saved=np.empty((G,n+1));parity_initial_saved=np.empty((G,n+1))
    max_norm=max_energy=max_parity=0.
    parity=np.eye(1<<n,dtype=complex)
    for operator in x:parity=parity@operator
    hfield=-sum(x)
    for graph,adj in enumerate(catalog['adjacency']):
        H=hfield.copy()
        for i,j in combinations(range(n),2):
            if adj[i,j]:H-=z[i]@z[j]
        energies,vectors=np.linalg.eigh(H)
        coefficients=initial@vectors.conj()
        states=np.array([(coefficients*np.exp(-1j*t*energies))@vectors.T for t in times])
        norms=np.sum(abs(states)**2,axis=-1)
        initial_energy=np.array([np.vdot(v,H@v).real for v in initial])
        evolved_energy=np.einsum('tbi,ij,tbj->tb',states.conj(),H,states).real
        initial_parity=np.array([np.vdot(v,parity@v).real for v in initial])
        evolved_parity=np.einsum('tbi,ij,tbj->tb',states.conj(),parity,states).real
        norms_saved[graph]=norms-1;energy_saved[graph]=evolved_energy-initial_energy
        parity_saved[graph]=evolved_parity-initial_parity
        energy_initial_saved[graph]=initial_energy;parity_initial_saved[graph]=initial_parity
        max_norm=max(max_norm,float(np.max(abs(norms-1))))
        max_energy=max(max_energy,float(np.max(abs(evolved_energy-initial_energy)/np.maximum(1,abs(initial_energy)))))
        max_parity=max(max_parity,float(np.max(abs(evolved_parity-initial_parity)/np.maximum(1,abs(initial_parity)))))
        for target in range(n):
            reduced=reduce_site(states,n,target)
            for component,sigma in enumerate(PAULI):bloch[graph,:,:,target,component]=np.einsum('tbij,ji->tb',reduced,sigma).real
            for source in range(n):
                if source!=target:
                    difference=reduced[:,source+1]-reduced[:,0]
                    response[graph,:,source,target]=np.abs(np.linalg.eigvalsh(difference)).sum(axis=1)/2
    return dict(baseline_bloch=bloch[:,:,0],probe_bloch=bloch[:,:,1:],response=response,
        norm_error=norms_saved,energy_drift=energy_saved,parity_drift=parity_saved,
        initial_energy=energy_initial_saved,initial_parity=parity_initial_saved,
        maximum_norm_error=max_norm,maximum_scaled_energy_drift=max_energy,maximum_scaled_parity_drift=max_parity)


def weighted_static(law,static):
    p=np.asarray(law,float)/sum(law)
    baseline=np.einsum('g,gtic->tic',p,static['baseline_bloch'])
    probe=np.einsum('g,gtsic->tsic',p,static['probe_bloch'])
    n=baseline.shape[1];mixture=np.zeros(probe.shape[:-1])
    for source in range(n):
        for target in range(n):
            if source==target:continue
            vector=probe[:,source,target]-baseline[:,target]
            matrices=sum(vector[:,i,None,None]*PAULI[i][None,:,:]/2 for i in range(3))
            mixture[:,source,target]=np.abs(np.linalg.eigvalsh(matrices)).sum(axis=1)/2
    conditional=np.einsum('g,gtsj->tsj',p,static['response'])
    return dict(baseline_bloch=baseline,probe_bloch=probe,mixture_response=mixture,conditional_response=conditional)


def safe_path(root,name):
    p=Path(name)
    if p.is_absolute() or '..' in p.parts:raise ValueError('external archive path')
    return root/p


def manifest_audit(root,checks):
    manifest=json.loads((root/'manifest.json').read_text())
    for name,expected in manifest['sha256'].items():
        actual=hashlib.sha256(safe_path(root,name).read_bytes()).hexdigest()
        checks.require('manifest:'+name,actual==expected)
    digest=hashlib.sha256()
    for name in manifest['scientific_files']:
        checks.require('manifest membership:'+name,name in manifest['sha256'])
        digest.update(name.encode());digest.update(safe_path(root,name).read_bytes())
    checks.require('scientific digest',digest.hexdigest()==manifest['scientific_digest'])
    return manifest['scientific_digest']


def degree_limits(c,checks,n):
    _,groups=groups_for(c);mixed=[]
    for group in groups:
        connected=[g for g in group if c['connected'][g]]
        if 0<len(connected)<len(group):mixed.append((tuple(c['degrees'][group[0]]),len(connected),len(group)-len(connected)))
    checks.require(f'degree mixed classes N{n}',len(mixed)==(0 if n==4 else 10))
    if n==5:
        for degree,connected,disconnected in mixed:
            checks.require('N5 path degree',sorted(degree)==[1,1,2,2,2])
            checks.require('N5 six paths one triangle-edge',connected==6 and disconnected==1)
    return dict(N=n,mixed_classes=len(mixed),maximum_connectivity_advantage=0. if n==4 else 1/7,
        minimum_path_mass_for_point1_advantage=None if n==4 else .7)


def classical_six(checks):
    connected=disconnected=0;spectra={}
    for integer in range(1<<15):
        _,_,a=decode(6,integer)
        if np.all(a.sum(1)==2):
            p=bfs_properties(a)
            if p['connected']:connected+=1;spectra['cycle_spectrum']=p['laplacian_spectra']
            else:disconnected+=1;spectra['triangles_spectrum']=p['laplacian_spectra']
    checks.equal('N6 C6 count',connected,60,0)
    checks.equal('N6 two triangles count',disconnected,10,0)
    result=dict(n=6,degree_two_graphs=connected+disconnected,connected_cycles=connected,
        disconnected_triangle_pairs=disconnected,connected_matter_microstates=2*connected,
        disconnected_matter_microstates=4*disconnected,
        canonical_zero_temperature_connectivity=2*connected/(2*connected+4*disconnected),
        uniform_graph_connectivity=connected/(connected+disconnected),**spectra)
    checks.equal('N6 Gibbs connectivity',result['canonical_zero_temperature_connectivity'],.75,0)
    return result


def seeded_draws(stream,n,cell,batch,rep,purpose,law):
    entropy=[20261025,7,{'smoke':1,'calibration':2,'pilot':3,'primary':4,'audit':5}[stream],n,cell,batch,rep,purpose]
    generator=np.random.default_rng(np.random.SeedSequence(entropy))
    probability=np.asarray(law)/sum(law)
    return generator.choice(len(probability),size=8,p=probability)


def encode(a):
    answer=0
    for i,j in combinations(range(len(a)),2):answer=2*answer+int(a[i,j])
    return answer


def static_control_records(root,catalogs,statics,checks):
    path=root/'static_controls.json'
    if not path.exists():return
    for record in json.loads(path.read_text()):
        n=record['N'];catalog=catalogs[n];static=statics[n]
        chain=np.zeros((n,n),int);matching=np.zeros((n,n),int)
        for i in range(n-1):chain[i,i+1]=chain[i+1,i]=1
        for i in range(0,n-1,2):matching[i,i+1]=matching[i+1,i]=1
        controls=dict(chain=encode(chain),complete=(1<<(n*(n-1)//2))-1,empty=0,matching=encode(matching))
        for key,index in controls.items():checks.equal('static control graph:'+key,record['control_graphs'][key],index,0)
        perm=record['chain_permutation'];checks.require('chain permutation',sorted(perm)==list(range(n)))
        graph=encode(chain[np.ix_(perm,perm)])
        checks.equal('permuted chain index',record['chain_graph_index'],graph,0)
        response=static['response'][graph];distance=catalog['distance'][graph]
        means=[response[2][distance==d].mean() for d in range(1,n)]
        checks.equal('chain response by distance',record['chain_mean_responses_at_delay_point1_by_distance'],means,RESPONSE_TOL)
        off=~np.eye(n,dtype=bool);uniform=np.ptp(static['response'][controls['complete']][:,off],axis=1).max()
        disconnected=catalog['distance'][controls['matching']]<0
        no_signal=max(response[0][off].max(),static['response'][controls['matching']][:,disconnected].max())
        checks.equal('complete response uniformity',record['maximum_complete_response_range'],uniform,RESPONSE_TOL)
        checks.equal('disconnected no signalling',record['maximum_no_signalling_error'],no_signal,RESPONSE_TOL)
        checks.require('supplied control assay passes',no_signal<2e-8 and uniform<2e-8 and all(a>b for a,b in zip(means,means[1:])) and means[0]>.01)
        checks.require('disconnected control rejected',not record['disconnected_connectivity'])


def audit_self_checks(checks):
    chain=np.array([[0,1,0],[1,0,1],[0,1,0]])
    prop=bfs_properties(chain)
    checks.equal('audit selftest BFS chain',prop['distance'],[[0,1,2],[1,0,1],[2,1,0]],0)
    checks.equal('audit selftest chain degrees',prop['degrees'],[1,2,1],0)
    checks.equal('audit selftest triangle count',bfs_properties(np.ones((3,3),int)-np.eye(3,dtype=int))['triangles'],1,0)
    bell=np.array([1.,0.,0.,1.],complex)/np.sqrt(2)
    checks.equal('audit selftest Bell partial trace',reduce_site(bell.reshape(1,1,4),2,0)[0,0],np.eye(2)/2,1e-14)
    complex_product=np.kron([1.,0.],np.array([1.,1j])/np.sqrt(2))
    rho=reduce_site(complex_product.reshape(1,1,4),2,1)[0,0]
    checks.equal('audit selftest Y convention',np.trace(rho@PAULI[1]).real,1.,1e-14)
    checks.equal('audit selftest trace norm',np.abs(np.linalg.eigvalsh(np.diag([1.,-1.]))).sum()/2,1.,0)


def audit(root):
    root=Path(root);checks=Checks();started=time.monotonic();audit_self_checks(checks);digest=manifest_audit(root,checks)
    metadata=json.loads((root/'metadata.json').read_text())
    rows=json.loads(gzip.decompress((root/'raw.json.gz').read_bytes()))
    sizes=sorted({row['N'] for row in rows});catalogs={};statics={};groups={};limits=[];graph_count=0
    for n in sizes:
        if n not in (4,5):raise ValueError('independent exhaustive matter audit supports admitted N4/N5 only')
        c=catalogue(n);catalogs[n]=c;groups[n]=groups_for(c)
        archived=np.load(root/'arrays'/f'catalog_N{n}.npz',allow_pickle=False)
        for key,value in c.items():checks.equal(f'catalog:{n}/{key}',archived[key],value)
        checks.equal(f'Laplacian trace identity:{n}',c['laplacian_spectra'].sum(axis=1),2*c['edge_count'])
        checks.equal(f'Laplacian zero modes:{n}',np.sum(abs(c['laplacian_spectra'])<1e-9,axis=1),c['components'],0)
        graph_count+=len(c['adjacency']);limits.append(degree_limits(c,checks,n))
        statics[n]=independent_static(c,metadata['delays'])
        energy0=-n/np.sqrt(2)-c['edge_count']/2
        energy_exact=np.column_stack((energy0,energy0[:,None]+np.sqrt(2)+c['degrees']))
        parity_exact=np.tile(np.r_[1.,-np.ones(n)]*2**(-n/2),(len(energy0),1))
        checks.equal(f'fresh product energy identity:{n}',statics[n]['initial_energy'],energy_exact)
        checks.equal(f'fresh product parity identity:{n}',statics[n]['initial_parity'],parity_exact)
        archived=np.load(root/'arrays'/f'static_N{n}.npz',allow_pickle=False)
        for key in ('baseline_bloch','probe_bloch','response','norm_error','energy_drift','parity_drift','initial_energy','initial_parity'):
            if key not in archived:continue
            checks.equal(f'static dense:{n}/{key}',archived[key],statics[n][key],RESPONSE_TOL)
        for key in ('maximum_norm_error','maximum_scaled_energy_drift','maximum_scaled_parity_drift'):
            checks.require(f'static independent conservation:{n}/{key}',statics[n][key]<2e-9)
    static_control_records(root,catalogs,statics,checks)
    laws=0;weighted=0;draw_laws=0
    for row_index,row in enumerate(rows):
        n=row['N'];c=catalogs[n]
        checks.require(f'valid row:{row_index}',row['status']=='ok')
        if row['status']!='ok':continue
        arrays=np.load(safe_path(root,row['array_file']),allow_pickle=False)
        for name,prefix,purpose in [('full','born_draws',100),('perturbed','perturbed_born_draws',200)]:
            for age,law in enumerate(arrays[name+'_born']):
                checks.equal(f'{name} law normalization:{row_index}/{age}',sum(law),1.,2e-9)
                if prefix in arrays:
                    draws=seeded_draws(row['stream'],n,row['cell'],row['batch'],row['replicate'],purpose+age,law)
                    checks.equal(f'unselected Born draw:{row_index}/{name}/{age}',arrays[prefix][age],draws,0);draw_laws+=1
        for age,law in enumerate(arrays['full_born']):
            laws+=1;checks.equal(f'Born normalization:{row_index}/{age}',sum(law),1.,2e-9)
            checks.require(f'Born positivity:{row_index}/{age}',np.all(law>=-2e-12))
            observed=properties(law,c);record=row['structure'][age]
            for key,expected in observed.items():checks.equal(f'Born properties:{row_index}/{age}/{key}',record['observed'][key],expected)
            nulls=null_laws(law,c,groups[n])
            for name,q in nulls.items():
                checks.equal(f'null normalization:{row_index}/{age}/{name}',sum(q),1.,2e-9)
                checks.equal(f'null TV:{row_index}/{age}/{name}',record['nulls'][name]['tv'],np.abs(law-q).sum()/2)
                props=properties(q,c)
                for key,value in record['nulls'][name]['properties'].items():checks.equal(f'null properties:{row_index}/{age}/{name}/{key}',value,props[key])
        if 'nonselective_measurement_tv' in row:
            measured=arrays['measurement_measured_future_born'];unmeasured=arrays['measurement_unmeasured_future_born']
            checks.equal(f'measurement normalization:{row_index}',sum(measured),1.,2e-9)
            checks.equal(f'measurement source Born:{row_index}',arrays['measurement_measurement_born'],arrays['full_born'][3])
            checks.equal(f'unmeasured continuation:{row_index}',unmeasured,arrays['full_born'][4],RESPONSE_TOL)
            checks.equal(f'measurement TV:{row_index}',row['nonselective_measurement_tv'],np.abs(measured-unmeasured).sum()/2)
        law=arrays['full_born'][3]
        for name,p in dict(born=law,**null_laws(law,c,groups[n])).items():
            weighted+=1;expected=weighted_static(p,statics[n])
            for key,value in expected.items():checks.equal(f'weighted static:{row_index}/{name}/{key}',arrays[f'static_{name}_{key}'],value,RESPONSE_TOL)
            checks.require(f'trace-distance convexity:{row_index}/{name}',np.all(expected['mixture_response']<=expected['conditional_response']+RESPONSE_TOL))
    equilibrium=json.loads((root/'equilibrium.json').read_text())
    for record in equilibrium:
        n=record['N'];cell=record['cell'];c=catalogs[n]
        arrays=np.load(root/'arrays'/f'equilibrium_N{n}_c{cell}.npz',allow_pickle=False)
        expected=properties(arrays['ground_born'],c)
        for key,value in record['properties'].items():checks.equal(f'ground graph properties:{n}/{cell}/{key}',value,expected[key])
        if 'ground_born_draws' in arrays:
            checks.equal(f'ground unselected Born draws:{n}/{cell}',arrays['ground_born_draws'],
                seeded_draws(metadata['mode'],n,cell,0,0,400,arrays['ground_born']),0);draw_laws+=1
        for thermal in record.get('thermal',[]):
            beta=thermal['beta'];law=arrays[f'thermal_born_beta{beta}'];expected=properties(law,c)
            for key,value in thermal['properties'].items():checks.equal(f'Gibbs graph properties:{n}/{cell}/{beta}/{key}',value,expected[key])
            key=f'thermal_born_draws_beta{beta}'
            if key in arrays:
                checks.equal(f'Gibbs unselected Born draws:{n}/{cell}/{beta}',arrays[key],seeded_draws(metadata['mode'],n,cell,0,0,401+int(beta),law),0);draw_laws+=1
    six=classical_six(checks)
    if (root/'classical_degeneracy.json').exists():
        record=json.loads((root/'classical_degeneracy.json').read_text())
        for key,value in six.items():checks.equal('classical degeneracy:'+key,record[key],value)
    return dict(passed=not checks.failures,checks=checks.checks,scalar_comparisons=checks.scalar_comparisons,
        failures=checks.failures,maximum_absolute_errors=checks.max_errors,
        graph_tolerance=GRAPH_TOL,response_tolerance=RESPONSE_TOL,
        catalogue_count=len(sizes),catalogue_sizes=sizes,graph_count=graph_count,all_graph_static_probes=graph_count,
        full_Born_laws=laws,unselected_Born_draw_laws=draw_laws,graph_weighted_controls=weighted,preparation_records=len(rows),stochastic_E_preparation_records=sum(r['preparation']=='E' for r in rows),
        deterministic_symmetric_preparation_records=sum(r['preparation']!='E' for r in rows),
        degree_null_limits=limits,classical_six={k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in six.items()},
        source_scientific_digest=digest,audit_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        implementation='No causal_lab imports; BFS graph properties, dense Kronecker TFIM, independently traced matrices/eigenvalue norms',
        elapsed_seconds=time.monotonic()-started)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('archive',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:result=audit(args.archive)
    except Exception as exc:result=dict(passed=False,exception_type=type(exc).__name__,exception=str(exc))
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result,sort_keys=True));raise SystemExit(0 if result['passed'] else 1)

if __name__=='__main__':main()
