import type { Dataset, DataRow, DataValue } from "./types";

/** Lossless transport schema. Column names occur once instead of on every row. */
export type PackedDataset = Omit<Dataset, "rows"> & { records: DataValue[][] };

export function hydrateDataset(packed: PackedDataset): Dataset {
  const { records, ...metadata } = packed;
  if (new Set(packed.columns).size !== packed.columns.length) {
    throw new Error(`Duplicate columns in ${packed.id}`);
  }
  const rows: DataRow[] = records.map((record, index) => {
    if (record.length !== packed.columns.length) {
      throw new Error(
        `Malformed archived record ${packed.id}[${index}]: column count differs`,
      );
    }
    return Object.fromEntries(
      packed.columns.map((column, i) => [column, record[i]]),
    );
  });
  return { ...metadata, rows };
}
