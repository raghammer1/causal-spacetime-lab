import { describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import {
  AdversarialLab,
  ConceptLab,
  DimensionLab,
  GrowthLab,
  LocalLab,
  TimeLab,
} from "./index";
function statistic(label: string) {
  return screen.getByText(label).closest(".lab-stat")! as HTMLElement;
}
describe("working teaching controls", () => {
  it("changes density and switches to the order-only drawing", () => {
    render(<TimeLab />);
    fireEvent.change(screen.getByLabelText("Sampling density"), {
      target: { value: "128" },
    });
    expect(screen.getByText("Poisson mean λ = ρ/2 = 64")).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText("Show generating coordinates"));
    expect(screen.getByText(/ABSTRACT ORDER LAYOUT/)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Time model"), {
      target: { value: "antichain" },
    });
    expect(
      within(statistic("Longest chain L")).getByText("1"),
    ).toBeInTheDocument();
    expect(screen.getByText("Not physical")).toBeInTheDocument();
  });
  it("requires a guess, reveals evidence, and resets a new mystery", () => {
    render(<DimensionLab />);
    expect(
      screen.getByRole("button", { name: "Reveal the model" }),
    ).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "3 dimensions" }));
    fireEvent.click(screen.getByRole("button", { name: "Reveal the model" }));
    expect(screen.getByRole("status")).toHaveTextContent("Minkowski sampling");
    fireEvent.click(screen.getByRole("button", { name: "New mystery sample" }));
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
    fireEvent.click(
      screen.getByLabelText("Use a fraction-matched artificial order"),
    );
    fireEvent.click(screen.getByRole("button", { name: "2 dimensions" }));
    fireEvent.click(screen.getByRole("button", { name: "Reveal the model" }));
    expect(screen.getByRole("status")).toHaveTextContent("two-layer impostor");
  });
  it("steps, plays, pauses, inspects, and replays growth deterministically", () => {
    vi.useFakeTimers();
    render(<GrowthLab />);
    expect(screen.getByText("1 / 48")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "+ One event" }));
    expect(screen.getByText("2 / 48")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Auto-play growth" }));
    act(() => vi.advanceTimersByTime(2100));
    expect(screen.getByText("5 / 48")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Pause growth" }));
    act(() => vi.advanceTimersByTime(2100));
    expect(screen.getByText("5 / 48")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Inspect growth event"), {
      target: { value: "4" },
    });
    expect(screen.getByText(/Event 5 selected/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Reset history" }));
    expect(screen.getByText("1 / 48")).toBeInTheDocument();
    vi.useRealTimers();
  });
  it("exposes both exact identification counterexamples", () => {
    render(<LocalLab />);
    expect(
      within(statistic("Induced 2+2 count")).getByText("12"),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText("Show the disconnected interior"));
    expect(
      within(statistic("Induced 2+2 count")).getByText("16"),
    ).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Exact counterexample"), {
      target: { value: "extended" },
    });
    expect(
      within(statistic("Induced 2+2 count")).getByText("42"),
    ).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Sampling region"), {
      target: { value: "box" },
    });
    expect(screen.getByText(/A spatial box can clip/)).toBeInTheDocument();
  });
  it("changes adversaries and explains all detector choices", () => {
    render(<AdversarialLab />);
    fireEvent.change(screen.getByLabelText("Adversarial family"), {
      target: { value: "rank" },
    });
    expect(
      screen.getByText(/positive equivalence control/),
    ).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: "E Five-feature maximum" }),
    );
    expect(
      screen.getByText(/largest standardized residual/),
    ).toBeInTheDocument();
  });
  it("has meaningful concept interactions and horizon-safe explanations", () => {
    render(<ConceptLab />);
    fireEvent.change(screen.getByLabelText("Space separation"), {
      target: { value: "1" },
    });
    expect(screen.getByText("Spacelike")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Educational concept"), {
      target: { value: "patterns" },
    });
    fireEvent.click(screen.getByLabelText("Add a cross relation"));
    expect(screen.getByText("Neither target motif")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Educational concept"), {
      target: { value: "singularities" },
    });
    fireEvent.change(
      screen.getByLabelText("Radius relative to event horizon"),
      { target: { value: "1" } },
    );
    expect(screen.getByText("At horizon")).toBeInTheDocument();
    expect(
      screen.getByText(/horizon is not a curvature singularity/),
    ).toBeInTheDocument();
  });
});

