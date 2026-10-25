# Independent Experiment 5 statistical review

Read-only review of the complete primary archive; no new generation, parameter selection or tracked-file changes.
Raw count aggregation and registered random streams were independently reconstructed without importing growth_statistics.

## Independent numerical audit

Checks: {'p22_point': 88, 'p22_ci': 88, 'global_point': 352, 'global_ci': 352, 'conditional_point': 1296, 'conditional_ci': 1296, 'tv_point': 216, 'tv_ci': 216, 'conditional_contrast_point': 486, 'conditional_contrast_ci': 486, 'primary_simultaneous_width': 1}. Total 4877; failures 0. Tolerance 2e-12 absolute/relative.
Primary common half-width reproduced: 0.001264661983448907. Scientific digest: `534c51d1745f4d370a87ced03b895b5ff935e3811a362f9349554b164f0a57da`.

This audit independently rebuilds whole-history strata, averages four thinnings before pooling, regenerates all shared reference/bootstrap arrays, and checks every reported conditional six-metric and TV point estimate/CI, paired conditional contrast, p22 pointwise CI and the joint primary width. It checks four global diagnostics in every cell. It is not an independent re-count of every raw causal matrix.

## Primary result

All six fixed-p settings fail the registered necessary finite signature. All 18 p22 levels at N128/256/512 contradict the d2 reference band; the failure does not depend only on drift or thinning criteria. Across the48 entries there are23 contradictions,19 equivalences and6 inconclusive outcomes. All54 batch-specific late-level means lie below the lower d2 practical-margin boundary. Every sampled p22 primary vector is nonconstant; no zero-event/constant safeguard was needed.

| p | p22 N32 | N64 | N128 | N256 | N512 (pointwise 95% CI) | 8 registered statuses |
|---|---:|---:|---:|---:|---|---|
| 0.005 | 8.5453745e-05 | 8.1660964e-05 | 0.00011594742 | 0.00017748334 | 0.00050552613 [0.0004864215, 0.00052534798] | FFFEEEEE |
| 0.01 | 0.00029025306 | 0.00042428945 | 0.00064571323 | 0.0017123952 | 0.0069558464 [0.0067794356, 0.0071208171] | FFFEIEEI |
| 0.02 | 0.0015202076 | 0.0022046657 | 0.0047661445 | 0.012641519 | 0.0097304516 [0.0095802068, 0.0098698597] | FFFFEEFE |
| 0.05 | 0.010653909 | 0.019415308 | 0.019909047 | 0.0060964369 | 0.0010331964 [0.0010082029, 0.0010591465] | FFFFIEFI |
| 0.1 | 0.033046846 | 0.022118383 | 0.0056015615 | 0.00086993878 | 0.00012148778 [0.00011885247, 0.00012415047] | FFFIEFIE |
| 0.3 | 0.0054166087 | 0.00082016724 | 0.00011160617 | 1.4003259e-05 | 1.7677483e-06 [1.714963e-06, 1.8179462e-06] | FFFEEEEE |

Status order: levels128/256/512, drift128→256, drift256→512, thinning128→64, thinning256→128, thinning512→256. E=within margin, F=contradicts, I=inconclusive, S=insufficient. These are registered finite-signature statuses, not geometric labels.

| p | late drift128→256 | drift256→512 | thinning128→64 | thinning256→128 | thinning512→256 | batch N512 p22 range |
|---|---:|---:|---:|---:|---:|---|
| 0.005 | 6.1535918e-05 | 0.00032804279 | 4.0707523e-05 | 6.2613267e-05 | 0.00032371989 | [0.00049328613, 0.00051738942] |
| 0.01 | 0.001066682 | 0.0052434512 | 0.00022229701 | 0.0010622913 | 0.0052493072 | [0.0067527625, 0.0071906141] |
| 0.02 | 0.0078753745 | -0.0029110674 | 0.0025485975 | 0.0078083152 | -0.0028935272 | [0.009467976, 0.0098909984] |
| 0.05 | -0.01381261 | -0.0050632404 | 0.00056579031 | -0.013803 | -0.0050632126 | [0.0010000263, 0.0010612153] |
| 0.1 | -0.0047316227 | -0.000748451 | -0.016521389 | -0.0047443169 | -0.00074905751 | [0.00011907526, 0.00012462573] |
| 0.3 | -9.7602907e-05 | -1.2235511e-05 | -0.00071236116 | -9.7479758e-05 | -1.2244196e-05 | [1.7261461e-06, 1.821402e-06] |

