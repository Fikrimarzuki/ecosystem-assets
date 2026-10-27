# Links branding

Brand identity for **Links** (FM Work Links), registry ID `links` in `ecosystem-config`
(`config/projects/links.json`). Status: **candidate, awaiting owner approval** (2026-10-30, Links M1.5).
Nothing here is approved until the owner commits it.

## Direction

**Link Network, "quarter fan".** A marigold hub (the one short address) connected to three destinations
placed a quarter circle apart, at 90°, 45° and 0°. The silhouette also reads as an L. It is built from filled
circles and bars only, so it holds at 16 px. The palette is the Links app's own: Signal `#2b50d6` tile (gradient
`#3056e0` → `#2443c6`, ring `#5a7cf0`), destinations `#ffffff`, hub Marigold `#f5b83d`, ink `#18203a`.

The wordmark is hand-drawn monoline lettering (stroke 16 on a 112 line, round caps); the i-dot is the
marigold hub. It needs no font to render or edit.

Concepts explored (kept for provenance, never shipped), compared in `branding/previews/concepts-v01.png`:

| Concept | File | Decision |
| --- | --- | --- |
| A. Network hub | `branding/concepts/network-hub-v01.svg` | **Chosen**, then refined: equal radius, quarter-circle placement, optical shift |
| B. Chain L | `branding/concepts/chain-l-v01.svg` | Rejected: chain links are a stock "link" icon; weak interlock |
| C. Stacked list | `branding/concepts/stacked-list-v01.svg` | Rejected: reads as a generic list icon |

The tile is brighter than the Group 1 family's navy tiles on purpose: Links isn't a Group 1 project, and the
tile matches the app. Its ring passes 3:1 on white, `#0d1117` and black.

## Files

| Path | Kind | Purpose |
| --- | --- | --- |
| `branding/source/{icon,tile,glyph,favicon,mono}.svg` | masters | Standard icon masters ([naming](../../docs/naming-conventions.md)) |
| `branding/source/icon.checks.json` | config | Optical shift (12, -12), small-size structure rules, colour probes |
| `branding/exports/**` | generated | `pnpm build:icons links`: favicon.ico/16/32, apple-touch-icon, 192/512, maskable 512, SVG |
| `branding/previews/contact-sheet.png` | preview | `pnpm contact-sheet links` |
| `logo/source/wordmark.svg` | master | The "Links" lettering (ink placeholder `#18203a`) |
| `logo/exports/lockup-light.svg`, `lockup-dark.svg` | generated | Horizontal lockup for light and dark backgrounds |
| `logo/exports/symbol.svg` | generated | Symbol only, transparent |
| `social/exports/og-image.png` | generated | 1200×630 Open Graph / social preview |

`pnpm build:logos links` composes the lockups, symbol and social image from the masters above, so they can't
drift from the icon; `pnpm verify:logos links` checks they are current, deterministic and within budget.

## Checks run (2026-10-30)

- `pnpm verify:icons links`: 92 passed, 0 warnings, 0 failed.
- `pnpm verify:logos links`: all checks passed.
- Contact sheet reviewed at 512, 192, 64, 32 and 16 px on light and dark backgrounds.

## Consumers

- `ecosystem-config`: `assets/projects/links/icon.png` is a byte copy of `branding/exports/png/icon-512.png`.
- `web-links`: copies the favicon, Apple touch icon, PWA icons, symbol, lockups and social image into its own
  repository (see its README, "Brand assets"); it never reads this repository at build or run time.

## To approve

Review the contact sheet and `social/exports/og-image.png`, then commit this folder, the `ecosystem-config`
icon and the `web-links` copies together. To reject, delete `projects/links/`, the `assets.icon` line and
`assets/projects/links/` in `ecosystem-config`, and the copies in `web-links/public/brand` (the app then has no
icon files and needs the old ones back).
