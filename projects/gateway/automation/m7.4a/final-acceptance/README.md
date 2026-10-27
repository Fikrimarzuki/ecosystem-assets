# M7.4a final bounded acceptance — 2026-10-13

`prepare.cjs` reuses the existing external camera probe to generate `acceptance.cjs`.
`acceptance-report.json`, `latest-entry.png` and `latest-corrected-settled.png` record
one installed headed Chrome 155.0.8059.40 session at 1440×900, actual NVIDIA GTX
1660 SUPER / ANGLE D3D11, not SwiftShader. Native TPS entry and S input precede
1.5-second settling and a 12-second stationary TPS sanity sample. Cold route/asset
loading is excluded. Full-mesh projections/ground scans and screenshots run outside
the timed window; temporary wrappers time existing callbacks without adding renders.

Results: 60.05 FPS, frame mean/p95/max 16.67/18.70/25.80 ms, zero frames >33.34 ms.
Camera callback mean/p95/max .192/.300/1.400 ms; animation .098/.200/.600 ms.
All 721 camera callbacks are sampled. This is a single development-mode stationary
sample, not another 30-second active-walking or production acceptance result.

Confirmed blocker: corrected Latest boots remain inside the frustum (minimum
NDC Y −.91201, bottom pixel 860.40), but the instruction HUD occupies y=840–878,
x=527.25–897.75. 257 of 1,460 foot-weighted vertices project into its .93-alpha
background. The settled PNG visibly hides the bottoms of the boots. Projection
counts are not visible-surface percentages. Reproduction: native Latest TPS entry,
S for 950 ms, release/settle; final position approximately (.05485, .18, .78221),
yaw .13553, pitch −.52. The source lens correction works; no HUD-safe-area
reservation exists. The known limitation is now measured UI interference.

The script records `stoppedUnderDefectRule: true` and closes Chrome immediately
after recording the defect. Deferred Tools/close-space, low-FPS, reduced-motion,
FPS/mobile/cycle/project-focus/Return acceptance was not executed in this pass.
Do not treat prior evidence as newly passed final acceptance. No production file,
asset, calibration, environment or canonical data was edited. Browser and server
were stopped. The repository was clean at e4e6f34 before the documentation update;
tracked unrelated pnpm files were untouched. No commit/push/deployment.

Review the HUD interference before any correction or further acceptance work.
Subjective visual approval, device/browser/assistive-technology checks and
asset-specific rights evidence remain pending. The milestone document records
the authoritative checklist and release-readiness assessment.
