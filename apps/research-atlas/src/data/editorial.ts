/** Editorial claims are sourced to the immutable, verified research baseline. */
export const SCIENTIFIC_REF = "4e1a667ad2d590ee365a395021f0c9772e63b8d1";
export const sourceUrl = (path: string): string =>
  /^https?:\/\//.test(path)
    ? path
    : `https://github.com/raghammer1/causal-spacetime-lab/blob/${SCIENTIFIC_REF}/${path}`;

export interface ScientificSource {
  label: string;
  path: string;
}
export interface Equation {
  label: string;
  expression: string;
  explanation: string;
}
export interface Experiment {
  id: number;
  slug: string;
  title: string;
  shortTitle: string;
  question: string;
  analogy: string;
  hypothesis: string;
  setup: string;
  assumptions: string[];
  measured: string;
  found: string;
  survived: string;
  failed: string;
  unresolved: string;
  next: string;
  explorer: string;
  engineer: string;
  researcher: string;
  equations: Equation[];
  limitations: string[];
  sources: ScientificSource[];
}
export type ClaimStatus = "supported" | "falsified" | "open" | "untested";
export interface Claim {
  id: string;
  title: string;
  status: ClaimStatus;
  precise: string;
  evidence: string;
  assumptions: string;
  scope: string;
  experiments: number[];
  sources: ScientificSource[];
}
export interface Concept {
  id: string;
  title: string;
  intro: string;
  detail: string;
  equation: string;
  experiment: number;
  sources: ScientificSource[];
}

