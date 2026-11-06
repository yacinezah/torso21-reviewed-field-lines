# Prospective annotation audit, v1 — no human scores collected

The intervention is annotation version, not training recipe. Target 240 pairs
from the reviewed overlay. The primary comparison is reviewed minus original
centerline F1 at 3 native pixels against a separately drawn, adjudicated
visible-line reference. Secondary outcomes: line Dice and IoU, clDice, line
boundary distances with defined denominators, empty-line misses/false positives
and blinded candidate preference. A positive preference does not substitute
for agreement against the reference.

## Selection and masking

Use the fixed selection algorithm in `quality/qa.py`: one hash-ranked image
per acquisition group first; then round-robin across change tiers and original
line/prevalence/anomaly bins, picking from the least represented available group
in the current bin. Freeze 240 IDs and the manifest/geometry/selection hashes
before seeing any new human judgments. One ambiguous original palette case is
excluded from this reference comparison; retain it in the release. The enriched
sample represents the specified audit mix; no design-based estimate for all of
TORSO-21 or all reviewed rows follows.

Two sessions with separate directories:

1. **Reference pass:** an independent human, uninvolved in the historical
   corrections, annotates the native RGB images without seeing either candidate.
   Use opaque IDs, an empty mask and a native-resolution raster editor. Record
   `reviewer_id`, independence, confidence and any uncertain regions separately.
   A second qualified person checks all uncertain cases and a fixed first 24
   hash-ranked IDs without seeing the candidates. Resolve disagreements from RGB
   and record the decision, reason and final adjudicated mask. Retain both
   versions; never change the reference after candidate unblinding.
2. **Candidate pass:** after reference freeze, show A/B with independently
   randomized sides per image and equal colors/opacity. The reviewer records
   `A`, `B`, `tie` or `uncertain`, reason and visibility concerns before
   unblinding. The operator keeps the mapping separate. Identical semantic pairs
   are controls. Candidate order can be blinded; appearance may reveal artifacts.

If only the original annotator is available, register the run as `REPEAT_AUDIT`
before first review. Do not call its references independently annotated. If no
reviewer is available, report NOT_RUN; software fixtures and prior human
acceptance do not substitute. Budget roughly 12–24 reviewer hours at 3–6 minutes
per reference plus adjudication. A 24-case fixed dry run may be used solely to
check workflow and convention adherence, before any aggregate statistics.

## Label convention

Label visible painted regulation lines at native resolution. Include the paint
footprint up to its visible boundary; label a pixel as line if its center is
judged inside visible paint. Use the same convention for curved, crossing and
intersecting paint; label the visible union once. Keep line separate from
exclusive field. Background includes people, robots, ball, signs and other
occluders; never extrapolate a line through them. Reflections, seams and white
objects are not paint. For blur or ambiguity, mark an ignore region rather than
guessing; do not use antialiasing or intermediate values. References may use
value 126 for ignore. Report the number/fraction ignored and any excluded
frames with reasons before decoding A/B. Raster conventions used here are
prospective and do not retroactively describe every historical stroke.

## Analysis freeze

Apply reference ignore to both candidates before scoring. Report paired per-image
differences and equal-weight acquisition-group means. Use a percentile bootstrap
of whole groups (10,000 resamples, seed 20261106); frames are not independent.
The target is the enriched audit mix, with uncertainty across observed
acquisition groups; grouping is conservative inferred family/duplicate closure,
not certified distinct matches. Exclude all-three-empty cases from primary
centerline scoring and report that count separately. If the reference has no
line but one candidate predicts one, use 1 for the candidate with no line and 0
for the other. When only one side has support, centerline F1 is 0. Boundary
distance is undefined with empty support. Report comparable counts and missing
judgments, no imputation. Repeat on adjudicated line-present rows and by change
tier as descriptive sensitivity checks; do not select claims from these.

Require an independent reference protocol, at least 200 scored pairs in at
least 30 groups, and a lower 95% group-bootstrap bound above zero plus a point
gain of at least 0.02 for the primary improvement claim. Report secondary
outcomes without confirmatory claims. If these conditions fail, describe
the data and uncertainty without a gain claim. No whole-corpus independent
validation claim follows from passing a sampled audit. No model experiment
until independent evaluation, group exclusions and paired training controls
can be frozen separately.
