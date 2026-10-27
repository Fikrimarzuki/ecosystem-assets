# Ecosystem Assets

Private repository for the **creative source files and asset production** behind my personal developer ecosystem: branding and icons, 2D illustrations, 2.5D artwork, 3D models and Blender sources, characters, environments, animations, audio, and the production exports made from them.

## Ownership

| Repository | Owns |
| --- | --- |
| **ecosystem-assets** (this repo) | Creative source files, concept work, asset production and the production exports made from them. |
| [config-ecosystem](../config-ecosystem) | Canonical project metadata and the **approved public asset references** (`assets.icon`, `assets.logo`, ...). |
| Individual applications | Their own **runtime asset integration**: favicon, manifest, SEO metadata and the copies of files they ship. |

Nothing here is read by an application at build time. An asset reaches a site only after it is approved, copied into `config-ecosystem` or an app, and referenced there. See [docs/asset-guidelines.md](docs/asset-guidelines.md).

## Structure

Project-first. Directories are created only when there is something to put in them.

```text
references/
  branding/              approved reference and concept sheets
incoming/
  momee/                 working collection awaiting a canonical registry ID
projects/
  <projectId>/           canonical project ID from config-ecosystem
  momee/                 proposed production workspace (registry ID pending)
    branding/
      concepts/          exploration, never shipped
      source/            hand-authored masters (SVG, ...)
      exports/           generated, production-ready files
      previews/          contact sheets and review images
  gateway/               imported models, planets and production history
  scriptoria/            imported Explorer character production collection
shared/
  branding/
    group1/              assets and notes shared by the Group 1 family
scripts/                 icon build, verify and contact-sheet tooling
docs/                    guidelines and conventions
```

The Group 1 personal ecosystem icons cover `cv`, `playground`, `support`, `projects`, `tools`, `configEcosystem` and `devtools`. `projects/cv/branding/concepts/` also keeps the CV design history. Gateway and Scriptoria include their existing 3D asset production collections. Momee's imported local collection remains under `incoming/momee/`; its proposed [production workspace](projects/momee/README.md) records recovery and export rules without promoting the intake or claiming a confirmed registry ID. Imported collections retain their original internal layouts; new asset kinds get their own folders under `projects/<projectId>/` when the first file exists. See [docs/asset-guidelines.md](docs/asset-guidelines.md#adding-a-new-project).

## Current contents

* [references/branding/group1-refined-concept.png](references/branding/group1-refined-concept.png): the approved Group 1 concept sheet (CV, Support, Playground, Projects, Tools, DevTools, Config Ecosystem). It is a conceptual reference, not a production asset.
* [shared/branding/group1/](shared/branding/group1/README.md): notes on the Group 1 family.
* [projects/gateway/](projects/gateway/NOTES.md): astronaut, spacecraft, Blender planet sources, exports and milestone production history.
* [projects/scriptoria/](projects/scriptoria/NOTES.md): Explorer character sources, optimization, rigs, animation, previews and tooling.
* [incoming/momee/](incoming/momee/NOTES.md): local character candidates, image layers, tools and review evidence.
* [projects/momee/](projects/momee/README.md): proposed production workspace, manifest, recovery snapshot and pillow pilot specification. No approved Momee exports exist.
* [projects/links/](projects/links/README.md): Links icon set, wordmark, lockups and social image (candidate awaiting owner approval).
* [projects/templates/](projects/templates/README.md): Templates swatch-fan icon set, outlined wordmark, lockups and social image (candidate awaiting owner approval).

## Documentation

The [EA2 asset catalog](docs/catalog.md) generates a private inventory, an explicit-approval public catalog, and a validation report. It does not publish or copy assets.

The [EA3–EA5B Asset Studio website](docs/website.md) presents approved work as grouped showcases with image galleries, detail pages, project collections, and an email request action. Preview publication and original downloads require separate rights and SHA-256 approvals. The real approval lists remain empty, so the current site has no public showcases and is not deployed.

| Guide | Contents |
| --- | --- |
| [Asset guidelines](docs/asset-guidelines.md) | Private source policy, source vs export, approval workflow, adding projects and branding, large binaries, Git LFS |
| [Naming conventions](docs/naming-conventions.md) | Folder, file and version naming |
| [Group 1 integration manifest](docs/group1-integration-manifest.md) | Per-project file locations, hashes, recommended consumer usage and integration notes for the seven icons (documentation only) |
| [Collection imports](docs/collection-imports.md) | Original locations, preserved layouts, exclusions, checksum verification and LFS policy for Gateway, Scriptoria and Momee |

## Tooling

Requires Node 24 and pnpm (`pnpm install`). Imported Blender sources, binary diagnostic samples and review videos use Git LFS: install it, run `git lfs install --local`, then `git lfs pull` after cloning. Chromium for icon tooling is taken from the local Playwright cache; nothing is installed globally by these scripts.

| Command | What it does |
| --- | --- |
| `pnpm verify:collections` | Checks every imported file's byte count and SHA-256 against the initial import manifest; original workspaces are not required. |
| `pnpm verify:momee` | Checks the Momee manifest and recovery snapshot: IDs, paths, formats, PNG dimensions, checksums and approval gate. |
| `pnpm build:icons [projectId]` | Regenerates every export of each project that has `branding/source/icon.svg` (or one project). Exports are fully regenerated, so never edit them by hand. `--out <dir>` writes elsewhere. |
| `pnpm verify:icons [projectId]` | Mechanical checks: SVG hygiene, PNG and ICO structure, safe areas, maskable crop, file budgets, contrast, small-size structure, deterministic builds and up-to-date exports. Exit code 1 on failure. |
| `pnpm compare-sheet <projectId> <variant>...` | Renders `branding/previews/variant-comparison.png`: the approved concept, the current production icon and candidate variants side by side. Nothing is replaced. |
| `pnpm pair-sheet <projectId> <variant>` | Renders `branding/previews/<variant>-comparison.png`: the current production icon (A) and one candidate variant (B) at identical displayed sizes, with close-ups. Nothing is replaced. |
| `pnpm contact-sheet [projectId]` | Renders `branding/previews/contact-sheet.png` from the committed exports for human review. |

Candidate variants live in `projects/<id>/branding/concepts/<variant>/source`. Pass `--variant <name>` to `build:icons` to generate its (git-ignored) exports, then to `verify:icons` to check them, without touching production exports. See [the CV design history](projects/cv/branding/concepts/README.md).

`verify:icons` does **not** judge whether artwork looks good or how it renders on real devices; review the contact sheet for that. Per-icon expectations live in `projects/<id>/branding/source/icon.checks.json`. Source SVGs mark the background group `id="bg"` and the symbol `id="glyph"` so the scripts can measure the symbol on its own. Implementation is in [scripts/](scripts/).

## Private source policy

This repository is private. Do not publish its contents or make it public without reviewing what it contains. Only explicitly approved previews and downloads leave it, and they leave by copying (see the guidelines). Never commit secrets, client or employer material, or unlicensed third-party assets.
