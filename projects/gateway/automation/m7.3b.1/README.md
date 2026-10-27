# M7.3b.1 — blended ground contact diagnostics

Run from `D:/Code/porto-projects`. All scripts use installed Node, TypeScript,
Three and Sharp. They read assets and write reports in this automation folder.
No GLB, FBX, BLEND or runtime flag files were edited.

- `baseline-animation.ts` preserves the pre-correction controller.
- `node gateway-assets/automation/m7.3b.1/reproduce-ground.mjs` reproduces the
  original 576 cases into `reproduced-ground-report.json` without overwriting M7.3b.
- `node gateway-assets/automation/m7.3b.1/diagnose-contact.mjs` writes `diagnosis.json`:
  boot masks, isolated clips, alternative fades/start phases, and nonlinear pose evidence.
- `node gateway-assets/automation/m7.3b.1/validate-contact.mjs` validates the current
  correction into `corrected-ground-report.json`. `--smooth` tries smoothstep only
  through in-memory transpilation and writes the separate `smooth-trial-report.json`.
- `unit-test-report.json`: five passing focused units. `browser-test-report.json`:
  three passing desktop flows. `runtime-ground-samples.json`: 48 independently
  measured live posed meshes after wrapper translation; minimum +0.914 micrometers
  player-local. Tests used only Tools at 1440x900, with one reduced-motion scenario.
- `browser-results/`: clear-view Idle/Walk captures and videos. Native mouse pitch
  was used for the view; camera code is unchanged. `transition-contact-sheet.png`
  contains decoded video poses, with approximate timestamps; screenshots do not
  replace the skinning measurements. Installed Playwright FFmpeg decoded the video.

The original sampled penetration was 9.041 mm player-local. An expanded 8,000-pose
sweep finds 10.318 mm before correction and zero penetration within tolerance after.
Maximum required visual lift is 10.319 mm; cap is 12.691 mm; numerical tolerance is
1.586 micrometers, all player-local. The cap throws to the existing procedural
fallback if exceeded. Pure clips receive zero offset, and corrections do not feed
back through moving/scaled/rotated parents.

Whole-visual lift keeps the lowest boot supported but does not lock both feet
independently. Largest sampled lift steps: 3.507 mm at 60 fps / 6.475 mm at 30 fps.
Review low-FPS/hitch perception and real-hardware gait before public rollout; normal
terrain/camera occlusion and existing native Walk velocity seam remain out of scope.

Typecheck, lint and default-off production build passed. One lint cleanup-ref warning
was fixed and only that component rechecked. The QA dev server was stopped before
building. Config reporter output paths were corrected after the reports were moved
into this folder; no tests were rerun to repair artifact locations.

Unchanged final GLB SHA-256:
cbe687ee68998b318a9faebcb1a9c93697f50419e9624ab6c1f6b5c278362544
Unchanged external corrected BLEND SHA-256:
ef7b3984d25fbe0a82dfdf921b83388c1d4e04932ca0e2b899a658c5379019f0

## Pruned historical frames (C1 Stage 2d, 2026-10-26)

The 1440x900 decoded-video and screenshot frames were pruned to representatives: 114 individual
PNGs (47 `frame-NNN.png`, 37 `transition-NNN.png`, 30 `contact-NNN.png`) were removed from the working
tree. The original browser videos in `browser-results/` are not part of this repository, so these
frames were the only decoded copies; nothing here reads them, and the JSON reports, scripts and
measurements above are unchanged.

- Kept frames: `frame-001`, `frame-025`, `frame-050`; `transition-001`, `transition-020`;
  `contact-001`, `contact-016`.
- Kept sheets: `motion-overview.png`, `transition-contact-sheet.png`, `ground-contact-sheet.png`.
- Archive: the removed files are in `~/ecosystem-assets-archive-2026-10-26/stage-2d/` (same disk, with
  `SHA256SUMS-originals.txt`) and remain in Git history on `origin`; their paths are listed in the
  `excluded` entries of `docs/collection-import.json`.
