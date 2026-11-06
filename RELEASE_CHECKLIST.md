# Release checklist — 0.1.0

- [x] Freeze population to the exact SEG-R1 master/refit pairs and retain old revisions.
- [x] Verify all 2,400 reviewed and retained source pairs, including source ZIP member mapping.
- [x] Separate byte differences, palette differences and semantic differences.
- [x] Keep all 435 semantic retentions identifiable; report model-assisted acceptance accurately.
- [x] Validate shapes, allowed classes, duplicates, group relations, flags and metric denominators.
- [x] Compare CSV and Parquet and rebuild the annotation payload deterministically.
- [x] Exercise the CLI and synthetic tests in an isolated Python 3.11 environment.
- [x] Keep the official attribution and MIT notice; include no RGB, private models or unrelated data.
- [x] Render examples by fixed rules outside the release, with aggregate plots in the package.
- [x] Freeze and stage the reference-only packet for 240 prospective QA rows; keep the blind key private.
- [ ] Independent human adjudication and paired quality analysis. Optional for resource-only release; required for an independent gain claim.
- [x] Public resource release authorized; [versioned release](https://github.com/yacinezah/torso21-reviewed-field-lines/releases/tag/v0.1.0).
- Upstream outreach is outside this release.

No new training or matched model comparison was warranted without an
adjudicated holdout. Do not claim this release is an untouched test split,
automatically replace the upstream archive, or release reviewer records.
