# Group 1 integration manifest

[Repository overview](../README.md) · [Asset guidelines](asset-guidelines.md) · [Naming conventions](naming-conventions.md)

**Documentation only.** This lists what exists in `ecosystem-assets` for the seven Group 1 icons and how a consumer could use it. Nothing here has been copied into `config-ecosystem` or any application, and nothing is deployed. The hashes identify the exact files audited in A2.10 (2026-10-22) and committed in A3.1a. The CV hashes were refreshed in A3.1d after the optical-balance refinement.

## Ownership (unchanged)

* **ecosystem-assets** owns the SVG masters, the generated exports and their previews.
* **config-ecosystem** owns the canonical record and the *approved public asset reference* (`assets.icon`).
* **Each application** owns its runtime favicon, manifest, `apple-touch-icon`, theme colours and SEO, and copies the files it uses into its own build.

## Overview

| Project ID | Name | Status | Listing | Repository | Deployment |
|---|---|---|---|---|---|
| `cv` | CV | active | public | `web-cv` (private) | https://cv.fikrimarzuki.work/ |
| `playground` | Playground | paused | public | `web-playground` (private) | https://play.fikrimarzuki.work/ |
| `support` | Support | active | public | `web-support` (private) | https://support.fikrimarzuki.work/ |
| `projects` | Projects | active | public | `web-projects` (private) | https://projects.fikrimarzuki.work/ |
| `tools` | Tools | active | public | `web-tools` (private) | https://tools.fikrimarzuki.work/ |
| `configEcosystem` | Config Ecosystem | active | public | `config-ecosystem` (public) | https://fikrimarzuki.github.io/config-ecosystem/ |
| `devtools` | DevTools | active | public | `web-devtools` (private) | https://devtools.fikrimarzuki.work/ |

All seven projects have the same export set (12 files each), listed per project below.

## Handing an icon to config-ecosystem

* The schema accepts `assets.icon` as one path under `assets/projects/<projectId>/` ending in `.png`, `.jpg`, `.jpeg`, `.webp`, `.svg`, `.avif` or `.gif` (`schema/project.schema.json`, `imagePath`). Names may only use letters, digits, `.`, `_` and `-`.
* **Recommended: the 512×512 PNG** as `icon.png`. It is the broadest-compatibility file and every export is 512 px or smaller by design. An SVG would also validate, but consumers must then sanitize and render it.
* config-ecosystem runs `pnpm build` and `pnpm validate` to check that the referenced file exists; commit the file together with the record change, in that repository, as its own commit.
* **Gateway does not use project icons today.** `web-gateway/scripts/public-ecosystem.mjs` projects only `assets.thumbnail` to the browser and withholds `icon`, `logo`, `cover` and `media`. Using icons there needs a deliberate Gateway change.
* `web-cv` is **blocked** in `.github/consumers.json` (as of `config-ecosystem` `a6d716e`). `web-gateway` is compatible; neither is notified automatically (`notify: false`).

## Using the files in an application (templates)

These are templates, not changes to any repository. An application should adapt them to its own framework and conventions.

```html
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
```

```json
"icons": [
  { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any" },
  { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any" },
  { "src": "/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
]
```

* Map: `favicon/favicon.ico` → `/favicon.ico`; `svg/favicon.svg` → `/icon.svg` (the simplified master is the right one for tab sizes); `apple/apple-touch-icon.png` → `/apple-touch-icon.png`; `pwa/*` → the manifest icons.
* Keep `any` and `maskable` as **separate** manifest entries; do not combine purposes on one file. The maskable icon is full-bleed and keeps its symbol inside the central 80% circle.
* Do not hotlink this repository or `raw.githubusercontent.com`; copy the files into the app's build output.
* Colours for `theme_color` / `background_color` are the app's decision; the tile colours in each section are available as a starting point.
* Do not add PWA support to an app only to use these icons.

## CV (`cv`)

| | |
|---|---|
| Canonical project ID | `cv` (matches `config-ecosystem/config/projects/cv.json`) |
| Registry name / status / listing | CV / active / public |
| Repository | `web-cv` (private) |
| Deployment (registry `main`) | https://cv.fikrimarzuki.work/ |
| Source SVG masters | `projects/cv/branding/source/` (`icon.svg`, `tile.svg`, `glyph.svg`, `favicon.svg`, `mono.svg`; checks in `icon.checks.json`) |
| Exports | `projects/cv/branding/exports/` |
| Review sheet | `projects/cv/branding/previews/contact-sheet.png` |
| Tile colours (top → bottom) / edge ring | `#12294d` → `#081426` / `#4a6a96` |
| Optical shift baked into the geometry | 0, -8 (canvas units) |

