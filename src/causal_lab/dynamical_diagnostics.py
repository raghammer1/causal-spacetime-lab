"""Descriptive diagnostics reconstructed from archived Experiment 7 arrays.

No decision threshold is fitted here. Graph drawings, graph measurements, response
concentration and intervention distinguishability retain their distinct meanings.
"""
from __future__ import annotations

import hashlib
import json

import numpy as np

from .dynamical_statistics import top_two


ONSET_THRESHOLDS = (.01, .05)
OCCUPATION_THRESHOLDS = (.25, .5, .75)
NULL_NAMES = ('born', 'density', 'product', 'count', 'degree')


def _number(value):
    value = float(value)
    return value if np.isfinite(value) else None


def _difference(left, right):
    return None if left is None or right is None else left-right


def response_hash(response):
    """Hash shape and canonical little-endian doubles, without changing the input."""
    array = np.ascontiguousarray(response, dtype='<f8')
    digest = hashlib.sha256(json.dumps(list(array.shape), separators=(',', ':')).encode())
    digest.update(array.tobytes())
    return digest.hexdigest()


def sampled_onsets(response, delays):
    """First observed crossing; censoring applies only to the registered time grid.

    A noncrossing sampled curve could still cross and recede between samples.
    The diagonal is excluded, rather than classified as zero-distance signalling.
    """
    values = np.asarray(response, dtype=float)
    times = np.asarray(delays, dtype=float)
    if (values.ndim != 3 or not len(values) or values.shape[1] < 1
            or values.shape[1] != values.shape[2]
            or times.shape != (len(values),) or not np.all(np.isfinite(values))
            or not np.all(np.isfinite(times)) or times[0] < 0
            or np.any(np.diff(times) <= 0) or np.min(values) < -2e-9
            or np.max(values) > 1+2e-9):
        raise ValueError('finite response [time,source,target] and increasing delays required')
    n = values.shape[1]
    off_diagonal = ~np.eye(n, dtype=bool)
    records = []
    for threshold in ONSET_THRESHOLDS:
        crossed = values >= threshold
        observed = crossed.any(axis=0) & off_diagonal
        index = crossed.argmax(axis=0)
        first = [[float(times[index[i, j]]) if observed[i, j] else None
                  for j in range(n)] for i in range(n)]
        records.append(dict(threshold=threshold, first_sampled_delay=first,
            observed_crossing=observed.tolist(),
            right_censored_on_sampled_grid=(~observed & off_diagonal).tolist(),
            excluded_diagonal=np.eye(n, dtype=bool).tolist(),
            last_sampled_delay=float(times[-1]),
            interpretation='First sampled crossing, not continuous first passage; between-time crossings are unresolved.'))
    return records


def _score_curve(response):
    answer = []
    for matrix in response:
        score = top_two(matrix)
        answer.append(dict(F=_number(score['F']),
            normalized_excess=_number(score['normalized_excess']),
            mean_response=_number(score['mean_response'])))
    return answer


def frozen_comparisons(arrays, delays):
    """Full-versus-static and Born-versus-null comparisons, with both estimands."""
    full = _score_curve(arrays['full_response'])
    scored = {}
    for name in NULL_NAMES:
        for kind in ('conditional', 'mixture'):
            key = f'static_{name}_{kind}_response'
            response = np.asarray(arrays[key], dtype=float)
            # Validate convention and finite values independently of whether its F is defined.
            sampled_onsets(response, delays)
            if response.shape != np.shape(arrays['full_response']):
                raise ValueError('static and full response shapes must match')
            scored[name, kind] = _score_curve(response)
    records = []
    n = np.shape(arrays['full_response'])[1]
    off_diagonal = ~np.eye(n, dtype=bool)
    for name in NULL_NAMES:
        conditional = np.asarray(arrays[f'static_{name}_conditional_response'])
        mixture = np.asarray(arrays[f'static_{name}_mixture_response'])
        curve = []
        for k, delay in enumerate(delays):
            item = dict(delay=float(delay), full=full[k])
            for kind in ('conditional', 'mixture'):
                here = scored[name, kind][k]
                born = scored['born', kind][k]
                item[kind] = here
                item['full_minus_'+kind+'_F'] = _difference(full[k]['F'], here['F'])
                item['born_minus_null_'+kind+'_F'] = _difference(born['F'], here['F'])
                item['born_minus_null_'+kind+'_mean_response'] = _difference(
                    born['mean_response'], here['mean_response'])
            delta = (conditional[k]-mixture[k])[off_diagonal]
            item['conditional_minus_mixture_response_mean'] = float(delta.mean())
            item['mixture_convexity_max_violation'] = float(max(0., -delta.min()))
            curve.append(item)
        records.append(dict(law=name, curve=curve,
            interpretation='Fresh supplied-graph matter probes; conditional averages trace distances, mixture averages states before distances.'))
    return records