export const experiments: Experiment[] = [
  {
    id: 1,
    slug: "time",
    title: "Can causal relationships reveal time?",
    shortTitle: "Reconstruct time",
    question:
      "If we know which events can influence which others, can we recover how much time separates two endpoints?",
    analogy:
      "Imagine reconstructing a journey from a stack of ordered receipts. The longest consistent sequence acts like a rough clock, once you know how frequently receipts were recorded.",
    hypothesis:
      "In a known flat 1+1-dimensional spacetime, the chain-based estimate should be biased low at finite density, with less bias at the highest tested density.",
    setup:
      "Sprinkle events independently into a known Minkowski causal diamond. Keep only the strict precedence relation for the order-only algorithm. Find the longest chain of interior events, then divide by the known density scale.",
    assumptions: [
      "Flat 1+1D Minkowski geometry and light speed c = 1.",
      "Uniform Poisson sprinkling at known physical spacetime density ρ.",
      "The two deterministic boundary endpoints do not count toward chain length.",
      "Absolute duration requires the density calibration; the abstract order alone supplies no seconds.",
    ],
    measured:
      "4,200 primary sprinklings: seven densities, three durations, 200 independent draws per cell. A separately seeded 8,000-draw follow-up investigated one adverse equal-count comparison.",
    found:
      "At density 8192, relative mean biases remained −7.844%, −4.914% and −3.338% for durations 0.5, 1 and 2. All 21 pointwise mean-bias intervals stayed below zero. The endpoint improvement supported the finite-range prediction.",
    survived:
      "Causal order carries recoverable temporal information under the stated geometry and density assumptions. Every eligible order-only and coordinate-based chain check agreed.",
    failed:
      "Finite-density reconstruction was not exact. One primary equal-count contrast excluded zero; the independent follow-up did not reproduce a persistent discrepancy.",
    unresolved:
      "This does not generate time, establish microscopic discreteness or recover gravitational dynamics. A finite sweep cannot prove an infinite-density limit.",
    next: "A clock-like statistic is only one clue. We next asked whether the same causal relationships encode spacetime dimension.",
    explorer:
      "More sampled events give a finer causal clock. A chain is a sequence in which every event can precede the next. Its longest possible length estimates elapsed time, but finite samples systematically miss some of the continuum duration.",
    engineer:
      "The order-only routine uses dynamic programming on a Boolean precedence matrix. An independent longest-increasing-subsequence routine reads the known null coordinates for efficiency. Their outputs are cross-checked at small N; only the first routine is coordinate-blind. Matched-count chain and antichain controls reuse the physical draws’ counts.",
    researcher:
      "For λ = ρT²/2, the Poissonized longest-increasing-subsequence law gives L ∼ 2√λ and T̂ = L/√(2ρ). The known leading relative bias is approximately −1.7711/(2λ^(1/3)); it is an asymptotic literature guide, not a fitted correction. Percentile bootstrap intervals resample entire independent sprinklings and quantify uncertainty of the mean, not systematic bias.",
    equations: [
      {
        label: "Known sampling volume",
        expression: "V = T²/2;  N ∼ Poisson(ρV)",
        explanation:
          "Null coordinates u = t + x and v = t − x map the diamond to a square. The Jacobian 1/2 fixes the physical volume normalization.",
      },
      {
        label: "Asymptotic time estimator",
        expression: "T̂ = L / √(2ρ)",
        explanation:
          "L counts interior events only. It is not an exact finite-sample identity; an empty sample has L = 0.",
      },
      {
        label: "Analytical negative controls",
        expression: "E[Ltotal] = λ;  E[Lantichain] = 1 − exp(−λ)",
        explanation:
          "These exact control trends differ from the sprinkled-order reference 2√λ. They do not test every possible artificial order.",
      },
    ],
    limitations: [
      "Pointwise bootstrap intervals are not simultaneous bands and do not include model uncertainty.",
      "The 8,000-draw follow-up was post hoc and was not pooled into a preregistered result.",
      "A negative finite-density bias remains even when the uncertainty in its mean is small.",
      "The generator supplies geometry; the fast chain algorithm uses that geometry.",
    ],
    sources: [
      {
        label: "Full results and uncertainties",
        path: "docs/FINITE_DENSITY_RESULTS.md",
      },
      { label: "Registered protocol", path: "docs/FINITE_DENSITY_PROTOCOL.md" },
      { label: "Derivation and primary references", path: "docs/THEORY.md" },
      {
        label: "Primary raw trials",
        path: "docs/experiments/finite-density-scaling-v1/raw.csv",
      },
      {
        label: "Independent follow-up",
        path: "docs/experiments/equal-count-followup/summary.csv",
      },
      { label: "Python reconstruction", path: "src/causal_lab/core.py" },
      { label: "Study implementation", path: "src/causal_lab/scaling.py" },
    ],
  },
  {
    id: 2,
    slug: "dimensions",
    title: "Can causal relationships reveal dimensions?",
    shortTitle: "Reconstruct dimensions",
    question:
      "Can we tell a two-, three- or four-dimensional spacetime sample apart without seeing its coordinates?",
    analogy:
      "In a narrow corridor, many people can reach one another by walking forward. In a room with more directions, fewer pairs are connected by the same travel rule. Pair connectivity becomes a clue to dimension.",
    hypothesis:
      "The ordering fraction should recover the dimensions of uniform flat diamonds, while deliberately matched artificial orders should expose its insufficiency as a geometry test.",
    setup:
      "Generate uniform fixed-count samples in flat diamonds of spacetime dimension d = 2, 3 and 4. Count comparable pairs from their order matrices, invert the Myrheim–Meyer relation, and evaluate on independent held-out orders.",
    assumptions: [
      "Dimension includes time: d = 4 means one time and three spatial dimensions.",
      "Uniform sampling in a flat Alexandrov interval, not an arbitrary boundary or curved spacetime.",
      "Each related unordered pair is counted once: r = R / choose(N, 2).",
      "Entire orders are independent units; pairs sharing events are correlated.",
    ],
    measured:
      "1,800 primary orders at N = 64, 128 and 256, plus 900 separate calibration samples and 3,006 controls. Every primary dimension/count cell contains 200 independent orders.",
    found:
      "At N = 256, mean inferred dimensions were 1.9980 [1.9906, 2.0057], 3.0161 [3.0029, 3.0297] and 3.9914 [3.9715, 4.0107]. Each dimension had 200/200 correct labels, with a 95% Wilson lower bound of 98.1%.",
    survived:
      "The ordering fraction is dimension-sensitive under the registered sampling assumptions. N = 128 was the smallest tested count supporting the 90% classification target for all three dimensions.",
    failed:
      "All 1,800 fraction-matched two-layer holdouts fooled the single-statistic detector and received their target label. An apparent dimension is not a spacetime certificate.",
    unresolved:
      "The richer five-feature detector rejected these easy controls but accepted 49/200 random DAGs at N = 64, including 36 that the single-statistic detector rejected. More features are not automatically safer.",
    next: "We needed to attack the detectors deliberately, separate easy successes from harder failures, and account for calibration uncertainty.",
    explorer:
      "Pick two events at random. Could one influence the other? In these particular flat diamonds the answer is yes for half the pairs in d = 2, about 22.86% in d = 3, and 10% in d = 4. Those patterns help us infer dimension, but an artificial network can imitate them.",
    engineer:
      "Uniform spacetime-volume sampling needs the correct radial and time distributions, not uniform time or uniform radius. Inference receives only the closed relation. A bounded bisection solves for real d in [1, 10]; out-of-domain values remain unavailable. The optional nearest-class label 2/3/4 is a separate rule, applied only to estimates in [1.5, 4.5].",
    researcher:
      "The analytic expectation is p(d) = Γ(d + 1)Γ(d/2)/(2Γ(3d/2)). This normalization is twice the literature convention E[R]/E[N]². Nonlinear inversion is biased in general: E[p⁻¹(r)] ≠ p⁻¹(E[r]). Pointwise mean intervals use whole-order bootstrap resampling; classification uncertainty uses Wilson intervals, conditional on the studied populations.",
    equations: [
      {
        label: "Ordering fraction",
        expression: "r = 2R / [N(N − 1)]",
        explanation:
          "N ≥ 2 is required. Comparability includes either temporal orientation, and each unordered pair contributes at most once.",
      },
      {
        label: "Flat-diamond reference",
        expression: "p(d) = Γ(d + 1)Γ(d/2) / [2Γ(3d/2)]",
        explanation:
          "p(2) = 1/2, p(3) = 8/35 and p(4) = 1/10 exactly. This prediction assumes uniform flat-diamond sampling.",
      },
      {
        label: "A deliberately matched adversary",
        expression: "E[r] = q·a·b / choose(N, 2);  H ≤ 2",
        explanation:
          "With a lower and b upper events, independent cross-layer edges can match the expected fraction while keeping every open interval empty.",
      },
    ],
    limitations: [
      "The d = 3, N = 256 mean interval excludes the true integer; accurate classification does not imply an unbiased estimator.",
      "A total order gives d = 1 at the inversion boundary. An antichain is out of domain, not infinitely dimensional.",
      "Original detector intervals condition on one frozen calibration and omit refitting uncertainty.",
      "Two-dimensional projections and network layouts are display devices, not literal views of four-dimensional geometry.",
    ],
    sources: [
      {
        label: "Full dimension results",
        path: "docs/DIMENSION_RECONSTRUCTION_RESULTS.md",
      },
      {
        label: "Registered protocol",
        path: "docs/DIMENSION_RECONSTRUCTION_PROTOCOL.md",
      },
      {
        label: "Sampling and inversion derivation",
        path: "docs/DIMENSION_THEORY.md",
      },
      {
        label: "Archived summary",
        path: "docs/experiments/dimension-reconstruction-v1/summary.csv",
      },
      {
        label: "Raw held-out orders",
        path: "docs/experiments/dimension-reconstruction-v1/raw.csv",
      },
      {
        label: "Python dimension implementation",
        path: "src/causal_lab/dimension.py",
      },
      {
        label: "Original chain-count formula: Roy, Sinha & Surya",
        path: "https://arxiv.org/abs/1212.0631",
      },
    ],
  },
  {
    id: 3,
    slug: "adversaries",
    title: "Can fake universes fool our mathematics?",
    shortTitle: "Attack the detectors",
    question:
      "If a network is designed to look geometric, which of our measurements can actually expose it?",
    analogy:
      "Two songs can have the same duration, tempo and average pitch without being the same song. Matching a short list of statistics can erase the structure we hoped to identify.",
    hypothesis:
      "At least one of six detectors might retain genuine samples and reject every registered artificial family across three independently calibrated fits. Harder controls could falsify that advancement claim.",
    setup:
      "Freeze six detector definitions, fit them on independent data, set thresholds using separate validation samples, then test genuine diamonds and adversarial orders. Bounded searches try to match first height and ordering fraction, then a 15-component feature vector.",
    assumptions: [
      "“Genuine” means sampled from the specified flat-diamond model, not observed physical spacetime.",
      "Calibration, development, validation and final tests use disjoint seeded streams.",
      "Detectors share a nominal 95% validation target; ties can produce different achieved rates.",
      "The two checkpoints of a search and the decisions of different detectors are paired observations.",
    ],
    measured:
      "52,218 recorded orders across dimensions 2–4, sizes 64–256 and three fits. The archive retains both checkpoints of 5,400 searches, every failed match, per-fit Wilson bounds and paired hierarchical comparisons.",
    found:
      "All six detectors failed the registered advancement benchmark. Height alone rejected every easy matched two-layer control. At target d = 2, N = 64, the interval detector F still accepted 63.17% of full-search outputs [57.33%, 69.00%], a pointwise hierarchical interval.",
    survived:
      "Some richer summaries distinguish particular adversarial families. Exact nonisomorphic orders nevertheless share every selected old summary; selected statistics cannot uniquely identify an arbitrary order.",
    failed:
      "No detector qualified as a general winner. Zero of 5,400 searches met all 15 one-SD constraints, yet 361 N = 64 outputs passed all six detectors in a post hoc descriptive inspection. Detector acceptance and target matching are different tests.",
    unresolved:
      "F and E trade advantages; complexity is neither universally useful nor universally useless. Larger-N rejection also reflects an adversary with a fixed search budget. Rank-two and d = 2 diamond samplers have exactly the same full order law.",
    next: "Instead of fitting another classifier, we asked which local relationships the global summaries lose, and which laws can be derived under explicit assumptions.",
    explorer:
      "Try the artificial families. A shallow two-layer network can imitate the pair fraction, but its short chains give it away. Harder networks can imitate more clues. The lesson is to ask what a detector has measured, not to treat an accepted score as reality.",
    engineer:
      "A measures standardized fraction; B standardized H/N; C their RMS; D the original five-feature RMS; E the largest of those five residuals; F Hellinger distance on ten interval-abundance categories. Every score minimizes over calibrated d = 2, 3, 4 templates. E prevents compensation inside a template, but its independently fitted cutoff does not make its accepted set a subset of A’s.",
    researcher:
      "The registered gate required every positive per-fit Wilson lower bound ≥ 90%, every stochastic negative upper bound ≤ 5%, and rejection of exact controls. This intersection is not a simultaneous 95% confidence claim. Across-fit comparisons resample fits and whole paired orders; three fits provide limited calibration-variation information. An exact ten-event pair has N = 10, R = 25, H = 4 and histogram (16,0,8,0,0,0,0,0,1), but different internal connectivity.",
    equations: [
      {
        label: "Compensating score D",
        expression: "SD = min_d √mean(z₁², …, z₅²)",
        explanation:
          "Several small residuals can compensate for a large one. A low score is compatibility with the chosen summaries, not proof of an embedding.",
      },
      {
        label: "Non-compensating score E",
        expression: "SE = min_d max_j |zⱼ|",
        explanation:
          "All five residuals must fit one template, but the acceptance threshold is still separately calibrated.",
      },
      {
        label: "Interval detector F",
        expression: "SF = min_d √[½ Σⱼ(√pⱼ − √μd,j)²]",
        explanation:
          "Ten probabilities include incomparable pairs and bins of interior cardinality, all normalized by choose(N,2). Their full sum is one.",
      },
    ],
    limitations: [
      "The raw family name multi_matched denotes attempted matching; no search achieved the full registered target.",
      "Observed fit ranges are not confidence intervals. Repeated fits are not one pooled binomial experiment.",
      "Two independent rankings form an exact positive overlap control, not a negative family that should be rejected.",
      "Flat boxes change the boundary while retaining Lorentzian geometry; their rejection is reference-model sensitivity.",
    ],
    sources: [
      {
        label: "Complete detector comparison",
        path: "docs/ADVERSARIAL_GEOMETRY_RESULTS.md",
      },
      {
        label: "Registered benchmark",
        path: "docs/ADVERSARIAL_GEOMETRY_PROTOCOL.md",
      },
      {
        label: "Exact information-loss proofs",
        path: "docs/ADVERSARIAL_GEOMETRY_THEORY.md",
      },
      {
        label: "Per-fit rates and Wilson intervals",
        path: "docs/experiments/adversarial-geometry-v1/rates.csv",
      },
      {
        label: "Hierarchical summaries",
        path: "docs/experiments/adversarial-geometry-v1/summary.json",
      },
      {
        label: "Exact counterexample matrices",
        path: "docs/experiments/adversarial-geometry-v1/exact_counterexamples.json",
      },
      {
        label: "Python detector definitions",
        path: "src/causal_lab/adversarial_detectors.py",
      },
    ],
  },
  {
    id: 4,
    slug: "local-structure",
    title: "Does local structure contain more information?",
    shortTitle: "Look inside the order",
    question:
      "Can we learn more by examining what happens between pairs of events, rather than averaging over the whole sample?",
    analogy:
      "A city’s average street count hides its neighbourhoods. Looking inside a well-defined district can reveal connections lost in a city-wide average—provided the district boundary does not cut the roads we want to count.",
    hypothesis:
      "Conditional interval laws should be independent of the outer boundary for uniform, causally convex flat regions. Local patterns should distinguish some exact collisions of the old global summaries.",
    setup:
      "Compare diamonds, central time slabs and spatial boxes in d = 2, 3, 4. Select related endpoint pairs and examine their open intervals with exactly 2, 4 or 8 events. Compare pooled conditional counts with independent small-diamond reference laws.",
    assumptions: [
      "The local theorem assumes uniform iid sampling in a finite-volume, causally convex flat region.",
      "Causal convexity means every full interval between related endpoints remains inside the sampling region.",
      "Open intervals exclude endpoints; closing them would make connectivity trivial.",
      "Independent parent orders, not overlapping intervals, are the resampling units.",
    ],
    measured:
      "31,392 parent/checkpoint records, 3,600 exact matched pairs and 864 searches. The primary gate comprises 42 N = 256 diamond/slab conditional checks, with 126 corresponding per-fit checks.",
    found:
      "All 42 primary checks met their registered practical equivalence margins. For flat slabs in d = 2, 3, 4, global estimates were 2.5282, 3.6085 and 4.5813; local estimates were 1.9976, 2.9929 and 3.9948. The d = 4 local interval was [3.9478, 4.0401].",
    survived:
      "Local information can improve dimension reconstruction under stated sampling conditions. Exact 2+2 counts and interval connectivity distinguish the old ten-event summary collision.",
    failed:
      "The extended measured summaries still do not identify every finite order. A separate postregistration 12-event pair matches the complete measured structural vector while one comparability graph is connected and the other has two components.",
    unresolved:
      "Boxes retain clipping bias, sparse intervals remain unavailable, and 528 searches accepted no move. Neither a successful local test nor a stalled search certifies geometric embeddability.",
    next: "We now had useful reconstruction laws and explicit limits. The next question was genuinely different: what does a law generate when no spacetime coordinates are supplied at all?",
    explorer:
      "A slab is still flat spacetime, even when a whole-sample dimension formula gives the wrong number. Looking inside complete causal intervals restores the right reference law. In a spatial box, some intervals are clipped, so the same guarantee is lost.",
    engineer:
      "For each parent and interval size m, retain Aₘ = number of intervals and B = sum of the internal observable. Pool as ΣB/ΣA within each fit, then equally average the fitwise estimates. Do not average per-parent ratios or treat all intervals as independent. Parents with no interval remain in resampling; insufficient support stays missing.",
    researcher:
      "Condition on related endpoints and exactly m interior points in a uniform causally convex flat region. The points are iid uniform in that Alexandrov interval, and translation, Lorentz transformation and scale map it to the standard diamond. Thus E[Bf,m − μ(d,m)Aₘ] = 0. It does not follow that E[B/A] = μ. The local d estimate inverts the pooled m = 2 connectivity law. Practical margins and pointwise uncertainty do not constitute an exact-law test.",
    equations: [
      {
        label: "Open causal interval",
        expression: "I(a,b) = {x : a ≺ x ≺ b}",
        explanation:
          "Connectivity is measured on this interior’s comparability graph, with the two endpoints excluded.",
      },
      {
        label: "Conditional count law",
        expression: "E[Bf,m − μ(d,m)Aₘ] = 0",
        explanation:
          "Conditional iid uniform sampling inside a complete interval yields the reference m-event diamond law; random denominators require pooled counts.",
      },
      {
        label: "Exact induced 2+2 count",
        expression: "n₂₂ = Σa∥c |F(a) ∖ F(c)| · |F(c) ∖ F(a)|",
        explanation:
          "Sum over unordered incomparable minima. Exclusive future choices give two chains with no cross-relations. The ten-event examples yield 12 and 16.",
      },
    ],
    limitations: [
      "Local reconstruction here is an ensemble estimator, not a proof of consistent reconstruction from one increasingly dense order.",
      "All 42 passing checks use practical margins; a confidence interval merely containing zero is not equivalence.",
      "TV is nonsmooth and its percentile bootstrap can be upward-biased near zero; some interval bounds exceed their point estimate.",
      "The 12-event collision is a postregistration exact deduction, not a preregistered numerical outcome or ambiguity theorem for a restricted manifoldlike class.",
    ],
    sources: [
      {
        label: "All 42 primary checks and complete results",
        path: "docs/LOCAL_CAUSAL_STRUCTURE_RESULTS.md",
      },
      {
        label: "Registered conditional-law protocol",
        path: "docs/LOCAL_CAUSAL_STRUCTURE_PROTOCOL.md",
      },
      {
        label: "Mathematical derivations",
        path: "docs/LOCAL_CAUSAL_STRUCTURE_THEORY.md",
      },
      {
        label: "Continuum requirements",
        path: "docs/LOCAL_CAUSAL_STRUCTURE_CONTINUUM.md",
      },
      {
        label: "Conditional-law archive",
        path: "docs/experiments/local-causal-structure-v1/conditional.csv",
      },
      {
        label: "Full-summary collision",
        path: "docs/experiments/local-causal-structure-v1/exact_counterexample.json",
      },
      {
        label: "Python local observables",
        path: "src/causal_lab/local_structure.py",
      },
    ],
  },
  {
    id: 5,
    slug: "growth",
    title: "Can geometry emerge without predefined space?",
    shortTitle: "Grow without geometry",
    question:
      "What happens if events acquire causal relationships from a growth rule, without ever being placed in a spacetime?",
    analogy:
      "A new document cites earlier documents and inherits all their ancestors. The resulting family tree needs no map. The question is whether its large-scale relationships resemble the particular spacetime sampling law we want.",
    hypothesis:
      "Transitive percolation is a coherent intrinsic growth law, but known mathematical restrictions exclude the required nondegenerate Minkowski sampling limit. The study tests its finite signatures, crossovers and consistency.",
    setup:
      "Start from one event. At each birth, independently select every earlier event with probability p, then inherit all selected events’ causal pasts. Record nested prefixes and uniformly thinned closed orders for six fixed probabilities.",
    assumptions: [
      "Primary p values are 0.005, 0.01, 0.02, 0.05, 0.1 and 0.3; none was retuned after observing outcomes.",
      "Birth order is a natural labeling; graph-layout coordinates have no physical meaning.",
      "Prefixes and thinnings of one history are dependent and stay together in uncertainty resampling.",
      "The wider no-go uses ordinary CSG with nonnegative couplings, t₀ or t₁ positive, and expected uniform finite-suborder sampling convergence.",
    ],
    measured:
      "1,056 independent stochastic histories across eleven families, with 17,986 dependent records including deterministic endpoints. Each stochastic family has 96 histories; prefixes use N = 32, 64, 128, 256 and 512.",
    found:
      "All six fixed-p families failed the registered finite signature. All 18 late-size 2+2 level bands lay below the d = 2 target 1/24 beyond the allowed ±0.005 margin. Across 48 entries: 23 contradictions, 19 practical equivalences and six inconclusive comparisons.",
    survived:
      "The rule generates consistent causal orders without geometry. Exact mathematics explains why its large-scale sampled order law cannot approach the target nondegenerate Minkowski law.",
    failed:
      "This investigated classical growth route does not reproduce the required Minkowski sampling limit. Its no-go is model- and limit-specific; it does not disprove emergent spacetime.",
    unresolved:
      "Different microscopic dynamics, including quantum proposals, remain open. They need explicit assumptions, consistency, covariance, a convergence target and eventually physical tests. No gravity or black-hole interior was modeled.",
    next: "Historically, this obstruction led to Experiment 6: could quantum correlations reveal geometric structure? The completed programme now ends with Experiment 7 and the final synthesis; this transition is not a proposal for more simulations.",
    explorer:
      "A new dot chooses older dots, then inherits their ancestors. Some finite networks can look geometric, but the growth rule produces the wrong long-run relationship patterns for our target. The broader possibility of emergent spacetime remains untested.",
    engineer:
      "Store primitive Bernoulli selections separately from the transitive closure. Preserve prefixes when extending a seeded history. Thinning must restrict the closed relation; deleting intermediate primitive edges and reclosing would erase inherited precedence. Bootstrap complete histories within each batch and carry the same weights across all prefixes and thinning replicas.",
    researcher:
      "At fixed p > 0, E[1 − rN] ≤ 2(1 − p)/[(N − 1)p²], so all fixed-size uniformly sampled suborders approach chains almost surely. This does not make the infinite order total: limsup HN/N ≤ (1 + p)/2 < 1 for p < 1. More generally, Brightwell–Georgiou’s ordinary CSG class is o(N²) pair edits from semiorders in expectation, forcing induced 2+2 and 3+1 densities to vanish. Nondegenerate Minkowski diamonds have positive 2+2 probability. This obstruction concerns their precise sampling limit, not every local or metric limit.",
    equations: [
      {
        label: "Exact precursor transition",
        expression: "T(C,S) = pᵐ(1 − p)ⁿ⁻ˢ",
        explanation:
          "For a specified precursor down-set S with s events and m maxima in an n-event parent, choose all maxima, exclude all events outside S, and sum over redundant ancestral choices.",
      },
      {
        label: "Exact d = 2 reference",
        expression: "E[t₂₂] = 1/24 ≈ 4.1667%",
        explanation:
          "In the two-ranking representation of a uniform d = 2 diamond, exactly one of 24 four-event permutations has two isolated two-chains.",
      },
      {
        label: "Fixed-p asymptotic obstruction",
        expression: "E[t₂₂(N)] ≤ 3(1 − p) / [(N − 1)p²] → 0",
        explanation:
          "The bound may be loose at the tested sizes. It neither predicts a monotone finite trajectory nor says N ≤ 512 is already asymptotic.",
      },
      {
        label: "Deliberately misleading control",
        expression: "E[t₂₂] = ¾q²(1 − q)² = 1/24;  H ≤ 2",
        explanation:
          "Independent fair lower/upper labels and q = (1 − √(1 − 4/(3√2)))/2 match the expectation at every size, while all open intervals are empty and t₃₁ = 0.",
      },
    ],
    limitations: [
      "The primary maximum-error bands span 48 entries; pointwise 95% intervals in other charts are different quantities. Bootstrap simultaneous coverage remains approximate.",
      "Both the genuine d = 2 reference and the artificial matched height-two control passed their separate eight-entry screens; passing is insufficient.",
      "Adverse reference results remain: d = 2, N = 32 was falsely rejected by the secondary TV rule; d = 2, N = 512 local dimension was 2.01985 [2.00740, 2.03278], excluding 2 pointwise.",
      "Sparse intervals and out-of-domain inversions stay unavailable. A zero-width empirical interval alone cannot establish an exact identity.",
      "The known almost-semiorder theorem excludes this specified classical route and sampling target, not all emergent-spacetime theories.",
    ],
    sources: [
      {
        label: "Full growth results",
        path: "docs/BACKGROUND_FREE_GROWTH_RESULTS.md",
      },
      {
        label: "Registered protocol",
        path: "docs/BACKGROUND_FREE_GROWTH_PROTOCOL.md",
      },
      {
        label: "Workload and fresh-seed amendment",
        path: "docs/BACKGROUND_FREE_GROWTH_WORKLOAD.md",
      },
      {
        label: "Exact derivations and no-go scope",
        path: "docs/BACKGROUND_FREE_GROWTH_THEORY.md",
      },
      {
        label: "Primary simultaneous-band results",
        path: "docs/experiments/background-free-growth-v1/primary.csv",
      },
      {
        label: "Global pointwise results",
        path: "docs/experiments/background-free-growth-v1/global.csv",
      },
      {
        label: "Python intrinsic growth rule",
        path: "src/causal_lab/growth.py",
      },
      {
        label: "Rideout & Sorkin: classical sequential growth",
        path: "https://arxiv.org/abs/gr-qc/9904062",
      },
      {
        label: "Brightwell & Georgiou: continuum-limit restriction",
        path: "https://nicholasgeorgiou.webspace.durham.ac.uk/wp-content/uploads/sites/199/2021/04/contlim.pdf",
      },
    ],
  },
  {
    id: 6,
    slug: "quantum-information",
    title: "Can quantum information reveal space?",
    shortTitle: "Read quantum relationships",
    question:
      "Can relationships between quantum subsystems reveal geometry beyond the interactions already supplied to the model?",
    analogy:
      "A pattern of shared information can reveal who is connected, much as shared messages reveal a communication network. Recovering the wiring does not explain why that wiring forms a physical space.",
    hypothesis:
      "Mutual-information neighborhoods might show reproducible proximity beyond supplied couplings, while physical null states and exact counterexamples could falsify a geometric advancement claim.",
    setup:
      "Use transverse-field Ising systems with 6, 8 and 10 matter qubits: homogeneous all-to-all couplings, random all-to-all couplings, and a randomly relabeled chain whose locality is explicitly supplied. Infer from mutual information alone; evaluate against withheld couplings, perturbations, phase-scrambled states and exact controls.",
    assumptions: [
      "The tensor factorization, Hamiltonian, state preparation and external simulation time are supplied; no coordinates are needed to supply interactions.",
      "Fields h = 0.5, 1 and 2, three independent batches, and eight realizations per batch were fixed before primary execution.",
      "Fields, perturbations, phase scrambles and time snapshots from one realization are dependent branches, not fresh independent samples.",
      "Mutual information measures total correlation. Pair entanglement, operational signalling and geometric distance are different quantities.",
    ],
    measured:
      "1,818 state records, including 873 ground-state solves, with zero numerical failures. At h = 1, each size has 24 independent chain realizations; all 72 recover every supplied chain bond.",
    found:
      "The h = 1 chain has AUC = 1 and edge recall = 1 in all 72 cases; the multiplicity-adjusted exact success-probability lower bound is 0.84316 at each size. Random all-to-all models have stable proximity rankings, but the required advantage over physical phase-scrambled controls fails at n = 6 and 10.",
    survived:
      "Quantum correlations can recover supplied interaction structure and characterize finite proximity. The exact symmetric ground state has no distinguishable pair neighborhoods; sign gauges and multipartite examples expose information that pair summaries cannot identify.",
    failed:
      "No limited GO for geometric emergence. Nominal 95% bootstrap intervals covered only 365/400 independent calibration means, or 91.25%, so those intervals remain descriptive. Supplied-chain bond recovery also deteriorates at h = 0.5 as size grows.",
    unresolved:
      "A stable ranking is not a metric, a dimension or a controlled continuum limit. These fixed-interaction systems do not establish independent effective locality, emergent time, gravity or spacetime.",
    next:
      "Experiment 7 then made the links quantum degrees of freedom and tested operational influence under one frozen dynamical law. It was the final experiment, not the start of another search for better-looking networks.",
    explorer:
      "Two qubits can share information without being neighbors in a physical space. Our method recognized every bond in the supplied chain at the registered field, but other states also produced convincing diagrams. The controls kept that visual resemblance separate from evidence of geometry.",
    engineer:
      "Partial traces give one- and two-qubit density matrices; their entropies produce mutual information. Inference receives only that matrix and returns the full MDS spectrum, while a separate evaluator sees couplings and chain labels. Three distance floors, fractional tie handling, independent seeds and replay prevent hidden choices from becoming evidence. Shortest-path closure imposes triangle inequalities and can retain zero-distance degeneracy.",
    researcher:
      "For fixed finite n and weak Ising couplings, leading mutual information depends on Jᵢⱼ², so interaction reconstruction is expected. Perron–Frobenius gives a unique symmetric finite ground state for the homogeneous model at h > 0. Physical phase scrambles preserve all computational-basis probabilities but change quantum correlations. The bootstrap calibration failure invalidates a nominal coverage interpretation; the separate chain success gate uses exact binomial bounds. No MDS participation rank is interpreted as spacetime dimension.",
    equations: [
      {
        label: "Supplied fixed interaction law",
        expression: "H = −h Σᵢ Xᵢ − Σᵢ<ⱼ Jᵢⱼ ZᵢZⱼ",
        explanation:
          "The chain, homogeneous and random coupling matrices are different supplied microscopic assumptions. A hidden label permutation removes coordinate access, not the chain's imposed locality.",
      },
      {
        label: "Total pair correlation",
        expression: "I(i:j) = S(ρᵢ) + S(ρⱼ) − S(ρᵢⱼ)",
        explanation:
          "Entropy uses base-two logarithms. A Bell pair has I = 2 bits; a GHZ pair has I = 1 bit but zero pair negativity. Correlation alone is not a signal.",
      },
      {
        label: "An assumed dissimilarity, not an automatic metric",
        expression: "dᵢⱼ = −ln[max(I(i:j), ε)/2]",
        explanation:
          "Bell partners have zero distance despite being distinct subsystems, and a purified-AND counterexample violates triangle inequalities. A floor or layout does not repair the physical interpretation.",
      },
    ],
    limitations: [
      "The 1,818 records are not 1,818 independent realizations. Perturbations, fields, cuts and snapshots share a realization.",
      "The 91.25% calibration coverage failure is preserved; deterministic replay does not turn descriptive bootstrap intervals into calibrated guarantees.",
      "The h = 0.5 chain failure shows that a genuinely supplied local Hamiltonian can fail an information-based reconstruction criterion.",
      "Bell, GHZ and phase-scrambled controls expose degeneracies. Attractive projections and a small cut-law defect do not establish connected geometry.",
      "No feedback law was invented to improve the result. The completed programme's stopping decision is in the final synthesis.",
    ],
    sources: [
      { label: "Quantum results and uncertainty", path: "docs/QUANTUM_EMERGENCE_RESULTS.md" },
      { label: "Registered quantum protocol", path: "docs/QUANTUM_EMERGENCE_PROTOCOL.md" },
      { label: "Quantum derivations and primary references", path: "docs/QUANTUM_EMERGENCE_THEORY.md" },
      { label: "Archived quantum summary", path: "docs/experiments/quantum-information-v1/summary.csv" },
      { label: "Retained calibration failure", path: "docs/experiments/quantum-information-v1/calibration.json" },
      { label: "Independent state audit", path: "docs/experiments/quantum-information-v1/state_audit.json" },
      { label: "MI-only inference implementation", path: "src/causal_lab/quantum_geometry.py" },
    ],
  },
  {
    id: 7,
    slug: "dynamical-locality",
    title: "Can changing quantum links create locality?",
    shortTitle: "Test dynamical locality",
    question:
      "Can a permutation-invariant quantum law organize changing interaction links into persistent neighborhoods that support operationally local influence?",
    analogy:
      "Imagine a communication network whose switches can change as messages pass. The test is whether that changing network creates persistent neighborhoods, not whether a drawing of one switch configuration resembles a map.",
    hypothesis:
      "One registered quantum-link Hamiltonian might produce stable connected Born laws and concentrated, perturbation-stable target responses that improve over frozen links. Joint failure would reject this finite benchmark.",
    setup:
      "Evolve all matter and link qubits coherently at N = 4 and 5. Test six fixed parameter settings with symmetric preparations and 12 independently sampled exchangeable preparations per cell. Apply a local Pauli-Y intervention after age 2 and compare target reduced states with a matched unperturbed evolution.",
    assumptions: [
      "h = g = U = 1, μ ∈ {2, 0.1, −2}, Γ ∈ {0.25, 1}; no outcome-based parameter tuning or connectivity reward.",
      "Matter/link factorization, complete possible-pair incidence, degree costs and external time are supplied. Coordinate-free does not mean structure-free.",
      "A quantum link superposition is not a realized classical graph. Exact Born enumeration and unselected illustration draws have different roles.",
      "Each whole exchangeable preparation is one independent unit. Source-target pairs, times, perturbations and Born outcomes are dependent.",
    ],
    measured:
      "168 preparation bundles: 144 independent exchangeable preparations and 24 deterministic symmetric preparations; 12 ground states, 12 exact N = 4 Gibbs laws, 36 independent-link controls and all 1,088 labeled N = 4/5 classical graphs. No numerical failures or missing units.",
    found:
      "All twelve parameter/size cells have 0/12 joint successes. The simultaneous exact binomial upper bound is 0.402190, below the required success probability 0.8. Only 5/144 exchangeable preparations pass the connectedness condition across all late ages; none passes both late Born-law stability limits.",
    survived:
      "The links develop correlated Born laws, and nonselective measurement changes subsequent probabilities. A supplied static chain validates the operational response assay. These useful effects survive the model's failed advancement test.",
    failed:
      "NO-GO for the registered finite-system, unconditioned locality benchmark. Every parameter setting fails at both tested sizes. No N = 5 preparation passes the locality-concentration condition, although small Γ perturbations often preserve rankings.",
    unresolved:
      "Four and five vertices cannot settle geometric scaling, thermodynamic symmetry breaking or every graph-adapted relational instrument. The result is not a universal impossibility theorem for this Hamiltonian or emergent spacetime.",
    next:
      "The programme is closed. Final conclusion B: useful mathematical/computational research, but insufficient evidence to pursue the physical hypothesis through more simulations. Read the final synthesis; no Experiment 8 or replacement Hamiltonian is proposed.",
    explorer:
      "We changed one matter qubit and measured how distinguishable another became. That tests influence rather than shared information. A known chain gave the expected nearby-to-distant response, but the evolving quantum-link model failed its registered test. Some measured graphs look structured; that alone is not an emergent space.",
    engineer:
      "The full Hilbert space has Q = N + N(N − 1)/2 qubits: 10 at N = 4 and 15 at N = 5. Exact Born probabilities enumerate 64 and 1,024 graphs. Independent dense/static and state audits verify reduced-state trace distance, conservation, graph nulls and semantic seeds. A complete replay reproduced all 238 deterministic scientific artifacts byte for byte; it is computational reproducibility, not a new preparation cohort.",
    researcher:
      "A local unitary changes no other reduction at zero delay. The registered Y intervention probes the aged joint state; its linear response depends on ⟨nᵢⱼZᵢXⱼ⟩ and ⟨nᵢⱼZᵢYⱼ⟩, not edge occupation alone. Symmetric preparations retain equal labeled target responses, while relational Born structure remains possible. Exact two-sided Clopper–Pearson intervals use family size 12 and α = 0.05. The additional N = 5 degree-null GO gate is path-selective; the primary C/L/T/D rejection does not depend on it.",
    equations: [
      {
        label: "One frozen quantum-link law",
        expression: "H = −hΣᵢXᵢ − gΣᵢ<ⱼnᵢⱼZᵢZⱼ − ΓΣₑXₑ + μΣₑnₑ + UΣᵢDᵢ(Dᵢ−1)/2",
        explanation:
          "nₑ = (I − Zₑ)/2 and Dᵢ sums incident link occupations. The degree cost already supplies an energetic preference; no loop, target-dimension or connectivity reward was added.",
      },
      {
        label: "Operational target response",
        expression: "Rᵢ→ⱼ(τ) = ½ ‖ρⱼ[U(τ)Yᵢψ(2)] − ρⱼ[U(τ)ψ(2)]‖₁",
        explanation:
          "Matched states evolve with the same Hamiltonian. At zero delay, every other target is unchanged even if the aged state is entangled. This is not a correlation-derived distance.",
      },
      {
        label: "Simultaneous finite-cohort rejection",
        expression: "pupper = 1 − (0.05/24)^(1/12) = 0.402190 < 0.8",
        explanation:
          "Each of twelve cells has zero joint successes in twelve independent preparations. The bound applies to the registered population and joint screen, not every possible definition of locality.",
      },
    ],
    limitations: [
      "N = 6 quantum execution was excluded by the registered timing policy; no partial cohort or favorable parameter subset was substituted.",
      "Twelve preparations per cell cannot certify GO even with all successes. They do reject the observed large failure; continuum behavior remains unresolved.",
      "At N = 5 the extra degree-null connectivity gain of 0.1 requires at least 0.7 probability on P5 paths. This finite-size selection bias does not cause the primary NO-GO.",
      "Averaging graph-conditioned trace distances differs from the trace distance of averaged target states. Independent Born snapshots are not persistent graph trajectories.",
      "No physical spacetime, emergent time, gravitational equation or black-hole result follows. Programme conclusion B stops further model exploration without claiming universal impossibility.",
    ],
    sources: [
      { label: "Final dynamical results and decision", path: "docs/DYNAMICAL_LOCALITY_RESULTS.md" },
      { label: "Registered dynamical protocol", path: "docs/DYNAMICAL_LOCALITY_PROTOCOL.md" },
      { label: "Quantum-link theory and literature", path: "docs/DYNAMICAL_LOCALITY_THEORY.md" },
      { label: "Frozen workload and power limits", path: "docs/DYNAMICAL_LOCALITY_WORKLOAD.md" },
      { label: "Primary advancement data", path: "docs/experiments/dynamical-quantum-locality-v1/advancement.csv" },
      { label: "Independent numerical audit", path: "docs/experiments/dynamical-locality-independent-audit.json" },
      { label: "Complete frozen replay", path: "docs/experiments/dynamical-locality-replay-audit.json" },
      { label: "Quantum-link implementation", path: "src/causal_lab/dynamical_core.py" },
      { label: "Final synthesis and programme closure", path: "docs/FINAL_RESEARCH_SYNTHESIS.md" },
    ],
  },
];

