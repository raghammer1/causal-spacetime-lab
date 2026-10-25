import { describe, expect, it } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { loadDataset } from "../../data/loader";
import { QuantumLab } from "./QuantumLab";
import { DynamicalLab } from "./DynamicalLab";

const statistic = (label: string) => screen.getByText(label).closest(".lab-stat")! as HTMLElement;
const meterValue = (name: string) => Number(screen.getByRole("meter", { name }).getAttribute("value"));

describe("archived quantum evidence interactions", () => {
  it("labels evidence and recovers supplied bonds without inventing a simulation", async () => {
    render(<QuantumLab />);
    expect(screen.getByText("ARCHIVED EVIDENCE · INTERACTIVE READING")).toBeInTheDocument();
    expect(screen.queryByText(/LIVE TEACHING MODEL/)).not.toBeInTheDocument();
    await screen.findByRole("meter", { name: "Recovered supplied bonds" });
    expect(meterValue("Recovered supplied bonds")).toBe(1);
    expect(meterValue("Bond-ranking AUC")).toBe(1);
    expect(screen.getByText(/interaction chain was an input/)).toBeInTheDocument();
    expect(within(statistic("Independent coupling realizations")).getByText("24")).toBeInTheDocument();
  });

  it("loads secondary size/field evidence and labels the changed scope", async () => {
    const dataset = await loadDataset("quantum-summary");
    render(<QuantumLab />);
    await screen.findByRole("meter", { name: "Recovered supplied bonds" });
    fireEvent.change(screen.getByLabelText("Quantum system size"), { target: { value: "10" } });
    fireEvent.change(screen.getByLabelText("Quantum transverse field"), { target: { value: "0.5" } });
    const expected = dataset.rows.find((r) => r.family === "chain" && r.n === 10 && r.h === 0.5 && r.delta === 0 && r.time === 0 && r.preparation === "ground" && r.metric === "edge_recall_top_n_minus_1");
    expect(meterValue("Recovered supplied bonds")).toBe(expected?.mean);
    expect(screen.getByText(/No registered chain-success bound for this secondary field setting/)).toBeInTheDocument();
  });

  it("retains physical-null failures and bootstrap undercoverage", async () => {
    render(<QuantumLab />);
    await screen.findByRole("meter", { name: "Recovered supplied bonds" });
    fireEvent.change(screen.getByLabelText("Quantum interaction model"), { target: { value: "B" } });
    fireEvent.change(screen.getByLabelText("Quantum system size"), { target: { value: "6" } });
    fireEvent.click(screen.getByRole("button", { name: "What do the null controls change?" }));
    expect(screen.getByRole("table", { name: "Recorded paired layout-stress effects" })).toBeInTheDocument();
    expect(screen.getByText(/model B misses the required phase-null advantage at n=6 and n=10/)).toBeInTheDocument();
    expect(screen.getByText(/365 of 400 calibration means/)).toBeInTheDocument();
    expect(screen.getByText(/not validated confidence guarantees/)).toBeInTheDocument();
  });

  it("gives the symmetric model no artificial ensemble interval", async () => {
    render(<QuantumLab />);
    await screen.findByRole("meter", { name: "Recovered supplied bonds" });
    fireEvent.change(screen.getByLabelText("Quantum interaction model"), { target: { value: "A" } });
    expect(within(statistic("Deterministic ground state")).getByText("1")).toBeInTheDocument();
    expect(screen.getByText("One state; no ensemble confidence interval")).toBeInTheDocument();
    expect(screen.getByText(/cannot select distinct labeled neighbors/)).toBeInTheDocument();
    expect(screen.getByRole("note")).toHaveTextContent("Uniform Model A has a degenerate MDS eigenspace. Its truncated three-dimensional stress and shuffle contrasts depend on an arbitrary basis and cannot support structural conclusions.");
    expect(within(statistic("Three-dimensional layout mismatch")).getByText("Basis-dependent truncated MDS result; see notice below")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "What do the null controls change?" }));
    expect(screen.getByText(/Model A's recorded truncated-layout stress and shuffle contrasts are basis-dependent/)).toBeInTheDocument();
  });
});

describe("archived dynamical locality interactions", () => {
  it("exposes exact gate counts and counts whole preparations", async () => {
    render(<DynamicalLab />);
    await screen.findByText("The registered joint screen is rejected.");
    expect(within(statistic("Joint successes")).getByText("0 / 12")).toBeInTheDocument();
    expect(within(statistic("Simultaneous upper probability bound")).getByText("40.22%")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Dynamical system size"), { target: { value: "4" } });
    fireEvent.change(screen.getByLabelText("Dynamical parameter setting"), { target: { value: "3" } });
    const local = screen.getByRole("button", { name: "L Concentrated response 3 / 12 successes" });
    fireEvent.click(local);
    expect(local).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText(/Fractional ties prevent arbitrary label choices/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "D Dynamically improved 2 / 12 successes" })).toBeInTheDocument();
  });

  it("exposes selection mass and distinguishes all response estimands", async () => {
    const recorded = await loadDataset("dynamical-conditioned");
    render(<DynamicalLab />);
    await screen.findByText("The registered joint screen is rejected.");
    fireEvent.change(screen.getByLabelText("Dynamical response preparation"), { target: { value: "Sempty" } });
    const selected = (delay: number) => recorded.rows.find((r) => r.N === 5 && r.cell === 0 && r.preparation === "Sempty" && r.law === "Born" && r.delay === delay)!;
    expect(meterValue("Graph-adapted F, conditional on being defined")).toBe(selected(0.25).mean_graph_conditioned_F_given_valid_mean);
    expect(within(statistic("Born mass with defined graph-adapted F")).getByText("0.39%")).toBeInTheDocument();
    expect(screen.getByRole("meter", { name: "Full-system response concentration F" })).toBeInTheDocument();
    expect(screen.getByRole("meter", { name: "No graph record: F of the mixed-state response" })).toBeInTheDocument();
    expect(screen.getByText(/registered gate counts above still refer to E preparations/)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Dynamical response delay"), { target: { value: "0.5" } });
    expect(meterValue("Graph-adapted F, conditional on being defined")).toBe(selected(0.5).mean_graph_conditioned_F_given_valid_mean);
    expect(within(statistic("Joint successes")).getByText("0 / 12")).toBeInTheDocument();
  });
});
