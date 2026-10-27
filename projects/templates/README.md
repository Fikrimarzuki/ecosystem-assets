# Templates branding

Brand identity for **Templates**, registry ID `templates` in `ecosystem-config`
(`config/projects/templates.json`). Status: **candidate, awaiting owner approval** (2026-10-30, Templates M1.3).
Nothing here is approved until the owner commits it.

## Direction

**Swatch fan.** This is the app's existing `LogoMark` (`web-templates/src/components/layout/logo.tsx`) made into a
production icon: five rounded swatch blades (Mint, Marigold, Cobalt, Blush, Paprika) fanned from one pivot like
a designer's fan deck, on an aubergine tile. The blade angles are the app's own, `rotate((i - 2) * 17 + 8)`
(-26°, -9°, 8°, 25°, 42°), so the fan keeps its slight lean to the right and stays recognisably the same mark.
The five category swatches are the brand's colour story. Every other colour comes from the app palette:

| Role | Colour |
| --- | --- |
| Tile | aubergine `#241736` → `#1b1029` (vertical gradient, never lighter than the ink) |
| Tile ring | `#6e6188`: 5.6:1 on white, 3.4:1 on `#0d1117`, 3.7:1 on black |
| Blades | Mint `#3cc8a4`, Marigold `#f6b321`, Cobalt `#2f5bea`, Blush `#f3b6c4`, Paprika `#e8553e` |
| Pivot | `#f1eef8` on the tile; aubergine `#241736` on transparent/light (as in the app header) |
| Wordmark ink | `#241736` (light backgrounds), `#f1eef8` (dark backgrounds) |

Refinements over the app's 32-unit SVG, all filled shapes only:

- **Cut blades (icon, tile, glyph, mono).** Where a blade passes under the next one, it is clipped along that
  blade's edge with a gap (0.55 app units, about 6.5 px at 512). Each card stays legible, and the mark works in
  one colour (`mono.svg`) where overlapping blades would otherwise merge into a blob.
- **Ring pivot.** The pivot is a rivet: a light ring with a hole, set just clear of the blade bases. The app's
  aubergine dot would disappear on an aubergine tile.
- **Simplified favicon (`favicon.svg`).** At 16 px the 6 px gaps turn into muddy dark pixels, so the small-size
  master uses five **wider** blades (9.2 units instead of 7.6) that overlap with no gaps, and a larger solid pivot
  that overlaps their bases. The fan becomes one solid wedge, with the blades told apart by colour. I kept all
  five blades, because a four-blade test drops a brand colour for no legibility gain at 16 px.
- **Optical shift (0, 16).** The wide blade tips make the fan top-heavy, so its bounding box sits 16 units
  below centre. That puts the visual centroid within 15 units of the canvas centre.
- **Cobalt contrast.** Cobalt on aubergine measures 3.04:1, just above the 3:1 rule for non-text elements.
  That's why the tile gradient only darkens from `#241736`.

The **wordmark** is "Templates" in Bricolage Grotesque, the app's typeface, set in its `.heading` style and
**outlined to paths** (no `<text>`, no font needed):

