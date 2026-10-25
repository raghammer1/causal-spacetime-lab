import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { getDataset } from "../data";
import DataPanel from "./DataPanel";
import ScientificChart from "./ScientificChart";
describe("archived-data exploration", () => {
  it("uses exact reference duration and updates filters and table", () => {
    render(<DataPanel dataset={getDataset("time-primary")} />);
    expect(screen.getByText("Known duration T = 1")).toBeInTheDocument();
    fireEvent.focus(
      screen.getAllByRole("button", { name: /sprinkled, density/ })[0],
    );
    expect(screen.getByText("Selected record")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("duration"), {
      target: { value: "0.5" },
    });
    expect(screen.getByText("Known duration T = 0.5")).toBeInTheDocument();
    expect(screen.queryByText("Selected record")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Numerical table" }));
    const table = screen.getByRole("table");
    expect(within(table).getAllByRole("row")).toHaveLength(8);
    expect(within(table).getByText("0.294375")).toBeInTheDocument();
  });
  it("removes the 2+2 reference for other metrics and blocks mixed units", () => {
    render(<DataPanel dataset={getDataset("growth-global")} />);
    expect(screen.getByText("d=2 exact E[t₂₂] = 1/24")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("metric", { exact: true }), {
      target: { value: "height" },
    });
    expect(
      screen.queryByText("d=2 exact E[t₂₂] = 1/24"),
    ).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("metric", { exact: true }), {
      target: { value: "" },
    });
    expect(screen.getByText(/Select one metric to plot/)).toBeInTheDocument();
  });
  it("preserves undefined conditional results as unavailable", () => {
    render(<DataPanel dataset={getDataset("growth-conditional")} />);
    fireEvent.change(screen.getByLabelText("parameter"), {
      target: { value: "0.005" },
    });
    fireEvent.change(screen.getByLabelText("count", { exact: true }), {
      target: { value: "32" },
    });
    expect(screen.getByText(/No defined estimates/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Numerical table" }));
    expect(screen.getAllByText("Not available").length).toBeGreaterThan(0);
  });
  it("shows advancement decisions as a table, not event-count pseudo-results", () => {
    render(<DataPanel dataset={getDataset("detector-advancement")} />);
    expect(screen.getByRole("button", { name: "Chart" })).toBeDisabled();
    expect(screen.getByRole("table")).toBeInTheDocument();
  });
  it("uses archived interval endpoints even when they exclude the point estimate", () => {
    const dataset = getDataset("local-primary");
    const row = dataset.rows.find(
      (r) => r.metric === "tv4" && Number(r.ci_low) > Number(r.difference),
    )!;
    expect(row).toBeDefined();
    render(<ScientificChart rows={[row]} spec={dataset.chart} />);
    const point = screen.getByRole("button");
    fireEvent.focus(point);
    expect(screen.getByRole("status")).toHaveTextContent("Selected record");
    expect(point.getAttribute("aria-label")).toContain("interval");
  });
});
