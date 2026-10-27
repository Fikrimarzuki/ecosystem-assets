# Momee M1.1e-A Gate A — painted arm

Status: **not visually successful yet**. The image contract is present, but the required comparison sheets could not be rendered, so the primary visual gate is incomplete. Rights: **unverified**. No asset registration.

## Selected output and generation count

Selected: [mom-neutral-painted-v1.png](mom-neutral-painted-v1.png), 1024×1280 RGBA PNG, derived from generation-01. **1 built-in image_gen call / 6 maximum**, one output, no edits, no rejected outputs.

Selection reason: this sole output preserves the warm palette, side-parted loose reddish-brown waves, coral collar, open eyes and closed smile. Its face is longer and its eye openings flatter than the previous Mom v1. Selection is provisional storage selection, not a visual-gate pass: the required primary comparisons are unavailable.

Rejected-output identity drift: none to report because no outputs were rejected. Selected-output drift observed in the full-size render: a more tapered chin, more defined lips and nose, heavier outer lashes, richer hair texture and brighter gloss than B. The exact requested 10–15% relative eye reduction is unverified.

## Files

- `inputs/`: four lossless reference crops and `crops.json` (coordinates, source and crop SHA-256).
- `generations/`: verbatim `prompt-01.txt`, byte-for-byte `generation-01-original.png`, and its source-path/hash record.
- `mom-neutral-painted-v1.png`: contract-size scale-only derivative.
- `derive-and-inspect.mjs`: reproducible full-frame scale and diagnostic measurements using installed pngjs and repository alphaStats.
- `review/`: candidate-eye crop, white/dark alpha diagnostics, measurements, alpha histogram and failed comparison commands/logs. These diagnostics are not substitutes for comparison sheets.
- `provenance.json`: tool, version, prompt, references, hashes, derivation, selection and blocker record.
- `session-start.json`, `session-end.json`: three-repository git status records.

## Inputs and crop verification

Both source PNGs are 1536×1024. Full SHA-256:

- Exploration: `118eca2c37ebc4db123e512c369998875cd87beffefb0861a206f21825989481`.
- Master: `907a9bd82ed5aec0fe7f50c0494bcdda1d74fddf59a1d51c2b07cd34fb77dd36`.

Observed: B is the middle column. The exact main portrait crop used is **x=541, y=191, w=294, h=351**; it includes crown to upper chest and collar. The eye tile is **541,730,112,109**. Master Mom crops: figure **600,27,181,376** and neutral bust **986,66,104,106**. All four were loaded with view_image before generation. The figure crop has a tiny unrelated fragment at its left edge; the neutral bust crop isolates Mom's face and collar. Fine facial detail is informed reconstruction because the portrait is only 294 px wide, the master bust 104 px wide.

Read-only identity spec was consulted. Mom v1 and M1.1c were viewed only as examples of circular sticker eyes, pointed lashes and flat/vector-like construction to avoid. They were not image_gen references. Only the skill's requested style-guide, facial-design, visual-review and comparison script were used beyond reading its entry instructions; no style-bible or other skill references were followed.

## Derivation and alpha

Measured: original **1122×1402**, SHA-256 `69cddba99205a6329d9af87007c7e625590cf5972a9f39dd56cc0921d54c03e9`. The preserved copy's bytes match the original.

Measured: the 1024×1280 derivative uses full-frame bilinear scaling with premultiplied-alpha interpolation, no crop. Horizontal scale 0.9126559715; vertical scale 0.9129814551; aspect ratio changes by −0.0356506%. No repainting, sharpening, alpha repair, matte removal or defringing. SHA-256: `9f6a61d128ebdb5c7cc392edc3702a7ddfd0e974678a2a3e79f041d1599baa78`.

Measured: derivative has 265,009 fully transparent pixels, 1,045,694 partial-alpha pixels and 17 fully opaque pixels. The most common alpha is **253** (929,758 pixels); interior translucency is mostly slight, not solely edge antialiasing. All four corners have alpha 0. At threshold 128 the bounding box is x=[1,1023), y=[17,1276). Some lower hair reaches the canvas sides at low alpha.

Observed on the inspected white/dark diagnostics: no broad white matte halo; a thin warm/light hair rim persists, strongest toward the crown and left fringe. The original tool preview also showed colored edge speckling; its significance is uncertain because it was not conspicuous in the saved white/dark composites. No correction was attempted. Primary-size fringe review is unavailable.

