# Games v2 — Hybrid Game Kingdom, refinement (M8.9b.3b, 2026-10-23)

Builds on `design-games-v1.md` (kept, with `games-v1.blend`, `exports/games-v1.glb` and the v1 scripts, as the rollback reference). Same
composition, irregular spheroid, structure ids (`kingdom-castle`, `arcade-hall`, `scriptorium`; `portal-plaza` stays an environment),
anchors (same eight roles at the same positions) and plateaus.

| Area | v2 change |
|---|---|
| Castle | royal-blue tower roofs, teal keep roof, gold bands, finials and lintel; crimson, yellow, blue and magenta banners; a framed round-topped gate with shield crest, torches, hanging banners, flower boxes and steps; extent unchanged (6.9345, the flag) |
| Terrain | one colour per face from patch fields: warm and yellow-green meadow, golden slope behind the village, lilac highland, slope-based rock patches, mossy glade; 29 flower clusters, golden, blossom, pine and giant-mushroom trees, cairns |
| Far side | a calm magical glade (plateau, no landmark): ruin with half arch, crystal altar and 5 crystal clusters, glowing mushrooms, blossom, pine and mana trees; a winding sand trail from the village (`GAMES_TRAIL_FOREST`) |
| Portal plaza | stone pillars and a voussoir arch with a gold keystone, violet portal and core, rune circle, floating runes, four runestones (violet accents) |
| Arcade | a pixel-art roof crest, a standing gold coin, a pixel sign, a joystick lamp, three tetromino sculptures (restrained, no neon) |

Stats: 16,218 triangles (terrain 5,120), 14 meshes, 8 anchors, 2 materials, 1,436,084 bytes, SHA-256
`88d59ec987e6e20ad23e7cf17feef34da40961711ee40a061b43cf9d7dbfd51a`, byte-identical across repeated exports (the export script checks).
Files: `games-v2.blend`, `exports/games-v2.glb`, `references/layout-v2.json`, `references/games-v2-metrics.json`,
`references/games-v2-{three-quarter,opposite,landmark-castle}.png`, `scripts/build_games_v2.py`, `scripts/export_games_v2.py`.
