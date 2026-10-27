# M7.4a.1 — Exploration Entry Pointer Fix

Two focused installed-headed-Chrome tests passed at 1440×900 and 768×700.
They check center hit ownership, native mouse FPS/TPS entry and pointer lock,
Return focus, Enter/Space entry, rotation drag, slider/Reset input and layout bounds.
Snapshots are in `test-results/`; the JSON report is `focused-tests.json`.
No performance windows were collected and no M7.4a acceptance was claimed.

The external Playwright config uses the isolated dev server at localhost:3001
with walking enabled only through its process environment. Repository defaults
are unchanged. Browser/server are stopped after checks. Production changes are
only `position: relative; z-index: 1` on the existing `.exploreEntry` row.

Typecheck, lint and git diff --check pass. No production build was needed for
this CSS/test change. See Gateway's M7.4a.1 record for the remaining acceptance work.
