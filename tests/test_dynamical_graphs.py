"""Exhaustive combinatorial and independent dense quantum control checks."""
from itertools import combinations, permutations
import math

import numpy as np
import pytest
from scipy.linalg import expm

from causal_lab.dynamical_graphs import (
    GraphCatalog, FrozenGraphResponse, classical_degree_two_degeneracy,
    degree_connectivity_identifiability, graph_catalog, static_controls,
)


def graph_from_bits(n, index):
    pairs=list(combinations(range(n),2))
    adjacency=np.zeros((n,n),dtype=int)
    for e,(i,j) in enumerate(pairs):
        adjacency[i,j]=adjacency[j,i]=(index >> (len(pairs)-1-e)) & 1
    return adjacency


def bfs_distances(adjacency):
    n=len(adjacency)
    distance=np.full((n,n),-1)
    for source in range(n):
        distance[source,source]=0
        queue=[source]
        while queue:
            current=queue.pop(0)
            for target in range(n):
                if adjacency[current,target] and distance[source,target]<0:
                    distance[source,target]=distance[source,current]+1
                    queue.append(target)
    return distance


def connected_graph_count(n):
    # The component containing vertex zero has k vertices; subtract every k<n.
    counts=[0,1]
    for size in range(2,n+1):
        counts.append(2**math.comb(size,2)-sum(math.comb(size-1,k-1)*counts[k]*
                      2**math.comb(size-k,2) for k in range(1,size)))
    return counts[n]


@pytest.mark.parametrize('n',[2,3,4,5])
def test_exhaustive_graph_catalogue_against_independent_bfs_and_triangle_count(n):
    catalog=graph_catalog(n)
    assert catalog.graph_count==2**math.comb(n,2)
    assert int(catalog.connected.sum())==connected_graph_count(n)
    for index in range(catalog.graph_count):
        adjacency=graph_from_bits(n,index)
        distance=bfs_distances(adjacency)
        np.testing.assert_array_equal(catalog.adjacency[index],adjacency)
        np.testing.assert_array_equal(catalog.degrees[index],adjacency.sum(axis=1))
        np.testing.assert_array_equal(catalog.distance[index],distance)
        assert catalog.index(adjacency)==index
        assert catalog.triangles[index]==sum(adjacency[i,j]*adjacency[i,k]*adjacency[j,k]
                                               for i,j,k in combinations(range(n),3))
        components={tuple(np.flatnonzero(distance[i]>=0)) for i in range(n)}
        assert catalog.components[index]==len(components)
        sizes=sorted([len(component) for component in components],reverse=True)+[0]*(n-len(components))
        np.testing.assert_array_equal(catalog.component_sizes[index],sizes)
        expected_diameter=int(distance.max()) if len(components)==1 else -1
        assert catalog.diameter[index]==expected_diameter
        for radius in range(n):
            np.testing.assert_array_equal(catalog.ball_sizes[index,:,radius],
                                          ((distance>=0)&(distance<=radius)).sum(axis=1))
    eig=catalog.laplacian_spectra
    np.testing.assert_array_equal((np.abs(eig)<1e-9).sum(axis=1),catalog.components)
    np.testing.assert_allclose(eig.sum(axis=1),2*catalog.edge_count,atol=1e-12)
    np.testing.assert_allclose((eig**2).sum(axis=1),(catalog.degrees**2).sum(axis=1)+2*catalog.edge_count,atol=1e-11)


def test_exact_named_controls_and_disconnected_sentinels():
    catalog=graph_catalog(4)
    controls=static_controls(catalog)
    chain=controls['chain'];complete=controls['complete'];matching=controls['matching']
    np.testing.assert_allclose(catalog.laplacian_spectra[chain],2-2*np.cos(np.arange(4)*np.pi/4),atol=1e-12)
    assert catalog.diameter[chain]==3
    assert catalog.triangles[complete]==4
    assert catalog.clustering[complete]==1
    assert catalog.transitivity[complete]==1
    assert catalog.components[matching]==2
    assert catalog.diameter[matching]==-1
    assert catalog.distance[matching,0,2]==-1
    assert catalog.distance[matching,0,1]==1
    assert catalog.clustering[matching]==0


