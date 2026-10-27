# Asset catalog (EA2–EA5B)

The catalog is an inventory of physical files, not a replacement for production manifests or an approval system for applications. `scripts/lib/catalog.mjs` discovers files under the explicit roots in [`catalog/config.json`](../catalog/config.json). It never scans the whole repository, follows symlinks, fetches Git LFS objects, or copies asset binaries. The roots are `projects/`, `incoming/`, `references/`, and `shared/`. Generated site output and dependencies are outside those roots; disposable nested output directories listed in the config are skipped. Tracked historical review evidence inside `incoming/.../checks/` remains in the inventory.

## Commands and outputs

With Node 24 or later and the existing dependencies installed:

```sh
node scripts/catalog.mjs build
node scripts/catalog.mjs validate
node --test scripts/catalog.test.mjs
```

The corresponding package scripts are `catalog:build`, `catalog:validate`, and `test:catalog`. `build` writes three deterministic JSON files to the ignored `catalog-output/` directory:

| File | Purpose |
| --- | --- |
| `internal.json` | Complete private inventory, including source metadata and logical groups. Never place it in a public build. |
| `public.json` | Explicitly approved legacy export records and showcase entries; currently empty. It contains no private records, manifest metadata, or asset binaries. |
| `validation.json` | Errors, warnings, and counts for internal review. Never place it in a public build. |

`validate` performs the same discovery and checks without writing outputs. Both commands exit nonzero for validation errors. Warnings do not block generation because legacy naming, missing editorial fields, intentional copies, and private draft assets are expected. Output order and JSON formatting are stable for identical input bytes and configuration. No timestamps or machine-specific absolute paths are included.

## Schema and IDs

[`catalog/schema-v1.json`](../catalog/schema-v1.json) describes catalog version 1. Each physical record has `id`, `projectId`, repository-relative `path`, `role`, `category`, `format`, byte size, SHA-256, `publication`, and `rightsStatus`. Extracted `dimensions` and editorial fields are optional. An ID is `file:` followed by the exact normalized repository-relative path, for example `file:projects/cv/branding/exports/png/icon-512.png`. The ID remains stable while the path remains stable. A rename is an explicit catalog migration and must update any approval reference. Names alone never identify a physical record.

`logicalAssets` is a small relationship layer. The Momee manifest contributes groups whose IDs are `momee:<existing-id>` and whose `legacyId` preserves the original identifier. The Group 1 integration document contributes seven `group1:<projectId>:icon` groups from its explicit source, export, and review paths. One physical file may belong to multiple Momee groups. Unmapped files remain ungrouped; filenames are never used to guess relationships. Public logical groups contain approved physical IDs only and omit private status and lineage.

Optional titles, descriptions, tags, versions, category corrections, and explicit `relatedAssetIds` belong in [`catalog/metadata.json`](../catalog/metadata.json), keyed by physical ID. It starts empty. Unknown IDs and broken related IDs are validation errors. This file is private editorial input and is never copied into `public.json`; the generated public record may include its category after explicit publication approval.

Roles describe the file's current repository function: `source`, `export`, `candidate`, `review`, `reference`, or `legacy`. Legacy collections retain their structure and may receive the conservative `legacy` role. `category: "uncategorized"` is a warning for later editorial review, not an invented classification. Project IDs under `incoming/` are intake labels and are not proof of registry membership.

## Existing metadata

- [`docs/collection-import.json`](collection-import.json) supplies import provenance and historical hashes. A changed snapshot hash is a warning because deliberate revisions are possible.
- [`projects/momee/manifest.json`](../projects/momee/manifest.json) supplies logical IDs, statuses, categories, dimensions, checksums, and rights for referenced physical files. Existing values and schema remain authoritative and unchanged. Its candidates and working assets stay private.
- [`docs/group1-integration-manifest.md`](group1-integration-manifest.md) supplies explicit Group 1 relationships. Its project listing and recommended consumer usage do **not** grant publication approval or verify rights.

If a manifest references a missing asset, generation reports an error. Checksum or dimension disagreements are warnings requiring review; discovery records the actual bytes. `sourceMetadata` and all manifest provenance remain internal.

## Publication workflow

[`catalog/publications.json`](../catalog/publications.json) is the publication authority in this repository. It starts with an empty `approved` array. Nothing is public by default, including files under `exports/` and the existing Group 1 icons. An owner-approved entry must refer to the exact physical catalog ID and provide verified rights, an approver, and an approval date:

```json
{
  "id": "file:projects/cv/branding/exports/png/icon-512.png",
  "sha256": "<64 lowercase hex characters for the approved file bytes>",
  "rightsStatus": "verified",
  "approvedBy": "owner name",
  "approvedOn": "YYYY-MM-DD"
}
```