**Exports (SHA-256 prefixes are of the files at audit time):**

| File | Pixels | Size | SHA-256 | Use |
|---|---|---|---|---|
| `png/icon-512.png` | 512×512 | 62.3 KB | `d56e7769f77f` | Canonical raster icon; PWA `any` 512 |
| `png/icon-192.png` | 192×192 | 21.3 KB | `544e3740fa9d` | PWA `any` 192 |
| `png/icon-maskable-512.png` | 512×512 | 42.4 KB | `9c009be01b15` | PWA `maskable` 512 (opaque, full-bleed) |
| `apple/apple-touch-icon.png` | 180×180 | 12.9 KB | `1b4f1c9aceda` | Apple touch icon, 180×180 (opaque) |
| `favicon/favicon.ico` | 16, 32, 48 | 3.5 KB | `c057a8fc837b` | Multi-size favicon: 16, 32, 48 (PNG frames) |
| `favicon/favicon-32.png` | 32×32 | 1.2 KB | `7fcbd7b7f2b9` | 32×32 favicon |
| `favicon/favicon-16.png` | 16×16 | 0.6 KB | `80a89684dad7` | 16×16 favicon |
| `svg/icon.svg` | vector | 1.0 KB | `2699da5eadfd` | Optimized SVG, rounded tile |
| `svg/favicon.svg` | vector | 0.4 KB | `96c9dbfb51f3` | Optimized SVG, simplified small-size master |
| `pwa/icon-192.png` | 192×192 | 21.3 KB | `544e3740fa9d` | Byte-identical copy of `png/icon-192.png` |
| `pwa/icon-512.png` | 512×512 | 62.3 KB | `d56e7769f77f` | Byte-identical copy of `png/icon-512.png` |
| `pwa/icon-maskable-512.png` | 512×512 | 42.4 KB | `9c009be01b15` | Byte-identical copy of `png/icon-maskable-512.png` |

**Recommended `config-ecosystem` reference:** copy `exports/png/icon-512.png` to `config-ecosystem/assets/projects/cv/icon.png` and set `assets.icon` to `assets/projects/cv/icon.png`.

**Recommended application files:** `favicon/favicon.ico` (+ `svg/favicon.svg` where the app supports SVG favicons), `apple/apple-touch-icon.png`, and only if the app already ships (or wants) a web manifest, the `pwa/` icons.

**Live today (probe of 2026-10-22, read-only; these are the *old* icons, none were replaced):** icon 192x192: 200 (192x192 png); `/favicon.ico` 404; manifest 200, 4 icons, purposes any.

**Integration considerations:**

* The live site publishes a PWA manifest with four `any` icons (192–512) and **no maskable icon**; add `pwa/icon-maskable-512.png` as a separate entry with `"purpose": "maskable"`.
* The live favicon is a 192×192 `icon.png` and `/favicon.ico` returns 404; the exports provide a real multi-size `favicon.ico`.
* The hashed `/icon.png?icon.<hash>.png` URL suggests the Next.js file-based icon convention (inference, not verified: web-cv is private and not available locally).
* `web-cv` is listed as **blocked** in `config-ecosystem/.github/consumers.json`; do not plan automated rollout until its consumer issues are resolved.

## Playground (`playground`)

| | |
|---|---|
| Canonical project ID | `playground` (matches `config-ecosystem/config/projects/playground.json`) |
| Registry name / status / listing | Playground / paused / public |
| Repository | `web-playground` (private) |
| Deployment (registry `main`) | https://play.fikrimarzuki.work/ |
| Source SVG masters | `projects/playground/branding/source/` (`icon.svg`, `tile.svg`, `glyph.svg`, `favicon.svg`, `mono.svg`; checks in `icon.checks.json`) |
| Exports | `projects/playground/branding/exports/` |
| Review sheet | `projects/playground/branding/previews/contact-sheet.png` |
| Tile colours (top → bottom) / edge ring | `#1b1845` → `#0b0922` / `#6a5fa8` |
| Optical shift baked into the geometry | 14, 0 (canvas units) |

**Exports (SHA-256 prefixes are of the files at audit time):**

