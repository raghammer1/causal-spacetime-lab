import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import {
  datasets,
  getDataset,
  provenance,
  sourceCommit,
  sourceUrl,
} from "./index";
import { hydrateDataset } from "./hydrate";
import packedTime from "./generated/time-primary.json";

const expectedRows: Record<string, number> = {
  "time-primary": 63,
  "time-followup": 12,
  "dimension-summary": 30,
  "detector-summary": 1350,
  "detector-rates": 4050,
  "detector-advancement": 396,
  "local-global": 525,
  "local-primary": 42,
  "local-conditional": 2691,
  "local-dimensions": 150,
  "growth-global": 2200,
  "growth-primary": 64,
  "growth-conditional": 4968,
};

describe("archived scientific data contract", () => {
  it("exposes every expected dataset with valid filter and chart columns", () => {
    expect(datasets.map((d) => d.id).sort()).toEqual(
      Object.keys(expectedRows).sort(),
    );
    expect(new Set(datasets.map((d) => d.experiment))).toEqual(
      new Set([1, 2, 3, 4, 5]),
    );
    for (const dataset of datasets) {
      expect(dataset.rows).toHaveLength(expectedRows[dataset.id]);
      expect(new Set(dataset.columns).size).toBe(dataset.columns.length);
      for (const key of [
        dataset.chart.x,
        dataset.chart.y,
        dataset.chart.low,
        dataset.chart.high,
        dataset.chart.series,
      ]) {
        if (key) expect(dataset.columns).toContain(key);
      }
      expect(
        dataset.rows.some((row) =>
          Object.entries(dataset.defaultFilters).every(
            ([key, value]) => row[key] === value,
          ),
        ),
      ).toBe(true);
      expect(dataset.uncertainty.length).toBeGreaterThan(30);
      expect(dataset.sampleUnit.length).toBeGreaterThan(30);
      expect(dataset.assumptions.length).toBeGreaterThan(30);
    }
    expect(() => getDataset("invented-data")).toThrow(
      "Unknown archived dataset",
    );
  });
  it("pins documentary references and verifies current bytes of actual data inputs", () => {
    expect(sourceCommit).toBe("9bc5984c656271c247354e0079fd900702642064");
    expect(provenance.schemaVersion).toBe(1);
    const lock = JSON.parse(
      readFileSync(resolve(process.cwd(), "scripts/source-lock.json"), "utf8"),
    ) as { sourceCommit: string; sha256: Record<string, string> };
    expect(lock.sourceCommit).toBe(sourceCommit);
    expect(provenance.sources.map((source) => source.path).sort()).toEqual(
      Object.keys(lock.sha256).sort(),
    );
    const inputPaths = new Set(datasets.map((dataset) => dataset.sourcePath));
    for (const artifact of provenance.sources) {
      expect(artifact.url).toBe(sourceUrl(artifact.path));
      expect(artifact.sha256).toBe(lock.sha256[artifact.path]);
      if (inputPaths.has(artifact.path)) {
        const bytes = readFileSync(
          resolve(process.cwd(), "../..", artifact.path),
        );
        expect(createHash("sha256").update(bytes).digest("hex")).toBe(
          artifact.sha256,
        );
      }
    }
    for (const dataset of datasets) {
      const source = provenance.sources.find(
        (item) => item.path === dataset.sourcePath,
      );
      expect(source).toBeDefined();
      expect(dataset.sha256).toBe(source?.sha256);
      expect(dataset.sourceUrl).toBe(source?.url);
    }
  });
  it("keeps runtime data scalar, finite, explicit and losslessly hydrated", () => {
    const malformed: string[] = [];
    for (const dataset of datasets)
      for (const [index, row] of dataset.rows.entries()) {
        if (Object.keys(row).length !== dataset.columns.length)
          malformed.push(`${dataset.id}[${index}]: columns`);
        for (const [key, value] of Object.entries(row)) {
          if (
            value !== null &&
            !["number", "string", "boolean"].includes(typeof value)
          )
            malformed.push(`${dataset.id}[${index}].${key}: type`);
          if (typeof value === "number" && !Number.isFinite(value))
            malformed.push(`${dataset.id}[${index}].${key}: nonfinite`);
        }
      }
    expect(malformed).toEqual([]);
    expect(hydrateDataset(packedTime).rows).toEqual(
      getDataset("time-primary").rows,
    );
    expect(() => hydrateDataset({ ...packedTime, records: [[1, 2]] })).toThrow(
      /column count differs/,
    );
    expect(() =>
      hydrateDataset({ ...packedTime, columns: ["same", "same"], records: [] }),
    ).toThrow(/Duplicate columns/);
  });
});

