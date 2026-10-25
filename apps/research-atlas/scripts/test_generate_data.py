"""Regression checks anchored in independently reported scientific outcomes."""
import csv
import gzip
import json
import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch

import generate_data as g


class ArchiveTransformationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.datasets = g.validate(g.build())
        cls.by_id = {d['id']: d for d in cls.datasets}

    def test_every_archived_time_summary_is_transcribed_without_rounding(self):
        for identifier, folder in [('time-primary', 'finite-density-scaling-v1'), ('time-followup', 'equal-count-followup')]:
            with (g.ROOT / f'docs/experiments/{folder}/summary.csv').open() as stream:
                originals = list(csv.DictReader(stream))
            converted = self.by_id[identifier]['rows']
            self.assertEqual(len(originals), len(converted))
            for old, new in zip(originals, converted):
                for field in ('density', 'duration', 'mean_estimate', 'ci_low', 'ci_high'):
                    self.assertEqual(float(old[field]), new[field])
        self.assertEqual(sum(r['repeats'] for r in self.by_id['time-primary']['rows'] if r['model'] == 'sprinkled'), 4200)
        self.assertEqual(sum(r['repeats'] for r in self.by_id['time-followup']['rows'] if r['model'] == 'sprinkled'), 8000)

    def test_reported_dimension_outcomes_and_missing_antichain_survive(self):
        rows = self.by_id['dimension-summary']['rows']
        genuine = [r for r in rows if r['family'] == 'genuine' and r['count'] == 256]
        self.assertEqual(len(genuine), 3)
        for row in genuine:
            self.assertEqual(row['classification_accuracy_successes'], 200)
            self.assertGreater(row['classification_accuracy_wilson_low'], .98)
        self.assertTrue(all(r['estimated_dimension_mean'] is None for r in rows if r['family'] == 'antichain'))

    def test_adversarial_failure_not_hidden_by_rich_detector(self):
        rows = self.by_id['detector-summary']['rows']
        case = next(r for r in rows if r['target'] == .95 and r['family'] == 'multi_matched' and r['dimension_label'] == 2 and r['count'] == 64 and r['detector'] == 'F')
        self.assertAlmostEqual(case['mean_acceptance'], .6316666666666667)
        self.assertLess(case['hierarchical_ci_low'], case['mean_acceptance'])
        self.assertGreater(case['hierarchical_ci_high'], case['mean_acceptance'])
        advancement = self.by_id['detector-advancement']['rows']
        self.assertEqual(set(r['detector'] for r in advancement if r['status'] == 'failed'), set('ABCDEF'))

    def test_all_42_checks_and_tv_interval_oddity_are_retained(self):
        rows = self.by_id['local-primary']['rows']
        self.assertEqual(len(rows), 42)
        self.assertEqual(set(r['status'] for r in rows), {'equivalent'})
        tv = next(r for r in rows if r['family'] == 'diamond' and r['dimension'] == 2 and r['metric'] == 'tv4')
        # A disclosed adverse bootstrap behavior must not be silently "repaired".
        self.assertGreater(tv['ci_low'], tv['estimate'])
        self.assertEqual([tv['ci_low'], tv['ci_high']], json.loads(tv['ci95']))

    def test_local_global_slab_result_uses_two_different_estimands(self):
        rows = [r for r in self.by_id['local-dimensions']['rows'] if r['family'] == 'slab' and r['dimension'] == 4 and r['count'] == 256]
        self.assertEqual(len(rows), 2)
        local = next(r for r in rows if r['method'] == 'local')
        global_ = next(r for r in rows if r['method'] == 'global')
        self.assertAlmostEqual(local['estimate'], 3.994787909186382)
        self.assertAlmostEqual(global_['estimate'], 4.5813, places=4)
        self.assertLess(local['ci_low'], 4)
        self.assertGreater(local['ci_high'], 4)

    def test_growth_has_six_p_and_preserves_paired_history_units(self):
        rows = self.by_id['growth-global']['rows']
        growth = [r for r in rows if r['family'] == 'percolation' and r['stage'] == 'prefix' and r['metric'] == 't22']
        self.assertEqual(len(growth), 30)
        self.assertEqual(set(r['parameter'] for r in growth), {.005, .01, .02, .05, .1, .3})
        self.assertEqual(set(r['history_count'] for r in growth), {96})
        self.assertEqual(set(r['count'] for r in growth), {32, 64, 128, 256, 512})
        primary = self.by_id['growth-primary']['rows']
        self.assertEqual(len([r for r in primary if r['scope'] == 'growth']), 48)
        for row in primary:
            self.assertEqual([row['band_low'], row['band_high']], json.loads(row['band']))
            self.assertEqual([row['pointwise_low'], row['pointwise_high']], json.loads(row['pointwise_ci95']))
        self.assertTrue(any(r['band_low'] != r['pointwise_low'] for r in primary))

    def test_quantum_selection_preserves_archived_estimates_and_failed_uncertainty(self):
        original=g.read_json('docs/experiments/quantum-information-v1/summary.json')
        lookup={(c['family'],c['n'],c['h'],c['preparation'],c['delta'],c['time']):c for c in original}
        rows=self.by_id['quantum-summary']['rows']
        self.assertEqual(len(rows),2043)
        self.assertEqual(len({r['metric'] for r in rows}),19)
        for row in rows:
            cell=lookup[tuple(row[k] for k in ('family','n','h','preparation','delta','time'))]
            if row['metric'] not in cell['metrics']:
                self.assertIsNone(row['mean'])
                self.assertIsNone(row['ci_low'])
                self.assertIsNone(row['ci_high'])
                self.assertEqual(row['independent_units'],0)
                self.assertEqual(row['undefined'],cell['undefined_metrics'][row['metric']])
                continue
            estimate=cell['metrics'][row['metric']]
            self.assertEqual(row['mean'],estimate['mean'])
            self.assertEqual([row['ci_low'],row['ci_high']],estimate.get('ci95') or [None,None])
            self.assertEqual(row['lower'],estimate.get('lower'))
            self.assertEqual(row['undefined'],estimate['undefined'])
        calibration=self.by_id['quantum-calibration']['rows']
        failed=next(r for r in calibration if r['method']=='normal_percentile_bootstrap')
        self.assertEqual(failed['coverage'],.9125)
        self.assertEqual(failed['trials'],400)
        self.assertLess(failed['coverage'],failed['nominal_coverage'])
        self.assertEqual(len([r for r in calibration if r['method']=='exact_binomial']),15)
        self.assertTrue(any(r['mean'] is None and r['undefined'] for r in rows))

    def test_exact_chain_bounds_are_separate_from_bootstrap_means(self):
        rows=self.by_id['quantum-chain']['rows']
        self.assertEqual(len(rows),3)
        self.assertEqual(sum(r['successes'] for r in rows),72)
        self.assertEqual({r['n'] for r in rows},{6,8,10})
        for row in rows:
            self.assertEqual(row['attempted'],24)
            self.assertEqual(row['success_fraction'],1)
            self.assertAlmostEqual(row['lower'],.8431607171566665)
            self.assertLess(row['lower'],1)
            self.assertTrue(row['gate_eligible'])

    def test_dynamical_decision_retains_components_and_both_exact_interval_families(self):
        rows=self.by_id['dynamical-primary']['rows']
        self.assertEqual(len(rows),12)
        self.assertEqual(sum(r['attempted'] for r in rows),144)
        self.assertEqual(sum(r['successes'] for r in rows),0)
        for row in rows:
            self.assertEqual(row['decision'],'NO-GO')
            self.assertEqual(row['lower'],0)
            self.assertEqual(row['upper'],.40218992470918974)
            self.assertGreater(row['go_upper'],row['upper'])
            self.assertLess(row['upper'],row['target_joint_probability'])
        cell=next(r for r in rows if r['N']==4 and r['cell']==3)
        self.assertEqual((cell['C'],cell['L'],cell['T'],cell['D']),(0,3,0,2))
        self.assertEqual((cell['mu'],cell['Gamma']),(.1,1))

    def test_dynamical_structure_and_actual_response_keep_preparation_identity(self):
        structure=self.by_id['dynamical-structure']['rows']
        response=self.by_id['dynamical-response']['rows']
        self.assertEqual(len(structure),1008)
        self.assertEqual(len(response),336)
        self.assertEqual(len({(r['N'],r['cell'],r['batch'],r['replicate']) for r in structure if r['preparation']=='E'}),144)
        self.assertEqual(len([r for r in structure if r['preparation']!='E']),24*6)
        raw=json.loads(gzip.decompress((g.ROOT/'docs/experiments/dynamical-quantum-locality-v1/raw.json.gz').read_bytes()))
        expected=[(unit,detail) for unit in raw for detail in unit['gate']['response_details']]
        for row,(unit,detail) in zip(response,expected):
            for name,value in detail.items():self.assertEqual(row[name],value)
            for name in ('mu','Gamma'):self.assertEqual(row[name],unit['parameters'][name])
            for name in ('N','cell','preparation','batch','replicate'):self.assertEqual(row[name],unit[name])
        self.assertIn('actual',self.by_id['dynamical-response']['title'].lower())

    def test_conditional_summary_keeps_validity_mass_and_is_not_actual_quantum_response(self):
        rows=self.by_id['dynamical-conditioned']['rows']
        self.assertEqual(len(rows),216)
        case=next(r for r in rows if (r['N'],r['cell'],r['preparation'],r['law'],r['delay'])==(5,0,'Sempty','Born',.25))
        self.assertGreater(case['mean_graph_conditioned_F_given_valid_mean'],.998)
        self.assertLess(case['valid_graph_F_probability_mean'],.004)
        self.assertGreater(case['undefined_graph_F_probability_mean'],.99)
        self.assertAlmostEqual(case['F_of_unobserved_mixture_response_mean'],.5)
        self.assertIsNone(case['mean_graph_conditioned_F_given_valid_sd'])
        originals=g.read_json('docs/experiments/dynamical-locality-conditioned-response.json')['aggregates']
        for row,original in zip(rows,originals):
            for metric,estimate in original['metrics'].items():
                for key,value in estimate.items():self.assertEqual(row[f'{metric}_{key}'],value)
            self.assertEqual(row['pooled_graph_conditioned_F_given_valid'],original['pooled_graph_conditioned_F_given_valid'])
        self.assertIn('Secondary',self.by_id['dynamical-conditioned']['description'])

    def test_default_filters_match_data_and_chart_columns_exist(self):
        for dataset in self.datasets:
            matching = [row for row in dataset['rows'] if all(row.get(key) == value for key, value in dataset['defaultFilters'].items())]
            self.assertTrue(matching, dataset['id'])
            self.assertIn(dataset['chart']['x'], dataset['columns'])
            self.assertIn(dataset['chart']['y'], dataset['columns'])

    def test_hash_mismatch_is_rejected_instead_of_rewriting_provenance(self):
        fake = {'sourceCommit': g.COMMIT, 'sha256': {'docs/FINITE_DENSITY_RESULTS.md': '0' * 64}}
        with patch.object(g, 'SOURCE_LOCK', fake):
            with self.assertRaisesRegex(ValueError, 'Archive differs from pinned verified commit'):
                g.source('docs/FINITE_DENSITY_RESULTS.md')

    def test_packed_transport_preserves_every_scalar_and_interval(self):
        for dataset in self.datasets:
            packed = g.pack(dataset)
            hydrated = [dict(zip(packed['columns'], record)) for record in packed['records']]
            self.assertEqual(hydrated, dataset['rows'], dataset['id'])
            self.assertNotIn('rows', packed)

    def test_metadata_catalog_contains_no_observations_and_has_exact_counts(self):
        files = g.generated_files()
        catalog = json.loads(files[g.OUTPUT / 'catalog.json'])
        self.assertEqual(len(catalog), len(self.datasets))
        for metadata in catalog:
            original = self.by_id[metadata['id']]
            self.assertNotIn('rows', metadata)
            self.assertNotIn('records', metadata)
            self.assertEqual(metadata['rowCount'], len(original['rows']))
            self.assertEqual({key: value for key, value in metadata.items() if key != 'rowCount'},
                             {key: value for key, value in original.items() if key != 'rows'})

    def test_later_research_documents_do_not_change_pinned_snapshot(self):
        expected = g.generated_files()
        with TemporaryDirectory() as folder:
            later_root = Path(folder)
            docs = later_root / 'docs'
            docs.mkdir()
            (docs / 'experiments').symlink_to(g.ROOT / 'docs/experiments', target_is_directory=True)
            (docs / 'RESEARCH_LOG.md').write_text('Later documentary change after the pinned research snapshot.\n')
            (docs / 'EXPERIMENTS.md').write_text('An updated research roadmap.\n')
            (docs / 'EXPERIMENT_SIX_RESULTS.md').write_text('A later experiment.\n')
            with patch.object(g, 'ROOT', later_root):
                self.assertEqual(g.generated_files(), expected)

    def test_altered_selected_data_input_still_fails(self):
        path = 'docs/experiments/finite-density-scaling-v1/summary.csv'
        original = (g.ROOT / path).read_bytes()
        with TemporaryDirectory() as folder:
            altered_root = Path(folder)
            target = altered_root / path
            target.parent.mkdir(parents=True)
            target.write_bytes(original + b'\n')
            with patch.object(g, 'ROOT', altered_root):
                with self.assertRaisesRegex(ValueError, 'Archive differs from pinned verified commit'):
                    g.build()

    def test_committed_outputs_are_deterministic_and_current(self):
        first = g.generated_files()
        self.assertEqual(first, g.generated_files())
        for path, content in first.items():
            self.assertEqual(path.read_text(), content, str(path))


if __name__ == '__main__':
    unittest.main()
