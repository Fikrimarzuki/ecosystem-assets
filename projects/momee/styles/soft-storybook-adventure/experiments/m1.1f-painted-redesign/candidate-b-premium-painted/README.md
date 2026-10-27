# B: Premium Painted Storybook

Status: not visually successful yet.

Premium picture-book painting with richer soft light, subtle brush texture, warm rim light and coloured painted edges with few hard outlines.

Calls used: 3 of 3. Calls 2 and 3 attempted only opacity/margin contract repairs; no polish calls. Deliverable: [mom-b-v1.png](mom-b-v1.png), derived from generation 02. Generation 02 keeps the richer brushed finish and the original adult identity, and has fewer widely scattered boundary particles than the other B attempts. It is retained only for review; opacity is unresolved.

All three originals remain byte-for-byte in generations/, each with its exact prompt and hashes. Rejected generations: 01, 03. Identity-drift note for each rejected output: generation 01 — No material identity drift observed in the separately viewed generated portrait: adult Mom, auburn side-parted waves, coral blouse and closed smile remain. Rejection: Interior alpha remains partial rather than fully opaque; boundary spill and/or insufficient original empty margins persist. Correction did not meet the opacity contract. generation 03 — No material identity drift observed in the separately viewed generated portrait: adult Mom, auburn side-parted waves, coral blouse and closed smile remain. Rejection: Interior alpha remains partial rather than fully opaque; boundary spill and/or insufficient original empty margins persist. Correction did not meet the opacity contract.

## Visual-review checklist

Observed below means direct inspection of separate images and thumbnails, not a comparison sheet. The coordinator owns comparison sheets outside this folder.

1. Identity — **yes (Observed)**: adult woman, side-parted reddish-brown loose waves, coral collar and a calm closed-mouth smile. Owner identity judgement remains open.
2. Eyes — **partly (Observed)**: horizontal almond openings, creases and lid-occluded brown irises, without sparkle dots or circular openings; outer lash tapers remain a little pointed and heavy.
3. Proportions — **partly (Assumption)**: adult lower-face length and smaller eyes appear intentional; exact same-displayed-height correspondence to B has not been checked on a comparison sheet.
4. Hair — **yes (Observed)**: asymmetric side sweep, overlapping wave masses, highlights following waves and varied visible ends; bust framing cannot establish full hair length.
5. Shading — **yes (Observed)**: richer warm cheek/neck modelling, soft coloured shadows and directional hair light; subtle brushed surface.
6. Line — **yes (Observed)**: hard contour lines are reduced; coloured edges and paint strokes carry most form boundaries.
7. Generic-vector test — **yes (Observed)**: the viewed 144 × 180 thumbnail reads as a painting rather than stock vector art; premium surface texture is mostly lost at this size.
8. Structure — not applicable to raster paintings.

## Gaps, most visible first

- Red/orange edge flecks and uneven fringe pixels remain around hair and the blouse cut edge.
- The more sculpted nose, jaw and lips move further from the small simplified Candidate B face.
- At 144 px, the softer brush texture largely disappears and B resembles A.
- Upper lash accents are still rather bold.

The measured alpha failure is separate from visual appearance: the figure is not fully opaque. No post-generation alpha cleanup was performed.

## Measurements

Measured by the top-level measure.mjs using existing repository pngjs only. Size: 1024 × 1280, 8-bit RGBA. Alpha counts: 782701 fully transparent; 4 fully opaque; 528015 partial. Nontransparent margins (left/right/top/bottom): 132/136/166/176 px. Opaque-pixel margins: 266/163/1048/193 px; because the interior is mostly partial alpha, these are not the figure silhouette. Nothing touches an edge. Left/right/top exceed 6%.

Derivation: preserve full 1122 × 1402 original; transparent-pad to 1400 × 1750 (left/right 139, top/bottom 174); uniformly scale by 128/175 to 1024 × 1280 with premultiplied-alpha bilinear interpolation. No crop of content, repainting, retouching or alpha cleanup.

Rights: unverified. Nothing in this folder constitutes an owner selection.
