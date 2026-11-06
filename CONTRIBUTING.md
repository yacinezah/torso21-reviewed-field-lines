# Contributing corrections

Please include the upstream archive member and source mask SHA-256, overlay
version, image-space reason for the proposed edit, and whether a model
candidate was used. Native-resolution hard classes are 0/127/255. Preserve
occlusion and do not antialias class labels. Keep the original and record
who reviewed/adjudicated the candidate, including uncertain regions.

Do not silently replace an existing reviewed file. Submit changes as a new
manifest and changelog entry; run package tests and `verify --torso-root`
against exact upstream bytes. Keep images, checkpoints, source access
credentials, unrelated datasets and private reviewer records outside the
repository. See [QA_PROTOCOL.md](quality/QA_PROTOCOL.md) for audit work.
