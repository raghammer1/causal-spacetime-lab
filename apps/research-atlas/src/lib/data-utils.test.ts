import { describe, expect, it } from "vitest";
import { filterRows, formatNumber, toCsv } from "./data-utils";
describe("scientific data presentation", () => {
  it("retains zero and distinguishes missing values from nonfinite inputs", () => {
    expect(formatNumber(0)).toBe("0");
    expect(formatNumber(null)).toBe("Not available");
    expect(formatNumber(NaN)).toBe("Not available");
    expect(formatNumber(0.00000176775)).toBe("1.768e-6");
    expect(formatNumber(4.5813)).toBe("4.5813");
  });
  it("filters exact parameter identities without pooling dependent rows", () => {
    const rows = [
      { parameter: 0.005, history: 1, stage: "prefix" },
      { parameter: 0.005, history: 1, stage: "thinned" },
      { parameter: 0.05, history: 2, stage: "prefix" },
    ];
    expect(filterRows(rows, { parameter: ".005" })).toEqual([]);
    expect(filterRows(rows, { parameter: "0.005" })).toHaveLength(2);
    expect(filterRows(rows, { parameter: "0.005", stage: "prefix" })).toEqual([
      rows[0],
    ]);
    expect(filterRows(rows, {}, "thinned")).toEqual([rows[1]]);
  });
  it("exports full precision, missing cells and valid CSV escaping", () => {
    expect(
      toCsv(
        [{ mean: 1 / 24, note: 'a,"b"', missing: null }],
        ["mean", "note", "missing"],
      ),
    ).toBe('"mean","note","missing"\r\n"0.041666666666666664","a,""b""",""');
  });
});
