import { describe, expect, it } from "vitest";
import reference from "./python-reference.json";
import {
  closure,
  components,
  cycleWitness,
  diamondSample,
  emptyOrder,
  estimateDimension,
  fraction,
  growth,
  induced,
  interval,
  intervalHistogram,
  layered,
  longestChain,
  minkowskiOrder,
  orderingProbability,
  random,
  relationCount,
  timeSample,
  twoPlusTwo,
  validateOrder,
} from "./simulation";
describe("independent Python parity", () => {
  it("reconstructs the archived implementation’s explicit coordinate fixture", () => {
    const order = minkowskiOrder(reference.points);
    expect(order).toEqual(reference.order);
    expect(longestChain(order).length).toBe(reference.chain_length);
    expect(longestChain(order).length / Math.sqrt(64)).toBeCloseTo(
      reference.inferred_duration,
      14,
    );
    for (const [dimension, probability] of Object.entries(
      reference.probabilities,
    ))
      expect(orderingProbability(+dimension)).toBeCloseTo(probability, 12);
  });
});
describe("strict causal orders", () => {
  it("closes paths, rejects cycles, and validates transitivity", () => {
    const a = emptyOrder(4);
    a[0][1] = a[1][2] = a[2][3] = true;
    expect(validateOrder(a)).toBe(false);
    const closed = closure(a);
    expect(relationCount(closed)).toBe(6);
    expect(longestChain(closed)).toEqual([0, 1, 2, 3]);
    expect(interval(closed, 0, 3)).toEqual([1, 2]);
    a[3][0] = true;
    expect(() => closure(a)).toThrow(/cycles/);
  });
  it("is invariant to event labels and excludes null separations", () => {
    const original = reference.order,
      permutation = [5, 2, 4, 1, 3, 0];
    expect(longestChain(induced(original, permutation)).length).toBe(
      reference.chain_length,
    );
    expect(
      minkowskiOrder([
        { t: 0, x: [0] },
        { t: 0.5, x: [0.5] },
      ])[0][1],
    ).toBe(false);
    expect(longestChain([])).toEqual([]);
    expect(fraction(emptyOrder(1))).toBeNull();
    expect(estimateDimension(0)).toBeNull();
  });
});
describe("seeded samplers", () => {
  it("replays and gives identical growth prefixes", () => {
    expect(timeSample(64, 100)).toEqual(timeSample(64, 100));
    expect(timeSample(64, 100)).not.toEqual(timeSample(64, 101));
    for (const p of [0, 0.005, 0.01, 0.02, 0.05, 0.1, 0.3, 1]) {
      const full = growth(48, p, 909),
        small = growth(12, p, 909);
      expect(
        induced(
          full.order,
          Array.from({ length: 12 }, (_, i) => i),
        ),
      ).toEqual(small.order);
      expect(closure(full.direct)).toEqual(full.order);
      expect(validateOrder(full.order)).toBe(true);
    }
    expect(relationCount(growth(20, 0, 1).order)).toBe(0);
    expect(relationCount(growth(20, 1, 1).order)).toBe(190);
    expect(() => growth(49, 0.1, 1)).toThrow();
  });
  it("uses the correct uniform-volume measure and dimension normalization", () => {
    for (const d of [2, 3, 4]) {
      const points = Array.from(
        { length: 100 },
        (_, seed) => diamondSample(d, 64, seed + 5000).points,
      ).flat();
      expect(
        points.every((p) => Math.hypot(...p.x) <= Math.min(p.t, 1 - p.t)),
      ).toBe(true);
      const tmean = points.reduce((s, p) => s + p.t, 0) / points.length;
      const qCDF =
        points.reduce((s, p) => s + (2 * Math.min(p.t, 1 - p.t)) ** d, 0) /
        points.length;
      const radialCDF =
        points.reduce(
          (s, p) =>
            s + (Math.hypot(...p.x) / Math.min(p.t, 1 - p.t)) ** (d - 1),
          0,
        ) / points.length;
      expect(Math.abs(tmean - 0.5)).toBeLessThan(0.01);
      expect(Math.abs(qCDF - 0.5)).toBeLessThan(0.02);
      expect(Math.abs(radialCDF - 0.5)).toBeLessThan(0.02);
      expect(estimateDimension(orderingProbability(d))).toBeCloseTo(d, 10);
    }
  });
  it("does not mistake a tuned statistic for geometry", () => {
    const order = layered(32, 0.5, 27);
    expect(longestChain(order).length).toBe(2);
    expect(estimateDimension(fraction(order))).not.toBeNull();
  });
  it("has deterministic independent PRNG streams", () => {
    const a = random(42),
      b = random(42);
    expect(Array.from({ length: 20 }, a)).toEqual(
      Array.from({ length: 20 }, b),
    );
  });
});
describe("exact local counterexamples and motif counting", () => {
  it("matches the N=10 report witness with 12 versus 16 induced 2+2s", () => {
    const a = cycleWitness("global", false),
      b = cycleWitness("global", true);
    expect(relationCount(a)).toBe(25);
    expect(relationCount(b)).toBe(25);
    expect(intervalHistogram(a)).toEqual(intervalHistogram(b));
    expect(longestChain(a).length).toBe(4);
    expect(twoPlusTwo(a)).toBe(12);
    expect(twoPlusTwo(b)).toBe(16);
  });
  it("matches the stronger N=12 witness with the same measured local summaries", () => {
    const a = cycleWitness("extended", false),
      b = cycleWitness("extended", true);
    expect(twoPlusTwo(a)).toBe(42);
    expect(twoPlusTwo(b)).toBe(42);
    expect(intervalHistogram(a)).toEqual(intervalHistogram(b));
    expect(components(a)).toBe(1);
    expect(components(b)).toBe(2);
  });
  it("agrees with independent exhaustive four-subset classification", () => {
    for (let seed = 1; seed <= 12; seed++) {
      const order = growth(10, 0.05 + seed / 30, seed).order;
      let count = 0;
      for (let a = 0; a < 10; a++)
        for (let b = a + 1; b < 10; b++)
          for (let c = b + 1; c < 10; c++)
            for (let d = c + 1; d < 10; d++) {
              const sub = induced(order, [a, b, c, d]);
              const degree = sub.map(
                (row, i) =>
                  row.filter(Boolean).length + sub.filter((r) => r[i]).length,
              );
              if (relationCount(sub) === 2 && degree.every((n) => n === 1))
                count++;
            }
      expect(twoPlusTwo(order)).toBe(count);
    }
  });
});