describe("scientific interpretation invariants", () => {
  it("keeps the primary and follow-up trials separate from paired controls", () => {
    const primary = getDataset("time-primary").rows.filter(
      (r) => r.model === "sprinkled",
    );
    const followup = getDataset("time-followup").rows.filter(
      (r) => r.model === "sprinkled",
    );
    expect(primary.reduce((n, r) => n + Number(r.repeats), 0)).toBe(4200);
    expect(followup.reduce((n, r) => n + Number(r.repeats), 0)).toBe(8000);
    expect(primary.every((r) => Number(r.normalized_bias) < 0)).toBe(true);
    expect(getDataset("time-followup").description).toMatch(/not pooled/);
  });
  it("retains undefined dimensions and uncertainty for perfect classifications", () => {
    const rows = getDataset("dimension-summary").rows;
    const antichains = rows.filter((r) => r.family === "antichain");
    expect(antichains).toHaveLength(3);
    expect(
      antichains.every(
        (r) =>
          r.estimated_dimension_mean === null &&
          r.estimated_dimension_ci_low === null &&
          r.invalid_estimates === 1,
      ),
    ).toBe(true);
    for (const row of rows.filter(
      (r) => r.family === "genuine" && r.count === 256,
    )) {
      expect(row.classification_accuracy_successes).toBe(200);
      expect(row.classification_accuracy_wilson_low).toBeGreaterThan(0.98);
      expect(row.classification_accuracy_wilson_low).toBeLessThan(1);
    }
  });
  it("retains every detector failure and omits binomial confidence for exact controls", () => {
    const decisions = getDataset("detector-advancement").rows;
    expect(
      new Set(
        decisions.filter((r) => r.status === "failed").map((r) => r.detector),
      ),
    ).toEqual(new Set(["A", "B", "C", "D", "E", "F"]));
    const exact = getDataset("detector-rates").rows.filter((r) => r.n === 1);
    expect(exact.length).toBeGreaterThan(0);
    expect(
      exact.every((r) => r.wilson_low === null && r.wilson_high === null),
    ).toBe(true);
    const case_ = getDataset("detector-summary").rows.find(
      (r) =>
        r.target === 0.95 &&
        r.family === "multi_matched" &&
        r.dimension_label === 2 &&
        r.count === 64 &&
        r.detector === "F",
    );
    expect(case_?.mean_acceptance).toBeCloseTo(0.6316666666666667, 14);
  });
  it("preserves 42 practical checks and adverse TV bootstrap behavior", () => {
    const checks = getDataset("local-primary").rows;
    expect(checks).toHaveLength(42);
    expect(checks.every((r) => r.status === "equivalent")).toBe(true);
    const tv = checks.find(
      (r) => r.family === "diamond" && r.dimension === 2 && r.metric === "tv4",
    );
    expect(tv).toBeDefined();
    expect(Number(tv?.ci_low)).toBeGreaterThan(Number(tv?.estimate));
    expect([tv?.ci_low, tv?.ci_high]).toEqual(JSON.parse(String(tv?.ci95)));
    const slab = getDataset("local-dimensions").rows.filter(
      (r) => r.family === "slab" && r.dimension === 4 && r.count === 256,
    );
    expect(slab.find((r) => r.method === "local")?.estimate).toBeCloseTo(
      3.994787909186382,
      12,
    );
    expect(slab.find((r) => r.method === "global")?.estimate).toBeCloseTo(
      4.5813,
      4,
    );
  });
  it("keeps six growth families and simultaneous bands distinct from pointwise intervals", () => {
    const rows = getDataset("growth-global").rows.filter(
      (r) =>
        r.family === "percolation" &&
        r.stage === "prefix" &&
        r.metric === "t22",
    );
    expect(rows).toHaveLength(30);
    expect(new Set(rows.map((r) => r.parameter))).toEqual(
      new Set([0.005, 0.01, 0.02, 0.05, 0.1, 0.3]),
    );
    expect(new Set(rows.map((r) => r.history_count))).toEqual(new Set([96]));
    const signatures = getDataset("growth-primary").rows;
    const primary = signatures.filter((r) => r.scope === "growth");
    expect(primary).toHaveLength(48);
    expect(
      primary.every((r) => r.family_status === "finite_signature_failure"),
    ).toBe(true);
    expect(primary.some((r) => r.band_low !== r.pointwise_low)).toBe(true);
    for (const row of signatures) {
      expect([row.band_low, row.band_high]).toEqual(
        JSON.parse(String(row.band)),
      );
      expect([row.pointwise_low, row.pointwise_high]).toEqual(
        JSON.parse(String(row.pointwise_ci95)),
      );
    }
    expect(
      signatures
        .filter((r) => r.family === "matched_bipartite")
        .every((r) => r.family_status === "finite_window_compatible"),
    ).toBe(true);
  });
  it("preserves insufficient local support as missing rather than successful zeros", () => {
    const rows = getDataset("growth-conditional").rows.filter(
      (r) => r.family === "matched_bipartite",
    );
    expect(rows.length).toBeGreaterThan(0);
    expect(rows.every((r) => r.status === "insufficient_information")).toBe(
      true,
    );
    expect(
      rows.every(
        (r) =>
          r.estimate === null &&
          r.difference === null &&
          r.ci_low === null &&
          r.ci_high === null,
      ),
    ).toBe(true);
  });
});