| File | Pixels | Size | SHA-256 | Use |
|---|---|---|---|---|
| `png/icon-512.png` | 512×512 | 58.6 KB | `01fee3de1acd` | Canonical raster icon; PWA `any` 512 |
| `png/icon-192.png` | 192×192 | 19.3 KB | `1dbe662027a8` | PWA `any` 192 |
| `png/icon-maskable-512.png` | 512×512 | 35.9 KB | `a6ae819daeb7` | PWA `maskable` 512 (opaque, full-bleed) |
| `apple/apple-touch-icon.png` | 180×180 | 10.1 KB | `7ce4787699ef` | Apple touch icon, 180×180 (opaque) |
| `favicon/favicon.ico` | 16, 32, 48 | 3.2 KB | `dd72815e489d` | Multi-size favicon: 16, 32, 48 (PNG frames) |
| `favicon/favicon-32.png` | 32×32 | 1.0 KB | `d6ede8f7d080` | 32×32 favicon |
| `favicon/favicon-16.png` | 16×16 | 0.5 KB | `24e6171ba644` | 16×16 favicon |
| `svg/icon.svg` | vector | 0.9 KB | `9427e79f9766` | Optimized SVG, rounded tile |
| `svg/favicon.svg` | vector | 0.5 KB | `2e3b9709665c` | Optimized SVG, simplified small-size master |
| `pwa/icon-192.png` | 192×192 | 19.3 KB | `1dbe662027a8` | Byte-identical copy of `png/icon-192.png` |
| `pwa/icon-512.png` | 512×512 | 58.6 KB | `01fee3de1acd` | Byte-identical copy of `png/icon-512.png` |
| `pwa/icon-maskable-512.png` | 512×512 | 35.9 KB | `a6ae819daeb7` | Byte-identical copy of `png/icon-maskable-512.png` |

**Recommended `config-ecosystem` reference:** copy `exports/png/icon-512.png` to `config-ecosystem/assets/projects/playground/icon.png` and set `assets.icon` to `assets/projects/playground/icon.png`.

**Recommended application files:** `favicon/favicon.ico` (+ `svg/favicon.svg` where the app supports SVG favicons), `apple/apple-touch-icon.png`, and only if the app already ships (or wants) a web manifest, the `pwa/` icons.

**Live today (probe of 2026-10-22, read-only; these are the *old* icons, none were replaced):** apple-touch-icon: 404; `/favicon.ico` 200; manifest 200, 4 icons, purposes any.

**Integration considerations:**

* The live page links `apple-touch-icon` to `/icon.png`, which **returns 404**; `apple/apple-touch-icon.png` fixes that.
* The live manifest lists four `any` icons (192–512) and no maskable icon.
* The registry status is `paused`; the icon is still part of Group 1.

## Support (`support`)

| | |
|---|---|
| Canonical project ID | `support` (matches `config-ecosystem/config/projects/support.json`) |
| Registry name / status / listing | Support / active / public |
| Repository | `web-support` (private) |
| Deployment (registry `main`) | https://support.fikrimarzuki.work/ |
| Source SVG masters | `projects/support/branding/source/` (`icon.svg`, `tile.svg`, `glyph.svg`, `favicon.svg`, `mono.svg`; checks in `icon.checks.json`) |
| Exports | `projects/support/branding/exports/` |
| Review sheet | `projects/support/branding/previews/contact-sheet.png` |
| Tile colours (top → bottom) / edge ring | `#0c2144` → `#061226` / `#3b7ca8` |
| Optical shift baked into the geometry | 0, 0 (canvas units) |

**Exports (SHA-256 prefixes are of the files at audit time):**