def test_all_n4_label_permutations_preserve_invariant_graph_data():
    catalog=graph_catalog(4)
    permutation=[3,1,0,2]
    for index in range(catalog.graph_count):
        changed=catalog.permute_index(index,permutation)
        np.testing.assert_array_equal(catalog.degrees[changed],catalog.degrees[index,permutation])
        np.testing.assert_array_equal(catalog.distance[changed],catalog.distance[index][np.ix_(permutation,permutation)])
        assert catalog.connected[changed]==catalog.connected[index]
        np.testing.assert_allclose(catalog.laplacian_spectra[changed],catalog.laplacian_spectra[index],atol=1e-12)


def test_born_basis_indexing_and_product_probabilities_are_exact():
    catalog=graph_catalog(3)
    for graph in range(catalog.graph_count):
        state=np.zeros(1 << (catalog.n+catalog.m),dtype=complex)
        state[(5 << catalog.m)|graph]=1
        expected=np.zeros(catalog.graph_count);expected[graph]=1
        np.testing.assert_array_equal(catalog.born(state),expected)
    probabilities=[.2,.4,.7]
    state=np.ones(8)/np.sqrt(8)
    for p in probabilities:
        state=np.kron(state,[np.sqrt(1-p),1j*np.sqrt(p)])
    expected=[]
    for index in range(8):
        value=1.
        for edge,p in enumerate(probabilities):
            value*=p if ((index >> (2-edge))&1) else 1-p
        expected.append(value)
    np.testing.assert_allclose(catalog.born(state),expected,atol=1e-15)


@pytest.mark.parametrize('n',[4,5])
def test_nulls_preserve_their_declared_marginals_and_degree_classes(n):
    catalog=graph_catalog(n)
    rng=np.random.default_rng(71004+n)
    p=rng.random(catalog.graph_count);p/=p.sum()
    nulls=catalog.nulls(p)
    assert set(nulls)=={'density','product','count','degree'}
    for q in nulls.values():
        assert q.sum()==pytest.approx(1)
        assert np.min(q)>=0
    np.testing.assert_allclose(nulls['product'] @ catalog.graph_bits,p @ catalog.graph_bits,atol=1e-13)
    assert nulls['density'] @ catalog.edge_count==pytest.approx(p @ catalog.edge_count)
    for count in range(catalog.m+1):
        selected=catalog.edge_count==count
        assert nulls['count'][selected].sum()==pytest.approx(p[selected].sum())
        np.testing.assert_allclose(nulls['count'][selected],np.mean(p[selected]),atol=1e-15)
    groups={tuple(degrees) for degrees in catalog.degrees}
    for degrees in groups:
        selected=np.all(catalog.degrees==degrees,axis=1)
        assert nulls['degree'][selected].sum()==pytest.approx(p[selected].sum())
        np.testing.assert_allclose(nulls['degree'][selected],np.mean(p[selected]),atol=1e-15)


def test_uniform_graph_law_is_fixed_by_every_null_and_summary_is_exact():
    catalog=graph_catalog(4)
    p=np.full(catalog.graph_count,1/catalog.graph_count)
    for q in catalog.nulls(p).values():
        np.testing.assert_allclose(q,p,atol=1e-15)
    summary=catalog.summarize(p)
    np.testing.assert_allclose(summary['occupation'],.5)
    np.testing.assert_allclose(summary['occupation_covariance'],np.eye(catalog.m)/4,atol=1e-15)
    assert summary['expected_edge_count']==3
    assert summary['edge_count_variance']==1.5
    assert summary['connected_probability']==38/64
    assert summary['expected_triangles']==.5
    assert summary['degree_distribution'].sum()==pytest.approx(1)
    assert summary['connected_diameter_distribution'].sum()==pytest.approx(38/64)
    for comparison in catalog.compare_nulls(p).values():
        assert all(abs(value)<1e-14 for value in comparison.values())


def test_empty_summary_and_extreme_probability_nulls_have_no_nan():
    catalog=graph_catalog(4)
    for index in (0,catalog.graph_count-1):
        p=np.zeros(catalog.graph_count);p[index]=1
        for q in catalog.nulls(p).values():
            np.testing.assert_array_equal(q,p)
    p=np.zeros(catalog.graph_count);p[0]=1
    summary=catalog.summarize(p)
    assert summary['connected_mean_diameter'] is None
    assert summary['expected_components']==4
    assert summary['largest_component_fraction']==.25
    assert summary['expected_isolated_vertices']==4
    np.testing.assert_array_equal(summary['expected_ball_sizes'],np.ones((4,4)))


