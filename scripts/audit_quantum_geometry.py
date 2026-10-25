#!/usr/bin/env python3
"""Independently verify archived Experiment 6 geometry without lab helpers.

Use saved coordinates for projection stresses: an eigensolver may rotate a
repeated eigenspace, so independently regenerated truncated coordinates would
not be an appropriate equality test. Dijkstra closure, explicit centered-Gram
matrix multiplication and SciPy's eigensolver provide alternative calculations.
This is an audit of frozen data, not a new experiment or fitted test.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import heapq
import itertools
import json
import math
from pathlib import Path
import time

import numpy as np
import scipy
from scipy.linalg import eigh

ATOL = 1e-9
RTOL = 1e-9
EPSILONS = (1e-12, 1e-9, 1e-6)


def tied(a, b):
    return abs(a-b) <= 1e-10 + 1e-8*max(abs(a), abs(b))


def top_weights(matrix, k):
    n = len(matrix)
    weights = np.zeros((n,n))
    ambiguous = 0
    for i in range(n):
        candidates = [j for j in range(n) if j != i]
        boundary = heapq.nlargest(k, (matrix[i,j] for j in candidates))[-1]
        ties = [j for j in candidates if tied(matrix[i,j], boundary)]
        above = [j for j in candidates if matrix[i,j] > boundary and j not in ties]
        remainder = k-len(above)
        ambiguous += 0 < remainder < len(ties)
        weights[i,above] = 1
        weights[i,ties] = remainder/len(ties)
    return weights, ambiguous/n


def dijkstra_closure(distance):
    n = len(distance)
    answer = np.empty_like(distance)
    for source in range(n):
        best = [math.inf]*n
        best[source] = 0.
        queue = [(0.,source)]
        while queue:
            length, current = heapq.heappop(queue)
            if length > best[current]:
                continue
            for target in range(n):
                candidate = length+distance[current,target]
                if candidate < best[target]:
                    best[target] = candidate
                    heapq.heappush(queue,(candidate,target))
        answer[source] = best
    return answer


def distance_metrics(distance):
    n = len(distance)
    off = [distance[i,j] for i in range(n) for j in range(i+1,n)]
    comparisons = violations = 0
    excesses = [0.]
    for i in range(n):
        for j in range(i+1,n):
            for k in range(n):
                if k in (i,j):
                    continue
                excess = distance[i,j]-(distance[i,k]+distance[k,j])
                excesses.append(excess)
                comparisons += 1
                tolerance = 1e-10+1e-8*max(distance[i,j],distance[i,k],distance[k,j])
                violations += excess > tolerance
    maximum = max(off)
    return dict(distance_symmetry_error=float(np.max(np.abs(distance-distance.T))),
        distance_min=min(off),distance_max=maximum,zero_distance_pairs=sum(x<=1e-10 for x in off),
        triangle_comparisons=comparisons,triangle_violation_fraction=violations/comparisons,
        triangle_max_excess=max(excesses),triangle_max_relative_excess=max(excesses)/maximum if maximum else 0.)


def spectral_check(distance):
    n = len(distance)
    center = np.eye(n)-np.ones((n,n))/n
    gram = -.5*center@(distance*distance)@center
    gram = (gram+gram.T)/2
    values, vectors = eigh(gram,driver='evr')
    values, vectors = values[::-1], vectors[:,::-1]
    threshold = 1e-12*max(1.,max(abs(values)))
    positive = values > threshold
    negative = values < -threshold
    chosen = values[positive]
    mass = np.sum(np.abs(values[np.abs(values)>threshold]))
    positive_gram = (vectors[:,positive]*chosen)@vectors[:,positive].T
    metrics = dict(positive_rank=int(sum(positive)),negative_rank=int(sum(negative)),
        negative_eigenvalue_mass=-sum(values[negative])/mass if mass else 0.,
        positive_participation_rank=sum(chosen)**2/sum(chosen**2) if len(chosen) else 0.,
        repeated_positive_eigenvalue_pairs=sum(tied(a,b) for a,b in zip(chosen[:-1],chosen[1:])))
    return values, positive_gram, metrics


def stress(distance, coordinates):
    numerator = denominator = 0.
    for i in range(len(distance)):
        for j in range(i+1,len(distance)):
            reconstructed = math.sqrt(sum(float(x*x) for x in coordinates[i]-coordinates[j]))
            numerator += (distance[i,j]-reconstructed)**2
            denominator += distance[i,j]**2
    return math.sqrt(numerator/denominator) if denominator else 0.


def component_count(adjacency):
    # Union-find, separate from the generator's depth-first component traversal.
    parent = list(range(len(adjacency)))
    def find(i):
        while parent[i] != i:
            i = parent[i]
        return i
    for i in range(len(adjacency)):
        for j in range(i+1,len(adjacency)):
            if adjacency[i,j]:
                parent[find(i)] = find(j)
    return len({find(i) for i in range(len(adjacency))})


class Audit:
    def __init__(self):
        self.comparisons = 0
        self.failures = []
        self.failure_count = 0
        self.max_errors = {}

    def check(self, category, actual, expected, sample):
        self.comparisons += 1
        a, b = np.asarray(actual,dtype=float), np.asarray(expected,dtype=float)
        valid = a.shape == b.shape and np.all(np.isfinite(a)) and np.all(np.isfinite(b))
        error = float(np.max(np.abs(a-b),initial=0)) if valid else math.inf
        self.max_errors[category] = max(self.max_errors.get(category,0),error)
        if not valid or not np.allclose(a,b,atol=ATOL,rtol=RTOL):
            self.failure_count += 1
            if len(self.failures) < 100:
                self.failures.append(dict(sample=sample,category=category,error=error,
                    actual_shape=list(a.shape),expected_shape=list(b.shape)))


def validate_manifest(archive):
    manifest = json.loads((archive/'manifest.json').read_text())
    for name, expected in manifest['sha256'].items():
        if Path(name).name != name:
            raise ValueError('nonlocal manifest name')
        if hashlib.sha256((archive/name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'archive hash mismatch: {name}')
    digest = hashlib.sha256()
    for name in manifest['scientific_files']:
        if Path(name).name != name:
            raise ValueError('nonlocal scientific name')
        digest.update(name.encode())
        digest.update((archive/name).read_bytes())
    if digest.hexdigest() != manifest['scientific_digest']:
        raise ValueError('scientific digest mismatch')
    return manifest['scientific_digest']


def audit_archive(archive):
    started = time.perf_counter()
    archive = Path(archive)
    digest = validate_manifest(archive)
    metadata = json.loads((archive/'metadata.json').read_text())
    check = Audit()
    states = inference_records = triangle_comparisons = null_records = 0
    all_rows = {}
    with gzip.open(archive/'raw.jsonl.gz','rt') as file:
        for line in file:
            row = json.loads(line)
            all_rows[row['sample_id']] = row
            if row['status'] != 'ok':
                continue
            states += 1
            sample = row['sample_id']
            original = np.asarray(row['observables']['mi'],dtype=float)
            mi = np.clip((original+original.T)/2,0,2)
            np.fill_diagonal(mi,0)
            n = len(mi)
            upper = np.triu_indices(n,1)
            check.check('mi_symmetry',original,original.T,sample)
            check.check('mi_diagonal',np.diag(original),np.zeros(n),sample)
            expected_neighbors = {}
            tie_metrics = {}
            for k in (1,2,3):
                weights, ambiguity = top_weights(mi,k)
                expected_neighbors[k] = weights
                tie_metrics[f'neighbor_tie_fraction_k{k}'] = ambiguity
                for permutation in (np.arange(n)[::-1],np.roll(np.arange(n),1)):
                    changed,_ = top_weights(mi[np.ix_(permutation,permutation)],k)
                    check.check('neighbor_relabel_equivariance',changed,weights[np.ix_(permutation,permutation)],sample)
                floored = [top_weights(np.maximum(mi,eps),k)[0] for eps in EPSILONS]
                overlap = min(np.minimum(a,b).sum()/(n*k) for a,b in itertools.combinations(floored,2))
                check.check(f'epsilon_agreement_k{k}',row['metrics'][f'epsilon_agreement_k{k}'],overlap,sample)
            scalar_metrics = dict(mi_mean=float(mi[upper].mean()),mi_std=float(mi[upper].std()),
                mi_contrast=float(np.ptp(mi[upper])),zero_information_pairs=int(np.sum(mi[upper]==0)),**tie_metrics)
            densities, components = [], []
            maximum = float(mi.max())
            for threshold in (.25,.5,.75):
                adjacency = mi >= threshold*maximum if maximum else np.zeros((n,n),dtype=bool)
                np.fill_diagonal(adjacency,False)
                density = sum(bool(adjacency[i,j]) for i,j in zip(*upper))/len(upper[0])
                component = component_count(adjacency)
                scalar_metrics[f'threshold_{threshold:g}_edge_density'] = density
                scalar_metrics[f'threshold_{threshold:g}_components'] = component
                densities.append(density)
                components.append(component)
            scalar_metrics['threshold_edge_density_range'] = max(densities)-min(densities)
            scalar_metrics['threshold_component_range'] = max(components)-min(components)
            check.check('registered_epsilon_count',len(row['inference']),3,sample)
            for epsilon in EPSILONS:
                inference_records += 1
                saved = row['inference'][str(epsilon)]
                distance = np.zeros((n,n))
                for i in range(n):
                    for j in range(i+1,n):
                        distance[i,j] = distance[j,i] = math.log(2)-math.log(max(mi[i,j],epsilon))
                closure = dijkstra_closure(distance)
                expected = dict(scalar_metrics)
                expected['regularized_pair_fraction'] = float(sum(mi[upper]<epsilon)/len(upper[0]))
                expected['closure_changed_pair_fraction'] = sum(not tied(a,b) for a,b in zip(distance[upper],closure[upper]))/len(upper[0])
                check.check('saved_epsilon',saved['epsilon'],epsilon,sample)
                check.check('saved_mi',saved['mi'],mi,sample)
                projections = {}
                for prefix, dist in (('',distance),('closure_',closure)):
                    check.check(prefix+'distance',saved[prefix+'distance'],dist,sample)
                    dm = distance_metrics(dist)
                    triangle_comparisons += dm['triangle_comparisons']
                    eigenvalues, positive_gram, sm = spectral_check(dist)
                    check.check(prefix+'eigenvalues',saved[prefix+'eigenvalues'],eigenvalues,sample)
                    coordinates = np.asarray(saved[prefix+'coordinates'],dtype=float).reshape(n,-1)
                    check.check(prefix+'coordinate_rank',coordinates.shape[1],sm['positive_rank'],sample)
                    check.check(prefix+'positive_gram',coordinates@coordinates.T,positive_gram,sample)
                    check.check(prefix+'centered_coordinates',coordinates.mean(axis=0),np.zeros(coordinates.shape[1]),sample)
                    expected.update({prefix+key:value for key,value in {**dm,**sm}.items()})
                    for dimension in (1,2,3):
                        projections[f'{prefix}stress_d{dimension}'] = stress(dist,coordinates[:,:dimension])
                        projections[f'{prefix}stress_d{dimension}_ambiguous'] = float(
                            dimension < coordinates.shape[1] and tied(eigenvalues[dimension-1],eigenvalues[dimension]))
                    projections[prefix+'stress_full'] = stress(dist,coordinates)
                check.check('saved_metric_count',len(saved['metrics']),len(expected),sample)
                for key,value in expected.items():
                    check.check('stored_metric:'+key,saved['metrics'][key],value,sample)
                for k,weights in expected_neighbors.items():
                    check.check('fractional_neighbors',saved['neighbors'][f'k{k}'],weights,sample)
                    check.check('neighbor_row_mass',np.asarray(saved['neighbors'][f'k{k}']).sum(axis=1),np.full(n,k),sample)
                if epsilon == 1e-9:
                    for key,value in {**expected,**projections}.items():
                        check.check('primary_metric:'+key,row['metrics'][key],value,sample)
            nulls = row.get('nulls',[])
            null_records += len(nulls)
            if nulls:
                for key in ('stress_d1','stress_d2','stress_d3','positive_participation_rank'):
                    check.check('conditional_null_mean:'+key,row['metrics']['shuffle_'+key+'_mean'],
                        sum(record[key] for record in nulls)/len(nulls),sample)
                check.check('conditional_null_stress_contrast',row['metrics']['shuffle_minus_stress_d3'],
                    row['metrics']['shuffle_stress_d3_mean']-row['metrics']['stress_d3'],sample)
    paired_rows = 0
    for row in all_rows.values():
        if row.get('baseline_id') is None or row['status'] != 'ok':
            continue
        baseline = all_rows[row['baseline_id']]
        paired_rows += 1
        for k in (1,2,3):
            first = np.asarray(row['inference']['1e-09']['neighbors'][f'k{k}'])
            second = np.asarray(baseline['inference']['1e-09']['neighbors'][f'k{k}'])
            check.check('paired_overlap_k'+str(k),row['metrics'][f'overlap_base_k{k}'],
                sum(np.minimum(first,second).flat)/(row['n']*k),row['sample_id'])
    return dict(audit='independent archived quantum geometry',status='pass' if not check.failure_count else 'fail',
        scientific_digest=digest,source_commit=metadata.get('source_commit'),
        audit_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        versions=dict(numpy=np.__version__,scipy=scipy.__version__),
        states=states,archive_rows=len(all_rows),inference_records=inference_records,
        raw_and_closure_triangle_inequalities=triangle_comparisons,paired_rows=paired_rows,
        conditional_null_scalar_records=null_records,comparisons=check.comparisons,
        failed_comparisons=check.failure_count,failures=check.failures,max_absolute_errors=check.max_errors,
        absolute_tolerance=ATOL,relative_tolerance=RTOL,elapsed_seconds=time.perf_counter()-started,
        limitations=['Quantum reductions are inputs to this separate geometry audit.',
            'Conditional null matrices were not stored; only their recorded metric means are audited.',
            'Coupling-normalized comparison embeddings were not stored; this audit covers MI inference.',
            'Projection stresses use archived coordinates to preserve arbitrary degenerate eigenspace choices.',
            'An audit pass verifies calculations, not the physical meaning of a geometric interpretation.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    result = audit_archive(args.archive)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({key:result[key] for key in ('status','states','inference_records','comparisons','failed_comparisons','elapsed_seconds')}))
    if result['failed_comparisons']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
