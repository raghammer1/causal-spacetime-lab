import { createContext, useContext, useState } from "react";
import type { ReactNode } from "react";
export type ReadingLevel = "explorer" | "engineer" | "researcher";
const Context = createContext<{
  level: ReadingLevel;
  setLevel: (l: ReadingLevel) => void;
}>({ level: "explorer", setLevel: () => {} });
export function ReadingProvider({ children }: { children: ReactNode }) {
  const [level, setLevel] = useState<ReadingLevel>("explorer");
  return (
    <Context.Provider value={{ level, setLevel }}>{children}</Context.Provider>
  );
}
export const useReadingLevel = () => useContext(Context);
export function LevelSwitch() {
  const { level, setLevel } = useReadingLevel();
  return (
    <div className="level-switch" role="group" aria-label="Explanation level">
      {(["explorer", "engineer", "researcher"] as const).map((l) => (
        <button key={l} aria-pressed={level === l} onClick={() => setLevel(l)}>
          {l}
        </button>
      ))}
    </div>
  );
}