| File | Pixels | Size | SHA-256 | Use |
|---|---|---|---|---|
| `png/icon-512.png` | 512×512 | 56.8 KB | `1527cff5761a` | Canonical raster icon; PWA `any` 512 |
| `png/icon-192.png` | 192×192 | 20.4 KB | `d535345a16db` | PWA `any` 192 |
| `png/icon-maskable-512.png` | 512×512 | 36.3 KB | `983ea10f51b2` | PWA `maskable` 512 (opaque, full-bleed) |
| `apple/apple-touch-icon.png` | 180×180 | 11.2 KB | `459a18edd204` | Apple touch icon, 180×180 (opaque) |
| `favicon/favicon.ico` | 16, 32, 48 | 3.3 KB | `ae0495370bc6` | Multi-size favicon: 16, 32, 48 (PNG frames) |
| `favicon/favicon-32.png` | 32×32 | 1.1 KB | `a817dc4c3807` | 32×32 favicon |
| `favicon/favicon-16.png` | 16×16 | 0.6 KB | `6d81cb624697` | 16×16 favicon |
| `svg/icon.svg` | vector | 1.0 KB | `a49f08a01751` | Optimized SVG, rounded tile |
| `svg/favicon.svg` | vector | 0.7 KB | `e3e8e512ddc2` | Optimized SVG, simplified small-size master |
| `pwa/icon-192.png` | 192×192 | 20.4 KB | `d535345a16db` | Byte-identical copy of `png/icon-192.png` |
| `pwa/icon-512.png` | 512×512 | 56.8 KB | `1527cff5761a` | Byte-identical copy of `png/icon-512.png` |
| `pwa/icon-maskable-512.png` | 512×512 | 36.3 KB | `983ea10f51b2` | Byte-identical copy of `png/icon-maskable-512.png` |

**Recommended `config-ecosystem` reference:** copy `exports/png/icon-512.png` to `config-ecosystem/assets/projects/support/icon.png` and set `assets.icon` to `assets/projects/support/icon.png`.

**Recommended application files:** `favicon/favicon.ico` (+ `svg/favicon.svg` where the app supports SVG favicons), `apple/apple-touch-icon.png`, and only if the app already ships (or wants) a web manifest, the `pwa/` icons.

**Live today (probe of 2026-10-22, read-only; these are the *old* icons, none were replaced):** icon: 200 (svg); `/favicon.ico` 404; no manifest.

**Integration considerations:**

* The live favicon is an inline `data:` SVG (the blue "FM" square) and `/favicon.ico` returns 404; there is no manifest. Do not add PWA support just to use these icons; the favicon and Apple touch files are enough.
* Live title is `Support · FM Work`, which is the display name consumers use; the registry name is `Support`.

## Projects (`projects`)

| | |
|---|---|
| Canonical project ID | `projects` (matches `config-ecosystem/config/projects/projects.json`) |
| Registry name / status / listing | Projects / active / public |
| Repository | `web-projects` (private) |
| Deployment (registry `main`) | https://projects.fikrimarzuki.work/ |
| Source SVG masters | `projects/projects/branding/source/` (`icon.svg`, `tile.svg`, `glyph.svg`, `favicon.svg`, `mono.svg`; checks in `icon.checks.json`) |
| Exports | `projects/projects/branding/exports/` |
| Review sheet | `projects/projects/branding/previews/contact-sheet.png` |
| Tile colours (top → bottom) / edge ring | `#0b2b2b` → `#061817` / `#36856f` |
| Optical shift baked into the geometry | 8, 8 (canvas units) |

**Exports (SHA-256 prefixes are of the files at audit time):**

| File | Pixels | Size | SHA-256 | Use |
|---|---|---|---|---|
| `png/icon-512.png` | 512×512 | 66.3 KB | `5d6b4fa7b264` | Canonical raster icon; PWA `any` 512 |
| `png/icon-192.png` | 192×192 | 19.8 KB | `452a1fe78eec` | PWA `any` 192 |
| `png/icon-maskable-512.png` | 512×512 | 44.9 KB | `b08f3549caaa` | PWA `maskable` 512 (opaque, full-bleed) |
| `apple/apple-touch-icon.png` | 180×180 | 11.5 KB | `9d4d35078c8b` | Apple touch icon, 180×180 (opaque) |
| `favicon/favicon.ico` | 16, 32, 48 | 3.0 KB | `c0fa05bbb275` | Multi-size favicon: 16, 32, 48 (PNG frames) |
| `favicon/favicon-32.png` | 32×32 | 1.0 KB | `a039bc35db7b` | 32×32 favicon |
| `favicon/favicon-16.png` | 16×16 | 0.5 KB | `52e709b0529b` | 16×16 favicon |
| `svg/icon.svg` | vector | 1.7 KB | `d92e70a7ec17` | Optimized SVG, rounded tile |
| `svg/favicon.svg` | vector | 1.1 KB | `7e4c575fd635` | Optimized SVG, simplified small-size master |
| `pwa/icon-192.png` | 192×192 | 19.8 KB | `452a1fe78eec` | Byte-identical copy of `png/icon-192.png` |
| `pwa/icon-512.png` | 512×512 | 66.3 KB | `5d6b4fa7b264` | Byte-identical copy of `png/icon-512.png` |
| `pwa/icon-maskable-512.png` | 512×512 | 44.9 KB | `b08f3549caaa` | Byte-identical copy of `png/icon-maskable-512.png` |

