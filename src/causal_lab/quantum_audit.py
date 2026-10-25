"""Independent raw-state audit; deliberately imports no experiment helpers.

Reductions use integer basis-index tables, cut entropies use singular values,
and Hamiltonian action uses direct bit flips. This validates archived finite
calculations, not their interpretation as geometry or calibrated uncertainty.
"""
from __future__ import annotations

import argparse
from collections import Counter
from functools import lru_cache
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path

import numpy as np


TOLERANCE = 1e-9


def _complex(value):
    if isinstance(value, dict):
        return np.asarray(value["real"], dtype=float) + 1j*np.asarray(value["imag"], dtype=float)
    return np.asarray(value, dtype=complex)


@lru_cache(maxsize=2048)
def basis_groups(n, keep):
    """Enumerate computational labels without tensor reshaping/transposition."""
    keep = tuple(keep)
    if len(set(keep)) != len(keep) or any(i < 0 or i >= n for i in keep):
        raise ValueError("invalid retained subsystem")
    rest = tuple(i for i in range(n) if i not in keep)
    basis = np.arange(2**n, dtype=np.int64)
    retained = np.zeros_like(basis)
    environment = np.zeros_like(basis)
    for site in keep:
        retained = 2*retained + ((basis >> (n-1-site)) & 1)
    for site in rest:
        environment = 2*environment + ((basis >> (n-1-site)) & 1)
    groups = np.empty((2**len(keep), 2**len(rest)), dtype=np.int64)
    groups[retained, environment] = basis
    groups.flags.writeable = False
    return groups


def explicit_reduction(state, n, keep):
    """Sum each matrix entry over matching environment labels explicitly."""
    groups = basis_groups(n, tuple(keep))
    matrix = np.empty((len(groups), len(groups)), dtype=complex)
    for a in range(len(groups)):
        for b in range(len(groups)):
            matrix[a, b] = np.vdot(state[groups[b]], state[groups[a]])
    return matrix


def schmidt_entropy(state, n, keep):
    probabilities = np.linalg.svd(state[basis_groups(n, tuple(keep))],
                                  compute_uv=False)**2
    positive = probabilities[probabilities > 0]
    return float(-np.sum(positive*np.log2(positive)))


def explicit_negativity(pair_density):
    partial_transpose = np.empty((4, 4), dtype=complex)
    for a in range(2):
        for b in range(2):
            for c in range(2):
                for d in range(2):
                    partial_transpose[2*a+b, 2*c+d] = pair_density[2*a+d, 2*c+b]
    eigenvalues = np.linalg.eigvalsh(partial_transpose)
    return float(-eigenvalues[eigenvalues < 0].sum())


def bit_hamiltonian_action(state, couplings, h):
    """Apply -h sum X - sum J ZZ without building or importing a Hamiltonian."""
    n = len(couplings)
    basis = np.arange(2**n, dtype=np.int64)
    signs = [1-2*((basis >> (n-1-i)) & 1) for i in range(n)]
    diagonal = np.zeros(2**n)
    for i, j in combinations(range(n), 2):
        diagonal -= couplings[i, j]*signs[i]*signs[j]
    result = diagonal*state
    for i in range(n):
        result = result-h*state[basis ^ (1 << (n-1-i))]
    return result


class _Checks:
    def __init__(self, tolerance):
        self.tolerance = tolerance
        self.counts = Counter()
        self.max_errors = {}
        self.failures = []

    def fail(self, sample, check, reason):
        self.failures.append({"sample_id": sample, "check": check, "reason": str(reason)})

    def compare(self, sample, check, actual, expected, tolerance=None):
        self.counts["numerical_comparisons"] += 1
        try:
            first = np.asarray(actual, dtype=np.complex128)
            second = np.asarray(expected, dtype=np.complex128)
        except (ValueError, TypeError):
            self.fail(sample, check, "nonnumeric comparison value")
            return
        if first.shape != second.shape:
            self.fail(sample, check, f"shape mismatch: {first.shape} versus {second.shape}")
            return
        if not np.all(np.isfinite(first)) or not np.all(np.isfinite(second)):
            self.fail(sample, check, "nonfinite numerical value")
            self.counts["nonfinite_failures"] += 1
            return
        error = float(np.max(np.abs(first-second))) if first.size else 0.0
        self.max_errors[check] = max(self.max_errors.get(check, 0.0), error)
        limit = self.tolerance if tolerance is None else tolerance
        if error > limit:
            self.fail(sample, check, f"error {error:.17g} exceeds tolerance {limit:.17g}")