def layout_controls(arrays, catalog):
    """Explicitly cosmetic drawings and chosen-threshold graph transformations.

    The invariant hash checks that this analysis does not mutate or feed back into
    the quantum response. It is not another physical measurement or evidence of
    locality. Spectral coordinates can be noncanonical in degenerate eigenspaces.
    """
    ages = np.asarray(arrays['ages'], dtype=float)
    matches = np.flatnonzero(ages == 2.)
    laws = np.asarray(arrays['full_born'], dtype=float)
    if len(matches) != 1 or laws.shape != (len(ages), catalog.graph_count):
        raise ValueError('one age2 law in the registered graph convention is required')
    p = laws[matches[0]]
    if not np.all(np.isfinite(p)) or np.min(p) < -2e-9 or abs(p.sum()-1) > 2e-9:
        raise ValueError('invalid Born law')
    original_response = arrays['full_response']
    before = response_hash(original_response)
    occupation = p @ catalog.graph_bits
    n = catalog.n
    adjacency = np.zeros((n, n))
    for value, (i, j) in zip(occupation, catalog.edges):
        adjacency[i, j] = adjacency[j, i] = value
    laplacian = np.diag(adjacency.sum(axis=1))-adjacency
    eigenvalues, eigenvectors = np.linalg.eigh(laplacian)
    circular = np.column_stack((np.cos(2*np.pi*np.arange(n)/n),
                                np.sin(2*np.pi*np.arange(n)/n)))
    spectral = eigenvectors[:, 1:3]
    tolerance = 1e-10*max(1., float(np.max(np.abs(eigenvalues))))
    # Either a repeated selected eigenvalue or a degeneracy at the cut prevents a unique basis.
    repeated = bool(any(abs(eigenvalues[j]-eigenvalues[k]) <= tolerance
                        for j in (1, 2) for k in range(n) if j != k))
    thresholded = []
    for threshold in OCCUPATION_THRESHOLDS:
        selected = occupation >= threshold
        a = np.zeros((n, n), dtype=np.int8)
        for active, (i, j) in zip(selected, catalog.edges):
            a[i, j] = a[j, i] = int(active)
        graph = catalog.index(a)
        thresholded.append(dict(threshold=threshold, graph_index=int(graph),
            adjacency=a.tolist(), edges=int(selected.sum()),
            connected=bool(catalog.connected[graph]), components=int(catalog.components[graph]),
            component_sizes=catalog.component_sizes[graph].tolist(),
            occupation_ties_within_1e_10=int(np.count_nonzero(np.abs(occupation-threshold) <= 1e-10)),
            response_sha256=before,
            interpretation='Chosen occupation threshold; this graph is not a Born measurement or a propagation law.'))
    after = response_hash(original_response)
    if after != before:
        raise RuntimeError('layout analysis changed the quantum response')
    return dict(age=2., occupation=occupation.tolist(), weighted_adjacency=adjacency.tolist(),
        circular_coordinates=circular.tolist(), spectral_coordinates=spectral.tolist(),
        spectral_laplacian_eigenvalues=eigenvalues.tolist(),
        spectral_basis_nonunique=repeated, thresholded_graphs=thresholded,
        circular_response_sha256=before, spectral_response_sha256=before,
        response_sha256_before=before, response_sha256_after=after,
        response_unchanged_by_construction=True,
        interpretation='Coordinates are combinatorial drawings, not physical positions; changing drawings/thresholds does not recompute or change the raw quantum assay.')


def analyze(arrays, catalog):
    """Return JSON-safe descriptive diagnostics; never alter the registered gate."""
    if catalog.n < 4:
        raise ValueError('the registered descriptive assay requires N>=4')
    delays = np.asarray(arrays['delays'], dtype=float)
    responses = {key.removesuffix('_response'): value for key, value in arrays.items()
                 if key.endswith('_response') and np.ndim(value) == 3}
    if 'full' not in responses:
        raise ValueError('full response is required')
    return dict(status='descriptive_only',
        onsets={name: sampled_onsets(value, delays) for name, value in sorted(responses.items())},
        frozen_comparisons=frozen_comparisons(arrays, delays),
        layout_controls=layout_controls(arrays, catalog))
