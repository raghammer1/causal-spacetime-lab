import { describe, expect, it } from "vitest";
import { datasetCatalog, provenance, sourceCommit, sourceUrl } from "./catalog";
import { loadDataset } from "./loader";

describe("metadata-first archive access", () => {
  it("offers the complete selection catalog without carrying observation rows", () => {
    expect(datasetCatalog).toHaveLength(13);
    expect(datasetCatalog.every((dataset) => dataset.rowCount > 0)).toBe(true);
    expect(
      datasetCatalog.every(
        (dataset) => !("rows" in dataset) && !("records" in dataset),
      ),
    ).toBe(true);
    expect(sourceCommit).toBe(provenance.sourceCommit);
    for (const dataset of datasetCatalog)
      expect(dataset.sourceUrl).toBe(sourceUrl(dataset.sourcePath));
  });

  it.each(datasetCatalog)(
    "loads $id with the exact catalog metadata and complete rows",
    async (metadata) => {
      const { rowCount, ...expected } = metadata;
      const dataset = await loadDataset(metadata.id);
      const { rows, ...actual } = dataset;
      expect(actual).toEqual(expected);
      expect(rows).toHaveLength(rowCount);
      expect(
        rows.every(
          (row) => Object.keys(row).length === metadata.columns.length,
        ),
      ).toBe(true);
      expect("records" in dataset).toBe(false);
    },
  );

  it("reuses the same request and hydrated data when navigating back", async () => {
    const first = loadDataset("time-primary");
    const second = loadDataset("time-primary");
    expect(first).toBe(second);
    expect(await first).toBe(await second);
  });

  it.each(["not-a-dataset", "__proto__", "constructor", "toString"])(
    "explicitly rejects unknown identifier %s",
    async (id) => {
      await expect(loadDataset(id)).rejects.toThrow(
        `Unknown archived dataset: ${id}`,
      );
    },
  );
});
