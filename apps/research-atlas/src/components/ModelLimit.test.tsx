import { describe, expect, it } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import ModelLimit, {
  matchedControl,
  MATCHED_EDGE_PROBABILITY,
  threePlusOne,
} from "./ModelLimit";
import {
  closure,
  emptyOrder,
  intervalHistogram,
  longestChain,
  random,
  twoPlusTwo,
  validateOrder,
} from "../lib/simulation";

describe("matched control and the model-specific limit", () => {
  it("uses independent fair labels, preserves imbalance and replays within a hard cap", () => {
    const first = matchedControl(32, random(20261025));
    expect(matchedControl(32, random(20261025))).toEqual(first);
    expect(validateOrder(first.order)).toBe(true);
    expect(longestChain(first.order).length).toBeLessThanOrEqual(2);
    expect(
      intervalHistogram(first.order)
        .slice(1)
        .every((n) => n === 0),
    ).toBe(true);
    expect(threePlusOne(first.order)).toBe(0);
    expect(first.lower.filter(Boolean)).not.toHaveLength(16);
    // A legitimate all-lower draw must remain an antichain, not be rebalanced.
    expect(matchedControl(4, () => 0.1)).toEqual({
      lower: [true, true, true, true],
      order: emptyOrder(4),
    });
    expect(() => matchedControl(49, random(1))).toThrow(/0≤N≤48/);
    expect(() => matchedControl(3.5, random(1))).toThrow();
  });

  it("exactly enumerates the iid four-event law: expected 2+2 is 1/24 and 3+1 is absent", () => {
    const q = MATCHED_EDGE_PROBABILITY;
    let totalProbability = 0,
      expected22 = 0;
    for (let labels = 0; labels < 16; labels++) {
      const lower = Array.from({ length: 4 }, (_, i) =>
        Boolean(labels & (1 << i)),
      );
      const possible =
        lower.filter(Boolean).length * lower.filter((v) => !v).length;
      for (let edges = 0; edges < 2 ** possible; edges++) {
        const chosen = Array.from({ length: possible }, (_, i) =>
          Boolean(edges & (1 << i)),
        );
        const draws = [
          ...lower.map((v) => (v ? 0.25 : 0.75)),
          ...chosen.map((v) => (v ? q / 2 : (1 + q) / 2)),
        ];
        let cursor = 0;
        const { order } = matchedControl(4, () => draws[cursor++]);
        const k = chosen.filter(Boolean).length;
        const probability = (q ** k * (1 - q) ** (possible - k)) / 16;
        totalProbability += probability;
        expected22 += probability * twoPlusTwo(order);
        expect(cursor).toBe(draws.length);
        expect(threePlusOne(order)).toBe(0);
      }
    }
    expect(totalProbability).toBeCloseTo(1, 13);
    expect(expected22).toBeCloseTo(1 / 24, 13);
    const chainWithIsolate = emptyOrder(4);
    chainWithIsolate[0][1] = true;
    chainWithIsolate[1][2] = true;
    expect(threePlusOne(closure(chainWithIsolate))).toBe(1);
    chainWithIsolate[2][3] = true;
    expect(threePlusOne(closure(chainWithIsolate))).toBe(0);
  });

  it("switches actual models while keeping the exact expectation separate from a single realization", () => {
    render(<ModelLimit />);
    expect(screen.getByText("1/24 ≈ 4.1667%")).toBeInTheDocument();
    expect(
      screen.getByText(/equal groups are not enforced/),
    ).toBeInTheDocument();
    const stat = screen
      .getByText("Longest-chain height H")
      .closest(".lab-stat") as HTMLElement;
    expect(within(stat).getByText("2")).toBeInTheDocument();
    const initialDiagram = screen.getByRole("img", {
      name: /Seeded height-two order/,
    }).outerHTML;
    fireEvent.change(screen.getByLabelText("Model comparison"), {
      target: { value: "minkowski" },
    });
    expect(
      screen.getByRole("img", { name: /Order-only drawing/ }).outerHTML,
    ).not.toBe(initialDiagram);
    expect(screen.getByText("1/24 ≈ 4.1667%")).toBeInTheDocument();
    expect(Number(stat.querySelector("strong")?.textContent)).toBeGreaterThan(
      2,
    );
    expect(
      screen.getByText(/no empirical confidence interval/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/does not rule out spacetime emerging/),
    ).toBeInTheDocument();
    const seed = screen.getByLabelText("Simulation seed");
    fireEvent.click(
      screen.getByRole("button", { name: "Next deterministic sample" }),
    );
    expect(seed).toHaveValue(20261026);
    fireEvent.change(seed, { target: { value: "20261025" } });
    fireEvent.change(screen.getByLabelText("Model comparison"), {
      target: { value: "matched" },
    });
    expect(
      screen.getByRole("img", { name: /Seeded height-two order/ }).outerHTML,
    ).toBe(initialDiagram);
    expect(
      screen.getByRole("link", { name: /original continuum-limit theorem/ }),
    ).toHaveAttribute("href", expect.stringContaining("contlim.pdf"));
  });
});
