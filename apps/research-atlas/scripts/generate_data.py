#!/usr/bin/env python3
"""Transcribe the reviewed research archive into frontend JSON, without simulation.

All numerical outputs are copied from the archived tables. Derived convenience
columns split existing intervals, display explicit count ratios, or join recorded
parameter labels; no sample is resampled,
pooled, fitted, removed for its outcome, or treated as a new observation.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import gzip
import json
import math
import re
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parents[1]
OUTPUT = APP / 'src/data/generated'
COMMIT = '4e1a667ad2d590ee365a395021f0c9772e63b8d1'
BASE = f'https://github.com/raghammer1/causal-spacetime-lab/blob/{COMMIT}/'
ARCHIVE = 'docs/experiments/'
SOURCE_LOCK = json.loads((APP / 'scripts/source-lock.json').read_text())
assert SOURCE_LOCK['sourceCommit'] == COMMIT
PRIMARY_METRICS = {'connected2', 'motif22_4', 'connected4', 'connected8', 'motif22_8', 'joint8', 'tv4'}


def scalar(value):
    """Parse unambiguous CSV scalars, preserving exact float round-trips."""
    if value is None or value == '':
        return None
    if not isinstance(value, str):
        if isinstance(value, (dict, list)):
            return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
        return value
    if value in ('True', 'true'):
        return True
    if value in ('False', 'false'):
        return False
    if re.fullmatch(r'-?(0|[1-9][0-9]*)', value):
        return int(value)
    try:
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError(f'Nonfinite source value: {value}')
        return parsed
    except ValueError:
        if value.lower() in {'nan', 'inf', '-inf', 'infinity', '-infinity'}:
            raise ValueError(f'Nonfinite source value: {value}')
        return value


def read_csv(path):
    with (ROOT / path).open(newline='', encoding='utf-8') as stream:
        return [{key: scalar(value) for key, value in row.items()} for row in csv.DictReader(stream)]


def read_json(path):
    return json.loads((ROOT / path).read_text())


def split_interval(rows, field='ci95', low='ci_low', high='ci_high'):
    for row in rows:
        value = row.get(field)
        endpoints = json.loads(value) if isinstance(value, str) else value
        row[low], row[high] = endpoints if endpoints is not None else (None, None)
        if endpoints is not None:
            assert len(endpoints) == 2
            assert endpoints == [None, None] or endpoints[0] <= endpoints[1]
    return rows


def compact(rows):
    """Omit bulky nested diagnostic objects, never scalar outcomes or statuses."""
    omit = {'support', 'batch_means', 'batch_difference_means', 'fit_difference_range', 'fit_means', 'accepted_unclassified_per_fit', 'per_fit'}
    return [{key: scalar(value) for key, value in row.items() if key not in omit} for row in rows]


def source(path):
    digest = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
    if digest != SOURCE_LOCK['sha256'].get(path):
        raise ValueError(f'Archive differs from pinned verified commit {COMMIT}: {path}')
    return {'path': path, 'sha256': digest, 'url': BASE + path}


def dataset(id, experiment, title, path, rows, chart, default_filters, description, uncertainty, sample_unit, assumptions, selection='All source rows and scalar columns. Empty fields become null. Nested CSV cells remain JSON strings.'):
    artifact = source(path)
    assert rows and all(isinstance(row, dict) for row in rows)
    columns = list(dict.fromkeys(key for row in rows for key in row))
    return dict(id=id, experiment=experiment, title=title, description=description, sourcePath=path, sourceUrl=artifact['url'], sha256=artifact['sha256'], rows=rows, columns=columns, chart=chart, defaultFilters=default_filters, uncertainty=uncertainty, sampleUnit=sample_unit, assumptions=assumptions, selection=selection)


def build():
    result = []
    def add(*args, **kwargs):
        result.append(dataset(*args, **kwargs))
    for identifier, folder, title, repeat, description in [
        ('time-primary', 'finite-density-scaling-v1', 'Time reconstruction · 4,200 primary trials', 200, 'Seven densities and three durations. Negative controls share event counts with physical draws and are not extra independent samples.'),
        ('time-followup', 'equal-count-followup', 'Time reconstruction · 8,000 follow-up trials', 2000, 'Separately seeded post hoc equal-count follow-up. The primary adverse contrast was retained; follow-up samples are not pooled with the primary study.'),
    ]:
        path = f'{ARCHIVE}{folder}/summary.csv'
        add(identifier, 1, title, path, read_csv(path), {'x':'density','y':'mean_estimate','low':'ci_low','high':'ci_high','series':'model','label':'Estimated proper time','unit':'input duration units'}, {'model':'sprinkled','duration':1 if repeat == 200 else .5}, description, f'Pointwise 95% percentile bootstrap interval of the mean; {2000 if repeat == 200 else 5000:,} bootstrap draws. SD is trial spread; SE is uncertainty in the mean. No familywise adjustment.', f'{repeat:,} independent Poisson sprinklings per density/duration cell; controls use the same counts.', 'Known density; uniform Poisson sampling in a flat 1+1D Minkowski diamond; c=1; interior chain counts only. Finite-density bias is not included in a mean CI.')
    path = f'{ARCHIVE}dimension-reconstruction-v1/summary.csv'
    add('dimension-summary',2,'Dimension estimates and adversarial controls',path,read_csv(path), {'x':'count','y':'estimated_dimension_mean','low':'estimated_dimension_ci_low','high':'estimated_dimension_ci_high','series':'dimension_label','label':'Myrheim–Meyer dimension','unit':'spacetime dimensions'}, {'family':'genuine'}, 'All 30 archived family/dimension/count summaries, including undefined estimates and deterministic controls.', 'Pointwise 95% whole-order percentile bootstrap intervals (2,000 resamples). Classification/rate Wilson columns are separate binomial intervals; deterministic controls have no binomial interval.', '200 independent orders per stochastic cell; 1,800 primary orders, 900 separate calibration orders, 3,006 controls.', 'Uniform fixed-count Minkowski diamonds for geometric samples; candidate dimensions 2,3,4; inversion bounded to [1,10]. An arbitrary control can match the pair fraction without geometry.')
    path = f'{ARCHIVE}adversarial-geometry-v1/summary.json'
    add('detector-summary',3,'Six detectors · hierarchical acceptance',path,compact(read_json(path)), {'x':'detector','y':'mean_acceptance','low':'hierarchical_ci_low','high':'hierarchical_ci_high','series':'detector','label':'Acceptance probability','unit':'fraction of orders'}, {'target':.95,'family':'multi_matched','dimension_label':2,'count':64}, 'All hierarchical summaries for six detectors and all three registered targets, including unsuccessful multistatistic search outputs.', 'Pointwise 95% hierarchical bootstrap: resample fits, then whole orders within fits (2,000 draws). Only three fits; constant samples may give zero-width bands. Per-fit Wilson bounds govern advancement.', 'Three independently calibrated fits × 200 independent test orders per stochastic cell. Search checkpoints are paired, not independent.', 'Acceptance is compatibility with selected summaries of a calibrated flat-diamond law, not geometric embeddability. Rank-two overlap is a positive control; box geometry is a boundary sensitivity control.', 'All 1,350 rows. Nested per-fit records are available in detector-rates and the exact source; all scalar fields retained.')
    path = f'{ARCHIVE}adversarial-geometry-v1/rates.csv'
    add('detector-rates',3,'Detector acceptance · per-fit Wilson intervals',path,read_csv(path), {'x':'detector','y':'rate','low':'wilson_low','high':'wilson_high','series':'detector','label':'Acceptance probability','unit':'fraction of orders'}, {'target':.95,'family':'multi_matched','dimension_label':2,'count':64,'fit':0}, 'All 4,050 per-fit results; independent calibration fits are kept separate.', 'Two-sided 95% Wilson intervals conditional on each fitted detector and development pool. These are not simultaneous confidence bands. Deterministic endpoints have null bounds.', '200 final orders per stochastic fit/cell; n is sample size, count is number of events in an order.', 'Frozen templates/thresholds; nominal acceptance target differs from achieved test acceptance. Missing bounds are unavailable, not zeros.')
    path = f'{ARCHIVE}adversarial-geometry-v1/advancement.json'
    raw = read_json(path)['primary']
    rows = []
    for detector, entry in raw.items():
        for row in entry['cells']:
            rows.append(dict(detector=detector, **row))
    add('detector-advancement',3,'Registered advancement decisions',path,rows, {'x':'detector','y':'count','label':'Registered cell event count','unit':'events'}, {'family':'genuine','dimension_label':2}, 'All designated benchmark cells. Every detector fails the full advancement benchmark; a supported cell alone is insufficient.', 'Decisions use an intersection of per-fit pointwise Wilson conditions; no simultaneous 95% claim.', '66 designated cells per detector across all three independent fits.', 'Positive lower bound ≥90%, negative upper bound ≤5%, every exact negative rejected; all conditions required.', 'Flatten primary[detector].cells; preserve every designated cell and status.')
    path = f'{ARCHIVE}local-causal-structure-v1/global.csv'
    add('local-global',4,'Global observables across sampling regions',path,split_interval(compact(read_csv(path))), {'x':'count','y':'estimate','low':'ci_low','high':'ci_high','series':'family','label':'Global mean','unit':'selected metric units'}, {'metric':'global_dimension','dimension':4,'family':'slab'}, 'All global summary outcomes from diamonds, slabs, boxes and synthetic controls. Global dimensions depend on region shape.', 'Pointwise 95% hierarchical whole-parent bootstrap across three fits. Inversions average only defined per-parent values; undefined counts retained.', 'Ordinary cells have 600 parents: 200 per fit. defined and undefined expose metric support.', 'Global diamond formulas require the diamond sampling law. A flat slab or box has geometry despite a shifted global estimate.', 'All 525 rows; nested fit means omitted, existing ci95 split into ci_low/high without rounding.')
    path = f'{ARCHIVE}local-causal-structure-v1/conditional.csv'
    local_rows = split_interval(compact([r for r in read_csv(path) if r['scope']=='across_fits']))
    primary_rows = [dict(r) for r in local_rows if r['count']==256 and r['family'] in ('diamond','slab') and r['dimension']==r['reference_dimension'] and r['metric'] in PRIMARY_METRICS]
    assert len(primary_rows)==42
    for identifier,title,rows,defaults,selection in [
        ('local-primary','All 42 primary conditional-law checks',primary_rows,{'family':'slab','dimension':4},'Across-fits N=256 diamond/slab rows, generating dimension equals reference dimension, seven registered observables; exactly 42 rows.'),
        ('local-conditional','Local conditional laws · all aggregate outcomes',local_rows,{'family':'slab','dimension':4,'reference_dimension':4,'metric':'connected2'},'All across_fits rows (including 16 motif categories); within-fit diagnostics and nested support remain available in the exact source.'),
    ]:
        add(identifier,4,title,path,rows,{'x':'metric' if identifier=='local-primary' else 'count','y':'difference','low':'ci_low','high':'ci_high','series':'family','reference':0,'referenceLabel':'Exact agreement / zero TV','label':'Reference difference / TV','unit':'probability units'},defaults,'All 42 primary checks meet their finite practical margins. Secondary failures, inconclusive tests and insufficient support are preserved. TV is a nonnegative distance, not a signed difference.','Pointwise 95% hierarchical percentile intervals, resampling parents and independent references; 2,000 draws. TV bootstrap bias near zero can put the interval above its point estimate; this does not establish a positive distance floor.','Three fits; 200 parents per ordinary fit. Intervals within a parent are dependent. Ratios pool counts within each fit and then average fits equally.','Conditional diamond law assumes uniform sampling in a causally convex flat region. Boxes may clip intervals. Support requires ≥30 positive parents and ≥100 intervals in every fit.',selection+' Existing interval fields are copied exactly; ci_low/high split ci95. Nested diagnostics omitted.')
    path = f'{ARCHIVE}local-causal-structure-v1/summary.json'
    summary = read_json(path)
    rows = []
    seen = set()
    for group in summary['conditional']:
        key=(group['family'],group['dimension'],group['count'])
        if key in seen: continue
        seen.add(key)
        local=group['local_dimension']
        rows.append(dict(family=group['family'],dimension=group['dimension'],count=group['count'],method='local',estimate=local['estimate'],ci95=scalar(local['ci95']),status=local['status'],parent_count=group['parent_count']))
    global_path=f'{ARCHIVE}local-causal-structure-v1/global.csv'
    for row in read_csv(global_path):
        if row['metric']=='global_dimension':
            rows.append(dict(family=row['family'],dimension=row['dimension'],count=row['count'],method='global',estimate=row['estimate'],ci95=row['ci95'],status='defined' if row['estimate'] is not None else 'undefined',parent_count=row['defined']))
    add('local-dimensions',4,'Global versus local dimension reconstruction',path,split_interval(rows),{'x':'dimension','y':'estimate','low':'ci_low','high':'ci_high','series':'method','label':'Reference-equivalent dimension','unit':'spacetime dimensions'},{'family':'slab','count':256},'Compare equal-fit means of per-parent global inversions with inversion of the pooled conditional two-event probability. These are different nonlinear estimands.','Pointwise 95% archived intervals. Missing local dimensions remain null; no endpoint clipping or invented uncertainty.','600 parents per ordinary cell; sparse support can leave a local estimate undefined.','Diamond/slab geometric cells recover known dimensions locally. Controls report reference-equivalent numbers, not physical dimensions.','Unique family/dimension/count local_dimension from summary.json, plus global_dimension rows transcribed from global.csv. Both source hashes are recorded in provenance.')
    path=f'{ARCHIVE}background-free-growth-v1/global.csv'
    add('growth-global',5,'Growth and reference ensemble trajectories',path,split_interval(compact(read_csv(path))),{'x':'count','y':'estimate','low':'ci_low','high':'ci_high','series':'parameter','reference':1/24,'referenceLabel':'d=2 exact E[t₂₂] = 1/24','label':'Induced 2+2 frequency','unit':'fraction of four-event subsets'},{'stage':'prefix','metric':'t22','family':'percolation'},'All prefix and thinning ensemble results; six registered p values and five reference/control families. Layout coordinates are never physical space.','Pointwise 95% within-batch whole-history bootstrap; 2,000 draws. Three batch means receive equal weight, without outer batch resampling. These bands do not replace the registered simultaneous decision bands.','96 independent histories per family: 32 per batch. Prefixes and four thinnings share a history; thinnings are averaged before resampling.','Fixed p transitive percolation with ancestral closure. References are supplied sampling laws. E[t22]=1/24 is a d=2 diamond reference only, not a reference for other metrics.','All 2,200 rows; nested support and batch means omitted, original ci95 retained and split exactly.')
    path=f'{ARCHIVE}background-free-growth-v1/primary.csv'
    rows=split_interval(read_csv(path),'band','band_low','band_high')
    split_interval(rows,'pointwise_ci95','pointwise_low','pointwise_high')
    add('growth-primary',5,'Registered simultaneous finite-signature screen',path,rows,{'x':'name','y':'estimate','low':'band_low','high':'band_high','series':'parameter','reference':0,'referenceLabel':'Target contrast = 0; allowed margin ±0.005','label':'Signature contrast','unit':'probability units'},{'scope':'growth','parameter':.02},'48 growth entries plus two separately screened eight-entry controls. Every fixed-p family fails; the d2 reference and deliberately misleading height-two control both pass.','Registered simultaneous max-centered-error bootstrap bands across 48 growth entries, with separate zero-event safeguards. Coverage is approximate. Pointwise bounds are separate columns. Controls have their own eight-entry bands.','96 independent histories per family; repeated prefixes and thinnings retain their common history bootstrap weights.','Each family must meet all eight ±0.005 practical margins: three late levels minus 1/24, two drifts and three thinning-prefix contrasts. Passing does not certify geometry.','All 64 rows. band_low/high split band; pointwise_low/high split pointwise_ci95. No bands clipped to a physical probability range.')
    path=f'{ARCHIVE}background-free-growth-v1/conditional.csv'
    rows=split_interval(compact([r for r in read_csv(path) if r['scope']=='equal_batch_mean']))
    add('growth-conditional',5,'Growth local-law comparisons and missing support',path,rows,{'x':'count','y':'difference','low':'ci_low','high':'ci_high','series':'parameter','reference':0,'referenceLabel':'Agreement with selected reference','label':'Conditional reference difference / TV','unit':'probability units'},{'family':'percolation','parameter':.02,'dimension':2,'stage':'prefix','metric':'connected2'},'All equal-batch conditional outcomes, preserving false rejections of genuine controls, insufficient information and reference disagreements.','Pointwise 95% history bootstrap with independent reference uncertainty. Near-zero TV percentile bootstrap is biased; it can exclude the point estimate. Not simultaneous bands.','96 histories per family. Conditional ratios pool counts within a batch; batch estimates are averaged equally. Interval counts are not independent sample sizes.','At least 30 positive histories and 100 mean interval exposures per batch. The matched height-two control has no nonempty intervals: missing is not agreement.','All equal_batch_mean rows; within-batch diagnostics and nested support remain in source. All scalar outcomes and original intervals retained; ci_low/high split ci95.')
    # Experiments 6 and 7: transcribe archived results, never rerun a model.
    path=f'{ARCHIVE}quantum-information-v1/summary.json'
    quantum=read_json(path)
    selected_metrics={
        'edge_auc','edge_recall_top_n_minus_1','mi_mean','mi_contrast','negativity_mean',
        'entangled_pair_fraction','stress_d3','positive_participation_rank',
        'triangle_violation_fraction','negative_eigenvalue_mass','phase_minus_stress_d3',
        'shuffle_minus_stress_d3','overlap_base_k2','overlap_ground_k2',
        'spearman_mi_coupling','spearman_mi_zz','cut_balanced_mean_abs_normalized_defect',
        'epsilon_agreement_k2','neighbor_tie_fraction_k2',
    }
    quantum_rows=[]
    for cell in quantum:
        for metric,estimate in cell['metrics'].items():
            if metric not in selected_metrics: continue
            ci=estimate.get('ci95') or (None,None)
            quantum_rows.append({**{key:cell[key] for key in ('family','n','h','preparation','delta','time','attempted','valid','failures')},
                'metric':metric,'mean':estimate['mean'],'sd':estimate.get('sd'),
                'ci_low':ci[0],'ci_high':ci[1],'lower':estimate.get('lower'),
                'alpha_lower':estimate.get('alpha_lower'),'independent_units':estimate['n'],
                'undefined':estimate['undefined'],'deterministic':estimate.get('deterministic',False),
                'weak_small_sample':estimate.get('weak_small_sample')})
    for cell in quantum:
        for metric,undefined in cell['undefined_metrics'].items():
            if metric not in selected_metrics or metric in cell['metrics']: continue
            assert undefined==cell['valid']
            quantum_rows.append({**{key:cell[key] for key in ('family','n','h','preparation','delta','time','attempted','valid','failures')},
                'metric':metric,'mean':None,'sd':None,'ci_low':None,'ci_high':None,'lower':None,'alpha_lower':None,
                'independent_units':0,'undefined':undefined,
                'deterministic':all(value.get('deterministic',False) for value in cell['metrics'].values()),'weak_small_sample':None})
    add('quantum-summary',6,'Quantum correlations · supplied and random interactions',path,quantum_rows,
        {'x':'n','y':'mean','low':'ci_low','high':'ci_high','series':'family','label':'Archived metric mean','unit':'selected metric units'},
        {'preparation':'ground','h':1,'delta':0,'time':0,'metric':'stress_d3'},
        'Supplied chains, symmetric and random all-to-all interactions, and state controls. A stable correlation ranking or a low-dimensional projection is not operational locality or spacetime.',
        'Archived percentile intervals and one-sided lower bounds are descriptive: independent calibration covered only 91.25% of known means at nominal 95%. They must not be read as validated confidence guarantees. Deterministic states have null intervals; exact chain-success bounds are separate.',
        'Whole independent coupling/preparation realizations; stochastic main cells have 24 units across three batches. Pairs, cuts, perturbations and repeated times are dependent within a unit. A symmetric deterministic preparation is one specified state.',
        'Fixed transverse-field Ising interactions; supplied tensor factors and external time. Mutual information measures total correlation. Participation rank is not a spacetime dimension. Uniform Model A has a degenerate MDS eigenspace. Its truncated three-dimensional stress and shuffle contrasts depend on an arbitrary basis and cannot support structural conclusions.',
        'Nineteen named scientific metrics from all 141 archived summary groups: 1,983 reported estimates and 60 explicit null rows for wholly undefined metrics declared by the source. Null rows have zero defined units and copied undefined counts. No field, preparation or adverse scalar result within that metric selection is filtered by outcome. Existing ci95 endpoints are split; batch means and other metrics remain in the source.')
    chain=[]
    for cell in quantum:
        if 'chain_success' not in cell:continue
        entry=cell['chain_success']
        chain.append({**{key:cell[key] for key in ('n','h','delta','preparation','time')},**entry,
            'success_fraction':entry['successes']/entry['attempted'] if entry['attempted'] else None})
    add('quantum-chain',6,'Supplied-chain recovery · exact success bounds',path,chain,
        {'x':'n','y':'success_fraction','low':'lower','series':'preparation','reference':.8,'referenceLabel':'Registered success-probability requirement 0.8','label':'Chain recovery success','unit':'fraction of independent chain realizations'},
        {'h':1,'delta':0},
        'All 72 registered h=1 supplied-chain realizations succeed. This validates reconstruction of locality already present in the Hamiltonian; it does not show that locality emerged.',
        'Exact one-sided Clopper–Pearson lower bounds, alpha=.05/3 per size. These separately validated binomial bounds are distinct from the undercovered bootstrap intervals. No upper bound was archived or invented.',
        '24 independent supplied-chain realizations per size, three sizes; each realization passes the joint archived chain-recovery criterion or fails as one unit.',
        'Known one-dimensional nearest-neighbor interactions with hidden labels. This is a positive control with supplied locality, not a background-free model.',
        'All three chain_success objects from summary.json, retaining every field and the copied cell labels. success_fraction is the displayed successes/attempted ratio; no uncertainty is recomputed.')
    path=f'{ARCHIVE}quantum-information-v1/calibration.json'
    calibration=read_json(path)
    calibration_rows=[dict(method='normal_percentile_bootstrap',n=None,p=None,
        coverage=calibration['normal_coverage'],coverage_mc_se=calibration['normal_coverage_mc_se'],
        trials=calibration['normal_trials'],nominal_coverage=.95)]
    calibration_rows += [dict(method='exact_binomial',n=entry['n'],p=entry['p'],coverage=entry['coverage'],
        coverage_mc_se=None,trials=None,nominal_coverage=1-.05/3) for entry in calibration['binomial_exact_coverage']]
    add('quantum-calibration',6,'Uncertainty calibration · the retained bootstrap failure',path,calibration_rows,
        {'x':'method','y':'coverage','series':'method','label':'Coverage in independent calibration','unit':'fraction of known parameters covered'},
        {'method':'normal_percentile_bootstrap'},
        'The nominal 95% percentile bootstrap covered 365 of 400 independent normal-mean calibration cases: 91.25%. Exact one-sided binomial coverage was enumerated separately.',
        'Normal coverage has the archived Monte Carlo standard error; binomial coverage is exact enumeration up to floating-point rounding, not a finite Monte Carlo estimate. Values marginally above 1 from source rounding are preserved.',
        '400 independent normal-mean coverage trials; fifteen exact binomial (n,p) calibration cells. These are numerical calibration cases, not physical spacetime samples.',
        'Calibration is independent of scientific state streams and did not tune the thresholds. Exact-binomial nominal per-cell coverage is 1−.05/3; normal-bootstrap nominal coverage is .95.',
        'One normal-coverage row and all fifteen binomial_exact_coverage rows. Missing n,p,standard errors or trial counts remain null; nominal coverage is the registered analytical level, not a fitted estimate.')

    raw_path=f'{ARCHIVE}dynamical-quantum-locality-v1/raw.json.gz'
    source(raw_path)
    dynamics=json.loads(gzip.decompress((ROOT/raw_path).read_bytes()))
    parameter_cells={}
    for row in dynamics:
        key=(row['N'],row['cell']);params={name:row['parameters'][name] for name in ('mu','Gamma')}
        if key in parameter_cells:assert parameter_cells[key]==params
        parameter_cells[key]=params
    def parameters_for(row):return parameter_cells[row['N'],row['cell']]
    path=f'{ARCHIVE}dynamical-quantum-locality-v1/summary.json'
    decision=read_json(path);primary=[]
    for cell in decision['cells']:
        primary.append({**{key:cell[key] for key in ('N','cell','attempted','valid','successes','assessment','cohort_complete')},
            **parameters_for(cell),**cell['component_successes'],
            'lower':cell['cp_family_bounds'][0],'upper':cell['cp_family_bounds'][1],
            'go_lower':cell['cp_go_bounds'][0],'go_upper':cell['cp_go_bounds'][1],
            'degree_null_successes':cell['degree_null_successes'],
            'degree_go_lower':cell['degree_null_go_bounds'][0],'degree_go_upper':cell['degree_null_go_bounds'][1],
            'success_fraction':cell['successes']/cell['attempted'] if cell['attempted'] else None,
            'target_joint_probability':decision['target_joint_probability'],'family_size':decision['family_size'],
            'alpha':decision['alpha'],'decision':decision['decision']})
    add('dynamical-primary',7,'Dynamical locality · registered joint decision',path,primary,
        {'x':'cell','y':'success_fraction','low':'lower','high':'upper','series':'N','reference':.8,'referenceLabel':'Required joint success probability0.8','label':'Joint C/L/T/D success','unit':'probability per independent exchangeable preparation'},
        {'N':5},
        'Every one of the 12 size/parameter cells has zero joint successes out of 12 preparations. The finite unconditioned labeled-locality screen is NO-GO; geometry and a continuum remain unresolved.',
        'Exact two-sided Clopper–Pearson bounds with total familywise alpha=.05 across 12 cells. The primary upper bound is .40218992470918974. Stricter GO and degree-null bounds are separate columns. Component counts are descriptive, without invented component intervals.',
        '12 independent E preparations per size/parameter cell, three batches of four. Source-target pairs, delays, perturbations and Born graphs stay inside that one preparation unit. Deterministic symmetric preparations do not enter these binomial counts.',
        'C: connected Born mass; L: concentrated nonzero response; T: ensemble/perturbation stability; D: improvement over initially frozen links. These practical necessary conditions are not a universal definition of locality or a spacetime classifier.',
        'All 12 summary.json cells, including component counts and both exact interval families. mu/Gamma join the hash-pinned raw archive by(N,cell). success_fraction is successes/attempted; no confidence fit or decision is recomputed.')
    path=f'{ARCHIVE}dynamical-quantum-locality-v1/structure.csv'
    structural=[{**row,**parameters_for(row)} for row in read_csv(path)]
    add('dynamical-structure',7,'Quantum-link evolution · exact Born structure',path,structural,
        {'x':'age','y':'connected_probability','series':'preparation','label':'Born probability of a connected graph','unit':'exact graph-measurement probability'},
        {'N':5,'cell':0,'preparation':'Splus'},
        'One-time Born graph laws under the full evolving-link Hamiltonian. Splus and Sempty are symmetric quantum states; E supplies realization-level asymmetry. Independent graph draws at different ages are not an edge trajectory.',
        'Exact enumeration of all 64 or 1,024 graphs per state; no graph-sampling confidence interval. E rows are separate independent preparations, not an aggregate mean. Numerical checks bound computational error; no continuum uncertainty estimate is claimed.',
        '168 preparation records: 144 stochastic E units and 24 specified symmetric states, each observed at six ages. Times and graph measurements within a preparation are dependent.',
        'N=4/5 matter qubits plus quantum links; external simulation time. Graph distance, connectivity and clustering are combinatorial observables, not physical geometry. TV compares exact density, marginal-product, count and labeled-degree null laws.',
        'All 1,008 rows and all columns of structure.csv, preserving batch/replicate identity. mu/Gamma join the pinned raw archive by(N,cell); no trajectories or confidence intervals are synthesized.')
    response_rows=[]
    for row in dynamics:
        assert row['status']=='ok'
        for detail in row['gate']['response_details']:
            response_rows.append({**{key:row[key] for key in ('N','cell','preparation','batch','replicate')},
                **parameters_for(row),**detail,**{key:row['gate'][key] for key in ('C','L','T','D','joint')}})
    add('dynamical-response',7,'Actual quantum response · evolving versus frozen links',raw_path,response_rows,
        {'x':'delay','y':'F','series':'preparation','label':'Full quantum top-two response capture F','unit':'fraction of off-diagonal target response'},
        {'N':5,'cell':0,'preparation':'Splus'},
        'Actual Pauli-Y signalling probes after age2 under the full quantum law, with paired Gamma+5% and initially frozen-link controls. These are distinct from the fresh-matter frozen-graph conditional summaries.',
        'Exact finite-state response calculations per preparation, not confidence intervals. E has 12 independent units per cell; symmetric controls one state each. F and gain are descriptive realization values; exact joint decision bounds are in dynamical-primary.',
        '168 complete preparations, two registered response delays each. Sources, targets, perturbations and times are dependent within each preparation. Locality capture excludes the source diagonal and preserves fractional ties.',
        'Target trace distance measures operational distinguishability, not pre-existing correlation. A source row with no response gives undefined F, never perfect locality. Mean E summaries in the interface are descriptive arithmetic averages only.',
        'All 336 gate.response_details objects from the pinned raw archive, plus exact cell labels and C/L/T/D/joint flags. Full states and individual source-target arrays remain in the source; none are copied into the app.')
    path=f'{ARCHIVE}dynamical-locality-conditioned-response.json'
    conditioned=read_json(path);conditional_rows=[]
    for row in conditioned['aggregates']:
        flat={**{key:row[key] for key in ('N','cell','preparation','law','delay','preparation_units','pooled_graph_conditioned_F_given_valid')},**parameters_for(row)}
        for metric,estimate in row['metrics'].items():
            flat.update({f'{metric}_{key}':value for key,value in estimate.items()})
        conditional_rows.append(flat)
    add('dynamical-conditioned',7,'Conditional graphs versus unobserved quantum mixtures',path,conditional_rows,
        {'x':'cell','y':'F_of_unobserved_mixture_response_mean','series':'law','label':'Unobserved frozen-mixture response capture','unit':'fraction of off-diagonal target response'},
        {'N':5,'preparation':'E','delay':.25},
        'Secondary descriptive controls: reset matter to a fresh product and freeze each graph. Mean graph-conditioned F, F of averaged conditional responses, and F of the unobserved mixture are different quantities. High conditional capture can coexist with tiny valid or connected graph mass.',
        'No confidence intervals or new hypothesis test. Copied means, SDs and ranges describe independent E preparations; deterministic Splus/Sempty use one specified state and null SD. Defined and undefined unit counts and all graph-validity masses are retained.',
        '216 archived aggregate rows over 168 preparations: E uses 12 independent units per cell; Splus/Sempty one. Born, density and degree laws are exact weighted graph controls on the same finite catalogues, not extra independent physical evidence.',
        'An accessible graph record and a frozen Hamiltonian change the operational protocol. Undefined graph-conditioned F mass is reported rather than discarded. No connectivity postselection is used. These controls do not change the registered unconditioned NO-GO.',
        'All 216 existing aggregates, all ten metric objects flattened into scalar suffix columns, and the separate pooled conditional ratio. No per-preparation means are newly pooled, no intervals are invented, and the 1,008 detailed secondary unit rows remain in the linked source.')
    return result


def validate(datasets):
    ids=[d['id'] for d in datasets]
    assert len(ids)==len(set(ids))
    assert set(d['experiment'] for d in datasets)=={1,2,3,4,5,6,7}
    for data in datasets:
        assert data['sourceUrl']==BASE+data['sourcePath']
        assert data['sha256']==source(data['sourcePath'])['sha256']
        for row in data['rows']:
            for value in row.values():
                assert value is None or isinstance(value,(str,int,float,bool))
                assert not isinstance(value,float) or math.isfinite(value)
    lookup={d['id']:d for d in datasets}
    assert len(lookup['local-primary']['rows'])==42
    assert all(r['status']=='equivalent' for r in lookup['local-primary']['rows'])
    growth=lookup['growth-primary']['rows']
    primary=[r for r in growth if r['scope']=='growth']
    assert len(primary)==48 and {r['parameter'] for r in primary}=={.005,.01,.02,.05,.1,.3}
    assert all(r['family_status']=='finite_signature_failure' for r in primary)
    assert len(lookup['time-primary']['rows'])==63 and len(lookup['time-followup']['rows'])==12
    return datasets


def serialize(value):
    return json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n'


def pack(dataset):
    """Lossless transport: store column names once, preserve every scalar/interval."""
    columns = dataset['columns']
    assert all(set(row) == set(columns) for row in dataset['rows'])
    packed = {key: value for key, value in dataset.items() if key != 'rows'}
    packed['records'] = [[row[column] for column in columns] for row in dataset['rows']]
    return packed


def generated_files():
    datasets=validate(build())
    files={OUTPUT/f"{d['id']}.json":serialize(pack(d)) for d in datasets}
    # Input bytes are checked by build()/validate(). Documentary links point to
    # the immutable reviewed commit, even when the current research log evolves.
    # This is the explicitly pinned seven-experiment research snapshot, not a
    # claim about the moving main branch or future documentary changes.
    sources = [dict(path=path, sha256=digest, url=BASE + path)
               for path, digest in sorted(SOURCE_LOCK['sha256'].items())]
    provenance=dict(schemaVersion=1,sourceCommit=COMMIT,repository='https://github.com/raghammer1/causal-spacetime-lab',transformation='python3 apps/research-atlas/scripts/generate_data.py',sources=sources)
    files[OUTPUT/'provenance.json']=serialize(provenance)
    imports='\n'.join(f"import data{i} from './generated/{d['id']}.json';" for i,d in enumerate(datasets))
    files[APP/'src/data/index.ts']=f"// Generated by scripts/generate_data.py; do not edit measurements by hand.\nimport type {{ Dataset, Provenance }} from './types';\nimport {{ hydrateDataset }} from './hydrate';\n{imports}\nimport sourceProvenance from './generated/provenance.json';\nexport const datasets: Dataset[] = [{', '.join(f'hydrateDataset(data{i})' for i in range(len(datasets)))}];\nexport const provenance: Provenance = sourceProvenance;\nexport const sourceCommit = provenance.sourceCommit;\nexport const sourceUrl = (path: string) => `https://github.com/raghammer1/causal-spacetime-lab/blob/${{sourceCommit}}/${{path}}`;\nexport const getDataset = (id: string): Dataset => {{\n  const found = datasets.find(dataset => dataset.id === id);\n  if (!found) throw new Error(`Unknown archived dataset: ${{id}}`);\n  return found;\n}};\nexport type {{ Dataset, DataRow, DataValue, ChartSpec, Provenance }} from './types';\n"
    catalog = [{**{key: value for key, value in data.items() if key != 'rows'}, 'rowCount': len(data['rows'])} for data in datasets]
    files[OUTPUT/'catalog.json'] = serialize(catalog)
    files[APP/'src/data/catalog.ts'] = """// Generated by scripts/generate_data.py; metadata only, no observation rows.