- 48pt optical size, SemiCondensed width (`wdth` 87.5, the closest static instance to the app's 86).
- Weight 650, interpolated 50/50 from the SemiBold 600 and Bold 700 instances, whose outlines are
  point-compatible.
- Tracking -0.02em.
- GPOS kerning (`Te` -71, `te` -8.5, `es` +4.5, `at` -2), measured in Chromium. opentype.js 1.3.4 doesn't read the
  font's extension kern lookups.

A side-by-side render against live text in the variable font (wght 650, wdth 86, opsz 48) matched closely.
Bricolage Grotesque is © 2022 The Bricolage Grotesque Project Authors and licensed under the **SIL Open Font
License 1.1**. The OFL allows outlined artwork made from the font. No font files are stored here.

Concepts explored (kept for provenance, never shipped), compared in `branding/previews/concepts-v01.png`:

| Concept | File | Decision |
| --- | --- | --- |
| A. Swatch fan | `branding/concepts/swatch-fan-v01.svg` | **Chosen**, then refined: cut blades, ring pivot, simplified favicon, optical shift |
| B. Layout grid | `branding/concepts/layout-grid-v01.svg` | Rejected: reads as a generic dashboard or wireframe icon |
| C. Swatch T | `branding/concepts/swatch-t-v01.svg` | Rejected: drops the mark the app already uses |

## Files

| Path | Kind | Purpose |
| --- | --- | --- |
| `branding/source/{icon,tile,glyph,favicon,mono}.svg` | masters | Standard icon masters ([naming](../../docs/naming-conventions.md)) |
| `branding/source/icon.checks.json` | config | Optical shift (0, 16), small-size structure rules, colour probes for every blade and the pivot |
| `branding/concepts/*.svg` | exploration | Concepts A–C (above) |
| `branding/exports/**` | generated | `pnpm build:icons templates`: favicon.ico/16/32, apple-touch-icon, 192/512, maskable 512, SVG |
| `branding/previews/contact-sheet.png` | preview | `pnpm contact-sheet templates` |
| `branding/previews/concepts-v01.png` | preview | Concepts A–C next to the refined icon at 200/64/32/16 px |
| `logo/source/wordmark.svg` | master | The outlined "Templates" lettering (size 100, baseline y=0, cap height 66; ink `#241736`) |
| `logo/exports/lockup-light.svg` | composed | Swatch fan + wordmark, aubergine ink and pivot, for light backgrounds |
| `logo/exports/lockup-dark.svg` | composed | Same, with `#f1eef8` ink and pivot, for dark backgrounds |
| `logo/exports/symbol.svg` | composed | Swatch fan alone, transparent (optimised `glyph.svg`; aubergine pivot) |
| `social/source/og-image.svg` | composed | 1200×630 social image: lilac paper `#f2f1f7`, the light lockup, the tagline "Designs for every idea" (the app's `meta.homeTitle`, outlined in Bricolage SemiBold, `#5f5672`) and a five-swatch strip along the bottom edge |
| `social/exports/og-image.png` | rendered | Chromium (Playwright) render of `og-image.svg`, 1200×630 RGB, 37 KB |

## How the files are produced

- **Icon masters** were generated from one parametric description of the fan by a helper script kept outside
  the repository. The masters are plain SVG and can be edited by hand. In app units (32 grid): detail scale 11.8,
  blade width 7.6, blade from 3.4 to 24 from the pivot, corner radius 2.6, gap 0.55, pivot ring r 2.5 with hole
  0.95. Favicon: scale 10.6, blade width 9.2, blades from 2.0, radius 2.8, no gaps, solid pivot r 3.3.
  `glyph.svg`, `favicon.svg` and `mono.svg` use the repository's `scale(1.2)` group transform.
- **Icon exports** come only from `pnpm build:icons templates` and are never hand-edited.
- **Lockups, symbol and social image** were composed by a helper script outside the repository, because
  `pnpm build:logos` is not part of the committed tooling. The fan is set at 1.76× the cap height, 34 units from
  the wordmark, and centred 6 units below the cap-height midline. Output is optimised with the repository's SVGO
  settings (`scripts/lib/svg.mjs`). If the icon masters change, these files need recomposing. No
  `verify:logos` covers them yet. If the owner adopts `build:logos`, it needs a Templates layout and palette
  first: it currently hardcodes the Links colours.

## Checks run (2026-10-30)

- `pnpm verify:icons templates`: **101 passed, 0 warnings, 0 failed**. The results cover:
  - Glyph/tile contrast 3.0:1 (cobalt, the limiting colour).
  - Tile edge 5.6:1 on white and 3.4:1 on dark.
  - Maskable glyph within 200.7 of 205.
  - Icon margin 74, favicon 52, glyph 37.
  - Centroids within 15.
  - ICO 16/32/48.
  - All 12 colour probes.
  - Deterministic, current exports.
- `pnpm contact-sheet templates` reviewed at 512, 192, 64, 32 and 16 px on light and dark, in browser tabs,
  on iOS and on Android masks. 32 px shows all five blades distinctly. At 16 px it reads as a five-colour fan
  with a light pivot. The circle mask crops nothing.
- Lockups rendered at 116 px and 32 px tall on `#f2f1f7`, white and `#17112a`. Social image inspected at
  1200×630.
- Logo and social SVGs: each has a `<title>`. None has `<text>`, `<image>`, `<script>`, `<style>`, `url()`, `href` or external references.

## Consumers

These copies will be made by the Templates integration, not from here:

- `ecosystem-config`: `assets/projects/templates/icon.png`, a byte copy of `branding/exports/png/icon-512.png`
  (and `assets.icon` in `config/projects/templates.json`).
- `web-templates`: copies the favicon (`favicon/favicon.ico`, `svg/favicon.svg`), Apple touch icon, PWA icons,
  `svg/icon.svg`, the symbol, the lockups and the social image into its own repository. It never reads this
  repository at build or run time.

## To approve

Review `branding/previews/contact-sheet.png`, `branding/previews/concepts-v01.png`, the lockups and
`social/exports/og-image.png`. Then commit this folder, the `ecosystem-config` icon and the `web-templates`
copies together.

To reject, delete `projects/templates/` and its line in the repository README. Also remove any `assets.icon`
line and `assets/projects/templates/` in `ecosystem-config`, and any copies already made in `web-templates`.
The app keeps its inline `LogoMark` either way.
