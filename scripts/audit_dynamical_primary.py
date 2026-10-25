#!/usr/bin/env python3
"""Independent Experiment 7 archive audit; imports no causal_lab implementation.

Reconstructs exact graph laws, reduced-state trace distances, registered gates and
binomial intervals. Direct basis-index operators audit checkpoints and regenerate
fixed selected states. Audit replay is not additional independent physical evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import gzip
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import subprocess
import time

import numpy as np
from scipy.linalg import eigh
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import expm_multiply

AGES = (0., .5, 1., 2., 3., 4.)
DELAYS = (0., .05, .1, .25, .5, 1., 2.)
CELLS = tuple((mu, gamma) for mu in (2., .1, -2.) for gamma in (.25, 1.))
STREAMS = {'smoke': 1, 'calibration': 2, 'pilot': 3, 'primary': 4, 'audit': 5}
TOL = 5e-8
X = np.array([[0, 1], [1, 0]], complex)
Y = np.array([[0, -1j], [1j, 0]], complex)
Z = np.diag([1., -1.]).astype(complex)
I = np.eye(2, dtype=complex)
OCC = np.diag([0., 1.]).astype(complex)


class Audit:
    def __init__(self, tolerance=TOL):
        self.tolerance = tolerance
        self.counts = Counter()
        self.maximum_errors = {}
        self.failures = []

    def require(self, condition, category, label):
        self.counts[category] += 1
        if not bool(condition):
            self.failures.append({'category': category, 'label': str(label)})

    def close(self, observed, expected, category, label='', tolerance=None):
        self.counts['numerical_comparisons'] += 1
        if observed is None or expected is None:
            self.require(observed is None and expected is None, category, label)
            return
        a, b = np.asarray(observed), np.asarray(expected)
        if a.shape != b.shape or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
            self.require(False, category, str(label)+' shape/nonfinite discrepancy')
            return
        error = float(np.max(np.abs(a.astype(complex)-b.astype(complex)))) if a.size else 0.
        self.maximum_errors[category] = max(self.maximum_errors.get(category, 0.), error)
        self.counts[category] += int(a.size)
        bound = self.tolerance if tolerance is None else tolerance
        if error > bound:
            self.failures.append({'category': category, 'label': str(label),
                                  'maximum_error': error, 'tolerance': bound})

    def probability(self, p, label):
        self.require(np.all(np.isfinite(p)) and np.min(p) >= -2e-9,
                     'finite_probability', label)
        self.close(float(np.sum(p)), 1., 'probability_normalization', label, 2e-9)

    def report(self):
        return dict(passed=not self.failures, counts=dict(sorted(self.counts.items())),
                    maximum_errors=dict(sorted(self.maximum_errors.items())),
                    failure_count=len(self.failures), failures=self.failures,
                    tolerance=self.tolerance)


def binomial_mass(n, p):
    return np.array([math.comb(n, k)*p**k*(1-p)**(n-k) for k in range(n+1)])


def cp_bounds(k, n, family, alpha=.05):
    """Invert elementary finite-binomial tails by bisection, without beta quantiles."""
    if n < 1 or not 0 <= k <= n or family < 1:
        raise ValueError('invalid binomial parameters')
    tail = alpha/(2*family)
    low = 0.
    if k:
        left, right = 0., 1.
        for _ in range(80):
            middle = (left+right)/2
            if sum(binomial_mass(n, middle)[k:]) < tail:
                left = middle
            else:
                right = middle
        low = (left+right)/2
    high = 1.
    if k < n:
        left, right = 0., 1.
        for _ in range(80):
            middle = (left+right)/2
            if sum(binomial_mass(n, middle)[:k+1]) > tail:
                left = middle
            else:
                right = middle
        high = (left+right)/2
    return [low, high]


def finite_score(response):
    """Literal top-two mass with fractional boundary ties, excluding the diagonal."""
    a = np.asarray(response, float)
    n = len(a)
    weights = np.zeros_like(a)
    fractions = []
    for source in range(n):
        indices = [j for j in range(n) if j != source]
        values = [float(a[source, j]) for j in indices]
        if not all(math.isfinite(v) and v >= -1e-10 for v in values):
            return None, None, weights
        boundary = sorted(values, reverse=True)[1]
        certain = [j for j in indices if a[source, j] > boundary+1e-10]
        ties = [j for j in indices if abs(a[source, j]-boundary) <= 1e-10]
        for j in certain:
            weights[source, j] = 1.
        for j in ties:
            weights[source, j] = (2-len(certain))/len(ties)
        total = sum(values)
        fractions.append(None if total <= 1e-10 else
                         sum(weights[source, j]*a[source, j] for j in indices)/total)
    f = None if any(x is None for x in fractions) else sum(fractions)/n
    mean = sum(a[i, j] for i in range(n) for j in range(n) if i != j)/(n*(n-1))
    return f, float(mean), weights


def graph_catalog(n):
    """Independent integer graph construction, BFS components/distances and triples."""
    edges = list(combinations(range(n), 2)); count = 1 << len(edges)
    bits = np.array([[int(bool(mask & (1 << (len(edges)-1-e))))
                      for e in range(len(edges))] for mask in range(count)], dtype=np.int8)
    adj = np.zeros((count, n, n), dtype=np.int8)
    for mask in range(count):
        for present, (u, v) in zip(bits[mask], edges):
            adj[mask, u, v] = adj[mask, v, u] = present
    degrees = adj.sum(2)
    distances = np.full((count, n, n), -1, dtype=int)
    sizes = np.zeros((count, n), dtype=int)
    triangles = np.zeros(count, dtype=int)
    local_clustering = np.zeros((count, n))
    spectra = np.zeros((count, n))
    for mask, a in enumerate(adj):
        for start in range(n):
            distances[mask, start, start] = 0
            queue = deque([start])
            while queue:
                u = queue.popleft()
                for v in range(n):
                    if a[u, v] and distances[mask, start, v] < 0:
                        distances[mask, start, v] = distances[mask, start, u]+1
                        queue.append(v)
        unseen = set(range(n)); component_sizes = []
        while unseen:
            start = min(unseen)
            component = {v for v in unseen if distances[mask, start, v] >= 0}
            component_sizes.append(len(component)); unseen -= component
        sizes[mask, :len(component_sizes)] = sorted(component_sizes, reverse=True)
        for u, v, w in combinations(range(n), 3):
            triangles[mask] += int(a[u, v] and a[u, w] and a[v, w])
        for u in range(n):
            neighbors = [v for v in range(n) if a[u, v]]
            pairs = list(combinations(neighbors, 2))
            local_clustering[mask, u] = sum(a[v, w] for v, w in pairs)/len(pairs) if pairs else 0.
        spectra[mask] = np.linalg.eigvalsh(np.diag(degrees[mask])-a)
    classes = {}; class_ids = []
    for d in degrees:
        key = tuple(d)
        if key not in classes:
            classes[key] = len(classes)
        class_ids.append(classes[key])
    component_count = np.count_nonzero(sizes, axis=1)
    connected = component_count == 1
    wedges = (degrees*(degrees-1)/2).sum(1)
    transitivity = np.divide(3*triangles, wedges, out=np.zeros(count), where=wedges > 0)
    return dict(n=n, edges=edges, graph_bits=bits, adjacency=adj, degrees=degrees,
        edge_count=bits.sum(1), distance=distances, component_sizes=sizes,
        components=component_count, connected=connected,
        largest_component_fraction=sizes[:, 0]/n,
        isolated_vertices=(degrees == 0).sum(1), maximum_degree=degrees.max(1),
        universal_vertices=(degrees == n-1).sum(1),
        diameter=np.where(connected, distances.max(axis=(1, 2)), -1),
        ball_sizes=np.stack([((distances >= 0)&(distances <= r)).sum(2) for r in range(n)], axis=2),
        triangles=triangles, local_clustering=local_clustering,
        clustering=local_clustering.mean(1), transitivity=transitivity,
        laplacian_spectra=spectra, classes=np.array(class_ids))


def null_laws(p, catalog):
    p = np.asarray(p)/sum(p); bits = catalog['graph_bits']
    occupation = p@bits; density = occupation.mean()
    output = dict(density=np.prod(np.where(bits, density, 1-density), axis=1),
                  product=np.prod(np.where(bits, occupation, 1-occupation), axis=1))
    for name, labels in [('count', catalog['edge_count']), ('degree', catalog['classes'])]:
        total = np.bincount(labels, weights=p)
        size = np.bincount(labels)
        output[name] = total[labels]/size[labels]
    return output


def graph_properties(p, c):
    p = np.asarray(p)/sum(p); n = c['n']; bits = c['graph_bits']
    occupation = p@bits; count = float(p@c['edge_count'])
    connected = float(p@c['connected']); degree = c['degrees']
    result = dict(occupation=occupation, occupation_variance=occupation*(1-occupation),
        occupation_covariance=np.einsum('g,ge,gf->ef', p, bits, bits)-np.outer(occupation, occupation),
        occupation_contrast=float(max(occupation)-min(occupation)),
        expected_edge_count=count, edge_count_variance=float(p@(c['edge_count']-count)**2),
        edge_count_distribution=np.bincount(c['edge_count'], weights=p, minlength=bits.shape[1]+1),
        expected_degrees=p@degree,
        degree_distribution=np.array([sum(p[g]*np.count_nonzero(degree[g] == k)/n
                                         for g in range(len(p))) for k in range(n)]),
        connected_probability=connected, expected_components=float(p@c['components']),
        component_count_distribution=np.bincount(c['components'], weights=p, minlength=n+1),
        expected_sorted_component_sizes=p@c['component_sizes'],
        largest_component_fraction=float(p@c['largest_component_fraction']),
        largest_component_size_distribution=np.bincount(c['component_sizes'][:, 0], weights=p, minlength=n+1),
        expected_isolated_vertices=float(p@c['isolated_vertices']),
        probability_any_isolated=float(p@(c['isolated_vertices'] > 0)),
        expected_maximum_degree=float(p@c['maximum_degree']),
        expected_universal_vertices=float(p@c['universal_vertices']),
        expected_triangles=float(p@c['triangles']), expected_clustering=float(p@c['clustering']),
        expected_transitivity=float(p@c['transitivity']),
        connected_mean_diameter=float(p[c['connected']]@c['diameter'][c['connected']]/connected) if connected else None,
        connected_diameter_distribution=np.bincount(c['diameter'][c['connected']], weights=p[c['connected']], minlength=n),
        expected_ball_sizes=np.einsum('g,gir->ir', p, c['ball_sizes']),
        mean_sorted_laplacian_eigenvalues=p@c['laplacian_spectra'])
    return result


def tensor_operator(q, operators):
    value = np.ones((1, 1), complex)
    for axis in range(q):
        value = np.kron(value, operators.get(axis, I))
    return value


def dense_tensor_hamiltonian(n, h, g, gamma, mu, congestion):
    edges = list(combinations(range(n), 2)); q = n+len(edges)
    matrix = np.zeros((1 << q, 1 << q), complex)
    for i in range(n):
        matrix -= h*tensor_operator(q, {i: X})
    for e, (i, j) in enumerate(edges):
        matrix -= g*tensor_operator(q, {n+e: OCC, i: Z, j: Z})
        matrix -= gamma*tensor_operator(q, {n+e: X})
        matrix += mu*tensor_operator(q, {n+e: OCC})
    for a, b in combinations(range(len(edges)), 2):
        if set(edges[a])&set(edges[b]):
            matrix += congestion*tensor_operator(q, {n+a: OCC, n+b: OCC})
    return matrix


def independent_hamiltonian(n, params):
    """Assemble matrix entries directly from every full basis label."""
    edges = list(combinations(range(n), 2)); q = n+len(edges); dimension = 1 << q
    labels = np.arange(dimension, dtype=np.int64)
    signs = [1-2*((labels >> (q-1-i))&1) for i in range(n)]
    degrees = np.zeros((n, dimension), dtype=np.int16)
    diagonal = np.zeros(dimension)
    for e, (i, j) in enumerate(edges):
        occupied = (labels >> (q-1-n-e))&1
        diagonal += occupied*(params['mu']-params['g']*signs[i]*signs[j])
        degrees[i] += occupied; degrees[j] += occupied
    diagonal += params['U']*sum(d*(d-1)/2 for d in degrees)
    rows = [labels]; columns = [labels]; data = [diagonal]
    for axis in range(q):
        strength = params['h'] if axis < n else params['Gamma']
        if strength:
            rows.append(labels); columns.append(labels ^ (1 << (q-1-axis)))
            data.append(np.full(dimension, -strength))
    matrix = coo_matrix((np.concatenate(data), (np.concatenate(rows), np.concatenate(columns))),
                        shape=(dimension, dimension)).tocsr()
    return matrix


def partials(state, n):
    """Explicit basis-index one-qubit matrices, independent of tensor reshaping."""
    q = n+n*(n-1)//2; labels = np.arange(len(state))
    matrices = []; bloch = []
    for target in range(n):
        bit = 1 << (q-1-target)
        zero = labels[(labels&bit) == 0]; one = zero | bit
        rho = np.array([[np.vdot(state[zero], state[zero]), np.vdot(state[one], state[zero])],
                        [np.vdot(state[zero], state[one]), np.vdot(state[one], state[one])]])
        matrices.append(rho)
        bloch.append([float(np.trace(rho@operator).real) for operator in (X, Y, Z)])
    return np.array(matrices), np.array(bloch)


def born_from_state(state, n):
    m = n*(n-1)//2; law = np.zeros(1 << m)
    # Accumulate by low edge bits; no production partial-trace or Born helper.
    np.add.at(law, np.arange(len(state))&((1 << m)-1), abs(state)**2)
    return law


def joint_moments(state, n):
    q = n+n*(n-1)//2; labels = np.arange(len(state)); edges = list(combinations(range(n), 2))
    zx = np.zeros((n, n)); zy = np.zeros((n, n))
    for source in range(n):
        for target in range(n):
            if source == target:
                continue
            e = edges.index(tuple(sorted((source, target))))
            target_bit = 1 << (q-1-target)
            zero = labels[(labels&target_bit) == 0]; one = zero | target_bit
            occupation = (zero >> (q-1-n-e))&1
            sign = 1-2*((zero >> (q-1-source))&1)
            coherence = np.sum(state[zero].conj()*state[one]*occupation*sign)
            zx[source, target], zy[source, target] = 2*coherence.real, 2*coherence.imag
    return zx, zy


def kick(state, n, source):
    q = n+n*(n-1)//2; labels = np.arange(len(state)); bit = 1 << (q-1-source)
    # Output coefficient is -i for a zero target bit and +i for a one target bit.
    return np.where(labels&bit, 1j, -1j)*state[labels ^ bit]


def prepare(n, probabilities, phases):
    factors = [np.array([math.cos(math.pi/8), math.sin(math.pi/8)])]*n
    factors += [np.array([math.sqrt(1-p), np.exp(1j*phase)*math.sqrt(p)])
                for p, phase in zip(probabilities, phases)]
    state = np.array([1.], complex)
    for factor in factors:
        state = np.kron(state, factor)
    return state


def advance(matrix, state, duration, maximum_step=.25):
    steps = max(1, math.ceil(abs(duration)/maximum_step)); dt = duration/steps
    result = state
    for _ in range(steps):
        result = expm_multiply(-1j*dt*matrix, result, traceA=-1j*dt*matrix.diagonal().sum())
    return result


def distances_from_bloch(baseline, probes, zero_diagonal=False):
    difference = np.asarray(probes)-np.asarray(baseline)[..., None, :, :]
    matrix = np.empty(difference.shape[:-1]+(2, 2), complex)
    matrix[..., 0, 0] = difference[..., 2]/2
    matrix[..., 1, 1] = -difference[..., 2]/2
    matrix[..., 0, 1] = (difference[..., 0]-1j*difference[..., 1])/2
    matrix[..., 1, 0] = matrix[..., 0, 1].conj()
    distance = np.abs(np.linalg.eigvalsh(matrix)).sum(-1)/2
    if zero_diagonal:
        size = distance.shape[-1]; distance[..., np.arange(size), np.arange(size)] = 0
    return distance


def registered_gate(arrays, catalog):
    born = arrays['full_born']; connected = born@catalog['connected']
    tv = [.5*sum(abs(born[3]-born[4])), .5*sum(abs(born[4]-born[5]))]
    details = []; local = []; stable = []; advantage = []
    for delay in (.25, .5):
        k = list(arrays['delays']).index(delay)
        f, mean, weights = finite_score(arrays['full_response'][k])
        pert, pert_mean, pweights = finite_score(arrays['perturbed_response'][k])
        frozen, _, _ = finite_score(arrays['initial_frozen_response'][k])
        overlap = sum(min(weights[i, j], pweights[i, j]) for i in range(catalog['n'])
                      for j in range(catalog['n']))/(2*catalog['n'])
        gain = None if f is None or frozen is None else f-frozen
        details.append(dict(delay=delay, F=f, normalized_excess=None if f is None else
            (f-2/(catalog['n']-1))/(1-2/(catalog['n']-1)), response_mean=mean,
            perturbed_F=pert, perturbed_response_mean=pert_mean, frozen_F=frozen,
            overlap=overlap, dynamic_gain=gain))
        local.append(f is not None and f >= .8 and mean >= .01)
        stable.append(pert is not None and pert >= .8 and pert_mean >= .01 and overlap >= .8)
        advantage.append(gain is not None and gain >= .1)
    flags = dict(C=bool(all(connected[k] >= .8 for k in (3, 4, 5))), L=all(local),
                 T=bool(all(x <= .1 for x in tv) and all(stable)), D=all(advantage))
    flags['joint'] = all(flags.values())
    return dict(**flags, late_connectivity=connected[3:6].tolist(), late_tv=tv, response_details=details)


def compare_dictionary(check, actual, expected, category, label):
    for key, value in expected.items():
        if key not in actual:
            check.require(False, category, label+'/'+key+' missing')
        elif isinstance(value, dict):
            compare_dictionary(check, actual[key], value, category, label+'/'+key)
        elif isinstance(value, (bool, str)):
            check.require(actual[key] == value, category, label+'/'+key)
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            check.require(len(actual[key]) == len(value), category, label+'/'+key+' length')
            for i, item in enumerate(value[:len(actual[key])]):
                compare_dictionary(check, actual[key][i], item, category, label+'/'+key+str(i))
        else:
            check.close(actual[key], value, category, label+'/'+key)


def safe_json(path):
    return json.loads(Path(path).read_text())


def semantic_rng(mode, n, cell, batch, replicate, purpose):
    return np.random.default_rng(np.random.SeedSequence(
        [20261025, 7, STREAMS[mode], n, cell, batch, replicate, purpose]))


def expected_factors(mode, n, cell, preparation, batch=0, replicate=0, purpose=1):
    m = n*(n-1)//2
    if preparation == 'Splus':
        return np.full(m, .5), np.zeros(m)
    if preparation == 'Sempty':
        return np.zeros(m), np.zeros(m)
    rng = semantic_rng(mode, n, cell, batch, replicate, purpose)
    return rng.uniform(.25, .75, m), rng.uniform(0, 2*np.pi, m)


def expected_draws(law, rng):
    return rng.choice(len(law), size=8, p=np.maximum(law, 0)/np.maximum(law, 0).sum())


def audit_diagnostics(check, value, label):
    """Validate all archived conservation branches, including source-specific kicks."""
    if isinstance(value, dict):
        for key, item in value.items():
            if key == 'valid':
                check.require(item is True, 'conservation_valid', label)
            elif key in ('norm_error', 'probability_error', 'max_norm_error', 'max_probability_error'):
                check.close(item, 0., 'conservation_norm', label+'/'+key, 2e-9)
            elif key in ('scaled_energy_drift', 'scaled_parity_drift',
                         'max_scaled_energy_drift', 'max_scaled_parity_drift'):
                check.close(item, 0., 'conservation_drift', label+'/'+key, 2e-8)
            elif key == 'energy_imaginary_error':
                check.close(item, 0., 'conservation_imaginary_energy', label, 2e-8)
            elif isinstance(item, (dict, list)):
                audit_diagnostics(check, item, label+'/'+key)
    elif isinstance(value, list):
        for k, item in enumerate(value):
            audit_diagnostics(check, item, label+'/'+str(k))


def audit_response(check, arrays, prefix, label, zero_diagonal=False):
    base = arrays[prefix+'baseline_bloch']; probe = arrays[prefix+'probe_bloch']
    expected = distances_from_bloch(base, probe, zero_diagonal)
    check.close(arrays[prefix+'response'], expected, 'reduced_trace_distance', label+prefix)
    check.require(np.max(np.linalg.norm(base, axis=-1)) <= 1+2e-9 and
                  np.max(np.linalg.norm(probe, axis=-1)) <= 1+2e-9,
                  'reduced_density_positive', label+prefix)
    if prefix+'global_source_distance' in arrays:
        # For any pure global state, <psi|Y_i|psi> is its one-site Y Bloch value.
        global_distance=np.sqrt(np.maximum(0.,1-base[0,:,1]**2))
        check.close(arrays[prefix+'global_source_distance'],global_distance,
                    'pure_global_source_distance',label+prefix)
        check.require(np.max(expected-global_distance[None,:,None])<=2e-8,
                      'partial_trace_contractivity',label+prefix)
    n = base.shape[-2]; off = ~np.eye(n, dtype=bool)
    check.close(expected[..., 0, :, :][..., off] if expected.ndim == 4 else expected[0][off],
                np.zeros_like(expected[..., 0, :, :][..., off] if expected.ndim == 4 else expected[0][off]),
                'initial_no_signal', label+prefix, 2e-8)
    return expected


def audit_checkpoint(check, arrays, row):
    if 'checkpoint_age2_state' not in arrays:
        return
    psi = arrays['checkpoint_age2_state']; n = row['N']; label = row['array_file']
    check.counts['checkpoint_states'] += 1
    check.close(np.vdot(psi, psi).real, 1., 'checkpoint_norm', label, 2e-9)
    check.close(born_from_state(psi, n), arrays['full_born'][3], 'checkpoint_born', label)
    rhos, bloch = partials(psi, n)
    check.close(bloch, arrays['full_age2_bloch'], 'checkpoint_bloch', label)
    check.require(np.min(np.linalg.eigvalsh(rhos)) >= -2e-9, 'checkpoint_density_positive', label)
    zx, zy = joint_moments(psi, n)
    check.close(zx, arrays['direct_zx'], 'checkpoint_joint_zx', label)
    check.close(zy, arrays['direct_zy'], 'checkpoint_joint_zy', label)
    check.close(2*abs(row['parameters']['g'])*np.hypot(zx, zy), arrays['direct_slopes'],
                'checkpoint_response_slope', label)
    for prefix in ('full_', 'probe_frozen_'):
        for source in range(n):
            overlap = abs(np.vdot(psi, kick(psi, n, source)))**2
            check.close(arrays[prefix+'global_source_distance'][source],
                        math.sqrt(max(0., 1-overlap)), 'checkpoint_global_source_distance', label+prefix)
    check.require(hashlib.sha256(psi.tobytes()).hexdigest() == row['age2_state_sha256'],
                  'checkpoint_state_hash', label)


def audit_unit(check, row, arrays, catalog, static, mode, full_properties=False):
    n, cell = row['N'], row['cell']; label = row['array_file']; off = ~np.eye(n, dtype=bool)
    check.counts['units'] += 1
    check.require(row['status'] == 'ok', 'unit_status', label)
    check.close(arrays['ages'], AGES, 'registered_times', label)
    check.close(arrays['delays'], DELAYS, 'registered_times', label)
    p, phases = expected_factors(mode, n, cell, row['preparation'], row['batch'], row['replicate'])
    check.close(arrays['initial_link_probabilities'], p, 'semantic_preparation', label)
    check.close(arrays['initial_link_phases'], phases, 'semantic_preparation', label)
    check.require(row['stream'] == mode, 'semantic_stream', label)
    expected_params = dict(N=n, h=1., g=1., Gamma=CELLS[cell][1], mu=CELLS[cell][0], U=1.)
    compare_dictionary(check, row['parameters'], expected_params, 'registered_parameters', label)
    check.close(row['initial_matter_theta'], np.pi/4, 'registered_parameters', label)
    for branch, purpose in [('full', 100), ('perturbed', 200)]:
        for k, law in enumerate(arrays[branch+'_born']):
            check.probability(law, label+branch+str(k))
            draws = expected_draws(law, semantic_rng(mode, n, cell, row['batch'], row['replicate'], purpose+k))
            check.close(arrays['born_draws' if branch == 'full' else 'perturbed_born_draws'][k],
                        draws, 'semantic_born_draws', label)
    check.close(arrays['full_born'][0], np.prod(np.where(catalog['graph_bits'], p, 1-p), axis=1),
                'initial_born_product', label)
    check.probability(arrays['initial_frozen_born'], label+'initial_frozen')
    check.close(arrays['initial_frozen_born'], arrays['full_born'][0], 'frozen_link_conservation', label)
    for prefix in ('full_', 'perturbed_', 'initial_frozen_', 'probe_frozen_'):
        audit_response(check, arrays, prefix, label)
        check.counts['response_estimands'] += 1
    laws = {'born': arrays['full_born'][3], **null_laws(arrays['full_born'][3], catalog)}
    for name, law in laws.items():
        check.probability(law, label+name)
        prefix = 'static_'+name+'_'
        for key in ('baseline_bloch', 'probe_bloch'):
            check.close(arrays[prefix+key], np.tensordot(law, static[key], axes=1),
                        'static_weighted_density', label+prefix+key)
        conditional = np.tensordot(law, static['response'], axes=1)
        mixture = distances_from_bloch(arrays[prefix+'baseline_bloch'], arrays[prefix+'probe_bloch'], True)
        check.close(arrays[prefix+'conditional_response'], conditional, 'static_conditional_trace_distance', label+prefix)
        check.close(arrays[prefix+'mixture_response'], mixture, 'static_mixture_trace_distance', label+prefix)
        check.require(np.max(mixture-conditional) <= 2e-8, 'trace_distance_convexity', label+prefix)
        check.counts['response_estimands'] += 2
    gate = registered_gate(arrays, catalog)
    compare_dictionary(check, row['gate'], gate, 'registered_gate', label)
    qdegree = laws['degree']; law = laws['born']
    degree_event = bool(.5*abs(law-qdegree).sum() >= .1 and (law-qdegree)@catalog['connected'] >= .1)
    check.require(row['degree_null_event'] == degree_event, 'registered_degree_event', label)
    for k, record in enumerate(row['structure']):
        check.close(record['age'], AGES[k], 'structure_time', label)
        law = arrays['full_born'][k]
        if full_properties:
            observed = graph_properties(law, catalog)
            compare_dictionary(check, record['observed'], observed, 'graph_expectations', label+str(k))
        else:
            observed = dict(connected_probability=float(law@catalog['connected']),
                            occupation=law@catalog['graph_bits'])
            compare_dictionary(check, record['observed'], observed, 'graph_expectations', label+str(k))
        for name, null in null_laws(law, catalog).items():
            check.close(record['nulls'][name]['tv'], .5*abs(law-null).sum(), 'graph_null_tv', label+name+str(k))
            expected = graph_properties(null, catalog) if full_properties else {
                'connected_probability': float(null@catalog['connected'])}
            selected = {key: expected[key] for key in record['nulls'][name]['properties'] if key in expected}
            compare_dictionary(check, record['nulls'][name]['properties'], selected, 'graph_null_expectations', label+name+str(k))
    if row['preparation'] != 'E':
        occupation_range = np.ptp(arrays['full_born']@catalog['graph_bits'], axis=1).max()
        response_range = np.ptp(arrays['full_response'][:, off], axis=1).max()
        check.close(occupation_range, 0., 'exchange_symmetry_occupation', label, 2e-8)
        check.close(response_range, 0., 'exchange_symmetry_response', label, 2e-8)
        check.require(row['symmetry']['passed'], 'exchange_symmetry_flag', label)
    expected_checkpoint = row['preparation'] != 'E' or row['replicate'] == 0
    check.require(('checkpoint_age2_state' in arrays) == expected_checkpoint, 'checkpoint_schedule', label)
    audit_checkpoint(check, arrays, row)
    audit_diagnostics(check, row['diagnostics'], label)
    if 'nonselective_measurement_tv' in row:
        for key in ('measurement_measured_future_born', 'measurement_unmeasured_future_born', 'measurement_measurement_born'):
            check.probability(arrays[key], label+key)
        check.close(arrays['measurement_measurement_born'], arrays['full_born'][3], 'measurement_born', label)
        check.close(arrays['measurement_unmeasured_future_born'], arrays['full_born'][4], 'measurement_unmeasured', label)
        check.close(row['nonselective_measurement_tv'], .5*abs(arrays['measurement_measured_future_born']-
                    arrays['measurement_unmeasured_future_born']).sum(), 'measurement_tv', label)
        audit_diagnostics(check, row['measurement_branch_diagnostics'], label+'/measurement')
    return gate, degree_event


def audit_summary(check, rows, recalculated, summary, metadata, controls_pass):
    sizes, cells = metadata['sizes'], metadata['cells']; family = len(sizes)*len(cells)
    expected_ids = {(n, c, prep, b, r) for n in sizes for c in cells
                    for prep, b, r in ([('Splus', 0, 0), ('Sempty', 0, 0)]+
                        ([('E', 0, 0)] if metadata['mode'] == 'smoke' else
                         [('E', b, r) for b in range(3) for r in range(metadata['repeats_per_batch'])]))}
    actual_ids = [(r['N'], r['cell'], r['preparation'], r['batch'], r['replicate']) for r in rows]
    check.require(len(set(actual_ids)) == len(actual_ids) and set(actual_ids) == expected_ids,
                  'semantic_complete_schedule', 'all units including symmetric controls')
    table = []; expected_e = 1 if metadata['mode'] == 'smoke' else 3*metadata['repeats_per_batch']
    for n in sizes:
        for cell in cells:
            selected = [r for r in rows if r['N'] == n and r['cell'] == cell and r['preparation'] == 'E']
            valid = [r for r in selected if r.get('status') == 'ok' and r['array_file'] in recalculated]
            successes = sum(recalculated[r['array_file']][0]['joint'] for r in valid)
            structural = sum(recalculated[r['array_file']][1] for r in valid)
            count = len(selected)
            bounds = cp_bounds(successes, count, family)
            result = dict(N=n, cell=cell, attempted=count, valid=len(valid), successes=successes,
                component_successes={k: sum(recalculated[r['array_file']][0][k] for r in valid) for k in 'CLTD'},
                cp_family_bounds=bounds, cp_go_bounds=cp_bounds(successes, count, 2*family),
                degree_null_successes=structural, degree_null_go_bounds=cp_bounds(structural, count, 2*family),
                cohort_complete=count == expected_e,
                assessment='fails' if bounds[1] < .8 else 'passes necessary screen' if bounds[0] > .8 else 'unresolved')
            table.append(result)
    eliminated = [c for c in cells if any(r['cell'] == c and r['assessment'] == 'fails' for r in table)]
    eligible = [c for c in cells if all(any(r['N'] == n and r['cell'] == c and
        r['cp_go_bounds'][0] > .8 and (n < 5 or r['degree_null_go_bounds'][0] > .8) for r in table) for n in sizes)]
    complete = len(table) == family and all(r['cohort_complete'] for r in table)
    decision = 'NO-GO' if len(eliminated) == len(cells) and complete and all(r['status'] == 'ok' for r in rows) and controls_pass else 'INCONCLUSIVE'
    expected = dict(cells=table, family_size=family, eliminated_parameter_settings=eliminated,
                    statistically_eligible_parameter_settings=eligible, complete_expected_cohorts=complete,
                    independent_control_validation_passed=controls_pass, decision=decision,
                    limited_go_requires_independently_verified_mechanism=True)
    compare_dictionary(check, summary, expected, 'independent_statistical_decision', 'summary')
    return expected


def regenerate_unit(check, row, arrays):
    """Preselected first exchangeable preparation per cell; public SciPy action only."""
    n = row['N']; params = row['parameters']; label = row['array_file']
    matrix = independent_hamiltonian(n, params)
    psi = prepare(n, arrays['initial_link_probabilities'], arrays['initial_link_phases'])
    initial_energy = float(np.vdot(psi, matrix@psi).real)
    age = 0.; aged = None
    for k, target in enumerate(AGES):
        psi = advance(matrix, psi, target-age); age = target
        check.close(born_from_state(psi, n), arrays['full_born'][k], 'regenerated_born', label+str(target))
        check.close(np.vdot(psi, psi).real, 1., 'regenerated_norm', label, 2e-9)
        check.close(np.vdot(psi, matrix@psi).real, initial_energy, 'regenerated_energy', label, 2e-8)
        if target == 2:
            aged = psi.copy()
    check.close(aged, arrays['checkpoint_age2_state'], 'regenerated_state', label)
    base = partials(advance(matrix, aged, .25), n)[1]
    probes = np.array([partials(advance(matrix, kick(aged, n, i), .25), n)[1] for i in range(n)])
    check.close(base, arrays['full_baseline_bloch'][3], 'regenerated_baseline_bloch', label)
    check.close(probes, arrays['full_probe_bloch'][3], 'regenerated_probe_bloch', label)
    check.close(distances_from_bloch(base, probes), arrays['full_response'][3], 'regenerated_response', label)
    # Explicit sparse evolution also checks the optimized fixed-link sector path.
    frozen_params = dict(params, Gamma=0.)
    frozen_matrix = independent_hamiltonian(n, frozen_params)
    initial = prepare(n, arrays['initial_link_probabilities'], arrays['initial_link_phases'])
    initially_frozen = advance(frozen_matrix, initial, 2.)
    for prefix, branch_matrix, branch_age2 in (
            ('initial_frozen_', frozen_matrix, initially_frozen),
            ('probe_frozen_', frozen_matrix, aged)):
        branch_base = partials(advance(branch_matrix, branch_age2, .25), n)[1]
        branch_probes = np.array([partials(advance(branch_matrix, kick(branch_age2, n, i), .25), n)[1]
                                  for i in range(n)])
        check.close(branch_base, arrays[prefix+'baseline_bloch'][3], 'regenerated_frozen_baseline', label+prefix)
        check.close(branch_probes, arrays[prefix+'probe_bloch'][3], 'regenerated_frozen_probes', label+prefix)
        check.close(distances_from_bloch(branch_base,branch_probes), arrays[prefix+'response'][3],
                    'regenerated_frozen_response', label+prefix)
    perturb_matrix = independent_hamiltonian(n, dict(params, Gamma=1.05*params['Gamma']))
    perturb_age2 = advance(perturb_matrix, initial, 2.)
    check.close(born_from_state(perturb_age2,n),arrays['perturbed_born'][3], 'regenerated_perturbed_born',label)
    perturb_base = partials(advance(perturb_matrix,perturb_age2,.25),n)[1]
    perturb_probes = np.array([partials(advance(perturb_matrix,kick(perturb_age2,n,i),.25),n)[1] for i in range(n)])
    check.close(perturb_base,arrays['perturbed_baseline_bloch'][3], 'regenerated_perturbed_baseline',label)
    check.close(perturb_probes,arrays['perturbed_probe_bloch'][3], 'regenerated_perturbed_probes',label)
    check.close(distances_from_bloch(perturb_base,perturb_probes),arrays['perturbed_response'][3], 'regenerated_perturbed_response',label)
    if 'measurement_measured_future_born' in arrays:
        # Unnormalized projected columns retain their Born weights automatically.
        graph_count = len(arrays['full_born'][3]); indices = np.arange(len(aged))
        projected = np.zeros((len(aged),graph_count),complex)
        projected[indices,indices&(graph_count-1)] = aged
        projected = advance(matrix,projected,1.)
        final_diagonal = (abs(projected)**2).sum(1)
        measured = np.zeros(graph_count)
        np.add.at(measured,indices&(graph_count-1),final_diagonal)
        check.close(measured,arrays['measurement_measured_future_born'], 'regenerated_nonselective_measurement',label)
    check.counts['regenerated_units'] += 1


def mathematical_audit(check):
    """Dense tensor and bit-matrix paths, exact commutators, Taylor coefficient."""
    for n in (2, 3):
        parameters = dict(h=.7, g=1.1, Gamma=.6, mu=-.2, U=.9)
        dense = dense_tensor_hamiltonian(n, parameters['h'], parameters['g'], parameters['Gamma'],
                                         parameters['mu'], parameters['U'])
        bit = independent_hamiltonian(n, parameters).toarray()
        check.close(bit, dense, 'independent_hamiltonian_constructions', 'N'+str(n), 1e-12)
        q = n+n*(n-1)//2; edges = list(combinations(range(n), 2))
        parity = tensor_operator(q, {i: X for i in range(n)})
        check.close(dense@parity-parity@dense, np.zeros_like(dense), 'matter_parity_commutator', str(n), 1e-12)
        for e, (i, j) in enumerate(edges):
            xi = tensor_operator(q, {i: X}); xj = tensor_operator(q, {j: X})
            derivative = 1j*(dense@xi-xi@dense)
            expected = 4j*parameters['g']*tensor_operator(q, {i: Y, j: Y, n+e: OCC})
            check.close(derivative@xj-xj@derivative, expected, 'operator_first_response_commutator', str((n,i,j)), 1e-12)
            occ = tensor_operator(q, {n+e: OCC})
            check.close(1j*(dense@occ-occ@dense), parameters['Gamma']*tensor_operator(q, {n+e: Y}),
                        'link_number_commutator', str((n,e)), 1e-12)
        # General entangled-state one-sided trace-distance derivative from the
        # exact density commutator; this checks the aged n*Zi*Xj/Yj formula.
        labels=np.arange(1 << q)
        state=np.cos(labels*.73)+1j*np.sin(labels*1.13+.4)
        state=state/np.linalg.norm(state)
        zx,zy=joint_moments(state,n)
        for source in range(n):
            kicked=kick(state,n,source)
            delta=np.outer(kicked,kicked.conj())-np.outer(state,state.conj())
            derivative=-1j*(dense@delta-delta@dense)
            for target in range(n):
                if source==target:continue
                bit=1 << (q-1-target);zero=labels[(labels&bit)==0];one=zero|bit
                reduced=np.array([[derivative[zero,zero].sum(),derivative[zero,one].sum()],
                                  [derivative[one,zero].sum(),derivative[one,one].sum()]])
                slope=.5*sum(abs(np.linalg.eigvalsh(reduced)))
                check.close(slope,2*abs(parameters['g'])*math.hypot(zx[source,target],zy[source,target]),
                            'entangled_state_response_slope',str((n,source,target)),1e-12)
        # Exact Taylor coefficients of reduced density difference, not a small-step fit.
        if n == 2:
            psi = prepare(n, [0.], [0.]); kicked = kick(psi, n, 0)
            delta = np.outer(kicked, kicked.conj())-np.outer(psi, psi.conj())
            for order in range(1, 4):
                delta = -1j*(dense@delta-delta@dense)/order
                # Tr over source and link for target matter axis 1.
                reduced = np.zeros((2,2), complex)
                for a in range(2):
                    for b in range(2):
                        for source in range(2):
                            for link in range(2):
                                reduced[a,b] += delta[4*source+2*a+link,4*source+2*b+link]
                value = .5*sum(abs(np.linalg.eigvalsh(reduced)))
                expected = parameters['g']*parameters['Gamma']**2/3 if order == 3 else 0.
                check.close(value, expected, 'all_off_cubic_response_coefficient', str(order), 1e-12)
    # Analytic CP edge cases, independent of production beta inversion.
    for n in (1, 12, 24, 36):
        for family in (1,12,24,36):
            tail = .05/(2*family)
            check.close(cp_bounds(0,n,family), [0.,1-tail**(1/n)], 'binomial_analytic_edges', str((n,family)), 1e-12)
            check.close(cp_bounds(n,n,family), [tail**(1/n),1.], 'binomial_analytic_edges', str((n,family)), 1e-12)


def load_arrays(path):
    with np.load(path, allow_pickle=False) as saved:
        return {k: saved[k] for k in saved.files}


def audit_static(check, arrays, row, catalog, mode):
    n = catalog['n']; off = ~np.eye(n, dtype=bool)
    response = audit_response(check, arrays, '', 'all static graphs N'+str(n), True)
    check.close(arrays['norm_error'], np.zeros_like(arrays['norm_error']), 'static_norm', str(n), 2e-9)
    for key in ('energy_drift','parity_drift'):
        scaled = arrays[key]/np.maximum(1., abs(arrays['initial_'+key.removesuffix('_drift')]))[:,None,:]
        check.close(scaled, np.zeros_like(scaled), 'static_conservation_drift', key+str(n), 2e-8)
    permutation = semantic_rng(mode,n,0,0,0,77).permutation(n)
    check.close(row['chain_permutation'], permutation, 'static_semantic_permutation', str(n))
    chain = np.zeros((n,n), int)
    for i in range(n-1):
        chain[i,i+1] = chain[i+1,i] = 1
    permuted = chain[np.ix_(permutation, permutation)]
    index = sum(int(permuted[i,j]) << (len(catalog['edges'])-1-e) for e,(i,j) in enumerate(catalog['edges']))
    check.close(row['chain_graph_index'], index, 'static_chain_index', str(n))
    dist = catalog['distance'][index]
    means = [float(response[index,2][dist == d].mean()) for d in range(1,n)]
    check.close(row['chain_mean_responses_at_delay_point1_by_distance'], means, 'static_distance_response', str(n))
    matching = row['control_graphs']['matching']; complete = row['control_graphs']['complete']
    no_signal = max(float(response[index,0][off].max()), float(response[matching][:,catalog['distance'][matching]<0].max()))
    spread = float(np.ptp(response[complete][:,off], axis=1).max())
    passed = no_signal < 2e-8 and spread < 2e-8 and all(a>b for a,b in zip(means,means[1:])) and means[0] > .01
    check.close(row['maximum_no_signalling_error'], no_signal, 'static_no_signal', str(n))
    check.close(row['maximum_complete_response_range'], spread, 'static_complete_symmetry', str(n))
    check.require(row['passed'] == passed and passed, 'static_control_pass', str(n))
    return passed


def audit_independent(check, arrays, row, catalog, mode):
    n, cell = row['N'], row['cell']; label = 'independent '+str((n,cell,row['preparation']))
    p, phases = expected_factors(mode,n,cell,row['preparation'],purpose=31)
    check.close(arrays['initial_link_probabilities'],p,'independent_semantic_preparation',label)
    check.close(arrays['initial_link_phases'],phases,'independent_semantic_preparation',label)
    hlink = CELLS[cell][0]*OCC-CELLS[cell][1]*X
    values, vectors = eigh(hlink)
    for k, age in enumerate(AGES):
        unitary = (vectors*np.exp(-1j*age*values))@vectors.conj().T
        evolved = np.array([unitary@np.array([math.sqrt(1-x),math.sqrt(x)*np.exp(1j*phase)]) for x,phase in zip(p,phases)])
        probabilities = abs(evolved[:,1])**2
        expected = np.prod(np.where(catalog['graph_bits'],probabilities,1-probabilities),axis=1)
        check.close(arrays['born'][k],expected,'independent_analytic_product_law',label+str(age))
    response = audit_response(check,arrays,'independent_',label)
    maximum = float(response[:,~np.eye(n,dtype=bool)].max())
    tv = max(.5*abs(law-null_laws(law,catalog)['product']).sum() for law in arrays['born'])
    check.close(row['maximum_cross_response'],maximum,'independent_no_signal',label)
    check.close(row['maximum_product_tv'],tv,'independent_product_tv',label)
    check.require(maximum < 2e-8 and tv < 2e-8 and row['passed'],'independent_control_pass',label)
    audit_diagnostics(check,row['diagnostics'],label)
    return maximum < 2e-8 and tv < 2e-8


def audit_equilibrium(check, arrays, row, catalog, mode, thermal_replay=False):
    n, cell = row['N'],row['cell']; label = 'equilibrium '+str((n,cell))
    params = dict(h=1.,g=1.,Gamma=CELLS[cell][1],mu=CELLS[cell][0],U=1.)
    matrix = independent_hamiltonian(n,params)
    psi = arrays['ground_state']; born = born_from_state(psi,n)
    check.close(np.vdot(psi,psi).real,1.,'ground_norm',label,2e-9)
    check.close(born,arrays['ground_born'],'ground_born',label)
    energy = float(np.vdot(psi,matrix@psi).real)
    check.close(energy,row['solver']['energy'],'ground_energy',label)
    residual = np.linalg.norm(matrix@psi-energy*psi)
    check.close(residual,0.,'ground_residual',label,2e-8*max(1.,abs(energy)))
    q=n+n*(n-1)//2; flip=sum(1<<(q-1-i) for i in range(n))
    check.close(psi[np.arange(len(psi))^flip],psi,'ground_even_parity',label)
    response = audit_response(check,arrays,'ground_',label)
    check.close(np.ptp(response[:,~np.eye(n,dtype=bool)],axis=1),np.zeros(len(DELAYS)), 'ground_response_symmetry',label,2e-8)
    check.close(np.ptp(born@catalog['graph_bits']),0.,'ground_occupation_symmetry',label,2e-8)
    compare_dictionary(check,row['properties'],graph_properties(born,catalog),'ground_properties',label)
    check.close(arrays['ground_born_draws'],expected_draws(born,semantic_rng(mode,n,cell,0,0,400)), 'ground_semantic_draws',label)
    audit_diagnostics(check,row['response_diagnostics'],label)
    check.require(row['passed'] is True and row['solver']['valid'] is True,'equilibrium_control_pass',label)
    if n==4:
        eigenvalues = arrays['thermal_eigenvalues']
        check.close(eigenvalues[0],energy,'dense_ground_energy',label)
        if thermal_replay:
            direct_values,direct_vectors=eigh(matrix.toarray())
            check.close(eigenvalues,direct_values,'thermal_eigenspectrum',label)
        for thermal in row['thermal']:
            beta=thermal['beta']; weights=np.exp(-beta*(eigenvalues-eigenvalues[0]));weights/=sum(weights)
            law=arrays[f'thermal_born_beta{beta}'];check.probability(law,label+str(beta))
            check.close(thermal['energy'],weights@eigenvalues,'thermal_energy',label+str(beta))
            check.close(thermal['entropy_nats'],-sum(weights[weights>0]*np.log(weights[weights>0])),'thermal_entropy',label+str(beta))
            compare_dictionary(check,thermal['properties'],graph_properties(law,catalog),'thermal_properties',label+str(beta))
            check.close(arrays[f'thermal_born_draws_beta{beta}'],expected_draws(law,semantic_rng(mode,n,cell,0,0,401+int(beta))), 'thermal_semantic_draws',label)
            if thermal_replay:
                diagonal=abs(direct_vectors)**2@weights
                expected=np.zeros(len(born));np.add.at(expected,np.arange(len(diagonal))&(len(born)-1),diagonal)
                check.close(law,expected,'thermal_density_replay',label+str(beta))
    return bool(row['passed']) and residual <= 2e-8*max(1.,abs(energy))


def audit_calibration(check, calibration):
    passed=True
    for row in calibration['rows']:
        n,family=row['trials'],row['family'];label=str((n,family))
        intervals=np.array([cp_bounds(k,n,family) for k in range(n+1)])
        grid=np.unique(np.r_[np.linspace(0,1,1001),intervals.ravel()])
        coverage=[float(binomial_mass(n,p)@((intervals[:,0]<=p+1e-14)&(intervals[:,1]>=p-1e-14))) for p in grid]
        minimum=min(coverage)
        check.close(row['minimum_enumerated_coverage'],minimum,'binomial_calibration_coverage',label,2e-12)
        check.close(row['required_marginal_coverage'],1-.05/family,'binomial_calibration_target',label)
        valid=minimum>=1-.05/family-1e-12
        check.require(row['passed']==valid,'binomial_calibration_flag',label);passed &= valid
    check.require(calibration['passed']==passed,'binomial_calibration_overall','calibration')
    return bool(passed)


def audit_archive(path, regenerate=True, thermal_replay=False):
    path=Path(path);check=Audit();started=time.monotonic()
    manifest=safe_json(path/'manifest.json');metadata=safe_json(path/'metadata.json')
    digest=hashlib.sha256()
    for name,value in manifest['sha256'].items():
        relative=Path(name)
        check.require(not relative.is_absolute() and '..' not in relative.parts,'manifest_safe_path',name)
        check.require(hashlib.sha256((path/name).read_bytes()).hexdigest()==value,'manifest_hash',name)
    for name in manifest['scientific_files']:
        digest.update(name.encode());digest.update((path/name).read_bytes())
    check.require(digest.hexdigest()==manifest['scientific_digest'],'manifest_scientific_digest','archive')
    check.close(metadata['ages'],AGES,'registered_times','metadata')
    check.close(metadata['delays'],DELAYS,'registered_times','metadata')
    check.require(metadata['streams']==STREAMS,'semantic_stream_registry','metadata')
    check.require(metadata['baseline_commit']=='73baea299fb07d608bade8364d6cf66443e23166','baseline_provenance','metadata')
    check.require(metadata['protocol_commit']=='5b71924','protocol_provenance','metadata')
    if metadata['mode']=='primary':
        check.require(all(x=='1' for x in metadata['threads'].values()),'single_thread_provenance','metadata')
        check.require(metadata['freeze_sha256'] is not None,'workload_freeze_provenance','metadata')
    # This auditor can be run from a later checkout: compare hashes to recorded commit,
    # not the current working file, and only enforce for primary (smoke may be uncommitted).
    if metadata['mode']=='primary':
        root=Path(__file__).resolve().parents[1]
        for name,value in metadata['sha256'].items():
            source=subprocess.check_output(['git','show',metadata['commit']+':'+name],cwd=root)
            check.require(hashlib.sha256(source).hexdigest()==value,'committed_source_provenance',name)
    with gzip.open(path/'raw.json.gz','rt') as handle:
        rows=json.load(handle)
    check.require(safe_json(path/'failures.json')==[],'retained_failure_file','archive')
    catalogs={};static={};controls=[]
    staticrows=safe_json(path/'static_controls.json')
    check.require(sorted(r['N'] for r in staticrows)==sorted(metadata['sizes']), 'static_control_schedule', 'archive')
    for n in metadata['sizes']:
        catalog=graph_catalog(n);catalogs[n]=catalog
        saved=load_arrays(path/'arrays'/f'catalog_N{n}.npz')
        for key,value in saved.items():
            if not key.startswith('_'):
                check.close(value,catalog[key],'exhaustive_graph_catalogue','N'+str(n)+'/'+key)
        static[n]=load_arrays(path/'arrays'/f'static_N{n}.npz')
        controls.append(audit_static(check,static[n],next(r for r in staticrows if r['N']==n),catalog,metadata['mode']))
    recalculated={}
    for row in rows:
        label=row.get('array_file',str((row['N'],row['cell'],row['preparation'])))
        try:
            arrays=load_arrays(path/row['array_file'])
            selected=row['preparation']=='E' and row['batch']==0 and row['replicate']==0
            recalculated[row['array_file']]=audit_unit(check,row,arrays,catalogs[row['N']],static[row['N']],metadata['mode'],selected)
            if selected and regenerate:
                regenerate_unit(check,row,arrays)
        except Exception as error:
            check.failures.append(dict(category='unit_audit_exception',label=label,type=type(error).__name__,message=str(error)))
    independent_rows=safe_json(path/'independent_controls.json')
    expected_independent={(n,c,p) for n in metadata['sizes'] for c in metadata['cells'] for p in ('Splus','Sempty','E')}
    independent_ids=[(r['N'],r['cell'],r['preparation']) for r in independent_rows]
    check.require(set(independent_ids)==expected_independent and len(independent_ids)==len(expected_independent), 'independent_control_schedule','archive')
    for row in independent_rows:
        arrays=load_arrays(path/'arrays'/f'independent_N{row["N"]}_c{row["cell"]}_{row["preparation"]}.npz')
        controls.append(audit_independent(check,arrays,row,catalogs[row['N']],metadata['mode']))
    equilibrium_rows=safe_json(path/'equilibrium.json')
    expected_equilibrium={(n,c) for n in metadata['sizes'] for c in metadata['cells']}
    equilibrium_ids=[(r['N'],r['cell']) for r in equilibrium_rows]
    check.require(set(equilibrium_ids)==expected_equilibrium and len(equilibrium_ids)==len(expected_equilibrium), 'equilibrium_control_schedule','archive')
    for row in equilibrium_rows:
        arrays=load_arrays(path/'arrays'/f'equilibrium_N{row["N"]}_c{row["cell"]}.npz')
        controls.append(audit_equilibrium(check,arrays,row,catalogs[row['N']],metadata['mode'],thermal_replay))
    calibration_pass=audit_calibration(check,safe_json(path/'calibration.json'))
    independent_summary=audit_summary(check,rows,recalculated,safe_json(path/'summary.json'),metadata,all(controls) and calibration_pass)
    mathematical_audit(check)
    compare_dictionary(check,safe_json(path/'classical_degeneracy.json'),dict(n=6,connected_cycles=math.factorial(5)//2,disconnected_triangle_pairs=math.comb(6,3)//2,degree_two_graphs=70,connected_matter_microstates=120,disconnected_matter_microstates=40,canonical_zero_temperature_connectivity=.75,uniform_graph_connectivity=6/7,cycle_spectrum=[0,1,1,3,3,4],triangles_spectrum=[0,0,3,3,3,3]),'classical_degree_degeneracy','analytic N6')
    for row in safe_json(path/'degree_identifiability.json'):
        c=catalogs[row['n']];mixed=[]
        for identifier in set(c['classes']):
            members=c['classes']==identifier;connected=int(c['connected'][members].sum());size=int(members.sum())
            if 0<connected<size:mixed.append((members,connected,size))
        advantage=max((1-connected/size for _,connected,size in mixed),default=0.)
        compare_dictionary(check,row,dict(total_degree_classes=len(set(c['classes'])),ambiguous_degree_class_count=len(mixed),connectivity_advantage_possible=bool(mixed),maximum_connectivity_advantage=advantage,minimum_ambiguous_class_mass_for_registered_advantage=.1/advantage if advantage else None),'degree_connectivity_obstruction',str(row['n']))
    result=check.report()
    result.update(archive_scientific_digest=manifest['scientific_digest'],source_commit=metadata['commit'],
        auditor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        independent_decision=independent_summary['decision'],elapsed_seconds=time.monotonic()-started,
        scope=dict(graph_catalogues='all labeled graphs at every archived N, independent BFS and triangles',
            graph_expectations='full set for first exchangeable unit per N/cell, connectivity and null TV for all units',
            response='all 14 estimands, every source/target and sampled delay',
            checkpoints='all archived age-2 states, explicit basis partial traces and joint moments',
            regeneration='first E batch=0 replicate=0 in each N/cell, all six full Born ages, all four Hamiltonian branches/all sources at delay .25, N4 nonselective measurement' if regenerate else 'disabled',
            thermal_density_replay=thermal_replay,
            statistics='complete semantic cohorts, C/L/T/D and degree events, both Bonferroni families by elementary binomial inversion',
            calibration='same finite grid and endpoints; not a proof over a continuum of probabilities',
            limitation='a computation audit, not additional independent physical evidence'))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--no-regenerate',action='store_true')
    parser.add_argument('--thermal-replay',action='store_true')
    args=parser.parse_args()
    result=audit_archive(args.archive,not args.no_regenerate,args.thermal_replay)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('passed','failure_count','independent_decision','elapsed_seconds')},sort_keys=True))
    if not result['passed']:
        raise SystemExit(1)


if __name__=='__main__':
    main()