import type { Dataset, DataValue, Provenance } from './types';
import catalog from './generated/catalog.json';
import sourceProvenance from './generated/provenance.json';
export type DatasetMetadata = Omit<Dataset, 'rows'> & { rowCount: number };
// Copy only actual keys; JSON union inference adds optional undefined properties.
export const datasetCatalog: DatasetMetadata[] = catalog.map(entry => {
  const defaultFilters: Record<string, DataValue> = {};
  for (const [key, value] of Object.entries(entry.defaultFilters)) {
    if (value === null || typeof value === 'string' || typeof value === 'boolean' ||
        (typeof value === 'number' && Number.isFinite(value))) defaultFilters[key] = value;
    else throw new Error(`Invalid catalog filter ${entry.id}.${key}`);
  }
  return { ...entry, defaultFilters };
});
export const provenance: Provenance = sourceProvenance;
export const sourceCommit = provenance.sourceCommit;
export const sourceUrl = (path: string) => `https://github.com/raghammer1/causal-spacetime-lab/blob/${sourceCommit}/${path}`;
"""
    entries = '\n'.join(f"  '{data['id']}': () => import('./generated/{data['id']}.json')," for data in datasets)
    files[APP/'src/data/loader.ts'] = """// Generated by scripts/generate_data.py; each dataset is a separate lazy chunk.
