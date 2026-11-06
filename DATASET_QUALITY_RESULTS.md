# Dataset quality results

**Descriptive corpus audit. Independent annotation quality is unmeasured.**
Both grids describe the same source image; neither is treated as ground truth.
The analysis used every pair in the frozen review population.

| Check or statistic | Result |
|---|---:|
| Verified source/review pairs and valid reviewed PNGs | 2,400 |
| Definite class-label change / class-label unchanged | 1,965 / 435 |
| Byte-identical reviewed vs. original | 0 |
| Of the 435 label-unchanged rows: same decoded raw values / palette-only differences | 309 / 126 |
| Raw value changes (includes palette) / definite semantic changes | 148,318,079 / 14,136,926 pixels |
| Class change among comparable pixels | 1.357% of 1,042,031,964 pixels |
| Median per-mask changed fraction, all / modified-only | 0.801% / 1.034% |
| Modified-only p95 changed fraction | See [summary.json](quality/summary.json), `modified_change` |
| Line pixels, original → reviewed | 21,140,656 → 30,050,914 |
| Exclusive field pixels, original → reviewed | 702,388,024 → 693,613,472 |
| Original empty line → nonempty / original nonempty → empty | 88 / 6 masks |
| Field union changed | 959 masks; 180,740 pixels |
| Exact duplicate source RGB files or decoded image grids | 0 groups |
| Repeated reviewed mask bytes | 19 groups, 162 rows; different RGB inputs |
| Repeated original mask bytes | 15 groups, 155 rows |
| Related rows with same recorded sequence key | 309 repeated keys, 1,200 rows; see group-aware use guidance |

Semantic deltas use the upstream `>127 → 255` repair rule. One original has
36 ambiguous pixels below 127 (and above 0), outside the documented palette;
ignore these in the semantic difference and exclude this pair from geometry.
There are 1,928 originals with at least one field shade between 128 and 254.
The true intended labels of ambiguous pixels were not inferred. This is why
the byte, raw-value and class-label counts answer different questions.

| Paired geometry measurement | All comparable, median (n defined) | Modified only, median (n defined) |
|---|---:|---:|
| Line Dice | 0.734 (2,038) | 0.717 (1,964) |
| Line IoU | 0.579 (2,038) | 0.559 (1,964) |
| Exclusive field Dice | 0.994 (2,304) | 0.992 (1,959) |
| Field union Dice | 1.000 (2,309) | 1.000 (1,964) |
| Symmetric mean line boundary distance | 3.98 px (1,944) | 4.26 px (1,870) |
| Line boundary HD95 | 25.99 px (1,944) | 27.64 px (1,870) |
| Centerline F1@1 / @2 / @3 px | 0.538 / 0.639 / 0.711 (2,038) | 0.521 / 0.623 / 0.693 (1,964) |
| clDice | 0.757 (2,038) | 0.746 (1,964) |
| Line component count before → after | 12 → 3 (2,399) | 17 → 4 (1,964) |
| Skeleton graph length before → after | 820 → 982 px (2,399) | 991 → 1,152 px (1,964) |
| Median line-width proxy before → after | 5.00 → 5.32 px (1,950 / 2,032) | 5.00 → 5.32 px (1,876 / 1,958) |
| Tangent histogram total variation | 0.102 (1,918) | 0.106 (1,851) |

Use native pixel distances, not meters. Boundaries are 8-neighbor inner
contours, distance is Euclidean, symmetric mean averages the two directions
equally, and HD95 is the maximum directional 95th percentile. Centerlines are
one-pixel skeletons with separate symmetric tolerance matches. clDice uses
both skeletons and opposite line supports. Overlap and centerline metrics are
undefined when both line masks are empty, and score zero for one-sided
nonempty support; distances require nonempty support on both sides. Skeleton
graph length sums native horizontal/vertical/diagonal edges with redundant
diagonals removed. Width is `2 × distance-to-background − 1` at skeleton
pixels, a raster proxy rather than a physical width. Tangents use near-straight
degree-two skeleton pixels (at least 32 per mask) in four axial bins; compare
histograms, not pointwise orientation accuracy.

Triage flags are heuristic, not identified annotation errors: 367 reviewed
empty line masks, 90 empty field unions, five nonempty line masks without
exclusive field, 106 above 10% line area, 17 with over 20 line components and
eight with at least ten components of at most four pixels. Median width
flags include 66 under 2 px and 220 above max(20 px, 6% of the shorter image
side). Perspective, close paint, occlusion and dataset composition can explain
flags. Group tables preserve 45 groups, including 40 crossing the upstream
train/test split. No IID uncertainty interval is attached to these corpus totals.

The [aggregate figure](quality/edit_distributions.svg) and [per-image metrics](quality/geometry_change.csv)
are generated from fixed rules. [Example IDs](examples/selection.json) were
selected by hash within predeclared categories; examples include no semantic
change, palette-only change, three edit magnitudes, new/removed line and the
ambiguous original. Render them locally using the README command. No selected
RGB example is distributed here.

**Quality decision:** the [240-pair QA protocol](quality/QA_PROTOCOL.md) is
frozen and awaits a human reviewer. There are **zero independently validated
pairs** and no paired reference result. Historical segmentation scores reflect
changes in training, initialization, thresholds and labels. No new model run
was launched and no causal improvement estimate is reported.