def test_cycle_forcing_on_n5_and_degree_degeneracy_on_n6():
    five=graph_catalog(5)
    chosen=np.all(five.degrees==2,axis=1)
    assert chosen.sum()==math.factorial(4)//2
    assert np.all(five.connected[chosen])
    p=chosen/chosen.sum()
    np.testing.assert_allclose(five.nulls(p)['degree'],p,atol=1e-15)
    six=graph_catalog(6)
    selected=np.all(six.degrees==2,axis=1)&six.connected
    p=selected/selected.sum()
    assert six.nulls(p)['degree'] @ six.connected==pytest.approx(6/7)
    result=classical_degree_two_degeneracy()
    assert result['connected_cycles']==60
    assert result['disconnected_triangle_pairs']==10
    assert result['connected_matter_microstates']==120
    assert result['disconnected_matter_microstates']==40
    assert result['canonical_zero_temperature_connectivity']==.75
    np.testing.assert_allclose(result['cycle_spectrum'],[0,1,1,3,3,4],atol=1e-12)
    np.testing.assert_allclose(result['triangles_spectrum'],[0,0,3,3,3,3],atol=1e-12)
    assert int(six.connected.sum())==connected_graph_count(6)


def test_small_size_degree_null_connectivity_has_exact_path_selection_limitation():
    # With no isolates, a disconnected N5 graph can only split into 2+3.
    # It has at most four edges. The only potentially connected degree class
    # is (1,1,2,2,2): six P5 graphs and one triangle-plus-edge per labeled vector.
    for n in (4,5):
        catalog=graph_catalog(n)
        mixed=[]
        for degrees in {tuple(d) for d in catalog.degrees}:
            selected=np.all(catalog.degrees==degrees,axis=1)
            connected=int(np.count_nonzero(catalog.connected[selected]))
            total=int(selected.sum())
            if 0<connected<total:mixed.append((degrees,connected,total))
        if n==4:
            assert mixed==[]
        else:
            assert len(mixed)==math.comb(5,2)
            assert all(sorted(degrees)==[1,1,2,2,2] and connected==6 and total==7
                       for degrees,connected,total in mixed)


def test_degree_identifiability_report_matches_independently_constructed_paths_and_triangle():
    four=degree_connectivity_identifiability(4)
    assert four['ambiguous_degree_class_count']==0
    assert four['maximum_connectivity_advantage']==0
    assert four['minimum_ambiguous_class_mass_for_registered_advantage'] is None
    five=degree_connectivity_identifiability(5)
    assert five['ambiguous_degree_class_count']==10
    assert five['maximum_connectivity_advantage']==pytest.approx(1/7)
    assert five['minimum_ambiguous_class_mass_for_registered_advantage']==pytest.approx(.7)
    catalog=graph_catalog(5)
    paths=set()
    for middle in permutations((1,2,3)):
        sequence=(0,)+middle+(4,)
        adjacency=np.zeros((5,5),int)
        for i,j in zip(sequence[:-1],sequence[1:]):adjacency[i,j]=adjacency[j,i]=1
        paths.add(catalog.index(adjacency))
    triangle_edge=np.zeros((5,5),int)
    triangle_edge[0,4]=triangle_edge[4,0]=1
    for i,j in combinations((1,2,3),2):triangle_edge[i,j]=triangle_edge[j,i]=1
    expected_disconnected=catalog.index(triangle_edge)
    found=next(row for row in five['ambiguous_degree_classes'] if row['degrees']==[1,2,2,2,1])
    assert set(found['connected_graph_indices'])==paths
    assert found['disconnected_graph_indices']==[expected_disconnected]


def test_born_draws_are_unselected_reproducible_and_include_disconnected_graphs():
    catalog=graph_catalog(4)
    p=np.zeros(catalog.graph_count);p[0]=.999;p[-1]=.001
    a=catalog.sample(p,np.random.default_rng(71011),count=8)
    b=catalog.sample(p,np.random.default_rng(71011),count=8)
    np.testing.assert_array_equal(a,b)
    assert np.all(a==0)


def tensor(operators):
    answer=np.array([[1]],dtype=complex)
    for operator in operators:answer=np.kron(answer,operator)
    return answer


