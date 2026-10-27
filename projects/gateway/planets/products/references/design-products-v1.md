# Products v1 — Orbital Product City (Optimistic Futuristic Innovation)

Prototype only (M8.9b.5a, 2026-10-23). Not staged, not integrated: Gateway's Products world is still the procedural island.

## Audit (Gateway + config-ecosystem; source of truth `lib/generated/ecosystem.json`, `lib/universe-landmarks.ts`, `lib/universe-config.ts`)

| Item | Finding |
|---|---|
| Public Products projects (`destination: products`, `listing: public`) | **Nikah Yuk** (Wedding Marketplace, active), **Nikah Yuk Prototype** (completed), **Nikah Kuy** (Wedding Planning, completed), **Foodie Map** (Culinary Discovery, paused), **TCG Hub** (TCG Tournaments, paused), **Inventory** (paused). All six have a `main` deployment. Products has no hub project |
| Existing landmarks (five) | `landmark-foodie-map` → `city-spire` (signature), `landmark-tcg-hub` → `city-north-west`, `landmark-nikah-yuk` → `city-north-east`, `landmark-nikah-yuk-prototype` → `city-south-west`, `landmark-nikah-kuy` → `city-south-east` (standard). Inventory has no landmark today |
| Island today | deck 6.2 × 4.8, world scale 0.8387, camera sphere radius 3.132 centred at y 0.621, rotation (0.48, −0.35, −0.04); parking at planet-local x −4.35 (the −X side, mid height); the island carries the most landmarks of any world |
| Interactions plan | "Resource delivery between city buildings" (interactions-and-minigames.md) → the mini-game candidate is the delivery hub beside the plaza fountain |
| Contract conventions | `structure_id` + `footprint_radius` on structure meshes, `role: environment:<id>` for scenery, anchor empties with `role` (interaction:<id>, focus:<id>, landing, spawn, lander-arrival, minigame-candidate), vertex colours, 2 materials, Y up; calibration (bounding sphere → the island's camera sphere) is set in `approved.json` at integration |

## Landmark proposal (for Gateway's table; nothing is bound in the GLB)

| Project | Structure (`structure_id`) | Identity | Placement (lon°, lat°) | Role suggestion |
|---|---|---|---|---|
| Foodie Map | `culinary-spire` | the signature spire at the crown: silver tower, three gold-rimmed terraces, a floating teal culinary globe with coral map pins | 10, 62 | signature (as today) |
| Nikah Yuk | `wedding-pavilion` | white colonnaded pavilion under a lavender dome with a gold rim, arch gate, garden rings, two showcase wings | 58, 18 (sunny front-right) | standard |
| Nikah Kuy | `planner-atrium` | glass atrium in a white frame with a gold roof band, a planning wall with glowing boards, stepped entrance | 305, 22 (front-left) | standard |
| Nikah Yuk Prototype | `prototype-lab` | a small innovation laboratory: cube lab on stilts, gold scaffold around a half-built model, antenna | 340, −30 (front-low-left) | standard |
| TCG Hub | `card-arena` | hexagonal tournament arena with tiered seating, canopy masts and a holographic card | 125, 32 (right-back) | standard |
| Inventory | `inventory-depot` | logistics depot: silver warehouse, stacked containers in four colours, loading dock, conveyor, sorting arm | 235, 18 (back-left) | standard (new; Gateway decides whether to add a landmark) |
| (environment) | `innovation-plaza` | the central plaza: paved disc, holographic fountain, four light pylons, benches | 0, −4 (front) | none |
| (environment) | `orbital-ring` | the tilted ring with six stations and a cyan light band | — | none |

Landmark ids keep their existing identities (`landmark-foodie-map`, `landmark-nikah-yuk`, …); only the structure ids become meaningful. Each structure carries an
`interaction:<id>` anchor at its entrance and a `focus:<id>` anchor at its visual centre (the globe, the dome, the atrium, the lab, the card, the dock).
Navigation anchors: `landing` (front-right pad at 28°, −24°, r 0.3) with `spawn` and `lander-arrival` (0.55 above), `minigame-candidate` (plaza delivery hub, r 0.35).

## Composition

- **Planet:** R 4.2, squashed to 94 % on Y; blue-gray ground with lavender and teal patches, pale cliff facets, a small mesa behind the crown, a lake on the far side;
  paved plateaus under every structure; one colour per face (handcrafted facets).
- **Orbital ring (environment):** major radius 6.3, tube 0.12, tilted 26° about X (the front dips below the planet's equator, the back rises) and 12° about Z (the −X side dips to
  y −1.31, the +X side rises to +1.31); six white stations with gold finials and a continuous cyan light band. Surface clearance 1.62, building clearance 0.39 (the arena's canopy
  mast is the nearest). The −X dip keeps the rocket's parking corridor (mid height, −X) open; the front dip keeps the crown and the front districts unobscured from the default
  inspection camera (the ring crosses the planet's lower limb).
- **Paths:** nine silver pedestrian ribbons with a cyan conduit strip: plaza → pavilion, plaza → atrium, pavilion → spire, atrium → spire, pavilion → arena, arena → depot,
  atrium → depot, plaza → landing, plaza → lab; a loop links every district.
- **Decorations:** 34 crystal trees (teal canopy discs or violet bulbs), 8 light pylons, 2 observation platforms (180°/52° and 270°/−22°), 11 rocks, 3 benches, the landing pad with a
  cyan ring and four beacons.
- **Palette:** ground `#7e8da8`/`#98a6bd`, lavender `#a89cd8`, teal `#5fbfb8`, paving `#d8dde6`, white `#f2f4f8`, silver `#b8c0cc`, gold `#e0b85a`, glass `#9fd8e8`;
  emissive cyan `#5fe3ff`/`#bff3ff`, violet `#b48cff`, warm `#ffd98a`. No neon signage.

## Result

`products-v1.blend` (scene `PRODUCTS_V1`), `exports/products-v1.glb`: 1,311,460 bytes, SHA-256 `3178ba73ed5b4a153dd1991e924034c84c3712b39ee99dc4d60bf884cf29d654`,
byte-identical on repeat export; 16,290 triangles (terrain 5,120, ring 1,304, spire 1,032, pavilion 976), 21 meshes, 16 anchors, 2 materials (`ProductsDiorama`, `ProductsAccent`
emissive), no textures, cameras, lights or extensions; Y up; bounds x ±6.34, y −3.88..5.92, z ±5.91; extent 6.650 (the ring). `references/layout-v1.json` (planet, ring, structures,
anchors, routes, decorations), `references/products-v1-metrics.json` (GLB validation), renders `references/products-v1-{three-quarter,opposite,landmark-spire}.png`.
Scripts: `scripts/build_products_v1.py`, `scripts/export_products_v1.py`. Object names are prefixed `PRODUCTS_` (anchors `PRODUCTS_ANCHOR_*`).

## Integration considerations (next milestone)

- **Calibration:** the ring sets the extent (6.65 versus the spire's 6.1), so Learning's policy (bounding sphere → island camera sphere) would shrink the planet by ~10 % relative to
  the ring-less case; calibrating on the planet's own radius and letting the ring protrude is the alternative. The decision belongs to the integration milestone.
- **Overview:** the spherical overview works for the planet; the ring needs a torus in the lightweight overview (profile extension, like Tools' platforms), or it pops in with the detail.
- **Rocket:** the −X ring point is at y −1.31 (model), below the parking height; measure the approach corridor against the ring's tube with the real-mesh clearance test, and add a
  parking descriptor only if needed.
- **Camera / occlusion:** the ring's front segment crosses the planet's lower limb in the default view and sweeps across it during yaw; an inspection-time ring fade (like the rocket's
  overlap fade) may be wanted. The six landmark labels will crowd; the overview protrusion settings should exclude the ring.
- **Landmarks:** `inventory-depot` offers Inventory a landmark for the first time; the ring and plaza are `environment:` roles and never bind.
