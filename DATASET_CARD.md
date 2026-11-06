# Dataset card — reviewed TORSO-21 field lines

**[Version 0.1.0](https://github.com/yacinezah/torso21-reviewed-field-lines/releases/tag/v0.1.0).** This overlay makes historical manual
review work usable without replacing the canonical Hamburg Bit-Bots dataset.
Thin paint labels matter for field perception and geometry; agreement between
versions measures edits and cannot say which version is closer to the image.

| Item | Scope |
|---|---|
| Population | Exact SEG-R1 all-mask refit inventory: 2,400 TORSO-21 reality frames; 2,019 upstream train and 381 upstream test |
| Semantic status | 1,965 modified / 435 reviewed unchanged under the declared original-palette interpretation |
| Assets | Original reviewed 8-bit grayscale PNGs at native resolution; no images, YAML, robot assets or model weights |
| Classes | 0 background; 127 visible painted field line; 255 exclusive field. Field union is line or exclusive field |
| Upstream identity | Exact archive members, source and reviewed SHA-256, upstream Git commit, archive ETag/size; three normalized Windows filenames |
| Grouping | 45 inferred acquisition components (46 source families); includes historical related-image links. Recording independence is not guaranteed |
| Validation | Pairing, hashes, shape, palette, exact duplicates, numerical change and triage checks; independent human QA: 0 pairs |

Selection grew through difficult examples, annotation availability, model-assisted
queues, random controls and historical evaluation choices. It is not a random
TORSO sample. The earliest work used visible-paint editing with line suggestions
and minimal field-boundary changes. Later tools could start from a historical
model prediction, original/noisy line mask or an empty line mask. Reviewers could
accept a candidate, edit it or retain the original line layer. Where only
save-session counters survive, the specific image-space strokes are unknown.
No raw counts are reclassified as hand-drawn polygons.

Line labels describe visible paint, including curved markings and intersections;
the historical pilot convention avoided extrapolating through occlusion, labeling
reflections or antialiasing edges. The [prospective QA protocol](quality/QA_PROTOCOL.md)
specifies finer blur and boundary conventions for a future independent audit.
Actual historical consistency with those prospective rules has not been measured.

All rows have historical training exposure from the SEG-R1 refit. Earlier
splits also had sequence and near-duplicate relations. Use the release for
training, data inspection, annotation tooling, or a explicitly scoped paired
label audit. Do not use it as an untouched held-out benchmark for the internship
models, claim a causal training improvement, or call every changed pixel manual.
There is no new baseline accuracy score. The overlay does not repair boxes,
YAML labels, unrelated data or the canonical upstream archives.

Report release version, manifest hash, candidate/source paths and deviations
when using this resource. Update changed mask bytes or membership by versioned
release with a row-level changelog; never replace files under the same manifest
hash. Cite both the annotation overlay and Bestmann et al.,
*TORSO-21 Dataset: Typical Objects in RoboCup Soccer 2021* (RoboCup 2021);
see [citation metadata](CITATION.cff) and [license ledger](SOURCE_AND_LICENSE_LEDGER.md).
