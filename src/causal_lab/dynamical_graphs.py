"""Exact finite graph laws and explicitly classical frozen-graph probe controls.

Every graph is a possible LINK MEASUREMENT outcome, not an unconditioned quantum
geometry. Frozen controls reset matter to the registered product state. Averaging
conditional distances and taking the distance of a mixture are kept separate.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations
import math

import numpy as np
from scipy.linalg import eigh

from .quantum import tfim_hamiltonian

DELAYS = (0., .05, .1, .25, .5, 1., 2.)


def _probability(probability, size):
    if np.iscomplexobj(probability):
        raise ValueError("graph probabilities must be real")
    p = np.asarray(probability, dtype=float)
    if p.shape != (size,) or not np.all(np.isfinite(p)) or np.min(p) < -1e-12:
        raise ValueError("invalid graph probability vector")
    if abs(float(p.sum())-1) > 2e-9:
        raise ValueError("graph probabilities must sum to one")
    p = np.maximum(p, 0)
    return p/p.sum()


class GraphCatalog:
    """All simple labeled graphs, with lexicographic edges as most-significant bits."""

    def __init__(self, n: int):
        if isinstance(n, bool) or not isinstance(n, (int, np.integer)) or not 2 <= n <= 6:
            raise ValueError("the exact catalogue supports integer N from two through six")
        self.n = int(n)
        self.edges = np.array(list(combinations(range(n), 2)), dtype=np.int8)
        self.m = len(self.edges)
        self.graph_count = 1 << self.m
        masks = 1 << np.arange(self.m-1, -1, -1, dtype=np.int64)
        indices = np.arange(self.graph_count, dtype=np.int64)
        self.graph_bits = ((indices[:, None] & masks) != 0).astype(np.int8)
        self.adjacency = np.zeros((self.graph_count, n, n), dtype=np.int8)
        for edge, (i, j) in enumerate(self.edges):
            self.adjacency[:, i, j] = self.graph_bits[:, edge]
            self.adjacency[:, j, i] = self.graph_bits[:, edge]
        self.degrees = self.adjacency.sum(axis=2).astype(np.int8)
        self.edge_count = self.graph_bits.sum(axis=1).astype(np.int16)
        distance = np.where(self.adjacency, 1, n+1).astype(np.int16)
        distance[:, np.arange(n), np.arange(n)] = 0
        for k in range(n):
            distance = np.minimum(distance, distance[:, :, k, None]+distance[:, None, k, :])
        distance[distance > n] = -1
        self.distance = distance
        reachable = distance >= 0
        labels = np.argmax(reachable, axis=2)
        component_sizes = (labels[:, :, None] == np.arange(n)[None, None, :]).sum(axis=1)
        self.component_sizes = np.sort(component_sizes, axis=1)[:, ::-1].astype(np.int8)
        self.components = np.count_nonzero(self.component_sizes, axis=1).astype(np.int8)
        self.connected = self.components == 1
        self.largest_component_fraction = self.component_sizes[:, 0]/n
        self.isolated_vertices = np.count_nonzero(self.degrees == 0, axis=1).astype(np.int8)
        self.maximum_degree = self.degrees.max(axis=1)
        self.universal_vertices = np.count_nonzero(self.degrees == n-1, axis=1).astype(np.int8)
        self.diameter = np.where(self.connected, distance.max(axis=(1, 2)), -1).astype(np.int16)
        self.ball_sizes = np.stack([np.count_nonzero(reachable & (distance <= radius), axis=2)
                                    for radius in range(n)], axis=2).astype(np.int8)
        integer_adjacency = self.adjacency.astype(np.int16)
        local_triangles = ((integer_adjacency @ integer_adjacency)*integer_adjacency).sum(axis=2)//2
        self.triangles = (local_triangles.sum(axis=1)//3).astype(np.int16)
        wedges = self.degrees*(self.degrees-1)/2
        self.local_clustering = np.divide(local_triangles, wedges, out=np.zeros_like(wedges, dtype=float), where=wedges > 0)
        self.clustering = self.local_clustering.mean(axis=1)
        self.transitivity = np.divide(3*self.triangles, wedges.sum(axis=1),
                                      out=np.zeros(self.graph_count), where=wedges.sum(axis=1) > 0)
        laplacian = -self.adjacency.astype(float)
        laplacian[:, np.arange(n), np.arange(n)] = self.degrees
        self.laplacian_spectra = np.linalg.eigvalsh(laplacian)
        _, self._degree_class, self._degree_class_size = np.unique(
            self.degrees, axis=0, return_inverse=True, return_counts=True)
        self._count_class_size = np.bincount(self.edge_count, minlength=self.m+1)

    def index(self, adjacency):
        """Encode one undirected binary adjacency matrix in the tensor convention."""
        a = np.asarray(adjacency)
        if a.shape != (self.n, self.n) or not np.array_equal(a, a.T):
            raise ValueError("adjacency must be symmetric and match the catalogue")
        if np.any(np.diag(a)) or not np.all((a == 0) | (a == 1)):
            raise ValueError("adjacency must be binary with a zero diagonal")
        answer = 0
        for i, j in self.edges:
            answer = (answer << 1) | int(a[i, j])
        return answer

    def permute_index(self, graph, permutation):
        permutation = np.asarray(permutation)
        if permutation.shape != (self.n,) or sorted(permutation.tolist()) != list(range(self.n)):
            raise ValueError("invalid vertex permutation")
        return self.index(self.adjacency[graph][np.ix_(permutation, permutation)])

    def born(self, state):
        """Trace out matter exactly; axes are matter first, then link factors."""
        psi = np.asarray(state)
        if psi.shape != (1 << (self.n+self.m),) or not np.all(np.isfinite(psi)):
            raise ValueError("state has the wrong full matter-plus-link dimension")
        probabilities = (np.abs(psi.reshape(1 << self.n, self.graph_count))**2).sum(axis=0)
        _probability(probabilities, self.graph_count)  # Validate, without hiding drift.
        return probabilities

    def nulls(self, probability):
        """Exact density, marginal-product, count and labeled-degree null laws."""
        p = _probability(probability, self.graph_count)
        occupations = np.clip(p @ self.graph_bits, 0, 1)
        density = float(occupations.mean())
        q_density = np.prod(np.where(self.graph_bits, density, 1-density), axis=1)
        q_product = np.prod(np.where(self.graph_bits, occupations, 1-occupations), axis=1)
        count_mass = np.bincount(self.edge_count, weights=p, minlength=self.m+1)
        q_count = count_mass[self.edge_count]/self._count_class_size[self.edge_count]
        degree_mass = np.bincount(self._degree_class, weights=p, minlength=len(self._degree_class_size))
        q_degree = degree_mass[self._degree_class]/self._degree_class_size[self._degree_class]
        return dict(density=q_density, product=q_product, count=q_count, degree=q_degree)

    def summarize(self, probability):
        """Exact Born expectations; no graph draw is an independent state sample."""
        p = _probability(probability, self.graph_count)
        occupations = p @ self.graph_bits
        pair_occupations = self.graph_bits.T @ (p[:, None]*self.graph_bits)
        mean_count = float(p @ self.edge_count)
        connected_probability = float(p @ self.connected)
        degree_distribution = np.bincount(self.degrees.ravel(), weights=np.repeat(p/self.n, self.n), minlength=self.n)
        result = dict(
            occupation=occupations, occupation_variance=occupations*(1-occupations),
            occupation_covariance=pair_occupations-np.outer(occupations, occupations),
            occupation_contrast=float(np.ptp(occupations)),
            expected_edge_count=mean_count, edge_count_variance=float(p @ (self.edge_count-mean_count)**2),
            edge_count_distribution=np.bincount(self.edge_count, weights=p, minlength=self.m+1),
            expected_degrees=p @ self.degrees, degree_distribution=degree_distribution,
            connected_probability=connected_probability,
            expected_components=float(p @ self.components),
            component_count_distribution=np.bincount(self.components, weights=p, minlength=self.n+1),
            expected_sorted_component_sizes=p @ self.component_sizes,
            largest_component_fraction=float(p @ self.largest_component_fraction),
            largest_component_size_distribution=np.bincount(self.component_sizes[:, 0], weights=p, minlength=self.n+1),
            expected_isolated_vertices=float(p @ self.isolated_vertices),
            probability_any_isolated=float(p @ (self.isolated_vertices > 0)),
            expected_maximum_degree=float(p @ self.maximum_degree),
            expected_universal_vertices=float(p @ self.universal_vertices),
            expected_triangles=float(p @ self.triangles),
            expected_clustering=float(p @ self.clustering), expected_transitivity=float(p @ self.transitivity),
            connected_mean_diameter=float(p[self.connected] @ self.diameter[self.connected]/connected_probability)
                if connected_probability else None,
            connected_diameter_distribution=np.bincount(self.diameter[self.connected], weights=p[self.connected], minlength=self.n),
            expected_ball_sizes=np.einsum('g,gir->ir', p, self.ball_sizes),
            mean_sorted_laplacian_eigenvalues=p @ self.laplacian_spectra,
        )
        return result

    def compare_nulls(self, probability):
        """Distribution distance and explicitly oriented P-minus-null contrasts."""
        p = _probability(probability, self.graph_count)
        fields = dict(connected_probability=self.connected, expected_edge_count=self.edge_count,
            expected_components=self.components, largest_component_fraction=self.largest_component_fraction,
            expected_triangles=self.triangles, expected_clustering=self.clustering)
        return {name:dict(total_variation=float(np.abs(p-q).sum()/2),
                          **{key+'_advantage':float((p-q) @ values) for key,values in fields.items()})
                for name,q in self.nulls(p).items()}

    def sample(self, probability, rng, count=8):
        if not isinstance(rng, np.random.Generator) or not isinstance(count, (int,np.integer)) or count < 0:
            raise ValueError("an explicit generator and nonnegative sample count are required")
        return rng.choice(self.graph_count, size=count, p=_probability(probability, self.graph_count))

    def as_arrays(self):
        return {name:value for name,value in vars(self).items() if isinstance(value,np.ndarray) and not name.startswith('_')}


@lru_cache(maxsize=3)
def graph_catalog(n):
    return GraphCatalog(n)


def static_controls(catalog):
    """Named supplied graph patterns; none initializes the primary quantum law."""
    n = catalog.n
    chain = np.zeros((n,n), dtype=np.int8)
    for i in range(n-1):
        chain[i,i+1] = chain[i+1,i] = 1
    matching = np.zeros_like(chain)
    for i in range(0,n-1,2):
        matching[i,i+1] = matching[i+1,i] = 1
    result = dict(chain=catalog.index(chain), complete=catalog.graph_count-1,
                  empty=0, matching=catalog.index(matching))
    if n >= 6:
        triangles = np.zeros_like(chain)
        for group in (range(3),range(3,6)):
            for i,j in combinations(group,2):
                triangles[i,j] = triangles[j,i] = 1
        result['triangles'] = catalog.index(triangles)
    return result


def classical_degree_two_degeneracy():
    """N6 zero-field degree-two Gibbs counting, including matter multiplicities."""
    catalog = graph_catalog(6)
    selected = np.all(catalog.degrees == 2, axis=1)
    connected = selected & catalog.connected
    disconnected = selected & ~catalog.connected
    connected_graphs = int(connected.sum())
    disconnected_graphs = int(disconnected.sum())
    weights = 2.**catalog.components
    return dict(n=6, degree_two_graphs=int(selected.sum()), connected_cycles=connected_graphs,
        disconnected_triangle_pairs=disconnected_graphs,
        connected_matter_microstates=int(weights[connected].sum()),
        disconnected_matter_microstates=int(weights[disconnected].sum()),
        canonical_zero_temperature_connectivity=float(weights[connected].sum()/weights[selected].sum()),
        uniform_graph_connectivity=connected_graphs/int(selected.sum()),
        cycle_spectrum=catalog.laplacian_spectra[np.flatnonzero(connected)[0]],
        triangles_spectrum=catalog.laplacian_spectra[np.flatnonzero(disconnected)[0]])


def degree_connectivity_identifiability(n):
    """Exact N4/N5 limitation of connectivity advantage over the degree null.

    N5 has only ten mixed classes, each six paths plus one triangle/edge graph.
    Thus a connectivity advantage of .1 already demands at least .7 probability
    in these path-degree classes. This is a finite-screen selection restriction,
    not a physical definition of geometry or a change to the registered gate.
    """
    if n not in (4,5):
        raise ValueError("this exact interpretation is registered for N4 and N5")
    catalog=graph_catalog(n)
    degree_vectors=np.unique(catalog.degrees,axis=0)
    mixed=[]
    for degrees in degree_vectors:
        indices=np.flatnonzero(np.all(catalog.degrees==degrees,axis=1))
        connected=indices[catalog.connected[indices]]
        disconnected=indices[~catalog.connected[indices]]
        if len(connected) and len(disconnected):
            mixed.append(dict(degrees=degrees.tolist(),connected_graphs=len(connected),
                disconnected_graphs=len(disconnected),
                connected_graph_indices=connected.tolist(),disconnected_graph_indices=disconnected.tolist(),
                degree_null_connectivity=len(connected)/len(indices)))
    maximum=max((1-row['degree_null_connectivity'] for row in mixed),default=0.)
    return dict(n=n,total_degree_classes=len(degree_vectors),
        ambiguous_degree_class_count=len(mixed),ambiguous_degree_classes=mixed,
        ambiguous_degree_multisets=[list(d) for d in sorted({tuple(sorted(row['degrees'])) for row in mixed})],
        maximum_connectivity_advantage=maximum,
        registered_advantage_threshold=.1,
        minimum_ambiguous_class_mass_for_registered_advantage=.1/maximum if maximum else None,
        connectivity_advantage_possible=bool(mixed),
        proof=('Without isolated vertices a disconnected N5 graph splits into two and three vertices '
               'and has at most four edges. A possibly connected class therefore consists only of '
               'six P5 paths and one C3 plus K2, with fixed labeled degrees (1,1,2,2,2). '
               'For N4 every full-degree class has fixed connectivity.'),
        interpretation='Finite-size identifiability and gate restriction; not a criterion defining physical locality.')


def tilted_matter(n):
    state = np.array([1.],dtype=complex)
    factor = np.array([math.cos(math.pi/8),math.sin(math.pi/8)])
    for _ in range(n):
        state = np.kron(state,factor)
    return state


def _pauli_y(state, site, n):
    tensor = np.moveaxis(state.reshape((2,)*n),site,0)
    changed = np.stack((-1j*tensor[1],1j*tensor[0]))
    return np.moveaxis(changed,0,site).reshape(-1)


def _bloch(vectors, n):
    # Input (time, branch, basis), output (time, branch, target, XYZ).
    indices = np.arange(1 << n)
    answer = np.empty(vectors.shape[:2]+(n,3))
    for site in range(n):
        mask = 1 << (n-1-site)
        zero = indices[(indices & mask) == 0]
        one = zero | mask
        cross = (vectors[:,:,zero].conj()*vectors[:,:,one]).sum(axis=2)
        answer[:,:,site,0] = 2*cross.real
        answer[:,:,site,1] = 2*cross.imag
        answer[:,:,site,2] = (np.abs(vectors[:,:,zero])**2-np.abs(vectors[:,:,one])**2).sum(axis=2)
    return answer


class FrozenGraphResponse:
    """Cache exact fresh-matter TFIM probes for EVERY graph, with no postselection."""

    def __init__(self, catalog, *, h=1., g=1., times=DELAYS):
        self.catalog = catalog
        self.n = catalog.n
        self.h, self.g = float(h), float(g)
        self.times = np.asarray(times,dtype=float)
        if (self.times.ndim != 1 or not len(self.times) or not np.all(np.isfinite(self.times))
                or np.any(self.times < 0) or np.any(np.diff(self.times) <= 0)
                or not np.isfinite(h) or not np.isfinite(g)):
            raise ValueError("finite fields and increasing nonnegative probe times required")
        n = self.n
        initial = tilted_matter(n)
        branches = np.column_stack([initial]+[_pauli_y(initial,i,n) for i in range(n)])
        shape = (catalog.graph_count,len(self.times))
        self.baseline_bloch = np.empty(shape+(n,3))
        self.probe_bloch = np.empty(shape+(n,n,3))
        self.norm_error = np.empty(shape+(n+1,))
        self.energy_drift = np.empty(shape+(n+1,))
        self.parity_drift = np.empty(shape+(n+1,))
        self.initial_energy = np.empty((catalog.graph_count,n+1))
        self.initial_parity = np.empty((catalog.graph_count,n+1))
        self.maximum_norm_error = 0.
        self.maximum_scaled_energy_drift = 0.
        self.maximum_scaled_parity_drift = 0.
        for index, adjacency in enumerate(catalog.adjacency):
            H = tfim_hamiltonian(g*adjacency,h).toarray()
            energies, vectors = eigh(H,driver='evr')
            coefficients = vectors.conj().T @ branches
            phases = np.exp(-1j*self.times[:,None]*energies[None,:])
            evolved = np.einsum('ab,tbc->tac',vectors,phases[:,:,None]*coefficients[None,:,:]).transpose(0,2,1)
            initial_energy = np.einsum('dk,dk->k',branches.conj(),H@branches).real
            initial_parity = np.einsum('dk,dk->k',branches.conj(),branches[::-1]).real
            energy = np.einsum('tkd,dq,tkq->tk',evolved.conj(),H,evolved).real
            parity = (evolved.conj()*evolved[:,:,::-1]).sum(axis=2).real
            self.norm_error[index] = (np.abs(evolved)**2).sum(axis=2)-1
            self.energy_drift[index] = energy-initial_energy[None,:]
            self.parity_drift[index] = parity-initial_parity[None,:]
            self.initial_energy[index] = initial_energy
            self.initial_parity[index] = initial_parity
            self.maximum_norm_error = max(self.maximum_norm_error,float(np.max(np.abs(self.norm_error[index]))))
            self.maximum_scaled_energy_drift = max(self.maximum_scaled_energy_drift,
                float(np.max(np.abs(self.energy_drift[index])/np.maximum(1,np.abs(initial_energy))[None,:])))
            self.maximum_scaled_parity_drift = max(self.maximum_scaled_parity_drift,
                float(np.max(np.abs(self.parity_drift[index])/np.maximum(1,np.abs(initial_parity))[None,:])))
            bloch = _bloch(evolved,n)
            self.baseline_bloch[index] = bloch[:,0]
            self.probe_bloch[index] = bloch[:,1:]
        self.response = np.linalg.norm(self.probe_bloch-self.baseline_bloch[:,:,None,:,:],axis=-1)/2
        self.response[:,:,np.arange(n),np.arange(n)] = 0
        if self.maximum_norm_error > 2e-9:
            raise ArithmeticError("frozen-graph eigensystem propagation lost normalization")
        if self.maximum_scaled_energy_drift > 2e-8 or self.maximum_scaled_parity_drift > 2e-8:
            raise ArithmeticError("frozen-graph eigensystem propagation violated a conserved quantity")

    def weighted(self, probability):
        p = _probability(probability,self.catalog.graph_count)
        baseline = np.tensordot(p,self.baseline_bloch,axes=(0,0))
        probe = np.tensordot(p,self.probe_bloch,axes=(0,0))
        mixture = np.linalg.norm(probe-baseline[:,None,:,:],axis=-1)/2
        mixture[:,np.arange(self.n),np.arange(self.n)] = 0
        conditional = np.tensordot(p,self.response,axes=(0,0))
        return dict(conditional_response=conditional, mixture_response=mixture,
                    baseline_bloch=baseline, probe_bloch=probe)


@lru_cache(maxsize=3)
def frozen_graph_response(n, h=1., g=1., times=DELAYS):
    return FrozenGraphResponse(graph_catalog(n),h=h,g=g,times=times)
