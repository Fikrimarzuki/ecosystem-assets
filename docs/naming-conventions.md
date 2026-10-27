# Naming conventions

[Repository overview](../README.md) · [Asset guidelines](asset-guidelines.md)

Names follow the same character rules as `config-ecosystem`, so an approved file can be copied there unchanged. Use only letters, digits, `.`, `_` and `-`. No spaces, no leading dots, no non-ASCII characters. Keep letter case exact, since macOS is case-insensitive and Linux CI is not.

## Folders

| Kind | Convention | Example |
| --- | --- | --- |
| Project | Canonical project ID: camelCase, a lowercase letter then letters and digits | `projects/cv/`, `projects/configEcosystem/` |
| Asset kind | lowercase, one word | `branding`, `concepts`, `source`, `exports`, `previews` |
| Group or family | lowercase | `shared/branding/group1/` |
| Export format | lowercase | `svg`, `png`, `favicon`, `apple`, `pwa` |

Never invent a project ID. If the project has no record in `config-ecosystem`, add it there first before publication. The owner's M1.0e instruction explicitly names `projects/momee/` as a provisional production workspace; its registry status remains open.

An existing collection awaiting registration may be held in `incoming/<repositoryName>/` without creating a canonical ID. Imported legacy collections preserve their existing filenames and internal hierarchy for provenance; apply these naming conventions to new work. See [collection imports](collection-imports.md).

## Source files

Standard branding masters in `source/`:

| File | Meaning |
| --- | --- |
| `icon.svg` | Rounded tile with the symbol, full detail |
| `tile.svg` | Full-bleed square, source for maskable and Apple icons |
| `glyph.svg` | Symbol only, transparent |
| `favicon.svg` | Deliberately simplified small-size master |
| `mono.svg` | Single-colour symbol |

Other sources use a descriptive lowercase kebab-case name: `hero-scene.blend`, `bird-rig.blend`, `pillow-v1.kra`, `reward-flower-v1.svg`. Momee keeps editable raster masters in Krita format and vector masters in SVG.

## Exports

Use the conventional web names so they work without renaming:

| File | Meaning |
| --- | --- |
| `icon-512.png`, `icon-192.png` | Raster "any" icons |
| `icon-maskable-512.png` | Opaque full-bleed maskable icon |
| `favicon.ico`, `favicon-32.png`, `favicon-16.png` | Browser favicons |
| `apple-touch-icon.png` | 180x180, opaque |

Put the pixel size in the name when there is more than one (`icon-192.png`). Do not append `final`, `new` or dates.

## Concepts, previews and versions

* Concepts and previews carry a two-digit version: `name-v01.png`, `name-v02.png`. A new iteration is a new file; old ones are kept until they are clearly obsolete.
* References are never edited or overwritten. Add a new versioned file.
* Preview files describe their content: `favicon-sizes-light.png`, `maskable-masks.png`.

## Extensions

Lowercase only: `.svg`, `.png`, `.webp`, `.jpg`, `.ico`, `.blend`. This also matches the extensions `config-ecosystem` accepts for project images (`.png`, `.jpg`, `.jpeg`, `.webp`, `.svg`, `.avif`, `.gif`).

## Reference file in use

`references/branding/group1-refined-concept.png`: kind (`branding`), subject (`group1`), role (`refined-concept`).