**Recommended `config-ecosystem` reference:** copy `exports/png/icon-512.png` to `config-ecosystem/assets/projects/projects/icon.png` and set `assets.icon` to `assets/projects/projects/icon.png`.

**Recommended application files:** `favicon/favicon.ico` (+ `svg/favicon.svg` where the app supports SVG favicons), `apple/apple-touch-icon.png`, and only if the app already ships (or wants) a web manifest, the `pwa/` icons.

**Live today (probe of 2026-10-22, read-only; these are the *old* icons, none were replaced):** icon 256x256: 200 (ico[256x256]); icon: 200 (ico[256x256]); `/favicon.ico` 200; no manifest.

**Integration considerations:**

* The live favicon is a single 256×256 ICO frame; the exports provide 16/32/48 frames.
* The live `og:image` (`/og.png`) **returns 404**. That is a social-preview issue, separate from these icons.
* The registry ID is `projects` and the folder is `projects/projects/`; this is correct, not a typo.

## Tools (`tools`)

| | |
|---|---|
| Canonical project ID | `tools` (matches `config-ecosystem/config/projects/tools.json`) |
| Registry name / status / listing | Tools / active / public |
| Repository | `web-tools` (private) |
| Deployment (registry `main`) | https://tools.fikrimarzuki.work/ |
| Source SVG masters | `projects/tools/branding/source/` (`icon.svg`, `tile.svg`, `glyph.svg`, `favicon.svg`, `mono.svg`; checks in `icon.checks.json`) |
| Exports | `projects/tools/branding/exports/` |
| Review sheet | `projects/tools/branding/previews/contact-sheet.png` |
| Tile colours (top → bottom) / edge ring | `#161a24` → `#0a0c12` / `#8f6b2c` |
| Optical shift baked into the geometry | 0, 16 (canvas units) |

**Exports (SHA-256 prefixes are of the files at audit time):**

| File | Pixels | Size | SHA-256 | Use |
|---|---|---|---|---|
| `png/icon-512.png` | 512×512 | 64.8 KB | `2b30d2de23c5` | Canonical raster icon; PWA `any` 512 |
| `png/icon-192.png` | 192×192 | 20.3 KB | `998854976a36` | PWA `any` 192 |
| `png/icon-maskable-512.png` | 512×512 | 41.2 KB | `2c31f4f6ae48` | PWA `maskable` 512 (opaque, full-bleed) |
| `apple/apple-touch-icon.png` | 180×180 | 11.3 KB | `54402994df52` | Apple touch icon, 180×180 (opaque) |
| `favicon/favicon.ico` | 16, 32, 48 | 3.1 KB | `ffa9972523cd` | Multi-size favicon: 16, 32, 48 (PNG frames) |
| `favicon/favicon-32.png` | 32×32 | 1.0 KB | `c54498841faf` | 32×32 favicon |
| `favicon/favicon-16.png` | 16×16 | 0.5 KB | `be9d6a20bacf` | 16×16 favicon |
| `svg/icon.svg` | vector | 1.2 KB | `82fc89259a61` | Optimized SVG, rounded tile |
| `svg/favicon.svg` | vector | 0.9 KB | `2552726eb6bd` | Optimized SVG, simplified small-size master |
| `pwa/icon-192.png` | 192×192 | 20.3 KB | `998854976a36` | Byte-identical copy of `png/icon-192.png` |
| `pwa/icon-512.png` | 512×512 | 64.8 KB | `2b30d2de23c5` | Byte-identical copy of `png/icon-512.png` |
| `pwa/icon-maskable-512.png` | 512×512 | 41.2 KB | `2c31f4f6ae48` | Byte-identical copy of `png/icon-maskable-512.png` |

**Recommended `config-ecosystem` reference:** copy `exports/png/icon-512.png` to `config-ecosystem/assets/projects/tools/icon.png` and set `assets.icon` to `assets/projects/tools/icon.png`.

**Recommended application files:** `favicon/favicon.ico` (+ `svg/favicon.svg` where the app supports SVG favicons), `apple/apple-touch-icon.png`, and only if the app already ships (or wants) a web manifest, the `pwa/` icons.