The single simultaneous half-width .0012646619834489074 applies to all 48 entries, before safeguards. Secondary pointwise intervals are often much narrower. Small drift does not establish the correct limiting value: p=.005 and .3 have five equivalent stability contrasts but all three level checks fail. Curves need not decrease at small N: .005 and .01 are still rising at512; .02 peaks at256; .05 peaks at128 over this grid. The fixed-p theorem is asymptotic and permits these finite crossovers.

## Complete N512 global diagnostics

| family / parameter | r [95% CI] | H [95% CI] | H/N | t22 | t31 [95% CI] | global reference-equivalent d | local reference-equivalent d |
|---|---|---|---:|---:|---|---|---|
| percolation 0.005 | 0.013965863 [0.013663363, 0.01428056] | 8.4791667 [8.28125, 8.6875] | 0.016560872 | 0.00050552613 | 0.00038401066 [0.00036661594, 0.00040305057] | 6.2861059 [6.2609298, 6.3098364] | 1.006805 [1.0057224624146914, 1.0078974422854428] |
| percolation 0.01 | 0.081406326 [0.079471034, 0.083284288] | 13.5625 [13.28125, 13.864583] | 0.026489258 | 0.0069558464 | 0.0045446413 [0.0043809817, 0.0047024231] | 4.2523514 [4.2254571, 4.2809433] | 1.0165042 [1.0157968295134427, 1.0172366127490533] |
| percolation 0.02 | 0.36207775 [0.35867894, 0.36583017] | 23.083333 [22.697917, 23.489583] | 0.045084635 | 0.0097304516 | 0.020942786 [0.020719623, 0.021181372] | 2.4230768 [2.4099544, 2.435204] | 1.0313337 [1.0305776490817897, 1.0320639774197229] |
| percolation 0.05 | 0.7544787 [0.7524139, 0.7565062] | 49.302083 [48.520833, 50.0625] | 0.096293132 | 0.0010331964 | 0.0048233285 [0.0047253748, 0.0049272017] | 1.4304604 [1.4265708, 1.4344308] | 1.0742185 [1.072575546686, 1.0756963509748698] |
| percolation 0.1 | 0.89756979 [0.89674846, 0.89837543] | 85.760417 [84.78099, 86.71901] | 0.16750081 | 0.00012148778 | 0.00061129439 [0.0005985227, 0.00062409811] | 1.1711003 [1.1697163, 1.1725118] | 1.1366723 [1.1338918502801376, 1.13933405309798] |
| percolation 0.3 | 0.98158466 [0.98137904, 0.98179214] | 202.55208 [200.9263, 204.18828] | 0.39560954 | 1.7677483e-06 | 9.9190592e-06 [9.5939117e-06, 1.0266201e-05] | 1.030123 [1.0297822, 1.0304608] | 1.2979484 [1.2903429904778392, 1.3050679016521984] |
| minkowski 2 | 0.5002064 [0.49794141, 0.5026265] | 40.5 [40.051823, 40.9375] | 0.079101562 | 0.041579179 | 0.083436231 [0.08302864, 0.083833342] | 1.9998123 [1.9933352, 2.0058582] | 2.0198519 [2.0073961837081757, 2.032781797969986] |
| minkowski 3 | 0.22975393 [0.2272176, 0.23230549] | 14.583333 [14.333333, 14.854427] | 0.028483073 | 0.017464585 | 0.025838137 [0.025498164, 0.026186512] | 2.9954394 [2.9819783, 3.0092195] | 3.0023533 [2.9805896114062724, 3.0241374804352326] |
| minkowski 4 | 0.099277086 [0.097165972, 0.10141865] | 8.0729167 [7.9375, 8.2083333] | 0.015767415 | 0.0048380845 | 0.0049069494 [0.0047406683, 0.005079627] | 4.0144909 [3.9895195, 4.0392066] | 4.0127872 [3.963332603421472, 4.063582674848886] |
| semiorder 0.25 | 0.56155967 [0.5600627, 0.56316183] | 4 [4, 4] | 0.0078125 | 0 | 0 [0, 0] | 1.8439098 [1.8400334, 1.8475476] | undefined [None, None] |
| matched_bipartite 0.38042684413094974 | 0.19005742 [0.18984318, 0.19026417] | 2 [2, 2] | 0.00390625 | 0.041636504 | 0 [0, 0] | 3.2268377 [3.2255069, 3.2282149] | undefined None |