export const claims: Claim[] = [
  {
    id: "temporal-information",
    title: "Causal order contains recoverable temporal information",
    status: "supported",
    precise:
      "Longest-chain length, together with known sampling density, estimates proper time in the specified uniform 1+1D flat-diamond model.",
    evidence:
      "Established asymptotics derive the estimator. The 4,200-trial study found decreasing endpoint bias across its density range, with all 21 mean-bias intervals still below zero.",
    assumptions:
      "Known uniform Poisson density, flat 1+1D diamond, strict precedence, and interior-only chain counts.",
    scope:
      "Supported within this sampling model. This is reconstruction from supplied geometry, not creation of time or a physical measurement of spacetime microstructure.",
    experiments: [1],
    sources: [
      { label: "Time results", path: "docs/FINITE_DENSITY_RESULTS.md" },
      { label: "Derivation", path: "docs/THEORY.md" },
      {
        label: "Primary trials",
        path: "docs/experiments/finite-density-scaling-v1/raw.csv",
      },
    ],
  },
  {
    id: "dimension-information",
    title: "Causal order contains dimension-sensitive information",
    status: "supported",
    precise:
      "Ordering fractions and conditional local laws encode dimension under specified uniform flat-spacetime sampling assumptions.",
    evidence:
      "At N = 256, all 200 held-out samples in each of d = 2, 3, 4 received the correct label. Local slab estimates recovered dimensions despite global boundary bias.",
    assumptions:
      "The global formula assumes an Alexandrov interval. The local law assumes a causally convex flat region and appropriate pooled-count estimation.",
    scope:
      "A reference-equivalent dimension on an arbitrary network is not its physical dimension. Precision within a model does not certify the model.",
    experiments: [2, 4],
    sources: [
      {
        label: "Dimension results",
        path: "docs/DIMENSION_RECONSTRUCTION_RESULTS.md",
      },
      {
        label: "Local results",
        path: "docs/LOCAL_CAUSAL_STRUCTURE_RESULTS.md",
      },
      {
        label: "Dimension data",
        path: "docs/experiments/dimension-reconstruction-v1/summary.csv",
      },
    ],
  },
  {
    id: "one-statistic",
    title: "A single dimension statistic certifies geometry",
    status: "falsified",
    precise:
      "Matching the flat-diamond ordering fraction is sufficient to establish that an arbitrary order has the required geometric sampling structure.",
    evidence:
      "All 1,800 calibrated two-layer controls in Experiment 2 passed the fraction detector while having height at most two and empty open intervals. A 20-event outward star has r = 0.1 and therefore returns d = 4 without establishing geometry.",
    assumptions:
      "The rejected claim treats agreement with one statistic as a sufficient certificate, rather than a necessary diagnostic.",
    scope:
      "The counterexamples refute the sufficiency of this statistic. They do not refute causal geometry or dimension reconstruction for correctly specified inputs.",
    experiments: [2, 3],
    sources: [
      {
        label: "Adversarial dimension evidence",
        path: "docs/DIMENSION_RECONSTRUCTION_RESULTS.md",
      },
      {
        label: "Raw controls",
        path: "docs/experiments/dimension-reconstruction-v1/raw.csv",
      },
    ],
  },
  {
    id: "selected-statistics",
    title: "Selected summaries uniquely determine an arbitrary order",
    status: "falsified",
    precise:
      "The global and extended local summaries measured in these studies form a complete invariant of all finite causal orders.",
    evidence:
      "The ten-event witness has identical old summaries but different connectivity and 2+2 counts. A stronger postregistration 12-event pair matches the entire extended measured vector yet has comparability components [12] versus [6, 6].",
    assumptions:
      "The claim concerns these selected summaries and unrestricted finite orders, including height-two orders with no nonempty intervals.",
    scope:
      "This exact nonidentifiability does not rule out reconstruction with more information and additional geometric assumptions. Matching missing conditional estimates is not agreement with a reference law.",
    experiments: [3, 4],
    sources: [
      {
        label: "Exact old-summary witnesses",
        path: "docs/experiments/adversarial-geometry-v1/exact_counterexamples.json",
      },
      {
        label: "Exact extended-summary witness",
        path: "docs/experiments/local-causal-structure-v1/exact_counterexample.json",
      },
      {
        label: "Proof and scope",
        path: "docs/LOCAL_CAUSAL_STRUCTURE_RESULTS.md",
      },
    ],
  },
  {
    id: "classical-route",
    title: "The studied classical growth route reaches our Minkowski target",
    status: "falsified",
    precise:
      "Transitive percolation, or ordinary CSG in the specified theorem’s class, has the required nondegenerate d ≥ 2 Minkowski limit under uniform finite-suborder sampling.",
    evidence:
      "All six tested fixed-p families failed the registered finite signature. Independently, established almost-semiorder restrictions force 2+2 and 3+1 densities to vanish, while the Minkowski target has positive 2+2 probability.",
    assumptions:
      "Nonnegative CSG couplings with t₀ or t₁ positive; expected probabilities of every uniformly sampled finite labeled suborder; an atomless ordered-probability-space limit where applicable.",
    scope:
      "A model-specific no-go for a precise sampling limit. It does not cover arbitrary altered dynamics, every local scaling limit, quantum models, or all possible emergent spacetime.",
    experiments: [5],
    sources: [
      {
        label: "Primary finite-signature data",
        path: "docs/experiments/background-free-growth-v1/primary.csv",
      },
      {
        label: "Exact restriction and assumptions",
        path: "docs/BACKGROUND_FREE_GROWTH_THEORY.md",
      },
      {
        label: "Original continuum-limit theorem",
        path: "https://nicholasgeorgiou.webspace.durham.ac.uk/wp-content/uploads/sites/199/2021/04/contlim.pdf",
      },
    ],
  },
  {
    id: "quantum-reconstruction",
    title: "Quantum correlations can recover supplied interaction structure",
    status: "supported",
    precise:
      "MI-only inference recovers the supplied hidden-label chain in the registered h = 1 finite-system benchmark.",
    evidence:
      "All 72 independent chain realizations at n = 6, 8 and 10 have AUC = 1 and bond recall = 1. Each size has 24/24 successes and exact multiplicity-adjusted lower bound 0.84316 > 0.8.",
    assumptions:
      "Specified transverse-field Ising ground states, supplied nearest-neighbor couplings, h = 1, three sizes, and a separate evaluator with access to hidden chain labels.",
    scope:
      "Reconstruction of supplied locality, not creation of physical space. Recovery deteriorates at h = 0.5, and the failed bootstrap calibration does not validate unrelated descriptive intervals.",
    experiments: [6],
    sources: [
      { label: "Quantum chain results", path: "docs/QUANTUM_EMERGENCE_RESULTS.md" },
      { label: "Archived quantum summary", path: "docs/experiments/quantum-information-v1/summary.json" },
      { label: "Independent quantum statistics audit", path: "docs/experiments/quantum-information-v1/statistics_audit.json" },
    ],
  },
  {
    id: "fixed-quantum-emergence",
    title: "The fixed quantum models meet their geometric advancement criteria",
    status: "falsified",
    precise:
      "The registered fixed-interaction models pass every condition required for limited geometric advancement beyond supplied coupling structure.",
    evidence:
      "Random all-to-all ground states pass the descriptive proximity screen but fail required physical phase-scramble advantages at n = 6 and 10. Homogeneous ground states have no distinguished pair neighborhoods, and exact Bell/GHZ/AND controls expose interpretation failures.",
    assumptions:
      "The registered finite sizes, state families, field values, inference maps, nulls and advancement criteria. Bootstrap intervals have failed nominal coverage and remain descriptive.",
    scope:
      "Failure of these advancement criteria is not a theorem against every geometric interpretation or every quantum state. Stable rankings remain useful diagnostics; no independent geometric mechanism is established.",
    experiments: [6],
    sources: [
      { label: "Quantum decision and calibration limits", path: "docs/QUANTUM_EMERGENCE_RESULTS.md" },
      { label: "Physical-null comparison data", path: "docs/experiments/quantum-information-v1/summary.csv" },
      { label: "Exact quantum counterexamples", path: "docs/QUANTUM_EMERGENCE_THEORY.md" },
    ],
  },
  {
    id: "dynamical-locality",
    title: "The quantum-link model passes the registered locality benchmark",
    status: "falsified",
    precise:
      "At one of six frozen parameter settings, the specified exchangeable preparations pass the joint finite unconditioned locality screen with probability at least 0.8 across all tested sizes.",
    evidence:
      "Every N = 4/5 parameter cell has 0/12 joint successes. Its simultaneous exact binomial upper bound is 0.402190 < 0.8. Controls and independent audits pass, and the complete seeded replay reproduces 238 scientific artifacts.",
    assumptions:
      "One frozen Hamiltonian, N = 4 and 5, twelve independent preparations per cell, registered ages/delays and Y intervention. C/L/T/D measure connectedness, concentration, stability and improvement over initially frozen links.",
    scope:
      "Finite-model NO-GO for this unconditioned screen; geometric scaling and broader relational protocols remain unresolved. Final programme conclusion B closes this computational exploration without asserting universal impossibility.",
    experiments: [7],
    sources: [
      { label: "Finite-model decision and qualifications", path: "docs/DYNAMICAL_LOCALITY_RESULTS.md" },
      { label: "Primary joint-success bounds", path: "docs/experiments/dynamical-quantum-locality-v1/advancement.csv" },
      { label: "Independent primary audit", path: "docs/experiments/dynamical-locality-independent-audit.json" },
      { label: "Programme conclusion B", path: "docs/FINAL_RESEARCH_SYNTHESIS.md" },
    ],
  },
  {
    id: "emergence-impossible",
    title: "All possible emergent-spacetime theories are impossible",
    status: "untested",
    precise:
      "No microscopic quantum or mathematical mechanism can produce effective spacetime.",
    evidence:
      "None of these seven experiments tests this universal claim. They examine supplied geometric laws, one classical growth route, fixed quantum interactions and one finite quantum-link benchmark. Their failures have explicit model, state and limit conditions.",
    assumptions:
      "A universal impossibility claim would need arguments covering every candidate mechanism and a precise meaning of emergence. This research does not supply them.",
    scope:
      "The broader emergence hypothesis remains open. Programme conclusion B stops this computational exploration for insufficient physical evidence; it does not assert that every other route fails.",
    experiments: [1, 2, 3, 4, 5, 6, 7],
    sources: [
      {
        label: "Growth conclusion and open requirements",
        path: "docs/BACKGROUND_FREE_GROWTH_RESULTS.md",
      },
      {
        label: "Continuum interpretation",
        path: "docs/LOCAL_CAUSAL_STRUCTURE_CONTINUUM.md",
      },
      { label: "Final programme synthesis", path: "docs/FINAL_RESEARCH_SYNTHESIS.md" },
    ],
  },
  {
    id: "physical-discreteness",
    title: "Physical spacetime is fundamentally discrete",
    status: "untested",
    precise:
      "The events in these finite computer models represent actual indivisible constituents of our universe.",
    evidence:
      "The repository contains mathematical models and numerical experiments, not observations of microscopic spacetime. Discreteness is supplied to the models as a construction.",
    assumptions:
      "A physical claim requires a theory connected to measurable predictions and evidence that distinguishes it from alternatives.",
    scope:
      "Drawing dots and reproducing geometric statistics cannot establish the ontology of physical spacetime. The microscopic depiction in the introduction is explicitly speculative.",
    experiments: [1, 2, 3, 4, 5, 6, 7],
    sources: [
      { label: "Interpretation boundaries", path: "README.md" },
      { label: "Research log", path: "docs/RESEARCH_LOG.md" },
      { label: "Final synthesis and physical limits", path: "docs/FINAL_RESEARCH_SYNTHESIS.md" },
    ],
  },
  {
    id: "singularity-resolved",
    title: "Our models resolve black-hole singularities",
    status: "untested",
    precise:
      "These causal-order or quantum models provide a validated replacement for the classical black-hole singularity and recover appropriate gravitational dynamics.",
    evidence:
      "No black-hole solution, gravitational field equation, curved interior or empirically discriminating prediction is established in these seven studies.",
    assumptions:
      "Such a result would require controlled curved and continuum limits, consistent dynamics, exterior and horizon behavior, and a justified treatment of singular behavior.",
    scope:
      "Singularities motivate deeper theories. The event horizon is not itself a curvature singularity in the classical Schwarzschild solution, and the water analogy supplies no resolution.",
    experiments: [],
    sources: [
      { label: "Limits of the initial model", path: "docs/THEORY.md" },
      {
        label: "Missing gravitational requirements",
        path: "docs/ADVERSARIAL_GEOMETRY_RESULTS.md",
      },
      {
        label: "Finkelstein: the regular horizon",
        path: "https://doi.org/10.1103/PhysRev.110.965",
      },
      { label: "Final quantum-link limitations", path: "docs/DYNAMICAL_LOCALITY_RESULTS.md" },
    ],
  },
];