## Required comparison sheets — blocked

The exact skill script was invoked for B portrait | Mom v1 | painted candidate at **256**, **144**, and **720** px displayed height, plus B eye tile | candidate eyes at **360** px. All four exited 1 before producing PNGs. Exact commands and stderr are in [compare-sheet-attempts.json](review/compare-sheet-attempts.json).

Chromium binaries already exist. A direct launch diagnostic reported: `bootstrap_check_in ... Permission denied (1100)` at `mach_port_rendezvous_mac.cc`. The script's generic message mentions installation, but the diagnosed failure is the launch permission. No installation was attempted. The alternate Node tool probe failed with `The requested module './index.js' does not provide an export named 'default'`. No permissions were changed and no helper was edited.

Assumption: 256 px represents a dialogue portrait. Assumption: 144 px approximates gameplay, based on an adult about 290 px tall and a head about 80 px at @1x. These are the intended PRIMARY judgement sizes; neither could be reviewed. No thumbnail-style pass is claimed.

## Visual-review checklist

These are provisional full-size observations and explicit unverified items, not a completed sheet-based judgement. “Partly” includes missing comparison evidence.

| Item | Answer / evidence | Result |
| --- | --- | --- |
| 1. Identity and adult reading | **Partly — Observed** in raw render | Warm Mom cues and adult oval face; more tapered chin and defined lips drift from B. Same-character judgement at primary sizes remains unverified. |
| 2. Eye construction | **Partly — Observed** in eye crop | Almond openings, crease and upper-lid iris overlap present; pointed outer lash tips remain. No star sparkle. |
| 3. Proportions | **Partly — Assumption** | Face looks longer and eyes flatter, but eye line/width and the 10–15% reduction were not measured or checked on equal-height sheets. |
| 4. Hair | **Partly — Observed** in raw render | Asymmetric side sweep and overlapping waves; broad lower masses remain fairly balanced and gloss is stronger than B. |
| 5. Shading | **Partly — Observed** in raw render | Soft warm shading and blush without obvious isolated blobs; stronger texture/gloss and lip modeling than B. |
| 6. Line | **Partly — Observed** in raw render | Warm varied outlines, lighter inner skin detail; upper lashes remain too emphatic. Primary-size line judgement pending. |
| 7. Generic-vector test | **Partly — Assumption** | Full-size output looks painted; the required thumbnail comparison could not be made, so this item has no pass. |
| 8. Structure and frame swaps | **No — Measured / scope** | Output is a single raster PNG. SVG validation and frame swaps were not run; Gate A explicitly excludes SVG layers and expression frames. This is not a detected rig defect. |

Top provisional gaps vs B, most visible first: pointed/heavy outer lashes; more tapered chin and modeled lips; brighter hair gloss and more texture; tighter side hair framing. The eye-size target and small-size readability remain unresolved.

## Provenance and safety

Tool: **Codex built-in image_gen**. CLI version reported **codex-cli 0.167.1**. Image model: **not recorded** by tool. Date: **2026-11-15**. The prompt is preserved verbatim in both the prompt file and provenance JSON. No seed, model name or licence was inferred. The machine-readable provenance uses the required field `experimental candidate for owner review`; the visual-review status above remains `not visually successful yet`.

All task-authored files are inside this painted arm. The built-in tool itself saved the original under its default `~/.codex/generated_images/` path; it was copied and left intact as instructed. No writes were made to the sibling SVG arm, references, prior attempts, skill, manifest, style bible, D18, app repository or skills repository. No installs, CLI fallback, API keys, paid API calls, commits, pushes, pulls, branches, resets, cleans or deploys.

| Repository | Start `git status --short` | End `git status --short` |
| --- | --- | --- |
| ecosystem-assets | `?? projects/momee/styles/soft-storybook-adventure/experiments/m1.1e-a-neutral-bakeoff/` | Same parent untracked entry; includes newly created painted arm |
| app-momee | Clean (empty output) | Clean (empty output) |
| ecosystem-skills | Clean (empty output) | Clean (empty output) |

Blocker: required comparison-sheet rendering is unavailable under the current runtime permissions. The deliverable set is incomplete (four sheets and primary visual assessment). Stop for owner review of the image, provenance and blocker; no further generation or edits.
