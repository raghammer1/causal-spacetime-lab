"""Independent raw-count/registered-bootstrap review; no primary generation."""
from collections import Counter, defaultdict
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from causal_lab.local_structure import motif_catalog

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('archive', nargs='?', default='docs/experiments/background-free-growth-v1',
                    type=Path, help='complete registered Experiment 5 archive')
parser.add_argument('--output-prefix', type=Path, default=Path('results/growth-statistics-review'),
                    help='write PREFIX.md and PREFIX.json outside the archive')
args = parser.parse_args()
ROOT = args.archive.resolve()
if not ROOT.is_dir():
    parser.error('archive must be an existing directory')
output_md = Path(str(args.output_prefix) + '.md').resolve()
output_json = Path(str(args.output_prefix) + '.json').resolve()
if any(path.is_relative_to(ROOT) for path in (output_md, output_json)):
    parser.error('review outputs must be outside the source archive')
output_md.parent.mkdir(parents=True, exist_ok=True)
output_json.parent.mkdir(parents=True, exist_ok=True)
summaries = json.loads((ROOT / 'summary.json').read_text())
primary = json.loads((ROOT / 'primary.json').read_text())
metadata = json.loads((ROOT / 'metadata.json').read_text())
configuration = metadata['config']
DRAWS = configuration['bootstrap_draws']
if (metadata.get('run_kind') != 'primary' or configuration['batches'] != 3
        or configuration['probabilities'] != [.005, .01, .02, .05, .1, .3]
        or not isinstance(DRAWS, int) or isinstance(DRAWS, bool) or DRAWS < 2):
    parser.error('this review requires the full registered primary family/three-batch grid')
# The narrative below is the frozen experiment's scientific review, not a
# template for interpreting other seeds or newly tuned simulations. Numerical
# checks are recomputed from the supplied archive; the identity guard prevents
# applying that narrative to a different declared scientific dataset.
if metadata.get('scientific_sha256') != '534c51d1745f4d370a87ced03b895b5ff935e3811a362f9349554b164f0a57da':
    parser.error('this review is scoped to the registered Experiment 5 scientific dataset')
with gzip.open(ROOT / 'references.json.gz', 'rt') as stream:
    references = json.load(stream)
