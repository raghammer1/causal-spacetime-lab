/** A scalar exactly transcribed from an archived table; missing values are null. */
export type DataValue = string | number | boolean | null;
export type DataRow = Record<string, DataValue>;
export interface ChartSpec {
  x: string;
  y: string;
  low?: string;
  high?: string;
  series?: string;
  reference?: number;
  referenceLabel?: string;
  label: string;
  unit: string;
}
export interface Dataset {
  id: string;
  experiment: number;
  title: string;
  description: string;
  sourcePath: string;
  sourceUrl: string;
  sha256: string;
  uncertainty: string;
  sampleUnit: string;
  assumptions: string;
  selection: string;
  columns: string[];
  rows: DataRow[];
  chart: ChartSpec;
  defaultFilters: Record<string, DataValue>;
}
export interface Provenance {
  schemaVersion: number;
  sourceCommit: string;
  repository: string;
  transformation: string;
  sources: { path: string; sha256: string; url: string }[];
}