describe("replay, keyboard access, motion preferences, and teaching state", () => {
  it("replays growth and resets when p or seed changes", () => {
    render(<GrowthLab />);
    const step = () => {
      for (let i = 0; i < 15; i++)
        fireEvent.click(screen.getByRole("button", { name: "+ One event" }));
    };
    step();
    const first = statistic("Causal relations").textContent;
    fireEvent.click(screen.getByRole("button", { name: "Reset history" }));
    step();
    expect(statistic("Causal relations").textContent).toBe(first);
    fireEvent.change(screen.getByLabelText("Growth probability"), {
      target: { value: ".3" },
    });
    expect(screen.getByText("1 / 48")).toBeInTheDocument();
    step();
    fireEvent.change(screen.getByLabelText("Simulation seed"), {
      target: { value: "101" },
    });
    expect(screen.getByText("1 / 48")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "+ One event" }));
    fireEvent.keyDown(screen.getByRole("button", { name: "Inspect event 2" }), {
      key: "Enter",
    });
    expect(screen.getByLabelText("Inspect growth event")).toHaveValue("1");
    fireEvent.keyDown(screen.getByRole("button", { name: "Inspect event 1" }), {
      key: " ",
    });
    expect(screen.getByLabelText("Inspect growth event")).toHaveValue("0");
    fireEvent.click(screen.getByLabelText("Show inherited relations"));
    expect(screen.getByLabelText("Show inherited relations")).not.toBeChecked();
  });
  it("stops autoplay when reduced-motion preference becomes active", () => {
    vi.useFakeTimers();
    let change = () => {};
    const query = {
      matches: false,
      addEventListener: (_: string, fn: () => void) => {
        change = fn;
      },
      removeEventListener: vi.fn(),
    };
    const mock = vi
      .spyOn(window, "matchMedia")
      .mockReturnValue(query as unknown as MediaQueryList);
    const view = render(<GrowthLab />);
    fireEvent.click(screen.getByRole("button", { name: "Auto-play growth" }));
    act(() => vi.advanceTimersByTime(700));
    expect(screen.getByText("2 / 48")).toBeInTheDocument();
    act(() => {
      query.matches = true;
      change();
    });
    expect(
      screen.getByRole("button", { name: "Auto-play growth" }),
    ).toBeInTheDocument();
    act(() => vi.advanceTimersByTime(1400));
    expect(screen.getByText("2 / 48")).toBeInTheDocument();
    view.unmount();
    expect(query.removeEventListener).toHaveBeenCalled();
    mock.mockRestore();
    vi.useRealTimers();
  });
  it("enforces the 48-event computation limit", () => {
    render(<GrowthLab />);
    for (let i = 1; i < 48; i++)
      fireEvent.click(screen.getByRole("button", { name: "+ One event" }));
    expect(screen.getByText("48 / 48")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "+ One event" })).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Auto-play growth" }),
    ).toBeDisabled();
  });
  it("changes selected intervals and exposes their overlap", () => {
    render(<LocalLab />);
    fireEvent.change(screen.getByLabelText("Selected causal interval"), {
      target: { value: "5" },
    });
    expect(screen.getByLabelText("Selected causal interval")).toHaveValue("5");
    fireEvent.click(screen.getByLabelText("Compare an overlapping interval"));
    expect(screen.getByText("Shared interior events")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Simulation seed"), {
      target: { value: "101" },
    });
    expect(screen.getByLabelText("Selected causal interval")).toHaveValue("0");
    fireEvent.change(screen.getByLabelText("Sampling region"), {
      target: { value: "diamond" },
    });
    expect(screen.getByText(/causally convex flat region/)).toBeInTheDocument();
  });
  it("keeps geometry explanatory controls functional", () => {
    render(<TimeLab />);
    fireEvent.click(screen.getByLabelText("Show causal links"));
    expect(screen.getByLabelText("Show causal links")).not.toBeChecked();
    fireEvent.click(screen.getByLabelText("Highlight longest chain"));
    expect(screen.getByLabelText("Highlight longest chain")).not.toBeChecked();
    const original = screen.getByLabelText("Simulation seed");
    fireEvent.click(screen.getByRole("button", { name: "New sprinkle" }));
    expect(original).toHaveValue(20261026);
    fireEvent.change(screen.getByLabelText("Time model"), {
      target: { value: "total" },
    });
    expect(
      statistic("Interior events").querySelector("strong")?.textContent,
    ).toBe(statistic("Longest chain L").querySelector("strong")?.textContent);
    expect(screen.queryByText("t=1")).not.toBeInTheDocument();
    expect(screen.queryByText("space x · c=1")).not.toBeInTheDocument();
  });
  it("exposes the speculative limits in continuum, embedding and singularity interactions", () => {
    render(<ConceptLab />);
    fireEvent.change(screen.getByLabelText("Educational concept"), {
      target: { value: "continuum" },
    });
    fireEvent.change(screen.getByLabelText("Drawing resolution"), {
      target: { value: "40" },
    });
    expect(screen.getByText("Drawing resolution: 40")).toBeInTheDocument();
    fireEvent.click(
      screen.getByLabelText("Show the classical-growth obstruction"),
    );
    expect(
      screen.getByText(/almost-semiorder restrictions/),
    ).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Educational concept"), {
      target: { value: "embedding" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Change display coordinates" }),
    );
    expect(screen.queryByText(/ABSTRACT ORDER LAYOUT/)).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Educational concept"), {
      target: { value: "singularities" },
    });
    fireEvent.click(screen.getByLabelText("Compare the water analogy"));
    expect(
      screen.getByText(
        /Water has experimentally established microscopic constituents/,
      ),
    ).toBeInTheDocument();
  });
});
