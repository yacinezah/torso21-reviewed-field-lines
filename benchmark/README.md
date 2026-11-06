# Evaluation boundary

This release contains paired mask-change statistics and tooling for a
prospective adjudicated annotation audit. It does not supply an independent
segmentation benchmark or a causal training comparison. All 2,400 frames
entered the historical SEG-R1 refit and many are related sequences.

The optional matched model experiment is omitted: no independently
adjudicated holdout is available. A future study must first freeze that
holdout and exclude related groups from training. Match architecture,
initialization, input images, splits, seed pairs, augmentations, optimizer,
update budget, threshold selection and scoring; change supervision only.
Report paired group-level intervals for Dice, IoU, boundary, centerline
and clDice. No historical training comparison can substitute for it.
