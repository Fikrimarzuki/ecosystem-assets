# Imported asset collections

On 2026-10-23 the existing local collections were **copied**, preserving their internal paths and file bytes. The original workspaces remain in place so existing application scripts and historical links continue to work.

| Original workspace path | Repository location | Contents |
| --- | --- | --- |
| `gateway-assets/` | [`projects/gateway/`](../projects/gateway/NOTES.md) | Astronaut, spacecraft, Blender planet scenes and exports, inspection tools, milestone production scripts and review evidence |
| `scriptoria-assets/` | [`projects/scriptoria/`](../projects/scriptoria/NOTES.md) | Explorer source, optimized meshes, rigs, animations, previews, Blender scripts and reports |
| `momee/assets/.local-assets/` | [`incoming/momee/local-assets/`](../incoming/momee/NOTES.md) | M0.3c working character images, layers, candidate-specific tools and review screenshots |

`gateway` and `scriptoria` match canonical IDs in `config-ecosystem/config/projects/`. Momee has no registry record at import time. Its collection is held under `incoming/` until a canonical ID is established; no registry metadata or public asset reference was added by this import.

## Snapshot and verification

[`collection-import.json`](collection-import.json) records the original root, destination root, every included relative path, byte count and SHA-256, and every excluded file or directory. Run:

```sh
pnpm verify:collections
```

This checks the imported files against the snapshot without needing the original directories. Git LFS files must be hydrated (`git lfs pull` on a fresh clone). The manifest describes the initial import, not a continuously synchronized mirror. If an imported file is deliberately revised, keep its new production history and update its manifest entry as part of that change.

Files pruned after the import (for example the 296 redundant Scriptoria preview renders removed on 2026-10-26) are removed from `files` and listed under `excluded` with the reason, so `pnpm verify:collections` stays meaningful. Python caches, logs, Blender backups, temporary files and disposable Playwright run directories were omitted. Milestone screenshots, reports and scripts outside those run directories were retained as production history. The manifest lists the precise exclusions; these remain available in the original workspaces.

Some imported text files had CRLF or mixed line endings when the snapshot was hashed, while Git holds their LF-normalized versions (112 files: 94 CRLF, 18 mixed). The active manifest records the committed bytes; the original import sizes and hashes, with the exact CR positions needed to reproduce them, are preserved in [`collection-import-line-endings.json`](collection-import-line-endings.json). For future imports, calculate checksums from the exact bytes intended for version control.

## Imported layout and approval

These are legacy collections, so existing names and layouts are preserved rather than forcing mixed historical material into `source/` and `exports/`. Follow the usual repository conventions for new work. A planet's nested `games/` or `tools/` folder belongs to Gateway's scene, not to another project's top-level assets.

An import does **not** approve a candidate, certify rights, or make an export public. Existing provenance records and limitations remain authoritative. Momee's generation record explicitly marks rights as unverified. Review provenance and rights before committing affected assets or approving public use. No file was copied into `config-ecosystem` or an application's runtime assets.

Imported scripts and reports are preserved byte for byte, including historical absolute paths, sibling-repository imports and recorded file locations. They are historical production tools, not newly supported root-level commands. Review their input and output paths before running them; some still write to the original workspace. Future tooling changes should target this repository explicitly.

## Binary storage

Git LFS is available on the import machine. [`.gitattributes`](../.gitattributes) routes the imported Blender sources, Gateway FBX sources, NumPy diagnostic archives and review videos through LFS. This includes a diagnostic archive over 100 MiB. Small GLB web exports and raster images remain in ordinary Git; raster-heavy preview history still contributes substantially to clone size.

Install Git LFS and run `git lfs install --local` in each clone before committing or pushing these types. This import does not migrate existing Git history.