At p=.3, r≈.9816 while H/N≈.3956. The known chain-sampling limit must not be described as H/N→1. The growth global and local inversions disagree strongly and are diagnostic calibrations, not discovered geometric dimensions.

Global inversions are missing for six of96 p=.005 prefixN32 orders; every other stochastic record has a defined global inversion. These six were retained as missing, not clipped or filled with a selected dimension. The two deterministic endpoints are recorded once each: at N512, p=0 has r=0,H=1,t22=t31=0 and undefined global dimension; p=1 has r=1,H=512,t22=t31=0 and global equivalent dimension1. They contribute no independent stochastic repetitions. The total chain has509 open intervals of interior size2; the antichain has none.

## All N512 conditional reference comparisons

The seven columns retain every candidate reference: connected2, motif22_4, connected4, connected8, motif22_8, joint8, tv4. Every growth/control candidate is reported, without selecting a best-fitting d.

| family / parameter | candidate d | conn2 | 22_m4 | conn4 | conn8 | 22_m8 | joint8 | TV4 |
|---|---:|---|---|---|---|---|---|---|
| percolation 0.005 | 2 | 0.99582726 F | 0.015879366 F | 0.96651245 F | 0.8131063 S | 0.11453929 S | 0.042536734 S | 0.88237469 F |
| percolation 0.005 | 3 | 0.99582726 F | 0.015879366 E | 0.96651245 F | 0.8131063 S | 0.11453929 S | 0.042536734 S | 0.92537299 F |
| percolation 0.005 | 4 | 0.99582726 F | 0.015879366 I | 0.96651245 F | 0.8131063 S | 0.11453929 S | 0.042536734 S | 0.98294845 F |
| percolation 0.01 | 2 | 0.98989232 F | 0.023996072 F | 0.94121709 F | 0.76274522 I | 0.13027162 F | 0.056314164 F | 0.82097339 F |
| percolation 0.01 | 3 | 0.98989232 F | 0.023996072 I | 0.94121709 F | 0.76274522 F | 0.13027162 F | 0.056314164 F | 0.90401084 F |
| percolation 0.01 | 4 | 0.98989232 F | 0.023996072 F | 0.94121709 F | 0.76274522 F | 0.13027162 F | 0.056314164 F | 0.98154417 F |
| percolation 0.02 | 2 | 0.98084731 F | 0.042720532 E | 0.89561569 F | 0.73462766 E | 0.13351713 F | 0.06092209 F | 0.71981918 F |
| percolation 0.02 | 3 | 0.98084731 F | 0.042720532 F | 0.89561569 F | 0.73462766 F | 0.13351713 F | 0.06092209 F | 0.90034908 F |
| percolation 0.02 | 4 | 0.98084731 F | 0.042720532 F | 0.89561569 F | 0.73462766 F | 0.13351713 F | 0.06092209 F | 0.97788242 F |
| percolation 0.05 | 2 | 0.9549006 F | 0.069749224 F | 0.81609755 F | 0.7339278 E | 0.11339064 F | 0.058000701 F | 0.56875396 F |
| percolation 0.05 | 3 | 0.9549006 F | 0.069749224 F | 0.81609755 F | 0.7339278 F | 0.11339064 F | 0.058000701 F | 0.88132334 F |
| percolation 0.05 | 4 | 0.9549006 F | 0.069749224 F | 0.81609755 F | 0.7339278 F | 0.11339064 F | 0.058000701 F | 0.95885667 F |
| percolation 0.1 | 2 | 0.9177234 F | 0.08301365 F | 0.75726376 F | 0.76994679 I | 0.089349237 F | 0.053941489 F | 0.49581964 F |
| percolation 0.1 | 3 | 0.9177234 F | 0.08301365 F | 0.75726376 F | 0.76994679 F | 0.089349237 F | 0.053941489 F | 0.84639355 F |
| percolation 0.1 | 4 | 0.9177234 F | 0.08301365 F | 0.75726376 F | 0.76994679 F | 0.089349237 F | 0.053941489 F | 0.92770016 F |
| percolation 0.3 | 2 | 0.82554914 F | 0.060931544 F | 0.75244252 F | 0.91220338 F | 0.038708352 E | 0.033023251 E | 0.4053956 F |
| percolation 0.3 | 3 | 0.82554914 F | 0.060931544 F | 0.75244252 F | 0.91220338 F | 0.038708352 F | 0.033023251 F | 0.76972893 F |
| percolation 0.3 | 4 | 0.82554914 F | 0.060931544 F | 0.75244252 F | 0.91220338 F | 0.038708352 F | 0.033023251 F | 0.87958999 F |
| minkowski 2 | 2 | 0.49260271 E | 0.041133257 E | 0.54111953 E | 0.71623954 E | 0.041405697 E | 0.029181134 E | 0.011025947 E |
| minkowski 3 | 3 | 0.22813669 E | 0.016035793 E | 0.16968909 E | 0.17469764 E | 0.01713879 E | 0.004617003 E | 0.021493939 E |
| minkowski 4 | 4 | 0.098929311 E | 0.0049614687 E | 0.038388016 E | 0.019694523 E | 0.0050238639 E | 0.00034918173 E | 0.010730248 E |
| semiorder 0.25 | 2 | 0 F | 0 F | 0 F | 0 F | 0 F | 0 F | 0.95833333 F |
| semiorder 0.25 | 3 | 0 F | 0 F | 0 F | 0 F | 0 F | 0 E | 0.69786667 F |
| semiorder 0.25 | 4 | 0 F | 0 E | 0 F | 0 E | 0 E | 0 E | 0.3938 F |
| matched_bipartite 0.38042684413094974 | 2 | undefined S | undefined S | undefined S | undefined S | undefined S | undefined S | undefined S |
| matched_bipartite 0.38042684413094974 | 3 | undefined S | undefined S | undefined S | undefined S | undefined S | undefined S | undefined S |
| matched_bipartite 0.38042684413094974 | 4 | undefined S | undefined S | undefined S | undefined S | undefined S | undefined S | undefined S |