def single_operator(operator,site,n):
    return tensor([operator if i==site else np.eye(2) for i in range(n)])


def dense_control(adjacency,h,g,times):
    n=len(adjacency);d=2**n
    x=np.array([[0,1],[1,0]],complex)
    y=np.array([[0,-1j],[1j,0]],complex)
    z=np.diag([1,-1]).astype(complex)
    operators=[[single_operator(pauli,i,n) for pauli in (x,y,z)] for i in range(n)]
    H=np.zeros((d,d),complex)
    for i in range(n):
        H-=h*operators[i][0]
        for j in range(i+1,n):H-=g*adjacency[i,j]*(operators[i][2] @ operators[j][2])
    initial=np.array([1.])
    for i in range(n):initial=np.kron(initial,[np.cos(np.pi/8),np.sin(np.pi/8)])
    baseline=np.zeros((len(times),n,3))
    probe=np.zeros((len(times),n,n,3))
    for tindex,time in enumerate(times):
        U=expm(-1j*H*time)
        states=[U@initial]+[U@operators[source][1]@initial for source in range(n)]
        for branch,state in enumerate(states):
            for target in range(n):
                bloch=[np.vdot(state,op@state).real for op in operators[target]]
                if branch==0:baseline[tindex,target]=bloch
                else:probe[tindex,branch-1,target]=bloch
    return baseline,probe


@pytest.fixture(scope='module')
def frozen4():
    return FrozenGraphResponse(graph_catalog(4))


def test_frozen_cache_matches_independent_dense_tensor_response(frozen4):
    for name,index in static_controls(frozen4.catalog).items():
        baseline,probe=dense_control(frozen4.catalog.adjacency[index],1,1,frozen4.times)
        np.testing.assert_allclose(frozen4.baseline_bloch[index],baseline,atol=2e-12)
        np.testing.assert_allclose(frozen4.probe_bloch[index],probe,atol=2e-12)
    assert frozen4.maximum_norm_error<1e-12
    assert frozen4.maximum_scaled_energy_drift<1e-12
    assert frozen4.maximum_scaled_parity_drift<1e-12
    assert frozen4.energy_drift.shape==(64,7,5)
    # Y at the source reverses global-X parity, so each branch has its own invariant.
    np.testing.assert_allclose(frozen4.initial_parity[:,1:]+frozen4.initial_parity[:,0,None],0,atol=1e-14)


def test_no_signalling_complete_symmetry_and_disconnected_component_controls(frozen4):
    controls=static_controls(frozen4.catalog)
    np.testing.assert_allclose(frozen4.response[:,0],0,atol=1e-12)
    np.testing.assert_allclose(frozen4.response[controls['empty']],0,atol=1e-12)
    full=frozen4.response[controls['complete']]
    for response in full:
        off=response[~np.eye(4,dtype=bool)]
        np.testing.assert_allclose(off,off[0],atol=1e-12)
    matching=frozen4.response[controls['matching']]
    for i,j in ((0,2),(0,3),(1,2),(1,3)):
        np.testing.assert_allclose(matching[:,i,j],0,atol=1e-12)
    assert matching[2,0,1]>.01
    chain=frozen4.response[controls['chain']]
    assert chain[1,0,1]>chain[1,0,2]>chain[1,0,3]


def test_registered_short_time_tilted_y_slope_equals_supplied_edge():
    cache=FrozenGraphResponse(graph_catalog(3),times=(0.,1e-5,2e-5))
    for index,adjacency in enumerate(cache.catalog.adjacency):
        np.testing.assert_allclose(cache.response[index,1]/1e-5,adjacency,atol=3e-5)
        np.testing.assert_allclose(cache.response[index,2]/2e-5,adjacency,atol=6e-5)


def test_frozen_response_relabel_covariance(frozen4):
    permutation=[3,0,2,1]
    for index in (0,7,15,31,63):
        changed=frozen4.catalog.permute_index(index,permutation)
        np.testing.assert_allclose(frozen4.response[changed],frozen4.response[index][:,permutation][:,:,permutation],atol=1e-12)


