# M7.3b focused QA

Gateway uses one per-mounted-model mixer on its existing TPS asset. No asset or
navigation changes. See the Gateway milestone record for implementation details.

- 4 focused units passed with the default-disabled environment: 3 animation units
  and existing asset eligibility. The initial run reused the external M7.3a config.
- 5 enabled checks passed: existing collision/displacement unit, delayed loading,
  missing GLB, missing Walk, and the animated desktop flow. Only the desktop flow
  reran after replacing a continuous-movement assumption at a nearby collision.
- `test-report.json` describes the last desktop recheck; `test-results` retains
  initial browser artifacts/trace and `recheck-results` contains final captures.
- Typecheck, lint (affected-file rerun after the one prop-mutation fix and test
  edits), production build with flag=false, and diff/whitespace checks passed.
- Server was process-only flag=true, explicitly warmed, then stopped before build.
  Existing generated ecosystem data was used; no sync/config edits.

## Mixed ground contact — confirmed limitation

`measure-crossfade-ground.mjs` uses installed TypeScript/Sharp/Three only. It loads
and skins the actual unchanged GLB offline, reusing the production animation class
via in-memory TypeScript transpilation. It writes only the separate JSON report.

576 mixed poses at 120 Hz, four Idle phases and three Walk phases: minimum vertex
Y -0.0569895225 m, equivalent to -0.0090407447 m at player scale. Worst sample is a
Walk->Idle blend at roughly half weight. No correction or asset export performed.
This is a contact limitation of blended poses, not accumulated player/root motion;
individual clips retain earlier validation. The sampled range is not exhaustive.

Screenshots show coherent textures/HUD. Foreground geometry obscures the legs in
the moving capture; manual clear-view gait/contact inspection is still required.
Functional QA passes do not constitute visual release approval. Walking remains off.
