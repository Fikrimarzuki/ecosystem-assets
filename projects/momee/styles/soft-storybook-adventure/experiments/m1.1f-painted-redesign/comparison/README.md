# M1.1f comparison (experimental)

**Status:** three candidates for owner review. Nothing is selected, accepted or approved; rights are unverified.

| File | Contents |
| --- | --- |
| `m1.1f-joint-1280.png` | Full detail: Candidate B portrait (original), Gate A painted v1, then A, B and C at 1280 px |
| `m1.1f-joint-256.png` / `m1.1f-joint-144.png` | The same five at dialogue-portrait and approximate gameplay height, full canvas |
| `m1.1f-joint-256-figure-crop.png` / `m1.1f-joint-144-figure-crop.png` | The same, with A, B and C cropped to their measured non-transparent bounds, so their extra margin does not make them look smaller than the references |
| `m1.1f-joint-eyes.png` | Candidate B eye tile, then both eyes of each candidate, enlarged |

## Crops

- **Candidate B portrait:** `references/mom-art-direction-exploration-v1.png@541,191,294,351`; eye tile `@541,730,112,109`.
- **Figure crops** (from each `measurements.json`, non-transparent bounds): A `115,166,790,956`; B `132,166,756,938`; C `102,173,797,949`.
- **Eye crops:** Gate A `290,440,500,200`; A `360,460,320,128`; B `370,455,320,128`; C `370,450,320,128`.

## How the sheets were built

They were built by the coordinating Claude Code session on 2026-11-16 with `momee-character-art/scripts/compare-sheet.mjs`, from the ecosystem-assets root. Codex was told not to build them (its sandbox cannot launch Chromium). No candidate file was modified.