def _audit_state(row, checks):
    sample, n = row["sample_id"], row["n"]
    state = _complex(row["state"])
    if state.shape != (2**n,) or not np.all(np.isfinite(state)):
        raise ValueError("malformed or nonfinite state vector")
    checks.compare(sample, "state_norm", np.vdot(state, state), 1)
    observed = row["observables"]
    singles = np.array([schmidt_entropy(state, n, (i,)) for i in range(n)])
    pair_entropy = np.diag(singles)
    mi = np.zeros((n, n))
    negative = np.zeros((n, n))
    connected = np.zeros((n, n))
    basis = np.arange(2**n, dtype=np.int64)
    probabilities = np.abs(state)**2
    signs = [1-2*((basis >> (n-1-i)) & 1) for i in range(n)]
    z = [float(probabilities @ signs[i]) for i in range(n)]
    for i, j in combinations(range(n), 2):
        rho = explicit_reduction(state, n, (i, j))
        checks.compare(sample, "pair_trace", np.trace(rho), 1)
        eigenvalues = np.linalg.eigvalsh(rho)
        checks.compare(sample, "pair_negative_eigenvalue", min(0., float(eigenvalues.min())), 0)
        pair_s = schmidt_entropy(state, n, (i, j))
        pair_entropy[i, j] = pair_entropy[j, i] = pair_s
        mi[i, j] = mi[j, i] = singles[i]+singles[j]-pair_s
        negative[i, j] = negative[j, i] = explicit_negativity(rho)
        connected[i, j] = connected[j, i] = float(probabilities @ (signs[i]*signs[j]))-z[i]*z[j]
        checks.counts["pair_reductions"] += 1
    for name, expected in (("single_entropy", singles), ("pair_entropy", pair_entropy),
                           ("mi", mi), ("negativity", negative),
                           ("log_negativity", np.log2(1+2*negative)),
                           ("connected_zz", connected)):
        checks.compare(sample, name, observed[name], expected)
    checks.counts["single_entropies"] += n
    cuts_by_kind = {"singleton": [], "balanced": []}
    for cut in row["cuts"]:
        region = tuple(cut["region"])
        rest = [i for i in range(n) if i not in region]
        entropy = schmidt_entropy(state, n, region)
        prediction = float(sum(mi[i, j] for i in region for j in rest)/2)
        defect = entropy-prediction
        numerical_zero = max(entropy, prediction) <= 1e-10
        normalized = 0. if numerical_zero else defect/max(entropy, prediction, 1e-12)
        for name, value in (("entropy", entropy), ("pair_prediction", prediction),
                            ("defect", defect), ("normalized_defect", normalized)):
            checks.compare(sample, "cut_"+name, cut[name], value)
        if cut.get("numerically_zero_cut") != numerical_zero:
            checks.fail(sample, "cut_numerical_zero", "numerical-zero flag differs")
        cuts_by_kind[cut["kind"]].append(region)
        checks.counts["cut_svd_entropies"] += 1
    if set(cuts_by_kind["singleton"]) != {(i,) for i in range(n)}:
        checks.fail(sample, "singleton_schedule", "missing or invalid singleton cuts")
    balanced = cuts_by_kind["balanced"]
    if len(balanced) != 4 or len({frozenset(c) for c in balanced}) != 4:
        checks.fail(sample, "balanced_schedule", "expected four distinct balanced cuts")
    if any(len(c) != n//2 or 0 not in c for c in balanced):
        checks.fail(sample, "balanced_schedule", "invalid unordered balanced-cut representative")
    if row["preparation"] == "ground":
        coupling = np.asarray(row["couplings"], dtype=float)
        checks.compare(sample, "coupling_symmetry", coupling, coupling.T)
        checks.compare(sample, "coupling_diagonal", np.diag(coupling), np.zeros(n))
        applied = bit_hamiltonian_action(state, coupling, row["h"])
        energy = float(np.vdot(state, applied).real)
        checks.compare(sample, "ground_energy", energy, row["solver"]["energy"])
        scale = max(1., n*row["h"]+sum(abs(coupling[i, j]) for i, j in combinations(range(n), 2)))
        residual = float(np.linalg.norm(applied-row["solver"]["energy"]*state))/scale
        checks.compare(sample, "ground_scaled_residual", residual, 0, tolerance=1e-9)
        checks.counts["ground_hamiltonian_actions"] += 1
    checks.counts["states_audited"] += 1
    return {"state": state, "connected": connected, "n": n,
            "family": row["family"], "preparation": row["preparation"],
            "delta": row["delta"], "source_state_id": row.get("source_state_id"),
            "baseline_id": row.get("baseline_id"), "cuts": balanced,
            "couplings": np.asarray(row["couplings"]) if "couplings" in row else None,
            "noise": np.asarray(row["perturbation_noise"]) if "perturbation_noise" in row else None}


def _audit_pairing(states, checks):
    for sample, row in states.items():
        if row["preparation"] == "phase_scrambled":
            source = states.get(row["source_state_id"])
            if source is None:
                checks.fail(sample, "phase_source", "missing source state")
                continue
            checks.compare(sample, "phase_probabilities", abs(row["state"])**2, abs(source["state"])**2)
            checks.compare(sample, "phase_connected_zz", row["connected"], source["connected"])
            checks.compare(sample, "phase_couplings", row["couplings"], source["couplings"])
            if row["cuts"] != source["cuts"]:
                checks.fail(sample, "phase_cut_pairing", "phase and source cuts differ")
            checks.counts["phase_sources"] += 1
            if row["delta"]:
                phase_base = states.get(row["baseline_id"])
                ground_base = states.get(source["baseline_id"])
                if phase_base is None or ground_base is None:
                    checks.fail(sample, "shared_phase", "missing paired baseline")
                    continue
                # Cross multiplication avoids division by tiny ground amplitudes.
                checks.compare(sample, "shared_phase_vector", row["state"]*ground_base["state"],
                               source["state"]*phase_base["state"])
                if phase_base["source_state_id"] != source["baseline_id"]:
                    checks.fail(sample, "shared_phase_source", "crossed source identifiers")
                checks.counts["shared_phase_pairs"] += 1
        if row["preparation"] == "ground" and row["delta"]:
            base = states.get(row["baseline_id"])
            if base is None or row["noise"] is None:
                checks.fail(sample, "perturbation", "missing baseline or noise")
                continue
            checks.compare(sample, "coupling_perturbation", row["couplings"],
                           base["couplings"]+row["delta"]*row["noise"])
            if row["cuts"] != base["cuts"]:
                checks.fail(sample, "perturbation_cuts", "baseline and perturbation cuts differ")
            checks.counts["coupling_perturbations"] += 1


def expected_schedule(repeats, batches=3):
    """Independent expansion of the registered full primary factorial schedule."""
    result = set()
    for n in (6, 8, 10):
        for h in (.5, 1., 2.):
            result.add(("A", n, 0, -1, h, "ground", 0., 0.))
        for family in ("product", "GHZ", "Bell"):
            result.add((family, n, 0, -1, 0., "control", 0., 0.))
        for batch in range(batches):
            for rep in range(repeats):
                for family in ("A", "B", "chain"):
                    if family != "A":
                        for h in (.5, 1., 2.):
                            result.add((family, n, batch, rep, h, "ground", 0., 0.))
                    for delta in (0., .01, .05):
                        result.add((family, n, batch, rep, 1., "phase_scrambled", delta, 0.))
                        if delta:
                            result.add((family, n, batch, rep, 1., "ground", delta, 0.))
                    if rep == 0:
                        for time in (.5, 1., 2.):
                            result.add((family, n, batch, rep, 1., "quench_random_product", 0., time))
                            if family != "A" or batch == 0:
                                result.add((family, n, batch, rep, 1., "quench_plus", 0., time))
                for family in ("haar", "random_product"):
                    result.add((family, n, batch, rep, 0., "control", 0., 0.))
    return result


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024*1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit_archive(directory, *, tolerance=TOLERANCE, verify_schedule=True):
    """Audit every saved successful state, preserving all discrepancies in JSON."""
    directory = Path(directory)
    if not np.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("tolerance must be finite and positive")
    metadata = json.loads((directory/"metadata.json").read_text())
    manifest = json.loads((directory/"manifest.json").read_text())
    checks = _Checks(tolerance)
    for name, expected in manifest["sha256"].items():
        if Path(name).name != name:
            raise ValueError("manifest must use local artifact names")
        if _sha256(directory/name) != expected:
            checks.fail(name, "artifact_hash", "SHA-256 differs from manifest")
        checks.counts["artifact_hashes"] += 1
    states, schedule, statuses, identifiers = {}, set(), Counter(), set()
    independent_cells = {}
    keys = ("family", "n", "batch", "rep", "h", "preparation", "delta", "time")
    with gzip.open(directory/"raw.jsonl.gz", "rt") as handle:
        for line in handle:
            row = json.loads(line)
            sample = row.get("sample_id", "missing")
            checks.counts["raw_records"] += 1
            statuses[row["status"]] += 1
            key = tuple(row[k] for k in keys)
            if key in schedule or sample in identifiers:
                checks.fail(sample, "schedule_uniqueness", "duplicate state key or sample identifier")
            schedule.add(key)
            identifiers.add(sample)
            cell = tuple(row[k] for k in ("family", "n", "h", "preparation", "delta", "time"))
            units = independent_cells.setdefault(cell, set())
            if row["unit_id"] in units:
                checks.fail(sample, "independent_unit", "duplicate physical unit within a summary cell")
            units.add(row["unit_id"])
            if row["status"] == "ok":
                try:
                    states[sample] = _audit_state(row, checks)
                except (ValueError, KeyError, TypeError, IndexError, np.linalg.LinAlgError) as error:
                    checks.fail(sample, "state_audit_exception", error)
            elif row["status"] not in ("failed", "blocked_or_unattempted"):
                checks.fail(sample, "status", "unknown state status")
    if verify_schedule:
        expected = expected_schedule(metadata["repeats"])
        if schedule != expected:
            checks.fail("archive", "registered_schedule",
                        f"missing={len(expected-schedule)}, unexpected={len(schedule-expected)}")
        checks.counts["expected_records"] = len(expected)
    _audit_pairing(states, checks)
    return {"passed": not checks.failures, "all_scheduled_states_ok": statuses["ok"] == len(identifiers),
            "generating_commit": metadata["source_commit"], "tolerance": tolerance,
            "audit_source_sha256": _sha256(Path(__file__)), "audit_numpy_version": np.__version__,
            "raw_sha256": _sha256(directory/"raw.jsonl.gz"),
            "counts": dict(sorted(checks.counts.items())), "statuses": dict(statuses),
            "max_absolute_errors": dict(sorted(checks.max_errors.items())),
            "failures": checks.failures,
            "scope": "Independent raw-state arithmetic and schedule audit; no geometric or confidence-coverage claim."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    result = audit_archive(args.directory)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+"\n")
    print(f"Independent quantum audit: passed={result['passed']}; "
          f"states={result['counts'].get('states_audited', 0)}; failures={len(result['failures'])}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
