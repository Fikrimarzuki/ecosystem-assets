# Separate alpha-quality investigation

This investigation is independent of visual acceptance. No image-generation calls were used for alpha repair. Originals and M1.1f provenance remain untouched. No test correction was applied to a new candidate, presentation illustration or art-comparison thumbnail.

## What is measured

Using the existing PNG decoder and M1.1f read-only `measure()` helper, all new originals are 8-bit RGBA, 1122 × 1402. Fully opaque means alpha exactly 255; partial means 1–254. These counts are whole-image counts and do not by themselves distinguish legitimate antialiasing from unwanted interior translucency.

| New original | Alpha 0 | Alpha 1–254 | Alpha 255 | Modal nonzero alpha |
|---|---:|---:|---:|---:|
| A | 541,010 | 1,031,504 | 530 | 253 |
| B | 504,863 | 1,067,856 | 325 | 253 |
| C | 479,560 | 1,093,364 | 120 | 253 |

The alpha 252/253 pixel counts are A: 250,819 / 723,289; B: 61,071 / 941,734; C: 469,395 / 546,174. Their spatially broad distribution is inconsistent with a thin antialiased edge alone. Their near-opaque interior remains a technical limitation, separate from artistic merit.

The unmodified originals also contain very faint peripheral pixels. The alpha>0 bounds touch the left edge in A, and left/bottom in B and C. The stronger figure (alpha≥128) does not touch a canvas edge in any original. This explains why counting literally every nonzero pixel can disagree with the visible silhouette. No such pixels were manually erased. Full-source uniform scaling and padding gives each presentation copy more than 6% transparent left/right/top margin; records contain the exact bounds. Normal interpolation to 8-bit RGBA may quantize extremely faint pixels to zero.

## Non-destructive test on existing artwork

Source: `../../m1.1f-painted-redesign/candidate-b-premium-painted/generations/generation-02-original.png` (1122 × 1402), SHA-256 `6e2587b67ee7996af8fba87ea23d426c47a35ec8fb179330b22cc355deb11552`.

First, encode and decode this existing source with the repository PNG helpers. **Every decoded RGBA value stays identical.** Thus the partial opacity is already present in the stored source pixels; a plain PNG round trip does not repair it. This does not identify which stage originally introduced the values, or establish whether RGB is premultiplied.

Next, define near-opaque support as alpha≥240 and measure Manhattan distance to pixels below that threshold or outside the canvas. Among **835,488 deep-interior pixels** at distance≥32, alpha is:

- 252: 27,685 pixels
- 253: 807,166 pixels
- 254: 637 pixels
- 255: 0 pixels

This confirms an interior-opacity issue for the tested M1.1f source, rather than merely soft hair edges. Alpha 253 corresponds to about 99.22% opacity; the small numerical deviation should not decide visual acceptance on its own.

The saved **technical test copy** smoothly promotes only the selected near-opaque interior toward alpha 255. All pixels at alpha<240 and all pixels within 8 Manhattan pixels of that support boundary remain exactly unchanged. A smoothstep transition spans distances 8–32; deeper pixels become opaque. RGB is never changed, and the image is never flattened or colour-keyed.

Measured results from [measurements.json](measurements.json):

- 893,284 alpha values change, by at most 3 levels.
- **0 RGB values change.**
- **0 protected boundary pixels change.**
- Fully opaque pixels increase from 437 to 859,929.
- Source SHA-256 remains unchanged.

[Technical RGBA test copy](m11f-b-interior-opacity-test.png) is an isolated feasibility artifact, not a replacement or candidate. [test.mjs](test.mjs) records the exact algorithm and thresholds. Source and test are shown on white, cream, dark and magenta in the [background comparison](background-comparison.png), including a native-resolution crown-edge crop. These sheets are display composites only; both PNG sources retain their alpha.

Observed on that sheet: the change is subtle at small display size, and the protected crown boundary retains its soft appearance across the four backgrounds. The numerical identity check provides stronger evidence of boundary preservation than the small display alone. No broad visible crown halo or material detail loss was apparent in this inspected crop. Other hair gaps and blouse edges were not exhaustively pixel-reviewed.

## Conclusion and limits

A separate technical process can promote a known near-opaque interior on a copy while preserving the selected soft boundary pixels and all RGB values. Repeated generation to chase alpha=255 was unnecessary for this investigation. **This is not a validated production repair:** it does not infer intended translucency, remove coloured fringe, recover contaminated RGB or make every interior pixel opaque. The thresholds are test parameters, and a different support definition may be needed for other art.

The new originals intentionally retain their generated alpha. Visual style distinction and owner acceptance are assessed separately in [REVIEW.md](../REVIEW.md). No production tool, manifest or app integration was introduced.
