# Momee M1.1g — Distinct Painted Art Directions

2026-11-17, Asia/Jakarta. **Stopped for owner review. No candidate is visually accepted or production-approved.** Three independent built-in `image_gen` generations; no alpha retries. The active style bible, manifests and application were not changed.

| Direction | Consistently framed illustration | Untouched generation | Exact prompt / provenance |
|---|---|---|---|
| A — Classic Illustrated Storybook | [mom-a-v1.png](candidate-a-classic-storybook/mom-a-v1.png) | [original](candidate-a-classic-storybook/generation-01-original.png) | [prompt](candidate-a-classic-storybook/prompt-01.txt), [record](candidate-a-classic-storybook/provenance.json) |
| B — Cinematic 2D Animation | [mom-b-v1.png](candidate-b-cinematic-2d/mom-b-v1.png) | [original](candidate-b-cinematic-2d/generation-01-original.png) | [prompt](candidate-b-cinematic-2d/prompt-01.txt), [record](candidate-b-cinematic-2d/provenance.json) |
| C — Handcrafted Gouache | [mom-c-v1.png](candidate-c-handcrafted-gouache/mom-c-v1.png) | [original](candidate-c-handcrafted-gouache/generation-01-original.png) | [prompt](candidate-c-handcrafted-gouache/prompt-01.txt), [record](candidate-c-handcrafted-gouache/provenance.json) |

Originals are 1122 × 1402 RGBA, copied byte-for-byte from the tool's returned files. Presentation illustrations are 1024 × 1280 RGBA: the entire original is uniformly scaled and transparently padded, with the visible figure aligned to a common crown and blouse baseline. Per-candidate `presentation-provenance.json` records the transformation. No correction from the alpha experiment was applied to these illustrations.

## Review evidence

- [256 px: original Candidate B, retained M1.1e painting and new A/B/C](comparison/owner-comparison-256.png)
- [144 px: same comparison](comparison/owner-comparison-144.png)
- [256 px: all eight, including all M1.1f retained candidates](comparison/figure-normalized-256.png)
- [144 px: all eight](comparison/figure-normalized-144.png)
- [Facial detail](comparison/face-detail.png), [eye detail](comparison/eyes-detail.png)
- [Visual assessment and gaps](REVIEW.md)
- [Separate alpha-quality report](alpha-test/REPORT.md), [background diagnostics](alpha-test/background-comparison.png)

The displayed **figure**, rather than its transparent canvas, is normalized to exactly 256 or 144 px tall. Source boxes, filters and limitations are recorded in [crops-and-scales.json](comparison/crops-and-scales.json). Individual RGBA normalized images are retained in `comparison/`. Comparison sheets composite onto cream for viewing; originals and standalone illustrations retain alpha. Detail enlargement does not recover information absent from the original Candidate B crop.

Observed: the media are more distinguishable than M1.1f, including at 144 px. A uses drawn contours and washes; B uses smooth dimensional lighting; C uses broad matte paint shapes. Remaining gaps include lash points, youthful/round eyes in A and C, and B's tendency toward a 3D-rendered appearance. These are candidates for a decision, not a successful visual-acceptance claim.

## Method and provenance

[Art-direction brief](art-direction.md) was written before generation. The two [identity references](inputs/provenance.json) were used identically in all three calls. The retained painting and M1.1f images were comparison evidence only, never style-lock generation inputs. `momee-character-art` identity, facial/hair and visual-review references, `stylized-game-art` identity/presentation guidance and the built-in `imagegen` skill were used. SVG construction, animation and in-game validation were outside this task.

The tool did not report a model identifier or seed. Those are recorded as unknown; rights remain unverified. No rights or production approval is inferred. Exact tool arguments, input hashes, returned paths and original output hashes are in each provenance record. Historical generation provenance remains in its existing location unchanged.

Local experiment scripts reuse existing `pngjs`, PNG helpers, the cached Chromium renderer and the skill's `compare-sheet.mjs`. No packages or shared tools were added. `prepare.mjs` creates a new experiment only; `capture.mjs` archives returned originals; `build-review.mjs` creates review derivatives; `presentations.mjs` makes full-source padded illustrations; `alpha-test/test.mjs` performs the isolated technical probe; `verify.mjs` checks preservation and deliverables. All write only under this experiment. Initial-creation scripts refuse to overwrite their generated artifacts, except `build-review.mjs --alpha-only` can refresh this experiment's background diagnostic sheet.

[Verification](verification.json) checks all 438 pre-existing Momee files against the preservation snapshot, original copies against the returned files, source/prompt hashes, presentation alpha/margins, comparison dimensions and unchanged app status. No commits, pushes, pulls, branches, resets, cleans, deployments, production registration, expressions, animation layers, rigs or videos were made.
