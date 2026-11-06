# Provenance reconstruction

The release population is the intersection of exact SEG-R1 v2 master membership
and its all-mask refit manifest. Every one of 2,400 IDs, source stem identities,
group IDs and reviewed payload hashes matched both frozen records. This audit
resolves old aliases with the retained decoded image identity and checks every
canonical image/original mask against the current upstream ZIP index.

| Evidence stage | What it establishes |
|---|---|
| ANN-01/02/03, 160 pilot | Original thin-line noise/imbalance and 160 selected reviewed pairs. 160 rows link to the pilot and scale-up records. The pilot training results do not isolate supervision effects. |
| 580 freeze | 400/80/100 historical training, validation and corrected-evaluation roles. The 420 additional rows belong here. 578 final masks retain the scale-up hashes; two later versions take precedence through the full2000/SEG-R1 freeze. A one-case evaluation refresh records one of the later edits. |
| ANN-BATCH / Prompt56C / ANN-QA / ANN-ARBITRATION | 1,420 worklist entries, one technically excluded from the later 1,999 state. Early QA recorded 319 complete and reviewed risk flags; later expansion reached about 1,160 total usable masks (580 + 580), then 1,585 (580 + 1,005 at the later snapshot). Arbitration review queues were triage, not independent truth. |
| 1,999 valid / Prompt73A | 580 scale-up masks plus 1,419 valid later saved masks. Historical roles: 1,310 train, 281 validation, 100 corrected eval, 308 related quarantine. These are historical roles, not current independent samples. |
| ANN-2400 / Prompt74A | 401 additional final saves, including the reconciled legacy item. Hash-verified final-save metadata records 20 accepted Prompt73A candidates and 32 keep-noisy-GT decisions, alongside 349 edit or start-empty decisions. These are actions against a starting candidate, not a pixel-change count against upstream. |
| SEG-R1 v2 | 2,298 train/56 development/46 calibration grouped rows before refit; then all 2,400 entered the refit. Historical model comparisons and threshold changes cannot quantify causal label improvement. |

Frozen authority SHA-256:

| Record | Digest |
|---|---|
| SEG-R1 v2 master inventory | `b98eb9e111059913bd495c3aa9809c01f7fbe19ab24fc24ca9dabd7effb132d1` |
| Pre-refit manifest | `8f956665f59cd0bbdb514aa5d871bcee91947c01aeecf3b6dc3ddb7e01967b99` |
| All-mask refit manifest | `0667d8632f9ad9ecd87bd6edba57f554577b263ff5de9b2d366a28bd783894ca` |

The public manifest uses stable IDs derived from the exact upstream image
member. The private reconstruction receipt retains the original historical IDs,
source paths, and hashes of input logs. This avoids publishing private file
locations while preserving an audit chain. The sidecar contains save-session
counters for 1,820 rows, with recorded positive drawing/erasing counts in 1,345.
Zero counts can mean acceptance, review only, or counters reset in an earlier
session; they do not prove no prior manual edit. The 580 pilot/scale-up records
retain completion/freeze evidence but lack comparable save counters. Per-class
pixel transitions are directly measured for all rows; historical edit intent
cannot generally be reconstructed pixel by pixel.

The earlier grouping audit found 54 and 66 crossing sequence groups in two old
splits. The current 45 conservative groups link source families, timestamps,
accepted historical duplicate and sequence relations. The upstream
train/test split is reproduced only as provenance; 40 of these groups cross
it within this reviewed population. Separate nearby frames are not exact
duplicates, but they remain dependent.

The [official palette repair](https://github.com/bit-bots/TORSO_21_dataset/blob/master/scripts/fix_segmentations.py)
sets values above 127 to 255. We apply that interpretation to comparisons,
never rewriting the retained upstream mask. Raw decoded changes, byte changes
and semantic changes have separate columns. One upstream frame has 36 pixels
in 1–126; these are ignored for semantic differences and that image is omitted
from geometry metrics. It has 18,032 definite changes on the remaining grid.
The three colon-to-underscore filename aliases are recorded as literal archive
member plus normalized local path and were individually verified with upstream
SHA-256. Read the [results](DATASET_QUALITY_RESULTS.md) for all denominators.
