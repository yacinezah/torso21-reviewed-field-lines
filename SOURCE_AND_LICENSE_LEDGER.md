# Source and license ledger

| Material | Origin and disposition |
|---|---|
| TORSO-21 real images, upstream masks and upstream scripts | Hamburg Bit-Bots / Universität Hamburg; [official upstream repository](https://github.com/bit-bots/TORSO_21_dataset), commit `3daaf45926f08d082ebf23200818ee94adf29d5b`. [Upstream dataset citation metadata](https://github.com/bit-bots/TORSO_21_dataset/blob/master/CITATION.cff) declares MIT. The unmodified Hamburg Bit-Bots notice is in [LICENSES](LICENSES/TORSO-21-MIT.txt). RGB and upstream YAML are not redistributed. |
| Reviewed masks | Published as an opt-in overlay. Derived from the real-world TORSO-21 source, with inherited attribution and license notice retained. Manual review and edits: Yacine Zahouani during the ITAndroids internship. Model-initialized candidates accepted or edited after review are identified when the record survives. No checkpoint is distributed. |
| Overlay code, tables, plots | New overlay tooling and descriptive results; MIT with upstream notice retained for underlying TORSO material. The overlay contains only TORSO-21 masks and supporting tooling and records. |
| Illustrations and QA | Released figure is an aggregate plot and selection JSON, not a photo gallery. The local rendering and blind-review scripts require the user's verified TORSO installation. Local reviewer inputs, reference labels, judgments and unblinding keys stay outside the release. |

The [official download index](https://data.bit-bots.de/TORSO-21/reality/) and
[metadata.json](metadata.json) identify current archive locators, ETags and
sizes. The repository revision establishes script/format provenance; the
archives are separately versioned assets. All retained source pairs match the
official archive index by CRC32 and uncompressed size; a fixed 12-pair sample
also matches upstream SHA-256 on downloaded member bytes. SHA-256 of every
retained source file and saved review is in the manifest. When users extract
the selected pairs from official ZIPs, the tool requires every member SHA-256.
This is not a claim that all archive payload bytes were fetched during the audit.

The source train/test YAML blobs were checked against the pinned Git tree and match
`214d1ddc2d547a02cd4ce39c47a4bd7c8ee71466` and
`14485e6ed4931e135d54dcf938004ab055db6cfd`, respectively. YAML is outside the scope of this overlay.