export const concepts: Concept[] = [
  {
    id: "causality",
    title: "Events & causal relationships",
    intro:
      "An event is something that happens. A causal relation says one event could influence another.",
    detail:
      "A point in a spacetime diagram represents a time and place, not a particle. In this lab, strict future timelike separation defines precedence. Unrelated events can both exist without either preceding the other.",
    equation: "a ≺ b: event a lies in the causal past of b",
    experiment: 1,
    sources: [{ label: "Order conventions", path: "docs/THEORY.md" }],
  },
  {
    id: "light-cones",
    title: "Light cones",
    intro: "Light sets the boundary of what an event can influence.",
    detail:
      "In units where c = 1, the future of a flat-spacetime event satisfies Δt ≥ |Δx|. The lab uses strict timelike precedence, Δt > |Δx|; exact null ties have probability zero for the continuous random generators. In d > 2, the familiar V-shaped drawing is a section or projection.",
    equation: "Δt > ‖Δx‖, with c = 1",
    experiment: 1,
    sources: [
      { label: "Flat causal relation", path: "docs/DIMENSION_THEORY.md" },
    ],
  },
  {
    id: "proper-time",
    title: "Proper time",
    intro: "Proper time is the time a clock measures along its own path.",
    detail:
      "For a timelike inertial separation in flat spacetime, time and spatial displacement combine as τ² = Δt² − |Δx|². For the diamond endpoints at rest in the chosen frame, τ = T. A chain is a statistical estimator, not a clock with an exact finite-step tick.",
    equation: "τ² = Δt² − ‖Δx‖²",
    experiment: 1,
    sources: [{ label: "Proper-time reconstruction", path: "docs/THEORY.md" }],
  },
  {
    id: "dimensions",
    title: "Spacetime dimensionality",
    intro:
      "Count time as a dimension too: our familiar description has one time and three spatial dimensions.",
    detail:
      "The ordering-fraction formula distinguishes known uniform flat diamonds in d = 2, 3 and 4. It says nothing automatic about the physical dimension of an arbitrary graph. A two-dimensional layout can display a high-dimensional sample’s causal relationships without displaying its geometry literally.",
    equation: "p(2) = 1/2; p(3) = 8/35; p(4) = 1/10",
    experiment: 2,
    sources: [
      { label: "Dimension assumptions", path: "docs/DIMENSION_THEORY.md" },
    ],
  },
  {
    id: "diamonds",
    title: "Causal diamonds",
    intro:
      "A causal diamond contains events after one endpoint and before another.",
    detail:
      "Intersect the future of the lower endpoint with the past of the upper endpoint. Its diamond shape is specific to a 1+1D spacetime drawing. Uniform sampling means uniform physical spacetime volume, not arbitrary dot placement or uniform time.",
    equation: "I(a,b) = future(a) ∩ past(b)",
    experiment: 1,
    sources: [
      { label: "Uniform diamond sampling", path: "docs/DIMENSION_THEORY.md" },
    ],
  },
  {
    id: "orders",
    title: "Partial orders",
    intro:
      "Some events can be ordered relative to one another; other pairs remain incomparable.",
    detail:
      "A strict partial order has no self-relations and is transitive. If a precedes b and b precedes c, a must precede c. A directed acyclic graph can record only direct edges; its transitive closure is the full order used by these experiments.",
    equation: "a ≺ b and b ≺ c ⇒ a ≺ c; never a ≺ a",
    experiment: 3,
    sources: [
      {
        label: "Strict order definitions",
        path: "docs/BACKGROUND_FREE_GROWTH_THEORY.md",
      },
    ],
  },
  {
    id: "chains",
    title: "Longest chains",
    intro:
      "A chain follows events that are all causally ordered. Its height is the longest such sequence.",
    detail:
      "Count events, not edges. A total order of N events has height N; a nonempty antichain has height one. In a sprinkled 1+1D diamond, the large-count height grows like 2√N. Applying that scaling to a different order does not assign it a physical time.",
    equation: "H = max number of events in a chain",
    experiment: 1,
    sources: [
      { label: "Chain estimator and controls", path: "docs/THEORY.md" },
    ],
  },
  {
    id: "patterns",
    title: "Induced 2+2 & 3+1 patterns",
    intro: "Four events can reveal relationships that an average hides.",
    detail:
      "An induced 2+2 has exactly two disjoint two-event chains and no cross-relations. An induced 3+1 has a three-event chain and a fourth event incomparable with all three. “Induced” means retaining every relation among the selected events, including relations inherited through omitted events.",
    equation: "tF = nF / choose(N, 4)",
    experiment: 5,
    sources: [
      {
        label: "Exact motif definitions",
        path: "docs/BACKGROUND_FREE_GROWTH_THEORY.md",
      },
    ],
  },
  {
    id: "closure",
    title: "Transitive closure",
    intro:
      "Causal ancestry is inherited: an ancestor of your ancestor is also your ancestor.",
    detail:
      "The growth rule chooses primitive edges, then adds all relationships implied by paths. A directly selected edge may itself be redundant. When thinning an existing order, keep the closed relation among surviving events rather than deleting paths and starting again.",
    equation: "a → b → c implies a ≺ c",
    experiment: 5,
    sources: [
      {
        label: "Growth and thinning rules",
        path: "docs/BACKGROUND_FREE_GROWTH_THEORY.md",
      },
    ],
  },
  {
    id: "randomness",
    title: "Why randomness can mimic geometry",
    intro:
      "Different recipes can produce the same selected statistics—and sometimes the same complete probability law.",
    detail:
      "A two-layer network can be tuned to match a pair fraction without matching height. More strongly, two independent uniform rankings have exactly the causal-order law of a uniform d = 2 diamond. Order-only analysis cannot identify which of these equivalent recipes supplied a sample.",
    equation: "same summary ≠ same order; same law ⇒ same order-only evidence",
    experiment: 3,
    sources: [
      {
        label: "Exact rank-law equivalence",
        path: "docs/ADVERSARIAL_GEOMETRY_THEORY.md",
      },
    ],
  },
  {
    id: "embedding",
    title: "Embedding versus physical spacetime",
    intro:
      "An embedding places a mathematical order inside a geometry while preserving its relationships.",
    detail:
      "A faithful geometric interpretation also needs an appropriate volume-sampling law and scale control. Showing that a finite order can be drawn, or even mathematically embedded, does not establish that nature uses it. The displayed graph positions are visual aids unless explicitly marked as generator coordinates.",
    equation: "a ≺ b ⇔ φ(a) lies before φ(b) in the proposed geometry",
    experiment: 4,
    sources: [
      {
        label: "Embedding and uniqueness requirements",
        path: "docs/LOCAL_CAUSAL_STRUCTURE_CONTINUUM.md",
      },
    ],
  },
  {
    id: "continuum",
    title: "Continuum limits",
    intro:
      "A smooth-looking picture is not yet a mathematical continuum limit.",
    detail:
      "Specify a sequence of models and what must converge. Experiment 5 examines probabilities of uniformly sampled finite suborders. Such a limit can forget sparse but persistent structure: fixed-p percolation approaches a chain sampling law even though its longest chain need not contain almost all events. Metric, local and dynamical limits are different questions.",
    equation: "For every finite Q: E[λ(Q; CN)] → λ(Q; C∞)",
    experiment: 5,
    sources: [
      {
        label: "Precise sampling-limit scope",
        path: "docs/BACKGROUND_FREE_GROWTH_THEORY.md",
      },
    ],
  },
  {
    id: "singularities",
    title: "Why singularities motivate deeper theories",
    intro:
      "A singularity signals a limit of a classical description; it does not tell us what replaces that description.",
    detail:
      "In the classical Schwarzschild solution, the event horizon is a causal boundary, not a curvature singularity; the central singular behavior is different. A complete treatment involves the extendibility of physical paths and spacetime geometry. These flat-order experiments neither model a black-hole interior nor resolve its singularity. A microscopic spacetime analogy remains speculation.",
    equation:
      "Classical limitation → open physical question, not a demonstrated microscopic answer",
    experiment: 5,
    sources: [
      {
        label: "Gravitational requirements not established",
        path: "docs/ADVERSARIAL_GEOMETRY_RESULTS.md",
      },
      { label: "Interpretation boundaries", path: "README.md" },
      {
        label: "Finkelstein: horizon versus singularity",
        path: "https://doi.org/10.1103/PhysRev.110.965",
      },
      {
        label: "Penrose: gravitational collapse and singularities",
        path: "https://doi.org/10.1103/PhysRevLett.14.57",
      },
    ],
  },
];