assert isinstance(references, list)
CELLS = [('prefix', n, n) for n in (32, 64, 128, 256, 512)] + [('thinned', n, n // 2) for n in (128, 256, 512)]
NAMES = ['connected2', 'motif22_4', 'connected4', 'connected8', 'motif22_8', 'joint8', 'tv4']
short = {'equivalent': 'E', 'contradicts': 'F', 'inconclusive': 'I', 'insufficient_information': 'S'}
catalog = motif_catalog()
c4 = np.asarray([item['components'] == 1 for item in catalog])
n22 = np.asarray([item['n22'] for item in catalog])
failures = []
checked = Counter()
raw_review = {}
primary_boots = []
primary_points = []


def verify(actual, expected, label):
    checked[label.split(':')[0]] += 1
    a = np.asarray(np.nan if actual is None else actual, dtype=float)
    b = np.asarray(np.nan if expected is None else expected, dtype=float)
    if not np.allclose(a, b, atol=2e-12, rtol=2e-12, equal_nan=True):
        failures.append({'label': label, 'actual': actual, 'expected': expected.tolist() if isinstance(expected, np.ndarray) else expected})


def rng(batch, phase, family, parameter):
    key = json.dumps(['growth-v1', metadata['config']['seed'], batch, phase, family,
                      parameter, 0, None, None], separators=(',', ':'), ensure_ascii=True)
    seed = int.from_bytes(hashlib.sha256(key.encode('ascii')).digest(), 'big')
    return np.random.Generator(np.random.PCG64(seed))


def ratio(b, a):
    return np.divide(b, a, out=np.full_like(b, np.nan), where=a != 0)


def ci(values):
    return None if not np.all(np.isfinite(values)) else np.quantile(values, [.025, .975]).tolist()


def metric(cell, name, section='metrics'):
    return next(row for row in cell[section] if row['metric'] == name)


def reference_vectors(reference, draws):
    four = np.asarray(reference['m4']['counts'], dtype=float)
    four /= four.sum()
    table = np.asarray(reference['m8']['joint_counts'], dtype=float)
    eight = table[:, 2] / table[:, 2].sum()
    category = np.column_stack([table[:, 0], table[:, 1] / 70, table[:, 0] * table[:, 1] / 70])
    if reference['exact']:
        b4 = np.tile(four, (draws, 1))
        b8 = np.tile(eight, (draws, 1))
    else:
        random = rng(reference['fit'], 'bootstrap_reference', 'reference', reference['dimension'])
        b4 = random.multinomial(reference['m4']['count'], four, size=draws) / reference['m4']['count']
        b8 = random.multinomial(reference['m8']['count'], eight, size=draws) / reference['m8']['count']
    point = np.r_[reference['connected2'], four @ n22, four @ c4, eight @ category, four]
    boot = np.column_stack([np.full(draws, reference['connected2']), b4 @ n22, b4 @ c4, b8 @ category, b4])
    return point, boot


refcache = {(ref['fit'], ref['dimension']): reference_vectors(ref, DRAWS) for ref in references}
for summary in summaries:
    family, parameter = summary['family'], summary['parameter']
    name = f'{family}-{parameter}'
    with gzip.open(ROOT / 'raw' / f'{name}.jsonl.gz', 'rt') as stream:
        raw = [json.loads(line) for line in stream]
    groups = defaultdict(lambda: defaultdict(list))
    for row in raw:
        groups[row['batch']][row['history_number']].append(row)
    arrays = []
    for batch, histories in sorted(groups.items()):
        bs, ass, es, gs, vs = [], [], [], [], []
        for number, history in sorted(histories.items()):
            b, a, e, g = [], [], [], []
            for stage, source, count in CELLS:
                rows = [row for row in history if (row['stage'], row['source_count'], row['count']) == (stage, source, count)]
                assert len(rows) == (1 if stage == 'prefix' else 4)
                nums, dens, expos, global_values = [], [], [], []
                for row in rows:
                    motifs = np.asarray(row['interval_m4_motif_counts'])
                    a2, a4, a8 = [row[f'interval_m{m}_count'] for m in (2, 4, 8)]
                    nums.append([row['interval_m2_connected'], motifs @ n22, motifs @ c4,
                                 row['interval_m8_connected'], row['interval_m8_n22_sum'] / 70,
                                 row['interval_m8_connected_n22_sum'] / 70, *motifs])
                    dens.append([a2, a4, a4, a8, a8, a8] + [a4] * 16)
                    expos.append([a2, a4, a8])
                    global_values.append([row['ordering_fraction'], row['longest_chain'],
                                          row['n22'] / math.comb(count, 4), row['n31'] / math.comb(count, 4)])
                b.append(np.mean(nums, axis=0)); a.append(np.mean(dens, axis=0)); e.append(np.mean(expos, axis=0))
                g.append(np.mean(global_values, axis=0))
            bs.append(b); ass.append(a); es.append(e); gs.append(g)
            t = np.asarray(g)[:, 2]
            vs.append([t[2] - 1/24, t[3] - 1/24, t[4] - 1/24,
                       t[3] - t[2], t[4] - t[3], t[5] - t[1], t[6] - t[2], t[7] - t[3]])
        b, a, e, g, v = map(np.asarray, (bs, ass, es, gs, vs))
        w = rng(batch, 'bootstrap_history', family, parameter).multinomial(len(histories),
                  np.full(len(histories), 1 / len(histories)), size=DRAWS)
        bootb = (w @ b.reshape(len(b), -1)).reshape(DRAWS, 8, 22)
        boota = (w @ a.reshape(len(a), -1)).reshape(DRAWS, 8, 22)
        arrays.append({'batch': batch, 'b': b, 'a': a, 'e': e, 'g': g, 'v': v, 'w': w,
                       'ratio': ratio(b.sum(axis=0), a.sum(axis=0)), 'boot': ratio(bootb, boota)})
    point = np.mean([item['v'].mean(axis=0) for item in arrays], axis=0)
    boots = np.mean([item['w'] @ item['v'] / len(item['v']) for item in arrays], axis=0)
    for i, row in enumerate(summary['p22_vector']):
        verify(row['estimate'], point[i], 'p22_point:' + name + ':' + row['name'])
        verify(row['ci95'], ci(boots[:, i]), 'p22_ci:' + name + ':' + row['name'])
    if family == 'percolation':
        primary_points.append(point); primary_boots.append(boots)
    for cell in range(8):
        for i, field in enumerate(('ordering_fraction', 'height', 't22', 't31')):
            means = [item['g'][:, cell, i].mean() for item in arrays]
            boot = np.mean([item['w'] @ item['g'][:, cell, i] / len(item['g']) for item in arrays], axis=0)
            reported = metric(summary['global_cells'][cell], field)
            verify(reported['estimate'], np.mean(means), 'global_point:' + name + ':' + field)
            verify(reported['ci95'], ci(boot), 'global_ci:' + name + ':' + field)
    for reported in summary['conditional_cells']:
        cell = CELLS.index((reported['stage'], reported['source_count'], reported['count']))
        d = reported['dimension']
        means = np.asarray([item['ratio'][cell] for item in arrays])
        boot_est = np.asarray([item['boot'][:, cell] for item in arrays])
        refs = np.asarray([refcache[item['batch'], d][0] for item in arrays])
        boot_refs = np.asarray([refcache[item['batch'], d][1] for item in arrays])
        pooled = means.mean(axis=0)
        delta_boot = (boot_est - boot_refs).mean(axis=0)
        for i, field in enumerate(NAMES[:6]):
            row = metric(reported, field, 'pooled')
            verify(row['estimate'], pooled[i], 'conditional_point:' + name + ':' + field)
            verify(row['ci95'], ci(delta_boot[:, i]), 'conditional_ci:' + name + ':' + field)
        tv = np.mean(.5 * np.abs(means[:, 6:] - refs[:, 6:]).sum(axis=1))
        tv_boot = np.mean(.5 * np.abs(boot_est[:, :, 6:] - boot_refs[:, :, 6:]).sum(axis=2), axis=0)
        row = metric(reported, 'tv4', 'pooled')
        verify(row['estimate'], tv, 'tv_point:' + name)
        verify(row['ci95'], ci(tv_boot), 'tv_ci:' + name)
    for reported in summary['conditional_contrasts']:
        left = CELLS.index((reported['left']['stage'], reported['left']['source_count'], reported['left']['count']))
        right = CELLS.index((reported['right']['stage'], reported['right']['source_count'], reported['right']['count']))
        point = np.mean([item['ratio'][right, :6] - item['ratio'][left, :6] for item in arrays], axis=0)
        boot = np.mean([item['boot'][:, right, :6] - item['boot'][:, left, :6] for item in arrays], axis=0)
        for i, row in enumerate(reported['metrics']):
            verify(row['estimate'], point[i], 'conditional_contrast_point:' + name)
            verify(row['ci95'], ci(boot[:, i]), 'conditional_contrast_ci:' + name)
    raw_review[name] = {'history_count': sum(len(item['v']) for item in arrays),
                         'row_count': len(raw), 'zero_n22_histories_512': sum(row['n22'] == 0 for row in raw if row['stage'] == 'prefix' and row['count'] == 512),
                         'range_n22_density_512': [min(row['n22_density'] for row in raw if row['stage'] == 'prefix' and row['count'] == 512),
                                                   max(row['n22_density'] for row in raw if row['stage'] == 'prefix' and row['count'] == 512)]}
width = np.quantile(np.max(np.abs(np.concatenate(primary_boots, axis=1) - np.concatenate(primary_points)), axis=1), .975)
verify(primary['growth']['common_half_width'], width, 'primary_simultaneous_width')

def format_number(x):
    return 'undefined' if x is None else f'{x:.8g}'


def format_ci(row):
    value = format_number(row['estimate'])
    bounds = row.get('ci95')
    return value + (f' [{format_number(bounds[0])}, {format_number(bounds[1])}]' if bounds is not None else ' [undefined CI]')


lines = ['# Independent Experiment 5 statistical review', '',
         'Read-only review of the complete primary archive; no new generation, parameter selection or tracked-file changes. ',
         'Raw count aggregation and registered random streams were independently reconstructed without importing growth_statistics.', '',
         '## Independent numerical audit', '',
         f'Checks: {dict(checked)}. Total {sum(checked.values())}; failures {len(failures)}. Tolerance 2e-12 absolute/relative.',
         f'Primary common half-width reproduced: {width:.16g}. Scientific digest: `{metadata["scientific_sha256"]}`.', '',
         'This audit independently rebuilds whole-history strata, averages four thinnings before pooling, regenerates all shared reference/bootstrap arrays, and checks every reported conditional six-metric and TV point estimate/CI, paired conditional contrast, p22 pointwise CI and the joint primary width. It checks four global diagnostics in every cell. It is not an independent re-count of every raw causal matrix.', '',
         '## Primary result', '',
         'All six fixed-p settings fail the registered necessary finite signature. All 18 p22 levels at N128/256/512 contradict the d2 reference band; the failure does not depend only on drift or thinning criteria. Every sampled p22 primary vector is nonconstant; no zero-event/constant safeguard was needed.', '',
         '| p | p22 N32 | N64 | N128 | N256 | N512 (pointwise 95% CI) | 8 registered statuses |',
         '|---|---:|---:|---:|---:|---|---|']
for summary in summaries[:6]:
    vals = [metric(c, 't22') for c in summary['global_cells'][:5]]
    p = summary['parameter']
    result = next(item for item in primary['growth']['families'] if item['parameter'] == p)
    lines.append('| ' + ' | '.join([str(p)] + [format_number(m['estimate']) for m in vals[:4]]
                                   + [format_ci(vals[4]), ''.join(short[e['status']] for e in result['entries'])]) + ' |')
lines += ['', 'Status order: levels128/256/512, drift128→256, drift256→512, thinning128→64, thinning256→128, thinning512→256. E=within margin, F=contradicts, I=inconclusive, S=insufficient. These are registered finite-signature statuses, not geometric labels.', '',
          '| p | late drift128→256 | drift256→512 | thinning128→64 | thinning256→128 | thinning512→256 | batch N512 p22 range |',
          '|---|---:|---:|---:|---:|---:|---|']
for fam in primary['growth']['families']:
    entries = fam['entries']
    batch = [x + 1 / 24 for x in entries[2]['batch_means']]
    lines.append('| ' + ' | '.join([str(fam['parameter'])] + [format_number(e['estimate']) for e in entries[3:]]
                                   + [f'[{min(batch):.8g}, {max(batch):.8g}]']) + ' |')
lines += ['', 'The single simultaneous half-width .0012646619834489074 applies to all 48 entries, before safeguards. Secondary pointwise intervals are often much narrower. Small drift does not establish the correct limiting value: p=.005 and .3 have five equivalent stability contrasts but all three level checks fail. Curves need not decrease at small N: .005 and .01 are still rising at512; .02 peaks at256; .05 peaks at128 over this grid. The fixed-p theorem is asymptotic and permits these finite crossovers.', '',
          '## Complete N512 global diagnostics', '',
          '| family / parameter | r [95% CI] | H [95% CI] | H/N | t22 | t31 [95% CI] | global reference-equivalent d | local reference-equivalent d |',
          '|---|---|---|---:|---:|---|---|---|']
for summary in summaries:
    g = summary['global_cells'][4]
    c = next(c for c in summary['conditional_cells'] if c['stage'] == 'prefix' and c['count'] == 512)
    local = c['local_dimension']
    localstr = format_number(local['estimate']) + ' ' + str(local['ci95'])
    lines.append('| ' + ' | '.join([f'{summary["family"]} {summary["parameter"]}', format_ci(metric(g, 'ordering_fraction')),
                                   format_ci(metric(g, 'height')), format_number(metric(g, 'height_fraction')['estimate']),
                                   format_number(metric(g, 't22')['estimate']), format_ci(metric(g, 't31')),
                                   format_ci(metric(g, 'global_dimension')), localstr]) + ' |')
lines += ['', 'At p=.3, r≈.9816 while H/N≈.3956. The known chain-sampling limit must not be described as H/N→1. The growth global and local inversions disagree strongly and are diagnostic calibrations, not discovered geometric dimensions.', '',
          '## All N512 conditional reference comparisons', '',
          'The seven columns retain every candidate reference: connected2, motif22_4, connected4, connected8, motif22_8, joint8, tv4. Every growth/control candidate is reported, without selecting a best-fitting d.', '',
          '| family / parameter | candidate d | conn2 | 22_m4 | conn4 | conn8 | 22_m8 | joint8 | TV4 |',
          '|---|---:|---|---|---|---|---|---|---|']
for summary in summaries:
    for cell in summary['conditional_cells']:
        if cell['stage'] == 'prefix' and cell['count'] == 512:
            entries = [metric(cell, name, 'pooled') for name in NAMES]
            lines.append('| ' + ' | '.join([f'{summary["family"]} {summary["parameter"]}', str(cell['dimension'])]
                                          + [format_number(row['estimate']) + ' ' + short[row['status']] for row in entries]) + ' |')
lines += ['', 'Support below is identical across candidate dimensions. Each entry is three batch pairs (positive histories, total mean interval exposure). There are only32 histories per batch; the registered requirement is≥30 positive histories and exposure≥100 in each batch.', '',
          '| family / parameter | m2 support | m4 support | m8 support |', '|---|---|---|---|']
for summary in summaries:
    cell = next(c for c in summary['conditional_cells'] if c['stage'] == 'prefix' and c['count'] == 512)
    support = []
    for size in (2, 4, 8):
        row = next(m for m in cell['pooled'] if m['interval_size'] == size)
        support.append('; '.join(f'({x["positive_histories"]},{x["mean_interval_exposure"]:g})' for x in row['support']['by_batch']))
    lines.append('| ' + ' | '.join([f'{summary["family"]} {summary["parameter"]}'] + support) + ' |')
lines += ['', 'Small-p intervals can appear locally chainlike despite globally sparse orders: p=.005 gives connected2=.995827 and local d≈1.0068 while global d≈6.2861. p=.02 matches the d2 m4 2+2 margin and connected8 margin, but its complete m4 TV≈.7198 and other laws fail. At p=.3, the m8 2+2 and joint8 margins pass against d2 while the remaining five metrics fail. Single matching marginals therefore remain uninformative.', '',
          '## Thinning and history comparisons', '',
          '| family / parameter | Δr 512→256 [95% CI] | ΔH [95% CI] | Δt22 [95% CI] | unique conditional contrasts E/F/I/S over3sources×6metrics |',
          '|---|---|---|---|---|']
for summary in summaries:
    contrast = summary['global_contrasts'][-1]
    d = summary['conditional_cells'][0]['dimension']
    counts = Counter(row['status'] for c in summary['conditional_contrasts'] if c['dimension'] == d for row in c['metrics'])
    lines.append('| ' + ' | '.join([f'{summary["family"]} {summary["parameter"]}',
                                   format_ci(metric(contrast, 'ordering_fraction')), format_ci(metric(contrast, 'height')),
                                   format_ci(metric(contrast, 't22')),
                                   '/'.join(str(counts[s]) for s in ('equivalent', 'contradicts', 'inconclusive', 'insufficient_information'))]) + ' |')
lines += ['', 'Every growth Δr and ΔH 512→256 pointwise interval excludes zero, whereas all iid control counterparts include zero except analytically/observationally constant-height cases. Growth r differences are .005998,.053577,.230184,.194725,.093348,.017971. Conditional contrasts cancel calibration and are duplicated across candidate d only for presentation; they are not independent repeated tests. Motif parent-vs-thinning mean invariance is a counting identity, so the near-equality between late p22 drifts and corresponding thinning-vs-prefix contrasts is expected redundancy, not a second mechanism.', '',
          '## Negative controls, calibration failures and limitations', '',
          '- Both d2 Minkowski and matched22 height-two control pass all eight separately banded finite-signature entries. Their half-widths are .0017992728220161786 and .0005981699427123992. The matched control has mean p22=.04163650388024622, H=2, t31=0 and no nonempty open intervals; all21 N512 candidate-law checks are insufficient. Its passing p22 signature cannot support geometric emergence.',
          '- Every Minkowski own-reference N512 conditional margin passes:21/21. Across all eight cells, d2 has47E/8I/1F, d3 has45E/5I/6S, and d4 has35E/2I/19S.',
          '- Preserve the known-control failure: d2 prefixN32 TV4=.0870770572 gives registered status contradicts, with percentile CI[.1005624991,.1474986454] entirely above the estimate and above .08. All96 histories supply1693 size4 intervals. This is an adverse behavior of the secondary TV procedure/finite sample, not evidence against the exact conditional law; the nonsmooth positive-bootstrap-bias caveat was registered before outcomes.',
          '- Preserve the dimension coverage miss: d2 N512 local d=2.0198519366 with pointwise CI[2.0073961837,2.0327817980], excluding2, although its connected2 error remains practically equivalent under±.02. No claim that every inferred-dimension interval covers the true value is supported.',
          '- The semiorder has exact forbidden-motif zeros and height at most4; at N512 all96 observed heights equal4. Yet its global equivalent dimension≈1.8439 appears close to2. Against d4, four of its seven N512 conditional margins are equivalent even though connected2=0 and TV4=.3938 fail. Small reference motif frequencies plus broad absolute tolerances explain these individual matches. Observed small-interval connectivity zeros are not themselves an all-N semiorder theorem.',
          '- R=32 leaves the positive-history rule close to its ceiling. p=.005 N512 size8 support is only16/17/18 histories and38/68/60 intervals; this is insufficient, not equivalence. Many smaller cells are uninformative. Height-two missing interval laws are a structural degeneracy, not a statistical failure that more samples would cure.',
          '- There are96 independent histories per family, not1632 independent order records. Four thinning replicas and nested prefixes remain clustered; finite conditional ratios pool interval counts, and seed batches are not resampled as random populations. No raw interval count is an independent-sample size.',
          '- Primary simultaneous coverage is approximate bootstrap coverage with registered error allocation; the rare-event safeguard is valid for its zero-event target but does not prove the whole bootstrap procedure has exact finite-sample coverage. Secondary intervals are pointwise across many cells and metrics. Sampled global16-motif frequencies add conditional Monte Carlo noise; exact n22/n31 do not.',
          '- The positive control conclusions are practical finite-sample compatibility, not exact distributional equality. Finite-N conditional ratio estimators can be biased even when the count identity E[B−μA]=0 holds. TV is nonnegative and nonsmooth at equality; its bootstrap CIs can be upward-biased. No post hoc changes to thresholds or estimands were made.',
          '- The fixed-p mathematical obstruction predates these numerical outcomes. Positive drift at sparse p, isolated local marginal matches and reference-equivalent dimensions cannot overturn it. The numerical evidence supports a scoped no-go for Minkowski emergence from this baseline, not a universal no-go for intrinsic dynamics.', '',
          '## Recommendation', '',
          'Stop classifier/parameter optimization of this fixed-p baseline. The useful advance is the separation between coherent growth laws, exchangeable thinning, finite motif agreement, conditional local sampling laws and actual continuum convergence. A further intrinsic-dynamics experiment needs a mathematical reason to change a specified assumption, a fresh proof/test of covariance and consistency, a chosen convergence topology, control of all finite suborder laws or stronger reconstruction data, and a justified mesoscopic scale. No finite signature establishes an embedding, manifold uniqueness, curvature, Lorentz symmetry, continuum field equations or gravitational dynamics.', '',
          f'Machine-readable audit and compact summary are in {output_json.name}. Original arrays and tables remain unchanged in the supplied archive.']
output_md.write_text('\n'.join(lines) + '\n')
payload = {'audit': {'checks': dict(checked), 'total': sum(checked.values()), 'failures': failures,
                     'primary_common_half_width_reproduced': float(width)},
           'raw_family_review': raw_review,
           'conditional_status_counts': {f'{s["family"]}-{s["parameter"]}': {
               'N512': dict(Counter(row['status'] for c in s['conditional_cells'] if c['stage'] == 'prefix' and c['count'] == 512 for row in c['pooled'] if row['metric'] in NAMES)),
               'all_cells': dict(Counter(row['status'] for c in s['conditional_cells'] for row in c['pooled'] if row['metric'] in NAMES))}
               for s in summaries}}
output_json.write_text(json.dumps(payload, indent=2, allow_nan=False) + '\n')
print(json.dumps({'checks': sum(checked.values()), 'failures': len(failures),
                  'status': 'failed' if failures else 'passed',
                  'output_prefix': str(args.output_prefix)}, sort_keys=True))
raise SystemExit(1 if failures else 0)