Support below is identical across candidate dimensions. Each entry is three batch pairs (positive histories, total mean interval exposure). There are only32 histories per batch; the registered requirement is≥30 positive histories and exposure≥100 in each batch.

| family / parameter | m2 support | m4 support | m8 support |
|---|---|---|---|
| percolation 0.005 | (32,10627); (32,11272); (32,11001) | (32,2255); (32,2385); (32,2288) | (16,38); (17,68); (18,60) |
| percolation 0.01 | (32,61644); (32,61212); (32,63656) | (32,37055); (32,38099); (32,39958) | (32,7828); (32,8697); (32,9249) |
| percolation 0.02 | (32,124986); (32,124924); (32,122638) | (32,100693); (32,101758); (32,101019) | (32,49886); (32,50094); (32,50677) |
| percolation 0.05 | (32,97797); (32,96152); (32,97441) | (32,73585); (32,72453); (32,72662) | (32,44175); (32,43033); (32,43595) |
| percolation 0.1 | (32,63085); (32,63424); (32,63771) | (32,45237); (32,44801); (32,45195) | (32,29208); (32,29512); (32,29727) |
| percolation 0.3 | (32,28186); (32,28239); (32,28073) | (32,21650); (32,21727); (32,21535) | (32,17317); (32,17523); (32,17430) |
| minkowski 2 | (32,55198); (32,55066); (32,54996) | (32,45528); (32,45657); (32,45816) | (32,36229); (32,36246); (32,36296) |
| minkowski 3 | (32,64938); (32,64966); (32,64415) | (32,42513); (32,41870); (32,41500) | (32,24920); (32,24314); (32,24433) |
| minkowski 4 | (32,32894); (32,31680); (32,33213) | (32,16541); (32,15885); (32,16280) | (32,7132); (32,6793); (32,7207) |
| semiorder 0.25 | (32,7862); (32,8162); (32,8159) | (32,7764); (32,8245); (32,8129) | (32,7603); (32,7905); (32,7672) |
| matched_bipartite 0.38042684413094974 | (0,0); (0,0); (0,0) | (0,0); (0,0); (0,0) | (0,0); (0,0); (0,0) |

