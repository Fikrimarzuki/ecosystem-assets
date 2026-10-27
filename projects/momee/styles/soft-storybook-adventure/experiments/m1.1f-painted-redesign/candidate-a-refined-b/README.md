# A: Refined B Portrait

Status: not visually successful yet.

Closest to Candidate B: warm brown contours, gentle cel-soft painted shading and clean flowing hair masses, with a more mature oval face.

Calls used: 3 of 3. Calls 2 and 3 attempted only opacity/margin contract repairs; no polish calls. Deliverable: [mom-a-v1.png](mom-a-v1.png), derived from generation 02. Generation 02 preserves the first image identity and smooth contour-led technique while reducing isolated edge spill relative to the alternatives. It is retained only as the available review image; its interior opacity still fails.

All three originals remain byte-for-byte in generations/, each with its exact prompt and hashes. Rejected generations: 01, 03. Identity-drift note for each rejected output: generation 01 — No material identity drift observed in the separately viewed generated portrait: adult Mom, auburn side-parted waves, coral blouse and closed smile remain. Rejection: Interior alpha remains partial rather than fully opaque; boundary spill and/or insufficient original empty margins persist. Correction did not meet the opacity contract. generation 03 — No material identity drift observed in the separately viewed generated portrait: adult Mom, auburn side-parted waves, coral blouse and closed smile remain. Rejection: Interior alpha remains partial rather than fully opaque; boundary spill and/or insufficient original empty margins persist. Correction did not meet the opacity contract.

## Visual-review checklist

Observed below means direct inspection of separate images and thumbnails, not a comparison sheet. The coordinator owns comparison sheets outside this folder.

1. Identity — **yes (Observed)**: adult woman, side-parted reddish-brown loose waves, coral collar and a calm closed-mouth smile. Owner identity judgement remains open.
2. Eyes — **partly (Observed)**: horizontal almond openings, creases and lid-occluded brown irises, without sparkle dots or circular openings; outer lash tapers remain a little pointed and heavy.
3. Proportions — **partly (Assumption)**: adult lower-face length and smaller eyes appear intentional; exact same-displayed-height correspondence to B has not been checked on a comparison sheet.
4. Hair — **yes (Observed)**: asymmetric side sweep, overlapping wave masses, highlights following waves and varied visible ends; bust framing cannot establish full hair length.
5. Shading — **yes (Observed)**: soft warm modelling, flowing highlights and restrained contour shadows; no obvious circular plastic glints.
6. Line — **yes (Observed)**: warm brown contours are stronger at the silhouette and collar than within the face.
7. Generic-vector test — **yes (Observed)**: the viewed 144 × 180 thumbnail reads as a painted adult portrait with legible eyes and smile; A/B technique separation is less clear at this size.
8. Structure — not applicable to raster paintings.

## Gaps, most visible first

- Coloured edge flecks remain, particularly below the blouse and in hair gaps; the edge is not completely clean.
- The face is longer and narrower, and the nose and lips more modelled, than the Candidate B crop.
- A and B remain close in overall silhouette and colour at 144 px; their technique differences are clearer at full size.
- Upper lashes are heavier and more pointed at the outer corners than an entirely soft natural lash treatment.

The measured alpha failure is separate from visual appearance: the figure is not fully opaque. No post-generation alpha cleanup was performed.

## Measurements

Measured by the top-level measure.mjs using existing repository pngjs only. Size: 1024 × 1280, 8-bit RGBA. Alpha counts: 770825 fully transparent; 9 fully opaque; 539886 partial. Nontransparent margins (left/right/top/bottom): 115/119/166/158 px. Opaque-pixel margins: 185/223/174/193 px; because the interior is mostly partial alpha, these are not the figure silhouette. Nothing touches an edge. Left/right/top exceed 6%.

Derivation: preserve full 1122 × 1402 original; transparent-pad to 1400 × 1750 (left/right 139, top/bottom 174); uniformly scale by 128/175 to 1024 × 1280 with premultiplied-alpha bilinear interpolation. No crop of content, repainting, retouching or alpha cleanup.

Rights: unverified. Nothing in this folder constitutes an owner selection.
