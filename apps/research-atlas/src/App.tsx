import { Component, lazy, Suspense, useEffect, useRef, useState } from "react";
import type { ErrorInfo, ReactNode } from "react";
import { Link, NavLink, Route, Routes, useLocation } from "react-router-dom";
import * as Dialog from "@radix-ui/react-dialog";
import { ArrowUpRight, Menu, X } from "lucide-react";
import { ReadingProvider, LevelSwitch } from "./components/ReadingLevel";
import Home from "./pages/Home";
const Journey = lazy(() => import("./pages/Journey"));
const Experiment = lazy(() => import("./pages/Experiment"));
const Evidence = lazy(() => import("./pages/Evidence"));
const DataExplorer = lazy(() => import("./pages/DataExplorer"));
const Learn = lazy(() => import("./pages/Learn"));
const Sources = lazy(() => import("./pages/Sources"));
const Synthesis = lazy(() => import("./pages/Synthesis"));
const links = [
  { to: "/synthesis", label: "Final conclusion" },
  { to: "/journey", label: "The journey" },
  { to: "/experiment/1", label: "Experiments" },
  { to: "/evidence", label: "Evidence map" },
  { to: "/data", label: "Data explorer" },
  { to: "/learn", label: "Learn" },
];
export function Mark() {
  return (
    <svg viewBox="0 0 32 38" aria-hidden="true">
      <path d="m16 2 14 17-14 17L2 19Z M16 2v34 M2 19h28" />
      <circle cx="16" cy="19" r="3" />
    </svg>
  );
}
class Boundary extends Component<{ children: ReactNode }, { error: boolean }> {
  state = { error: false };
  static getDerivedStateFromError() {
    return { error: true };
  }
  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Atlas render failed", error, info.componentStack);
  }
  render() {
    return this.state.error ? (
      <section className="container page-head">
        <p className="eyebrow">Unable to display this view</p>
        <h1>Let’s try that again.</h1>
        <p>The atlas could not load. Your research archives are unchanged.</p>
        <button className="button" onClick={() => window.location.reload()}>
          Reload the atlas
        </button>
      </section>
    ) : (
      this.props.children
    );
  }
}
function Shell() {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const main = useRef<HTMLElement>(null);
  useEffect(() => {
    window.scrollTo(0, 0);
    main.current?.focus({ preventScroll: true });
    const label = location.pathname.startsWith("/experiment/")
      ? "Experiment " + location.pathname.split("/").pop()
      : (
          {
            "/": "The big question",
            "/journey": "The research journey",
            "/evidence": "What did we actually disprove?",
            "/data": "Data explorer",
            "/learn": "Visual education lab",
            "/sources": "Sources & methods",
            "/synthesis": "Final research conclusion",
          } as Record<string, string>
        )[location.pathname] || "Page not found";
    document.title = label + " — Causal Spacetime Lab";
  }, [location.pathname]);
  return (
    <>
      <a
        className="skip-link"
        href="#main-content"
        onClick={(e) => {
          e.preventDefault();
          main.current?.focus();
        }}
      >
        Skip to content
      </a>
      <header className="site-header">
        <div className="header-inner">
          <Link className="brand" to="/" aria-label="Causal Spacetime Lab home">
            <Mark />
            <span>
              CAUSAL
              <br />
              <strong>SPACETIME LAB</strong>
            </span>
          </Link>
          <nav className="desktop-nav" aria-label="Main navigation">
            {links.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                className={({ isActive }) =>
                  isActive ||
                  (l.to === "/experiment/1" &&
                    location.pathname.startsWith("/experiment/"))
                    ? "active"
                    : ""
                }
              >
                {l.label}
              </NavLink>
            ))}
          </nav>
          <Link className="header-source" to="/sources">
            Open research <ArrowUpRight size={14} />
          </Link>
          <Dialog.Root open={open} onOpenChange={setOpen}>
            <Dialog.Trigger
              className="mobile-menu"
              aria-label="Open navigation"
            >
              <Menu />
            </Dialog.Trigger>
            <Dialog.Portal>
              <Dialog.Overlay className="menu-overlay" />
              <Dialog.Content className="menu-panel">
                <Dialog.Title>Explore the atlas</Dialog.Title>
                <Dialog.Description>
                  Seven experiments. A completed research programme.
                </Dialog.Description>
                <Dialog.Close
                  className="menu-close"
                  aria-label="Close navigation"
                >
                  <X />
                </Dialog.Close>
                <nav aria-label="Mobile navigation">
                  {links.map((l) => (
                    <NavLink
                      key={l.to}
                      to={l.to}
                      onClick={() => setOpen(false)}
                    >
                      {l.label}
                    </NavLink>
                  ))}
                  <Link to="/sources" onClick={() => setOpen(false)}>
                    Sources & methods
                  </Link>
                </nav>
              </Dialog.Content>
            </Dialog.Portal>
          </Dialog.Root>
        </div>
      </header>
      <div className="reading-bar">
        <div className="container">
          <span>
            <i className="status-dot" /> RESEARCH PROGRAMME CLOSED{" "}
            <span className="reading-dash">/</span>{" "}
            <span className="atlas-version">ARCHIVE 01–07</span>
          </span>
          <LevelSwitch />
        </div>
      </div>
      <main id="main-content" ref={main} tabIndex={-1}>
        <Boundary key={location.pathname}>
          <Suspense
            fallback={
              <div className="container loading" role="status">
                Loading research…
              </div>
            }
          >
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/journey" element={<Journey />} />
              <Route path="/experiment/:id" element={<Experiment />} />
              <Route path="/evidence" element={<Evidence />} />
              <Route path="/data" element={<DataExplorer />} />
              <Route path="/learn" element={<Learn />} />
              <Route path="/sources" element={<Sources />} />
              <Route path="/synthesis" element={<Synthesis />} />
              <Route
                path="*"
                element={
                  <section className="container page-head">
                    <p className="eyebrow">404 / UNCHARTED TERRITORY</p>
                    <h1>This route isn’t in the atlas.</h1>
                    <Link className="button" to="/">
                      Return to the big question
                    </Link>
                  </section>
                }
              />
            </Routes>
          </Suspense>
        </Boundary>
      </main>
      <footer className="site-footer container">
        <Link className="brand" to="/">
          <Mark />
          <span>
            CAUSAL
            <br />
            <strong>SPACETIME LAB</strong>
          </span>
        </Link>
        <p>
          Seven experiments. Evidence preserved.
          <br />This research programme is closed.
        </p>
        <div>
          <Link to="/synthesis">
            Final conclusion <ArrowUpRight size={14} />
          </Link>
          <Link to="/sources">
            Sources & methods <ArrowUpRight size={14} />
          </Link>
          <a href="https://github.com/raghammer1/causal-spacetime-lab">
            Repository <ArrowUpRight size={14} />
          </a>
          <small>Educational numerical research · Open source</small>
        </div>
      </footer>
    </>
  );
}
export default function App() {
  return (
    <ReadingProvider>
      <Shell />
    </ReadingProvider>
  );
}