def test_unobserved_mixture_distinguishability_is_not_mean_conditional_response(frozen4):
    p=np.full(frozen4.catalog.graph_count,1/frozen4.catalog.graph_count)
    result=frozen4.weighted(p)
    assert result['conditional_response'].shape==(7,4,4)
    assert result['probe_bloch'].shape==(7,4,4,3)
    assert np.all(result['mixture_response']<=result['conditional_response']+1e-12)
    assert np.max(result['conditional_response']-result['mixture_response'])>.01
    # Independent target density-matrix trace norm after weighting all graph branches.
    x=np.array([[0,1],[1,0]],complex);y=np.array([[0,-1j],[1j,0]],complex);z=np.diag([1,-1])
    for time in range(7):
        for source in range(4):
            for target in range(4):
                if source==target:continue
                difference=np.zeros((2,2),complex)
                for graph,weight in enumerate(p):
                    delta=frozen4.probe_bloch[graph,time,source,target]-frozen4.baseline_bloch[graph,time,target]
                    difference+=weight*sum((delta[k]*operator/2 for k,operator in enumerate((x,y,z))),start=np.zeros((2,2),complex))
                expected=np.abs(np.linalg.eigvalsh(difference)).sum()/2
                assert result['mixture_response'][time,source,target]==pytest.approx(expected,abs=1e-12)


def test_single_graph_conditional_and_mixture_responses_coincide(frozen4):
    p=np.zeros(frozen4.catalog.graph_count);p[static_controls(frozen4.catalog)['chain']]=1
    result=frozen4.weighted(p)
    np.testing.assert_allclose(result['mixture_response'],result['conditional_response'],atol=1e-12)


def test_n5_full_graph_cache_and_weighted_bloch_linearity():
    catalog=graph_catalog(5)
    cache=FrozenGraphResponse(catalog,times=(0.,.05,.25))
    assert cache.probe_bloch.shape==(1024,3,5,5,3)
    # Regression allowance for platform-dependent 32-dimensional LAPACK rounding,
    # not a rigorous error bound or a change to the registered 2e-8 criterion.
    # Keep a 1000-fold margin and independently check the worst observed graph.
    assert cache.maximum_scaled_energy_drift<2e-11
    assert cache.maximum_scaled_parity_drift<1e-12
    scaled_drift=np.abs(cache.energy_drift)/np.maximum(1,np.abs(cache.initial_energy))[:,None,:]
    worst_graph=np.unravel_index(np.argmax(scaled_drift),scaled_drift.shape)[0]
    worst_baseline,worst_probe=dense_control(catalog.adjacency[worst_graph],1,1,cache.times)
    np.testing.assert_allclose(cache.baseline_bloch[worst_graph],worst_baseline,rtol=0,atol=2e-11)
    np.testing.assert_allclose(cache.probe_bloch[worst_graph],worst_probe,rtol=0,atol=2e-11)
    controls=static_controls(catalog)
    baseline,probe=dense_control(catalog.adjacency[controls['chain']],1,1,cache.times)
    np.testing.assert_allclose(cache.baseline_bloch[controls['chain']],baseline,atol=2e-12)
    np.testing.assert_allclose(cache.probe_bloch[controls['chain']],probe,atol=2e-12)
    p=np.zeros(1024);q=np.zeros(1024)
    p[controls['chain']]=1;q[controls['matching']]=1
    a,b,mixture=cache.weighted(p),cache.weighted(q),cache.weighted(.3*p+.7*q)
    for key in ('baseline_bloch','probe_bloch','conditional_response'):
        np.testing.assert_allclose(mixture[key],.3*a[key]+.7*b[key],atol=1e-12)
    assert np.all(mixture['mixture_response']<=mixture['conditional_response']+1e-12)


@pytest.mark.parametrize('n',[1,7,3.5,True])
def test_invalid_catalogue_size_rejected(n):
    with pytest.raises(ValueError):GraphCatalog(n)


def test_invalid_graph_state_and_law_inputs_are_rejected():
    catalog=graph_catalog(4)
    with pytest.raises(ValueError):catalog.born(np.ones(10))
    with pytest.raises(ValueError):catalog.born(np.ones(1024))
    with pytest.raises(ValueError):catalog.nulls(np.zeros(64))
    with pytest.raises(ValueError):catalog.summarize(np.full(64,np.nan))
    with pytest.raises(ValueError):catalog.index(np.ones((4,4)))
    with pytest.raises(ValueError):catalog.permute_index(0,[0,1,2,2])
