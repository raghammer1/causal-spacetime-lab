import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { getDataset } from "../data";
import type { ChartSpec } from "../data/types";
import { formatNumber } from "../lib/data-utils";
import ScientificChart from "./ScientificChart";

const baseSpec: ChartSpec = {
  x: "x", y: "estimate", label: "Recorded estimate", unit: "probability",
};

function markerPosition(marker: HTMLElement): [number, number] {
  const coordinates = marker.getAttribute("transform")?.match(/translate\(([^,]+),([^)]+)\)/);
  expect(coordinates).not.toBeNull();
  return [Number(coordinates![1]), Number(coordinates![2])];
}

describe("recorded one-sided uncertainty bounds", () => {
  it("plots every actual quantum-chain lower bound separately from its success estimate", () => {
    const dataset = getDataset("quantum-chain");
    expect(dataset.chart.low).toBe("lower");
    expect(dataset.chart.high).toBeUndefined();
    expect(dataset.rows).toHaveLength(3);
    expect(dataset.rows.every((row) => row.lower === 0.8431607171566665)).toBe(true);
    const { container } = render(<ScientificChart rows={dataset.rows} spec={dataset.chart} />);

    const markers = screen.getAllByRole("img", { name: /one-sided lower bound 0.8432; no upper bound recorded/ });
    expect(markers).toHaveLength(3);
    expect(container.querySelectorAll('[data-bound-kind="two-sided"]')).toHaveLength(0);
    expect(container.querySelectorAll('[data-bound-kind="upper"]')).toHaveLength(0);
    expect(screen.getByLabelText("One-sided bound legend")).toHaveTextContent(
      "Each horizontal cap marks the recorded bound; its arrow shows the allowed direction, not another endpoint.",
    );
    expect(screen.getByRole("group", { name: /Chain recovery success by n.*one-sided bounds/ })).toBeInTheDocument();

    const reference = screen.getByText(dataset.chart.referenceLabel!).parentElement!.querySelector("line")!;
    const referenceY = Number(reference.getAttribute("y1"));
    for (const marker of markers) {
      const [x, boundY] = markerPosition(marker);
      const point = screen.getAllByRole("button").find((element) => Number(element.getAttribute("cx")) === x)!;
      // SVG y decreases as probability increases: .8 < archived bound < estimate1.
      expect(boundY).toBeGreaterThan(Number(point.getAttribute("cy")));
      expect(boundY).toBeLessThan(referenceY);
      expect(point).toHaveAccessibleName(/one-sided lower bound 0.8432; no upper bound recorded/);
    }
    fireEvent.focus(screen.getAllByRole("button")[0]);
    expect(screen.getByRole("status")).toHaveTextContent("one-sided lower bound 0.8432; no upper bound recorded");
    expect(screen.getByRole("status")).not.toHaveTextContent("interval [");
  });

  it("shows an explicitly upper-only bound with the opposite direction and correct inspection text", () => {
    const { container } = render(
      <ScientificChart rows={[{ x: 1, estimate: 0.2, upper: 0.5 }]} spec={{ ...baseSpec, high: "upper" }} log />,
    );
    const marker = screen.getByRole("img", { name: "one-sided upper bound 0.5; no lower bound recorded" });
    expect(marker.querySelector("path")).toHaveAttribute("d", "M-5,0H5M0,0V10M-4,6L0,10L4,6");
    expect(markerPosition(marker)[1]).toBeLessThan(Number(screen.getByRole("button").getAttribute("cy")));
    expect(screen.getByLabelText("One-sided bound legend")).toHaveTextContent("↓ One-sided upper bound.");
    expect(screen.getByLabelText("One-sided bound legend")).not.toHaveTextContent("One-sided lower bound");
    expect(container.textContent).toContain("logarithmic y scale");
    fireEvent.click(screen.getByRole("button"));
    expect(screen.getByRole("status")).toHaveTextContent("one-sided upper bound 0.5; no lower bound recorded");
  });

  it("retains the archived two-sided interval even when it lies above the point estimate", () => {
    const dataset = getDataset("local-primary");
    const row = dataset.rows.find((value) => value.metric === "tv4" && Number(value.ci_low) > Number(value.difference))!;
    expect(row).toBeDefined();
    const { container } = render(<ScientificChart rows={[row]} spec={dataset.chart} />);
    const bar = container.querySelector('[data-bound-kind="two-sided"]')!;
    const coordinates = bar.getAttribute("d")!.match(/^M[^,]+,([^V]+)V([^M]+)/)!;
    const point = screen.getByRole("button");
    expect(Number(coordinates[1])).toBeLessThan(Number(point.getAttribute("cy")));
    expect(Number(coordinates[2])).toBeLessThan(Number(point.getAttribute("cy")));
    expect(point).toHaveAccessibleName(new RegExp(`interval ${formatNumber(row.ci_low)} to ${formatNumber(row.ci_high)}`));
    expect(screen.queryByLabelText("One-sided bound legend")).not.toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    fireEvent.focus(point);
    expect(screen.getByRole("status")).toHaveTextContent(`interval [${formatNumber(row.ci_low)}, ${formatNumber(row.ci_high)}]`);
  });

  it.each([
    { lower: 0.1, upper: null, missing: "upper", present: "lower endpoint 0.1" },
    { lower: null, upper: 0.8, missing: "lower", present: "upper endpoint 0.8" },
  ])("does not reinterpret an unavailable $missing endpoint as a one-sided interval", ({ lower, upper, missing, present }) => {
    const { container } = render(
      <ScientificChart rows={[{ x: 1, estimate: 0.5, lower, upper }]} spec={{ ...baseSpec, low: "lower", high: "upper" }} />,
    );
    expect(container.querySelectorAll("[data-bound-kind]")).toHaveLength(0);
    expect(screen.queryByLabelText("One-sided bound legend")).not.toBeInTheDocument();
    expect(screen.getByRole("button")).toHaveAccessibleName(new RegExp(`incomplete two-sided interval: ${present}; ${missing} endpoint unavailable`));
    fireEvent.focus(screen.getByRole("button"));
    expect(screen.getByRole("status")).toHaveTextContent("incomplete two-sided interval");
    expect(screen.getByRole("status")).not.toHaveTextContent("one-sided");
  });

  it("preserves a genuine zero bound while leaving a missing bound unavailable", () => {
    const { container } = render(
      <ScientificChart rows={[{ x: 1, estimate: 0.2, lower: 0 }, { x: 2, estimate: 0.3, lower: null }]} spec={{ ...baseSpec, low: "lower" }} log />,
    );
    expect(screen.getAllByRole("img")).toHaveLength(1);
    expect(screen.getByRole("img")).toHaveAccessibleName("one-sided lower bound 0; no upper bound recorded");
    expect(container.textContent).not.toContain("logarithmic y scale");
    expect(screen.getAllByRole("button")[1]).not.toHaveAccessibleName(/bound|interval/);
  });
});
