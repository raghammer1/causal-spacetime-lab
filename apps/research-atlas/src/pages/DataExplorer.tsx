import { useSearchParams } from "react-router-dom";
import { datasetCatalog as datasets } from "../data/catalog";
import AsyncDataPanel from "../components/AsyncDataPanel";
export default function DataExplorer() {
  const [params, setParams] = useSearchParams();
  const requested = datasets.find((d) => d.id === params.get("dataset"));
  const candidate =
    Number(params.get("experiment")) || requested?.experiment || 1;
  const experiment = [1, 2, 3, 4, 5].includes(candidate) ? candidate : 1;
  const choices = datasets.filter((d) => d.experiment === experiment);
  const current =
    requested?.experiment === experiment
      ? requested
      : choices[0] || datasets[0];
  return (
    <div className="container">
      <header className="page-head">
        <p className="eyebrow">THE RESEARCH, WITH ITS RECEIPTS</p>
        <h1>
          Explore the <em>evidence.</em>
        </h1>
        <p>
          Actual archived results. Exact analytical references. Uncertainty that
          keeps its meaning. Every point leads back to its source.
        </p>
      </header>
      <div className="explorer-selectors">
        <label>
          Experiment
          <select
            value={experiment}
            onChange={(e) => setParams({ experiment: e.target.value })}
          >
            {[1, 2, 3, 4, 5].map((n) => (
              <option key={n} value={n}>
                {String(n).padStart(2, "0")} ·{" "}
                {
                  [
                    "Time reconstruction",
                    "Dimension reconstruction",
                    "Adversarial geometry",
                    "Local causal structure",
                    "Background-free growth",
                  ][n - 1]
                }
              </option>
            ))}
          </select>
        </label>
        <label>
          Archived dataset
          <select
            value={current.id}
            onChange={(e) =>
              setParams({
                experiment: String(experiment),
                dataset: e.target.value,
              })
            }
          >
            {choices.map((d) => (
              <option key={d.id} value={d.id}>
                {d.title}
              </option>
            ))}
          </select>
        </label>
      </div>
      <AsyncDataPanel key={current.id} datasetId={current.id} />
      <aside className="note-box">
        <strong>Read uncertainty in context.</strong> Pointwise bootstrap
        intervals, Wilson intervals and simultaneous decision bands answer
        different questions. Some retained percentile intervals do not contain
        their point estimate. We preserve these adverse results rather than
        adjusting the display.
      </aside>
    </div>
  );
}
