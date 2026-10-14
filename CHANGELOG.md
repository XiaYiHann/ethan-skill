# Changelog

Notable changes to the skills in this repo. Versions track `.claude-plugin/plugin.json`.

## 0.4.0

### Changed

- Replace `rank-my-paper` with the locally maintained v3.4.0 skill, including its references, scripts, tests, and metadata.

## 0.3.0

### Added

- `darpa`: run the Heilmeier Catechism over the current work and answer the eight questions, ending in falsifiable mid-term and final exams. Ships a portable interface contract, governance metadata, and a trigger-eval pack.

### Changed

- `darpa` was audited against the Yao skill standard before publication: the body was split into `references/` (estimated initial load 1128 to 730 tokens), the description was rewritten (trigger recall 0.833 to 0.917), and its coupling to a local-only workflow was made conditional.

## 0.2.0

### Added

- `rank-my-paper`: benchmark a finished manuscript against up to seven officially accepted, same-domain peers, with one independent review per paper and an evidence-bound ranking.
- A preview image in the top-level README, showing an `imagegen-to-drawio` output.

## 0.1.0

### Added

- `imagegen-to-drawio`: build an editable draw.io framework figure from per-module text-free ImageGen artwork, with native labels and bound connectors.
