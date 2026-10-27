# Momee working asset collection

Copied from `momee/assets/.local-assets/` on 2026-10-23 into `local-assets/`, preserving its milestone hierarchy:

- `m0.3c.1/`: Boy candidate, generation provenance, image preparation tools, working images and separated layers.
- `m0.3c.2/`: cutout proof-of-concept review screenshots and inspection tooling.

Momee does not yet have a canonical record in `config-ecosystem/config/projects/`. This is an intake location, not a new registry ID. Once that ID is established, promote this collection into `projects/<canonicalId>/` and update the import manifest paths and documentation.

The original local files remain in Momee because `assets:poc` and `assets:poc:check` read them there. Momee's committed `assets/production/`, `assets/references/`, runtime files and their manifest paths were not changed. Those external references in generation records remain relative to the original Momee repository.

These working images are not approved production exports. `local-assets/m0.3c.1/boy/generation-log.json` preserves the known generation details, unconfirmed prompt history and unverified rights status. See the [import guide](../../docs/collection-imports.md) and [checksum manifest](../../docs/collection-import.json).