import type { Dataset } from './types';
import { hydrateDataset, type PackedDataset } from './hydrate';
const imports: Record<string, () => Promise<{ default: PackedDataset }>> = {
""" + entries + """
};
const cache = new Map<string, Promise<Dataset>>();

/** Load one archive only. A failed fetch may be retried; unknown IDs fail explicitly. */
export function loadDataset(id: string): Promise<Dataset> {
  const load = Object.prototype.hasOwnProperty.call(imports, id) ? imports[id] : undefined;
  if (!load) return Promise.reject(new Error(`Unknown archived dataset: ${id}`));
  const existing = cache.get(id);
  if (existing) return existing;
  const pending = load().then(module => hydrateDataset(module.default)).catch((error: unknown) => {
    cache.delete(id);
    throw error;
  });
  cache.set(id, pending);
  return pending;
}
"""
    return files


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true',help='Fail if committed frontend data differs from current archives; write nothing.')
    args=parser.parse_args()
    files=generated_files()
    stale=[]
    for path,content in files.items():
        if args.check:
            if not path.exists() or path.read_text()!=content: stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(content)
    if stale:
        raise SystemExit('Generated data is stale: '+', '.join(stale))
    count = sum(path.parent == OUTPUT and path.name not in {'catalog.json', 'provenance.json'} for path in files)
    print(f'{"Verified" if args.check else "Generated"} {count} datasets and lazy loaders from archived results; no studies rerun.')

if __name__=='__main__': main()
