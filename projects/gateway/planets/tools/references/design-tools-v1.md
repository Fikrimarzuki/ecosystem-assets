# Tools v1 — The Mechanical Workshop (Floating Industrial Fantasy)

Prototype only (M8.9b.4a, 2026-10-23). Not staged, not integrated: Gateway's Tools world is still the procedural island.

## Audit (Gateway + config-ecosystem, source of truth: `lib/generated/ecosystem.json`, `lib/universe-landmarks.ts`, `lib/universe-config.ts`)

| Item | Finding |
|---|---|
| Public Tools projects (`destination: tools`, `listing: public`) | **CareerLens** (completed, no deployment), **DevTools** (active, `main`), **Multiple Git Clone** (`multiRepoClone`, completed, no deployment), **Tools** (the hub project, active) |
| Existing landmark | `landmark-careerlens` → `workshop-hall` (standard). DevTools and Multiple Git Clone have no physical landmark; the hub's "hub entrance" role is derived from the registry, never from a structure |
| Island today | deck 5.2 × 4.4, reservation y −1.12..1.655, camera sphere radius 2.585 centred at y 0.266, scale 1, rotation (0.55, 0.3, −0.04); parking at planet-local x −3.657 (the −X side); landing/spawn on the road |
| Interactions plan | "Machine assembly at the workshop" (interactions-and-minigames.md) → the assembly station is the mini-game candidate |
| Contract conventions | `structure_id` + `footprint_radius` on structure meshes, `role: environment:<id>` for scenery, anchor empties with `role` (interaction:<id>, hub-entrance:<id>, landing, spawn, lander-arrival, minigame-candidate), vertex colours, 2 materials, Y up, model centred near the origin; the calibration (bounding sphere → the island's camera sphere) is set in `approved.json` at integration |

## Landmark proposal (for Gateway's table; nothing is bound in the GLB)

| Project | Structure (`structure_id`) | Identity | Role suggestion |
|---|---|---|---|
| CareerLens | `workshop-hall` (id kept from the island) | the central workshop: barrel roof, side flywheel and gear train, chimney, a great brass **lens** turret on a geared mount | signature |
| DevTools | `forge-station` | a tool forge: brick furnace with ember mouth, tall chimney, bellows, anvil under a geared hammer arm, tool rack, quench barrel | standard |
| Multiple Git Clone | `replicator-bay` | a duplication machine: one source crate enters a brass scanner arch (cyan sheet), identical crates roll out on a conveyor; control cabinet, exhaust stack | standard |
| Tools (hub) | `control-tower` is an **environment** (role `environment:control-tower`), with a `hub-entrance:control-tower` anchor for later | none (hub stays registry-derived) |

Every structure carries an `interaction:<id>` anchor at its door/work front and a `focus:<id>` anchor at its visual centre (the lens, the hammer,
the scanner arch, the tower cabin) for camera framing. Navigation anchors: `landing` (dock pad, r 0.3), `spawn`, `lander-arrival` (0.55 above the
pad), `minigame-candidate` (the assembly table on the main deck, r 0.35).

## Composition

- **Six floating platforms** on riveted tapered hulls (copper keel rings, lift rotors, hanging pipes with valve wheels), decks with plating lines, brass-railed rims:
  main workshop deck (octagon 4.3 × 3.5 at the origin), forge platform (round ⌀2.55, raised +0.55 at x 3.35), replicator bay (rect 2.5 × 2.0, low −0.5 at x −2.85, front),
  dock (round ⌀2.3 at the front, y −0.25: landing pad + control tower), power station (hex ⌀1.6, suspended at y 1.75 behind-right by three chains from a gantry mast),
  tank perch (hex ⌀1.3 at y 0.95 behind-left).
- **Links:** truss bridges with plank decks, brass handrails and a cyan conduit underneath (main→forge, main→bay, main→dock), sloped catwalks (main→power, main→spare), pipes and diagonal struts between hulls.
- **Machinery:** gear trains, two cranes (one lifting a crate), tanks with copper bands, Tesla-style coils and a caged cyan power core, crates, lamps.
- **Palette:** steel `#7f8a99`/`#4b5564`, deck `#66707f`, hull `#5a6474`, copper `#b87333`, brass `#c9a24b`, rust `#8a5a3c`, iron `#2f3640`, planks `#9a734f`; energy cyan `#5fe3ff`/`#2bb8d9` (emissive), warm windows `#ffd98a`, ember `#ff8c42`. No neon signage.
- **Rocket side:** the −X side holds only the low replicator bay and the small tank perch; the parked rocket (−X, mid height) faces open space. Clearance is measured at integration.
- **Future exploration:** every deck is a flat, continuous surface; bridges/catwalks (width 0.42–0.7) connect every platform to the main deck; the railings leave the bridge landings open.

## Result

`tools-v1.blend` (scene `TOOLS_V1`), `exports/tools-v1.glb`: 1,229,268 bytes, SHA-256 `dfb9803ef5b5e7673a4e78bd0201f6a8b9c868ae0bfdeb372d213c34fe16d558`,
byte-identical on repeat export; 18,372 triangles (platforms 8,588), 12 meshes, 12 anchors, 2 materials (`ToolsDiorama`, `ToolsAccent` emissive), no textures,
cameras, lights or extensions; Y up; bounds x −4.55..4.71, y −1.82..3.43, z −3.01..4.50; extent 5.318 (the AABB centre is (0.08, 0.81, 0.75): the calibration offset
re-centres it). `references/layout-v1.json` (platforms, structures, anchors, bridges), `references/tools-v1-metrics.json` (GLB validation),
renders `references/tools-v1-{three-quarter,opposite,landmark-workshop}.png`. Scripts: `scripts/build_tools_v1.py`, `scripts/export_tools_v1.py`.
Object names are prefixed `TOOLS_` (anchors `TOOLS_ANCHOR_*`) because Blender object names are global in a session that also holds the Games and Learning scenes.