Small-p intervals can appear locally chainlike despite globally sparse orders: p=.005 gives connected2=.995827 and local d≈1.0068 while global d≈6.2861. p=.02 matches the d2 m4 2+2 margin and connected8 margin, but its complete m4 TV≈.7198 and other laws fail. At p=.3, the m8 2+2 and joint8 margins pass against d2 while the remaining five metrics fail. Single matching marginals therefore remain uninformative.

## Thinning and history comparisons

| family / parameter | Δr 512→256 [95% CI] | ΔH [95% CI] | Δt22 [95% CI] | unique conditional contrasts E/F/I/S over3sources×6metrics |
|---|---|---|---|---|
| percolation 0.005 | 0.0059976416 [0.0057199695, 0.0062967896] | 0.47395833 [0.3046875, 0.64322917] | 0.00032371989 [0.0003064656, 0.00034203118] | 1/0/0/17 |
| percolation 0.01 | 0.053577059 [0.052073466, 0.055138291] | 0.80729167 [0.6093099, 1.0052083] | 0.0052493072 [0.0051103959, 0.005386467] | 0/3/1/14 |
| percolation 0.02 | 0.23018448 [0.22693627, 0.23364126] | 2.671875 [2.390625, 2.9375651] | -0.0028935272 [-0.0032315412, -0.0025650634] | 0/9/0/9 |
| percolation 0.05 | 0.19472513 [0.19150764, 0.19810439] | 5.7786458 [5.3983724, 6.171875] | -0.0050632126 [-0.0052366313, -0.0049017818] | 0/15/0/3 |
| percolation 0.1 | 0.093347726 [0.091430181, 0.095273783] | 10.453125 [9.8619141, 11.096354] | -0.00074905751 [-0.00077897636, -0.00072084816] | 2/15/1/0 |
| percolation 0.3 | 0.017971303 [0.017528738, 0.018419008] | 20.854167 [20.01543, 21.747526] | -1.2244196e-05 [-1.2848008e-05, -1.1650631e-05] | 5/12/1/0 |
| minkowski 2 | 0.00072771459 [-0.0025308028, 0.0040844906] | -0.080729167 [-0.4688151, 0.3281901] | -0.00033971664 [-0.0010768369, 0.00039830367] | 16/0/2/0 |
| minkowski 3 | -7.6912275e-05 [-0.0032697032, 0.0031149491] | 0.18229167 [-0.015625, 0.390625] | -0.00012290961 [-0.00035207993, 0.00011982753] | 14/0/4/0 |
| minkowski 4 | -0.0010859471 [-0.0027855408, 0.00067427891] | -0.041666667 [-0.1796875, 0.109375] | -7.5170171e-06 [-0.00011837357, 0.00010399051] | 12/0/1/5 |
| semiorder 0.25 | 6.7657271e-05 [-0.0015300975, 0.0015304266] | 0 [0, 0] | 0 [0, 0] | 18/0/0/0 |
| matched_bipartite 0.38042684413094974 | 7.8029259e-05 [-0.00034425424, 0.0005077766] | 0 [0, 0] | 4.6797058e-05 [-5.8098307e-05, 0.00014524146] | 0/0/0/18 |