This is an example of the format, **not an approved entry**. Review ownership, provenance, licence, the exact file hash, and intended public use before adding one. The generator refuses unknown IDs, non-export roles, Momee paths, changed bytes, unresolved rights, and records whose existing manifest reports restricted or unverified rights. An approval assertion is an explicit owner decision about rights; it is not inferred from a project listing or directory. Review the generated public JSON and validation report before any future deployment. Existing consumer-copy workflows stay separate.

The public catalog is a projection of approved technical fields. It omits internal provenance and private editorial fields, even if they are later added to a private record. An approval entry may explicitly include `title`, `description`, and `tags` as public copy; these fields are checked and then projected into the public record. A published record also has a deterministic `url` under `/published/`, derived from the SHA-256 of its physical ID and its format. The schema remains version 1, with these optional fields added to the shared record shape. Published records always have `url`; private records do not. Hiding a private entry in a UI is not a publication control.

EA4 copies only those approved export bytes into the website build. The preparation step checks the source path, symlinks, size, and SHA-256. The output audit requires exactly one matching binary per public catalog record. No real approval was added in EA4.

## Showcase publication (EA5B)

The optional `showcases` array in `catalog/publications.json` adds a showcase-first presentation layer without changing physical IDs or legacy `approved` entries. Its three public states are:

| State | Public result |
| --- | --- |
| Private | No catalog entry or binary is delivered. This is the default. |
| Showcase | Approved metadata and explicitly approved preview media are delivered. Source and export files remain private. |
| Downloadable | The showcase is visible and separately approved export files are delivered as download options. |

A showcase is one editorial entry at `<projectId>/<slug>`, such as `cv/icon`, with an ordered `media` array and optional `downloads` array. `logicalAssetId` may cite an existing group when all referenced files belong to it. An ungrouped work can be assembled by listing exact physical `assetId` values. The generator never groups by similar filenames. `relatedShowcaseIds` may cite only other published entries. The public projection omits physical IDs, repository paths, approver names, dates, and private production metadata.

The following is a **shape example only**. Its placeholder IDs, hashes, and approver are not publication decisions:

```json
{
  "projectId": "cv",
  "slug": "icon",
  "title": "CV Icon",
  "description": "Public editorial description",
  "category": "branding",
  "logicalAssetId": "group1:cv:icon",
  "showcaseApproval": { "approvedBy": "<owner>", "approvedOn": "YYYY-MM-DD" },
  "media": [
    { "key": "hero", "assetId": "file:projects/cv/branding/review/hero.png", "caption": "Final view", "approval": { "sha256": "<64 lowercase hex characters>", "rightsStatus": "verified", "approvedBy": "<owner>", "approvedOn": "YYYY-MM-DD" } }
  ],
  "downloads": []
}
```

`showcaseApproval` authorizes the public entry. Every preview and download also has its own verified-rights approval tied to the current SHA-256. Preview media must be image files with the `review` role; ordering follows the `media` array. Every download needs its own approval and must be an `export`, except an editable `source` may be downloaded only with `allowSource: true` on that exact download item. Approving a preview does not approve an original. A showcase with no downloads is still public, and its preview bytes can be fetched by anyone: use a public-safe derivative and remove private details from screenshots before approval. The generator rejects invalid files, unresolved rights, missing or changed hashes, unsafe public SVG, Momee paths, unpublished related entries, and repository-path-like text in showcase copy. These mechanical checks do not establish rights; the owner must verify provenance and intended use.

Existing `approved` export entries still generate direct binaries and are projected into fallback downloadable showcases, grouped by an existing public logical ID when present. Future entries should use `showcases` to control titles, media order, and independent download permissions. No real showcase, preview, or download approval was added in EA5B.

## Validation and limits

Validation checks ID and path collisions, required fields, unsupported asset-like extensions, missing manifest files, checksum conflicts, exact duplicate hashes, malformed SVG structure, selected file signatures, Git LFS pointers, publication references, and rights gates. Duplicate hashes are warnings because `exports/png/` and `exports/pwa/` intentionally contain byte-identical files. Legacy names are not errors. The current malformed SVG template is reported as a warning and remains private.

Format checks are deliberately lightweight. They do not prove that a Blender/Krita file fully opens, a model's dependencies resolve, or an image renders correctly. Compressed Blender files are recognized by their Zstandard header, without decompressing them. PNG, GIF, JPEG, WebP, ICO, and SVG dimensions are extracted when reliable; no dimensions are invented for other formats. For multi-frame ICO files, the first directory entry supplies the reported dimensions. SVG parsing uses SVGO plus a guard for comments inside quoted attributes; it is not a full security sanitizer. The website previews SVG with an `<img>` element and never inserts SVG markup into the DOM. SVG files are still downloadable, so approve only artwork suitable for public delivery.

The generator reads local bytes and reports an unhydrated Git LFS pointer as an error; it never runs `git lfs pull`. Catalog generation is an internal operation. `catalog-output/` is Git ignored and must never become a public static directory or be copied wholesale into one.