**Live today (probe of 2026-10-22, read-only; these are the *old* icons, none were replaced):** icon 256x256: 200 (ico[256x256]); `/favicon.ico` 200; no manifest.

**Integration considerations:**

* The live favicon is a single 256×256 ICO frame (yellow bolt); there is no manifest and no Open Graph image.
* Live title is `MFM Tools — Free Browser-Based Utilities`.

## Config Ecosystem (`configEcosystem`)

| | |
|---|---|
| Canonical project ID | `configEcosystem` (matches `config-ecosystem/config/projects/configEcosystem.json`) |
| Registry name / status / listing | Config Ecosystem / active / public |
| Repository | `config-ecosystem` (public) |
| Deployment (registry `main`) | https://fikrimarzuki.github.io/config-ecosystem/ |
| Source SVG masters | `projects/configEcosystem/branding/source/` (`icon.svg`, `tile.svg`, `glyph.svg`, `favicon.svg`, `mono.svg`; checks in `icon.checks.json`) |
| Exports | `projects/configEcosystem/branding/exports/` |
| Review sheet | `projects/configEcosystem/branding/previews/contact-sheet.png` |
| Tile colours (top → bottom) / edge ring | `#0b2733` → `#05141b` / `#2f8186` |
| Optical shift baked into the geometry | 8, 0 (canvas units) |

**Exports (SHA-256 prefixes are of the files at audit time):**

| File | Pixels | Size | SHA-256 | Use |
|---|---|---|---|---|
| `png/icon-512.png` | 512×512 | 69.4 KB | `98cae538e91f` | Canonical raster icon; PWA `any` 512 |
| `png/icon-192.png` | 192×192 | 23.6 KB | `2a59493049a7` | PWA `any` 192 |
| `png/icon-maskable-512.png` | 512×512 | 45.7 KB | `1beb7bf14474` | PWA `maskable` 512 (opaque, full-bleed) |
| `apple/apple-touch-icon.png` | 180×180 | 13.8 KB | `29442472c0a3` | Apple touch icon, 180×180 (opaque) |
| `favicon/favicon.ico` | 16, 32, 48 | 4.0 KB | `d27ea82dd850` | Multi-size favicon: 16, 32, 48 (PNG frames) |
| `favicon/favicon-32.png` | 32×32 | 1.3 KB | `209c41f79aee` | 32×32 favicon |
| `favicon/favicon-16.png` | 16×16 | 0.6 KB | `e1cb7fd48c81` | 16×16 favicon |
| `svg/icon.svg` | vector | 1.3 KB | `d5a3ccfa55ce` | Optimized SVG, rounded tile |
| `svg/favicon.svg` | vector | 0.9 KB | `cf864491acda` | Optimized SVG, simplified small-size master |
| `pwa/icon-192.png` | 192×192 | 23.6 KB | `2a59493049a7` | Byte-identical copy of `png/icon-192.png` |
| `pwa/icon-512.png` | 512×512 | 69.4 KB | `98cae538e91f` | Byte-identical copy of `png/icon-512.png` |
| `pwa/icon-maskable-512.png` | 512×512 | 45.7 KB | `1beb7bf14474` | Byte-identical copy of `png/icon-maskable-512.png` |

**Recommended `config-ecosystem` reference:** copy `exports/png/icon-512.png` to `config-ecosystem/assets/projects/configEcosystem/icon.png` and set `assets.icon` to `assets/projects/configEcosystem/icon.png`.

**Recommended application files:** `favicon/favicon.ico` (+ `svg/favicon.svg` where the app supports SVG favicons), `apple/apple-touch-icon.png`, and only if the app already ships (or wants) a web manifest, the `pwa/` icons.

**Live today (probe of 2026-10-22, read-only; these are the *old* icons, none were replaced):** icon: 200 (svg); `/favicon.ico` 404; no manifest.

**Integration considerations:**

* This icon belongs to the VitePress documentation site of the `config-ecosystem` repository itself. Its favicon is `docs/public/favicon.svg`, linked from `docs/.vitepress/config.mjs` as `${base}favicon.svg`; replacing it means a change **inside config-ecosystem**, separate from adding the registry's `assets.icon` reference.
* The registry URL `https://fikrimarzuki.github.io/config-ecosystem/` redirects to `http://config.fikrimarzuki.work/` (HTTP, not HTTPS) as observed; that is a hosting issue outside this milestone.
* No manifest and `/favicon.ico` returns 404 today.

