# M7.4a resumed diagnostic evidence — 2026-10-13

Temporary automation and reports live outside the Gateway repository. No runtime,
asset, environment or deployment files were changed. Installed headed Chrome
155.0.8059.40 at 1440×900 used the actual GTX 1660 SUPER through ANGLE/D3D11,
not SwiftShader. Samples used a warmed local Next development server with a
process-only walking flag. Browsers and the server were stopped after inspection.

- `prepare.cjs` / `performance-qa.cjs`: reuse existing external R3F probes; native
  entry/movement and approximately 30-second stationary/Tools/Latest TPS samples.
- `continuation-report.json`: complete passing performance/lifecycle report with
  raw frame/callback samples, movement evidence, GPU information and snapshots.
- `visual-template.cjs` / `visual-qa.cjs` / `visual-report.json`: directions,
  start/stop crossfade, ground samples, roof approach and projection captures.
- `camera-repro.cjs` / `camera-repro-report.json`: two fresh Latest entries,
  S held 950 ms then released, screenshots immediately and after 1.5 s at the
  same player position. Both settled captures crop boot vertices about 44.3 px
  below the viewport. See `latest-same-position-{1,2}-settled.png`.
- Other PNGs show entry/bench/roads, blocked Idle, directional Walk and crossfade.

The first `latest-crossbar-moving-repro.png` / `latest-crossbar-settled-repro.png`
pair is NOT a same-position comparison: movement continued during PNG capture.
Do not infer that waiting fixes framing from that pair. The later camera report
preserves position within each pair and confirms persistent cropping twice.

| Sample | Average FPS | P95 frame | Maximum frame | Moving frames |
| --- | --- | --- | --- | --- |
| Tools walking | 60.01 | 17.00 ms | 19.10 ms | 96.89% |
| Latest walking | 60.03 | 17.00 ms | 18.90 ms | 97.67% |
| Tools stationary | 59.99 | 17.10 ms | 26.30 ms | 0% |

No frames exceeded 33.34 ms in those windows. Animation callback mean costs:
.167 / .109 / .087 ms respectively. Combined camera callback means:
.148 / .247 / .180 ms; these include visibility, collision, smoothing and transforms,
not isolated visibility cost. Nested mixer/ground-scan costs must not be added twice.

Five entry/exit cycles retained stable 32 geometries / 5 textures / 5 programs;
one mesh/mixer active, zero after exit. This was bounded lifecycle verification,
not a dedicated 30-second entry/exit performance sample or long-term leak proof.
Reduced static TPS, settled Showcase and portfolio-offscreen probes each observed
zero renders for 2.5 seconds. Normal navigation, project freeze/Escape, Return,
Canvas persistence and FPS exclusion passed. Screenshots/ground vertex scans were
outside performance windows. Instrumentation overhead and development mode limit
generalization; refresh-capped measurements do not establish GPU headroom.

Confirmed production framing defect triggers the user's stop rule: no correction
implemented and no further acceptance diagnostics performed. Review projected
character coverage in existing camera candidate selection before resuming.
Naturalness, foot sliding, low-FPS fades, camera comfort and environment appearance
remain user/device acceptance items. Existing asset-specific rights and browser/
assistive-technology requirements remain unapproved. See the authoritative current
record in `app-gateway-fe/docs/milestone-7-walking-exploration.md`.
