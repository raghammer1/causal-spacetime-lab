#!/usr/bin/env python3
"""Transcribe the reviewed research archive into frontend JSON, without simulation.

All numerical outputs are copied from the archived tables. Derived convenience
columns only split an existing two-endpoint interval; no sample is resampled,
pooled, fitted, removed for its outcome, or treated as a new observation.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parents[1]
OUTPUT = APP / 'src/data/generated'
COMMIT = '9bc5984c656271c247354e0079fd900702642064'
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
    return result


def validate(datasets):
    ids=[d['id'] for d in datasets]
    assert len(ids)==len(set(ids))
    assert set(d['experiment'] for d in datasets)=={1,2,3,4,5}
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
    # Never sweep future experiment documents into this first-five snapshot.
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
