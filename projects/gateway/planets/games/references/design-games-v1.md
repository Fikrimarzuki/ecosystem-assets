# Games v1 — Hybrid Game Kingdom (visual specification)

**Direction (approved):** Hybrid Game Kingdom — Fantasy Adventure × Playful Arcade. A rounded, slightly squashed, irregular fantasy
world with a castle crowning the top, an arcade village on the sunny slope, a portal plaza at the front, rounded forests, a winding
road with a bridge, cliffs and floating rocks. Handcrafted low-poly, vivid and whimsical, distinct from Learning's tidy Academy Town.

## Audit (M8.9b.3a, 2026-10-23)

| Item | Finding |
|---|---|
| Public Games projects (`destination: games`, `listing: public`) | **Tinyverse** (active), **Playnest** (active), **Scriptoria** (paused, still public), **Games** (the hub project itself, active) |
| Existing landmark | only `landmark-tinyverse` → `terrain-castle` (the castle); Playnest and Scriptoria have no physical landmark today |
| Landmark rules (`lib/universe-landmarks.ts`) | one landmark per public project; `structureId` unique within the world; the project's primary world must be `games`; Gateway owns ids, mapping, roles and publication — never Blender metadata |
| Current Games recipe | a flat island (deck 5.2 × 4.4) with the ivory/dark-green castle, trail, crossing, rocks and three trees |
| Scale policy | rendered radius ≈ 2.6–2.7; Learning v3 authored at R = 4.2 local (14 astronaut heights), extent 6.215, calibrated by the contract |
| Rocket | parking is on the −x side (planet-local); the approach reaches the model from +z/−x: keep floating rocks away from lon 230°–310° |
| Contract staging (`stage-world-assets.mjs`) | derives bounds, structures (`structure_id`), anchors (`role`) and the lightweight overview from the GLB. The required anchor-role list is currently Learning-specific; integration will need a per-world list |

## Landmark plan (proposal for Gateway; nothing is bound in Blender)

| Project | Structure (`structure_id`) | Role suggestion | Placement (lon°, lat°) | Why |
|---|---|---|---|---|
| Tinyverse | `kingdom-castle` | signature | 10, 60 (the crown) | keeps the recognisable castle; a tiny universe seen from its keep |
| Playnest | `arcade-hall` | signature | 62, 16 (sunny slope, village) | an arcade hall with a marquee and cabinets: playful, nest-like village |
| Scriptoria | `scriptorium` | standard | 308, 20 (front-left) | a parchment tower with a scroll and a small arena: scripting-as-adventure |
| Games (hub) | `portal-plaza` (environment, hub candidate) | hub-entrance (future) | 0, −6 (front, low) | a portal gate on a paved plaza; the obvious "enter the Games world" spot |

Anchors (roles): `interaction:kingdom-castle`, `interaction:arcade-hall`, `interaction:scriptorium`, `hub-entrance:portal-plaza`,
`landing` (clearing at 330°, −2°), `spawn`, `lander-arrival`, `minigame-candidate` (the tournament green between castle and village,
per interactions-and-minigames.md: "Arcade challenge near the castle").

## Composition

- **Silhouette:** squashed spheroid (y × 0.92), low rolling relief, two mesas/cliffs, a lake basin, the castle's towers and flag as the
  crown, three floating rocks on the +x/+z sides.
- **Palette:** vivid lawn `#7fbf5f`, meadow `#5fa352`, deep green `#3f8a4e`, lilac highland `#8d82b4` near the crown, sand `#e5d29b`,
  cobble road `#d7bf8c`/`#bfa872`, lake `#4aa5cc`, cliff `#9d8d86`; castle ivory `#e3dcc4` + dark green roofs `#596653` (as today);
  arcade coral `#e8735f`, teal `#3fb3b0`, marquee yellow `#f2c94c`, deep navy cabinets `#2f3d55`; scriptorium parchment `#e9dcbd`
  with indigo roof `#6f5fa8`; portal stone `#8f8798` with a violet glow `#b48cff`; accents (screens, lanterns, crystals) emissive.
- **Roads:** portal plaza → (bridge over a gully) → arcade village → switchback up to the castle; plaza → scriptorium; a trail from the
  castle down to the tournament green. Ribbon strips, cobble colours, lifted 0.012 above the terrain.
- **Decoration budget:** ~36 rounded trees (a few violet "mana" trees), 10 mushrooms, ~14 rocks, 6 crystals, 3 cottages, 2 extra
  cabinets, 6 lanterns, 3 floating rocks. Nothing smaller than a mushroom; nothing hidden under the horizon from the default view
  except the far-side forest and the lake, which rotation reveals.
- **Triangle budget:** ≤ 18k (Learning v3: 15.5k). Terrain icosphere subdivision 5 (5,120 triangles).
- **Future exploration:** continuous terrain surface, plateaus under every structure, roads ≥ 0.2 wide, a landing clearing ≥ 0.3,
  no structure within the landing circle.

## Result (prototype v1, exported 2026-10-23)

- Files: `games-v1.blend` (scene `GAMES_V1`), `exports/games-v1.glb` (963,364 bytes, SHA-256
  `0cfb17aea76846f3aeaa6decd80b7eaeacce707bab1fb3db65216e57b5a0aa54`, byte-identical across three exports), `references/layout-v1.json`
  (authoring layout), `references/games-v1-metrics.json` (GLB validation), renders `references/games-v1-{three-quarter,opposite,landmark-castle}.png`.
- Geometry: 10,640 triangles (terrain 5,120), 13 meshes, 8 anchors, 2 materials (`GamesDiorama`, `GamesAccent` emissive), no textures,
  cameras, lights, animations or extensions; Y up, bounds x −4.94..4.86, y −4.04..6.03, z −5.53..5.38, extent 6.935 (the castle flag;
  Learning v3: 6.215). The contract calibration scales per asset, so the rendered radius policy (≈ 2.6–2.7) is applied at integration.
- Structures: `kingdom-castle` (footprint 0.897), `arcade-hall` (0.95), `scriptorium` (0.85); `portal-plaza` is `role: environment:portal-plaza`
  (0.95) so it never binds a landmark by itself. Anchor roles exactly as planned above; every anchor's up axis is the surface normal.
- Not done on purpose: no staging, no `approved.json` entry, no Gateway source change, no landmark mapping change. Integration will need a
  Games-specific anchor-role list in `stage-world-assets.mjs` (the current list is Learning's) and a landmark entry per public project.
