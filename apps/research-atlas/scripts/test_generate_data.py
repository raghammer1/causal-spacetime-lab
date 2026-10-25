"""Regression checks anchored in independently reported scientific outcomes."""
import csv
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

    def test_later_research_documents_do_not_change_first_five_snapshot(self):
        expected = g.generated_files()
        with TemporaryDirectory() as folder:
            later_root = Path(folder)
            docs = later_root / 'docs'
            docs.mkdir()
            (docs / 'experiments').symlink_to(g.ROOT / 'docs/experiments', target_is_directory=True)
            (docs / 'RESEARCH_LOG.md').write_text('New research after the first-five atlas.\n')
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
