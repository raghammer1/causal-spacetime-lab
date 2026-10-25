import { useEffect, useState } from "react";
import { loadDataset } from "../data/loader";
import type { Dataset } from "../data/types";
import DataPanel from "./DataPanel";
export default function AsyncDataPanel({
  datasetId,
  compact = false,
}: {
  datasetId: string;
  compact?: boolean;
}) {
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    loadDataset(datasetId)
      .then((data) => {
        if (active) {
          setDataset(data);
          setError(false);
        }
      })
      .catch(() => {
        if (active) setError(true);
      });
    return () => {
      active = false;
    };
  }, [datasetId, attempt]);
  if (error)
    return (
      <section className="empty-state" role="alert">
        <p>
          The archived dataset could not load. Check the connection and try
          again.
        </p>
        <button
          className="button"
          onClick={() => {
            setError(false);
            setAttempt(attempt + 1);
          }}
        >
          Retry dataset
        </button>
      </section>
    );
  if (!dataset || dataset.id !== datasetId)
    return (
      <div className="empty-state" role="status">
        Loading the archived evidence…
      </div>
    );
  return <DataPanel key={datasetId} dataset={dataset} compact={compact} />;
}