## DevTools (`devtools`)

| | |
|---|---|
| Canonical project ID | `devtools` (matches `config-ecosystem/config/projects/devtools.json`) |
| Registry name / status / listing | DevTools / active / public |
| Repository | `web-devtools` (private) |
| Deployment (registry `main`) | https://devtools.fikrimarzuki.work/ |
| Source SVG masters | `projects/devtools/branding/source/` (`icon.svg`, `tile.svg`, `glyph.svg`, `favicon.svg`, `mono.svg`; checks in `icon.checks.json`) |
| Exports | `projects/devtools/branding/exports/` |
| Review sheet | `projects/devtools/branding/previews/contact-sheet.png` |
| Tile colours (top → bottom) / edge ring | `#0d1740` → `#050a22` / `#4468c8` |
| Optical shift baked into the geometry | 0, 0 (canvas units) |

**Exports (SHA-256 prefixes are of the files at audit time):**

| File | Pixels | Size | SHA-256 | Use |
|---|---|---|---|---|
| `png/icon-512.png` | 512×512 | 53.2 KB | `ec21de86041a` | Canonical raster icon; PWA `any` 512 |
| `png/icon-192.png` | 192×192 | 17.6 KB | `f8f3b1ddbc6f` | PWA `any` 192 |
| `png/icon-maskable-512.png` | 512×512 | 34.1 KB | `eb736c489674` | PWA `maskable` 512 (opaque, full-bleed) |
| `apple/apple-touch-icon.png` | 180×180 | 10.5 KB | `cfae50f8f185` | Apple touch icon, 180×180 (opaque) |
| `favicon/favicon.ico` | 16, 32, 48 | 2.6 KB | `66e92a0c97da` | Multi-size favicon: 16, 32, 48 (PNG frames) |
| `favicon/favicon-32.png` | 32×32 | 0.9 KB | `88338b6af54c` | 32×32 favicon |
| `favicon/favicon-16.png` | 16×16 | 0.5 KB | `178cc3ba72d0` | 16×16 favicon |
| `svg/icon.svg` | vector | 0.9 KB | `d844288ce8be` | Optimized SVG, rounded tile |
| `svg/favicon.svg` | vector | 0.6 KB | `a8fa2178a3a4` | Optimized SVG, simplified small-size master |
| `pwa/icon-192.png` | 192×192 | 17.6 KB | `f8f3b1ddbc6f` | Byte-identical copy of `png/icon-192.png` |
| `pwa/icon-512.png` | 512×512 | 53.2 KB | `ec21de86041a` | Byte-identical copy of `png/icon-512.png` |
| `pwa/icon-maskable-512.png` | 512×512 | 34.1 KB | `eb736c489674` | Byte-identical copy of `png/icon-maskable-512.png` |

**Recommended `config-ecosystem` reference:** copy `exports/png/icon-512.png` to `config-ecosystem/assets/projects/devtools/icon.png` and set `assets.icon` to `assets/projects/devtools/icon.png`.

**Recommended application files:** `favicon/favicon.ico` (+ `svg/favicon.svg` where the app supports SVG favicons), `apple/apple-touch-icon.png`, and only if the app already ships (or wants) a web manifest, the `pwa/` icons.

**Live today (probe of 2026-10-22, read-only; these are the *old* icons, none were replaced):** icon 256x256: 200 (ico[16x16,32x32,48x48,256x256]); `/favicon.ico` 200; no manifest.

**Integration considerations:**

* The live favicon is the framework-default 4-frame ICO (16/32/48/256); there is no manifest and no Open Graph image.
* Live title is `MFM Utils`, which differs from the registry name `DevTools`.

## Verification state at audit time

**Verified (mechanical):** all seven icons pass `pnpm verify:icons` (627 checks, 0 warnings, 0 failures); a full `pnpm build:icons` reproduced all 177 files under `projects/` byte for byte; dimensions, ICO frames, SVG validity and opacity were also cross-checked with system tools (`file`, `sips`, `xmllint`).

**Not verified:** rendering on real devices (iOS/Android home screens, Safari), loading the icons through real pages and manifests, installability, and whether the artwork looks good (that is a human review of the contact sheets). Exports were generated and checked on one platform (macOS, Playwright 1.64.0, Chromium 156); byte-identical output on another OS or browser version is not guaranteed.

**Requires user action:** pushing the commits, deciding which icons to hand to `config-ecosystem`, and any change to the applications.
