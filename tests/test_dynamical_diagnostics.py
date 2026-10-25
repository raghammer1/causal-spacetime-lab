"""Independent arithmetic fixtures for descriptive archived-array diagnostics."""
import json

import numpy as np
import pytest

from causal_lab.dynamical_diagnostics import (
    analyze, frozen_comparisons, layout_controls, response_hash, sampled_onsets,
)
from causal_lab.dynamical_graphs import GraphCatalog


def response_matrix(values):
    """Explicit cyclic row permutations of three specified off-diagonal values."""
    result = np.zeros((4, 4))
    for i in range(4):
        for shift, value in enumerate(values, start=1):
            result[i, (i+shift) % 4] = value
    return result


@pytest.fixture
def archive_arrays():
    catalog = GraphCatalog(4)
    delays = np.array([0., .05, .1, .25, .5, 1., 2.])
    scales = np.minimum(delays, 1.)[:, None, None]
    full = scales*response_matrix([.9, .9, .2])
    law = np.prod(np.where(catalog.graph_bits, .4, .6), axis=1)
    arrays = dict(ages=np.array([0., .5, 1., 2., 3., 4.]), delays=delays,
                  full_born=np.tile(law, (6, 1)), full_response=full,
                  perturbed_response=full*.95, initial_frozen_response=full*.5,
                  probe_frozen_response=full*.8)
    for name in ('born', 'density', 'product', 'count', 'degree'):
        arrays[f'static_{name}_conditional_response'] = scales*response_matrix([.8, .6, .2])
        arrays[f'static_{name}_mixture_response'] = scales*response_matrix([.2, .2, .2])
    arrays['static_density_conditional_response'] = scales*response_matrix([.3, .3, .3])
    return catalog, arrays


def test_sampled_crossing_censoring_and_excluded_source():
    times = [0., .05, .1, .25]
    response = np.zeros((4, 4, 4))
    response[:, np.arange(4), np.arange(4)] = 1.
    response[:, 0, 1] = [0, .009, .011, .02]
    response[:, 0, 2] = [0, .01, .051, .01]  # Nonmonotonic, first sample still retained.
    response[:, 0, 3] = [0, 0, 0, .05]
    low, high = sampled_onsets(response, times)
    assert low['first_sampled_delay'][0] == [None, .1, .05, .25]
    assert high['first_sampled_delay'][0] == [None, None, .1, .25]
    assert high['right_censored_on_sampled_grid'][0] == [False, True, False, False]
    assert high['last_sampled_delay'] == .25
    assert 'between-time' in high['interpretation']
    assert all(low['excluded_diagonal'][i][i] for i in range(4))


@pytest.mark.parametrize('times', [[.1, 0], [0, 0], [0, np.nan]])
def test_invalid_onset_grid_rejected(times):
    with pytest.raises(ValueError):
        sampled_onsets(np.zeros((2, 4, 4)), times)


@pytest.mark.parametrize('bad', [np.nan, np.inf, -1., 2.])
def test_invalid_response_not_silently_censored(bad):
    response = np.zeros((2, 4, 4)); response[1, 0, 1] = bad
    with pytest.raises(ValueError):
        sampled_onsets(response, [0, 1])


def test_frozen_estimands_and_f_contrasts_have_explicit_signs(archive_arrays):
    _, arrays = archive_arrays
    records = frozen_comparisons(arrays, arrays['delays'])
    born = next(row for row in records if row['law'] == 'born')['curve'][-1]
    # Independently: full=(.9+.9)/2=.9; conditional=(.8+.6)/1.6=.875;
    # mixture has three equal responses, so selecting two captures 2/3.
    assert born['full']['F'] == pytest.approx(.9)
    assert born['conditional']['F'] == pytest.approx(.875)
    assert born['mixture']['F'] == pytest.approx(2/3)
    assert born['full_minus_conditional_F'] == pytest.approx(.025)
    assert born['full_minus_mixture_F'] == pytest.approx(.9-2/3)
    assert born['conditional_minus_mixture_response_mean'] == pytest.approx(1.6/3-.2)
    assert born['mixture_convexity_max_violation'] == 0
    density = next(row for row in records if row['law'] == 'density')['curve'][-1]
    assert density['born_minus_null_conditional_F'] == pytest.approx(.875-2/3)
    assert density['born_minus_null_conditional_mean_response'] == pytest.approx(1.6/3-.3)


def test_zero_response_score_is_missing_not_a_favorable_zero(archive_arrays):
    _, arrays = archive_arrays
    row = frozen_comparisons(arrays, arrays['delays'])[0]['curve'][0]
    assert row['full']['F'] is None
    assert row['full_minus_conditional_F'] is None
    assert row['conditional']['mean_response'] == 0
    json.dumps(row, allow_nan=False)


def test_thresholds_can_create_opposite_graphs_without_changing_response(archive_arrays):
    catalog, arrays = archive_arrays
    original = arrays['full_response'].copy()
    result = layout_controls(arrays, catalog)
    # The same uniform .4 occupations give K4 at .25 and the empty graph at .5/.75.
    assert [x['edges'] for x in result['thresholded_graphs']] == [6, 0, 0]
    assert [x['components'] for x in result['thresholded_graphs']] == [1, 4, 4]
    assert [x['connected'] for x in result['thresholded_graphs']] == [True, False, False]
    assert result['spectral_basis_nonunique']
    assert result['spectral_laplacian_eigenvalues'] == pytest.approx([0, 1.6, 1.6, 1.6])
    assert np.linalg.norm(result['circular_coordinates'], axis=1) == pytest.approx(np.ones(4))
    assert np.array_equal(arrays['full_response'], original)
    hashes = {x['response_sha256'] for x in result['thresholded_graphs']}
    hashes.update([result['circular_response_sha256'], result['spectral_response_sha256'],
                   result['response_sha256_before'], result['response_sha256_after']])
    assert hashes == {response_hash(original)}
    assert 'not physical' in result['interpretation']


def test_integration_is_json_safe_and_preserves_all_input_arrays(archive_arrays):
    catalog, arrays = archive_arrays
    before = {key: value.copy() for key, value in arrays.items()}
    result = analyze(arrays, catalog)
    assert result['status'] == 'descriptive_only'
    assert len(result['onsets']) == 14  # Four quantum branches, five laws times two estimands.
    assert all(len(records) == 2 for records in result['onsets'].values())
    assert len(result['frozen_comparisons']) == 5
    json.dumps(result, allow_nan=False)
    assert all(np.array_equal(arrays[key], value) for key, value in before.items())


def test_missing_required_null_is_not_silently_omitted(archive_arrays):
    catalog, arrays = archive_arrays
    del arrays['static_degree_mixture_response']
    with pytest.raises(KeyError):
        analyze(arrays, catalog)


def test_missing_or_duplicate_age2_is_rejected(archive_arrays):
    catalog, arrays = archive_arrays
    arrays['ages'][3] = 1.5
    with pytest.raises(ValueError):
        layout_controls(arrays, catalog)


def test_response_hash_includes_shape_and_ignores_native_byte_order():
    value = np.arange(16, dtype=float).reshape(4, 4)
    assert response_hash(value) != response_hash(value.reshape(2, 8))
    assert response_hash(value) == response_hash(value.astype('>f8'))
