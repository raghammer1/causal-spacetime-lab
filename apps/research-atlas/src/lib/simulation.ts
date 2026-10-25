/** Small, seeded teaching models. These are not the archived research ensembles. */
export type Order = boolean[][];
export interface EventPoint {
  t: number;
  x: number[];
}
export type Random = () => number;
export function random(seed: number): Random {
  let a = seed >>> 0;
  return () => {
    a += 0x6d2b79f5;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
export const emptyOrder = (n: number): Order =>
  Array.from({ length: n }, () => Array<boolean>(n).fill(false));
export function closure(edges: Order): Order {
  const n = edges.length;
  if (edges.some((row) => row.length !== n))
    throw new Error("Order matrix must be square.");
  const a = edges.map((row) => [...row]);
  for (let k = 0; k < n; k++)
    for (let i = 0; i < n; i++)
      if (a[i][k]) for (let j = 0; j < n; j++) a[i][j] ||= a[k][j];
  if (a.some((row, i) => row[i]))
    throw new Error("Causal orders cannot contain cycles.");
  return a;
}
export function validateOrder(order: Order): boolean {
  const closed = closure(order);
  return closed.every((row, i) => row.every((v, j) => v === order[i][j]));
}
export function longestChain(order: Order): number[] {
  if (!validateOrder(order))
    throw new Error("A transitive strict order is required.");
  const n = order.length;
  if (!n) return [];
  const indices = Array.from({ length: n }, (_, i) => i).sort((a, b) =>
    order.reduce((s, row) => s + Number(row[a]) - Number(row[b]), 0),
  );
  const lengths = Array(n).fill(1),
    parents = Array(n).fill(-1);
  for (const j of indices)
    for (let i = 0; i < n; i++)
      if (order[i][j] && lengths[i] + 1 > lengths[j]) {
        lengths[j] = lengths[i] + 1;
        parents[j] = i;
      }
  const chain: number[] = [];
  let i = lengths.indexOf(Math.max(...lengths));
  while (i !== -1) {
    chain.push(i);
    i = parents[i];
  }
  return chain.reverse();
}
export function relationCount(order: Order): number {
  return order.reduce((sum, row) => sum + row.filter(Boolean).length, 0);
}
export function fraction(order: Order): number | null {
  const n = order.length;
  return n < 2 ? null : relationCount(order) / ((n * (n - 1)) / 2);
}
export function covers(order: Order): Order {
  return order.map((row, i) =>
    row.map(
      (value, j) => value && !order.some((_, k) => order[i][k] && order[k][j]),
    ),
  );
}
export function interval(order: Order, a: number, b: number): number[] {
  return order.flatMap((_, k) => (order[a]?.[k] && order[k]?.[b] ? [k] : []));
}
export function induced(order: Order, indices: number[]): Order {
  return indices.map((i) => indices.map((j) => order[i][j]));
}
export function twoPlusTwo(order: Order): number {
  let total = 0;
  for (let a = 0; a < order.length; a++)
    for (let c = a + 1; c < order.length; c++)
      if (!order[a][c] && !order[c][a]) {
        let left = 0,
          right = 0;
        for (let b = 0; b < order.length; b++) {
          if (order[a][b] && !order[c][b]) left++;
          if (order[c][b] && !order[a][b]) right++;
        }
        total += left * right;
      }
  return total;
}
export function poisson(mean: number, rng: Random): number {
  if (!(mean >= 0 && mean <= 100))
    throw new Error("The teaching sampler supports means between 0 and 100.");
  const limit = Math.exp(-mean);
  let product = 1,
    k = 0;
  do {
    k++;
    product *= rng();
  } while (product > limit);
  return k - 1;
}
export function minkowskiOrder(points: EventPoint[]): Order {
  return points.map((a) =>
    points.map((b) => b.t - a.t > Math.hypot(...a.x.map((v, k) => v - b.x[k]))),
  );
}
export function timeSample(
  density: number,
  seed: number,
): { points: EventPoint[]; order: Order } {
  const rng = random(seed),
    count = poisson(density / 2, rng);
  const points = Array.from({ length: count }, () => {
    const u = rng(),
      v = rng();
    return { t: (u + v) / 2, x: [(u - v) / 2] };
  });
  return { points, order: minkowskiOrder(points) };
}
function normal(rng: Random): number {
  return (
    Math.sqrt(-2 * Math.log(Math.max(rng(), Number.EPSILON))) *
    Math.cos(2 * Math.PI * rng())
  );
}
export function diamondSample(
  dimension: number,
  count: number,
  seed: number,
): { points: EventPoint[]; order: Order } {
  if (
    ![2, 3, 4].includes(dimension) ||
    count < 0 ||
    count > 128 ||
    !Number.isInteger(count)
  )
    throw new Error("Teaching sampler: d=2,3,4 and 0≤N≤128.");
  const rng = random(seed);
  const points = Array.from({ length: count }, () => {
    const q = 0.5 * rng() ** (1 / dimension),
      t = rng() < 0.5 ? q : 1 - q;
    const radius = q * rng() ** (1 / (dimension - 1));
    let vector = Array.from({ length: dimension - 1 }, () => normal(rng));
    const norm = Math.hypot(...vector);
    vector = vector.map((v) => (radius * v) / (norm || 1));
    return { t, x: vector };
  });
  return { points, order: minkowskiOrder(points) };
}
// Lanczos log-gamma; the same mathematical formula and [1,10] inversion domain as Python.
export function logGamma(z: number): number {
  const c = [
    676.5203681218851, -1259.1392167224028, 771.32342877765313,
    -176.61502916214059, 12.507343278686905, -0.13857109526572012,
    9.9843695780195716e-6, 1.5056327351493116e-7,
  ];
  if (z < 0.5)
    return (
      Math.log(Math.PI) - Math.log(Math.sin(Math.PI * z)) - logGamma(1 - z)
    );
  z -= 1;
  let x = 0.99999999999980993;
  for (let i = 0; i < c.length; i++) x += c[i] / (z + i + 1);
  const t = z + c.length - 0.5;
  return (
    0.5 * Math.log(2 * Math.PI) + (z + 0.5) * Math.log(t) - t + Math.log(x)
  );
}
export function orderingProbability(d: number): number {
  return Math.exp(
    logGamma(d + 1) + logGamma(d / 2) - Math.log(2) - logGamma(1.5 * d),
  );
}
export function estimateDimension(r: number | null): number | null {
  if (r === null || !Number.isFinite(r) || r < orderingProbability(10) || r > 1)
    return null;
  let lo = 1,
    hi = 10;
  for (let i = 0; i < 60; i++) {
    const mid = (lo + hi) / 2;
    if (orderingProbability(mid) > r) lo = mid;
    else hi = mid;
  }
  return (lo + hi) / 2;
}
export function growth(
  count: number,
  probability: number,
  seed: number,
): { order: Order; direct: Order } {
  if (
    !Number.isInteger(count) ||
    count < 0 ||
    count > 48 ||
    !Number.isFinite(probability) ||
    probability < 0 ||
    probability > 1
  )
    throw new Error("Growth requires N≤48 and 0≤p≤1.");
  const rng = random(seed),
    direct = emptyOrder(count),
    order = emptyOrder(count);
  for (let j = 0; j < count; j++)
    for (let i = 0; i < j; i++) {
      const selected = rng() < probability;
      if (selected) {
        direct[i][j] = true;
        order[i][j] = true;
        for (let k = 0; k < i; k++) order[k][j] ||= order[k][i];
      }
    }
  return { order, direct };
}
export function layered(count: number, target: number, seed: number): Order {
  const rng = random(seed),
    a = Math.floor(count / 2),
    q = Math.min(1, (target * count * (count - 1)) / (2 * a * (count - a))),
    order = emptyOrder(count);
  for (let i = 0; i < a; i++)
    for (let j = a; j < count; j++) order[i][j] = rng() < q;
  return order;
}
export function intervalOrder(count: number, seed: number): Order {
  const rng = random(seed),
    spans = Array.from({ length: count }, () => {
      const a = rng(),
        b = rng();
      return [Math.min(a, b), Math.max(a, b)];
    });
  return spans.map((a) => spans.map((b) => a[1] < b[0]));
}
/** Exact witnesses derived in LOCAL_CAUSAL_STRUCTURE_THEORY.md. */
export function cycleWitness(
  kind: "global" | "extended",
  disconnected: boolean,
): Order {
  const m = kind === "global" ? 4 : 6,
    extra = kind === "global" ? 2 : 0,
    n = m * 2 + extra,
    shift = extra ? 1 : 0,
    order = emptyOrder(n);
  for (let i = 0; i < m; i++) {
    const group = disconnected ? m / 2 : m,
      start = disconnected ? Math.floor(i / group) * group : 0;
    order[shift + i][shift + m + i] = true;
    order[shift + i][shift + m + start + ((i - start + 1) % group)] = true;
  }
  if (extra) {
    for (let i = 1; i < n - 1; i++) {
      order[0][i] = true;
      order[i][n - 1] = true;
    }
  }
  return closure(order);
}
export function intervalHistogram(order: Order): number[] {
  const bins = Array(order.length).fill(0);
  order.forEach((row, i) =>
    row.forEach((value, j) => {
      if (value) bins[interval(order, i, j).length]++;
    }),
  );
  return bins;
}
export function components(order: Order): number {
  const visited = new Set<number>();
  let count = 0;
  for (let start = 0; start < order.length; start++)
    if (!visited.has(start)) {
      count++;
      const stack = [start];
      visited.add(start);
      while (stack.length) {
        const i = stack.pop()!;
        for (let j = 0; j < order.length; j++)
          if ((order[i][j] || order[j][i]) && !visited.has(j)) {
            visited.add(j);
            stack.push(j);
          }
      }
    }
  return count;
}
