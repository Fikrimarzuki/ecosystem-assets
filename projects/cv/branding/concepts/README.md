# CV icon design history

Kept for reference; nothing here ships. The canonical icon is `../source/` and `../exports/`, which is the approved **optical-balance** version (promoted in A3.1d).

| Folder | Status |
| --- | --- |
| `original-m/` | First A2.3b pilot: symmetric two-tone M. Superseded. |
| `variant-a/` | Integrated asymmetric M, as reviewed in A2.3b.1. **Selected**, then refined (wedge trimmed 60 concept-units from its left end along the unchanged hypotenuse, glyph lifted 8 units) and promoted in A2.3b.2. This folder is the pre-refinement version. |
| `variant-b/` | Minimal M with a diagonal slit. **Rejected.** |
| `pre-optical-balance/` | The production CV icon from A2.3b.2 to A3.1c, preserved exactly as it was before the optical-balance refinement. Superseded by `../source/`. |
| `optical-balance/` | **Approved and promoted to production (A3.1d).** The previous production masters with the left stem's inner edge moved 4 units right (stem 56 → 60 units, +7%); the diagonal's underside angle, wedge, palette, tile, ring and bounding box are unchanged. Its masters are byte-identical to `../source/`; it is kept as the history of that decision. |

Every folder holds the five SVG masters (`icon`, `tile`, `glyph`, `favicon`, `mono`) and an `icon.checks.json`.

## Comparison sheets

* `../previews/variant-comparison.png` (A2.3b.1) shows the pre-refinement icon as "current".
* `../previews/optical-balance-comparison.png` (A3.1c) compares the production icon of that time (column A, now `pre-optical-balance/`) with the approved candidate (column B, now the production icon). It is a static record of the decision. Running `pnpm pair-sheet cv optical-balance` today would compare production with an identical copy, so it is not regenerated.

## Regenerating historical exports

Only the SVG masters are kept. The exports of every folder above are disposable and git-ignored; each reproduces byte for byte from its `source/` folder (checked for `variant-a` and `variant-b` in A3.1a, and for `optical-balance` in A3.1d).

```sh
pnpm build:icons cv --variant pre-optical-balance    # writes concepts/pre-optical-balance/exports/
pnpm verify:icons cv --variant pre-optical-balance   # needs the exports above, so build first
```

Use the same commands with `original-m`, `variant-a`, `variant-b` or `optical-balance`. Building a variant never touches the production exports.