Every growth Δr and ΔH 512→256 pointwise interval excludes zero, whereas all iid control counterparts include zero except analytically/observationally constant-height cases. Growth r differences are .005998,.053577,.230184,.194725,.093348,.017971. Conditional contrasts cancel calibration and are duplicated across candidate d only for presentation; they are not independent repeated tests. Motif parent-vs-thinning mean invariance is a counting identity, so the near-equality between late p22 drifts and corresponding thinning-vs-prefix contrasts is expected redundancy, not a second mechanism.

## Negative controls, calibration failures and limitations

- Both d2 Minkowski and matched22 height-two control pass all eight separately banded finite-signature entries. Their half-widths are .0017992728220161786 and .0005981699427123992. The matched control has mean p22=.04163650388024622, H=2, t31=0 and no nonempty open intervals; all21 N512 candidate-law checks are insufficient. Its passing p22 signature cannot support geometric emergence.
- Every Minkowski own-reference N512 conditional margin passes:21/21. Across all eight cells, d2 has47E/8I/1F, d3 has45E/5I/6S, and d4 has35E/2I/19S.
- Preserve the known-control failure: d2 prefixN32 TV4=.0870770572 gives registered status contradicts, with percentile CI[.1005624991,.1474986454] entirely above the estimate and above .08. All96 histories supply1693 size4 intervals. This is an adverse behavior of the secondary TV procedure/finite sample, not evidence against the exact conditional law; the nonsmooth positive-bootstrap-bias caveat was registered before outcomes.
- Preserve the dimension coverage miss: d2 N512 local d=2.0198519366 with pointwise CI[2.0073961837,2.0327817980], excluding2, although its connected2 error remains practically equivalent under±.02. No claim that every inferred-dimension interval covers the true value is supported.
- The semiorder has exact forbidden-motif zeros and height at most4; at N512 all96 observed heights equal4. Yet its global equivalent dimension≈1.8439 appears close to2. Against d4, four of its seven N512 conditional margins are equivalent even though connected2=0 and TV4=.3938 fail. Small reference motif frequencies plus broad absolute tolerances explain these individual matches. Observed small-interval connectivity zeros are not themselves an all-N semiorder theorem.
- R=32 leaves the positive-history rule close to its ceiling. p=.005 N512 size8 support is only16/17/18 histories and38/68/60 intervals; this is insufficient, not equivalence. Many smaller cells are uninformative. Height-two missing interval laws are a structural degeneracy, not a statistical failure that more samples would cure.
- There are96 independent histories per family, not1632 independent order records. Four thinning replicas and nested prefixes remain clustered; finite conditional ratios pool interval counts, and seed batches are not resampled as random populations. No raw interval count is an independent-sample size.
- Primary simultaneous coverage is approximate bootstrap coverage with registered error allocation; the rare-event safeguard is valid for its zero-event target but does not prove the whole bootstrap procedure has exact finite-sample coverage. Secondary intervals are pointwise across many cells and metrics. Sampled global16-motif frequencies add conditional Monte Carlo noise; exact n22/n31 do not.
- The positive control conclusions are practical finite-sample compatibility, not exact distributional equality. Finite-N conditional ratio estimators can be biased even when the count identity E[B−μA]=0 holds. TV is nonnegative and nonsmooth at equality; its bootstrap CIs can be upward-biased. No post hoc changes to thresholds or estimands were made.
- The fixed-p mathematical obstruction predates these numerical outcomes. Positive drift at sparse p, isolated local marginal matches and reference-equivalent dimensions cannot overturn it. The numerical evidence supports a scoped no-go for Minkowski emergence from this baseline, not a universal no-go for intrinsic dynamics.

## Recommendation

Stop classifier/parameter optimization of this fixed-p baseline. The useful advance is the separation between coherent growth laws, exchangeable thinning, finite motif agreement, conditional local sampling laws and actual continuum convergence. A further intrinsic-dynamics experiment needs a mathematical reason to change a specified assumption, a fresh proof/test of covariance and consistency, a chosen convergence topology, control of all finite suborder laws or stronger reconstruction data, and a justified mesoscopic scale. No finite signature establishes an embedding, manifold uniqueness, curvature, Lorentz symmetry, continuum field equations or gravitational dynamics.

Machine-readable audit and compact summary are in statistics_audit.json. Full original arrays/tables remain in growth-primary.
