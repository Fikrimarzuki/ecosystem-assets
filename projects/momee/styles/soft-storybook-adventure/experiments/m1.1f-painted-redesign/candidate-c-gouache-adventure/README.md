# C: Gouache Adventure Storybook

Status: not visually successful yet.

Matte gouache adventure storybook: visible opaque-looking directional brushwork, confident larger shapes and a limited warm auburn/coral/peach palette.

Calls used: 3 of 3. Calls 2 and 3 attempted only opacity/margin contract repairs; no polish calls. Deliverable: [mom-c-v1.png](mom-c-v1.png), derived from generation 03. Generation 03 retains the distinct broad gouache strokes and same adult Mom while showing less scattered spill below the bust than generation 02. It remains a review choice with a failed opacity contract.

All three originals remain byte-for-byte in generations/, each with its exact prompt and hashes. Rejected generations: 01, 02. Identity-drift note for each rejected output: generation 01 — No material identity drift observed in the separately viewed generated portrait: adult Mom, auburn side-parted waves, coral blouse and closed smile remain. Rejection: Interior alpha remains partial rather than fully opaque; boundary spill and/or insufficient original empty margins persist. Correction did not meet the opacity contract. generation 02 — No material identity drift observed in the separately viewed generated portrait: adult Mom, auburn side-parted waves, coral blouse and closed smile remain. Rejection: Interior alpha remains partial rather than fully opaque; boundary spill and/or insufficient original empty margins persist. Correction did not meet the opacity contract.

## Visual-review checklist

Observed below means direct inspection of separate images and thumbnails, not a comparison sheet. The coordinator owns comparison sheets outside this folder.

1. Identity — **yes (Observed)**: adult woman, side-parted reddish-brown loose waves, coral collar and a calm closed-mouth smile. Owner identity judgement remains open.
2. Eyes — **partly (Observed)**: horizontal almond openings, creases and lid-occluded brown irises, without sparkle dots or circular openings; outer lash tapers remain a little pointed and heavy.
3. Proportions — **partly (Assumption)**: adult lower-face length and smaller eyes appear intentional; exact same-displayed-height correspondence to B has not been checked on a comparison sheet.
4. Hair — **yes (Observed)**: asymmetric side sweep, overlapping wave masses, highlights following waves and varied visible ends; bust framing cannot establish full hair length.
5. Shading — **partly (Observed)**: warm painted shadow planes and highlights provide volume; continuous smooth gradients are intentionally replaced with gouache strokes.
6. Line — **partly (Observed)**: warm painted edge accents replace most linework; silhouette contrast varies with the brush strokes.
7. Generic-vector test — **yes (Observed)**: the viewed 144 × 180 thumbnail reads as a painted adult character, with broader colour planes than A/B; fine texture and lid creases diminish.
8. Structure — not applicable to raster paintings.

## Gaps, most visible first

- A ragged coloured fringe remains around the bottom of the blouse and sections of hair.
- The face and neck are longer and more anatomically modelled than the Candidate B crop.
- Hair highlights still have some luminosity; the matte technique is clearest in the broad brush strokes on the blouse and hair.
- Lid creases are subtler and less legible at thumbnail size than in A.

The measured alpha failure is separate from visual appearance: the figure is not fully opaque. No post-generation alpha cleanup was performed.

## Measurements

Measured by the top-level measure.mjs using existing repository pngjs only. Size: 1024 × 1280, 8-bit RGBA. Alpha counts: 758065 fully transparent; 22 fully opaque; 552633 partial. Nontransparent margins (left/right/top/bottom): 102/125/173/158 px. Opaque-pixel margins: 212/231/444/174 px; because the interior is mostly partial alpha, these are not the figure silhouette. Nothing touches an edge. Left/right/top exceed 6%.

Derivation: preserve full 1122 × 1402 original; transparent-pad to 1400 × 1750 (left/right 139, top/bottom 174); uniformly scale by 128/175 to 1024 × 1280 with premultiplied-alpha bilinear interpolation. No crop of content, repainting, retouching or alpha cleanup.

Rights: unverified. Nothing in this folder constitutes an owner selection.
