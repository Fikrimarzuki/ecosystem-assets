# Mom art direction and animation feasibility v1 (M1.1c)

**Status:** study for owner review. No new Mom artwork, rig, animation or Phaser change. Nothing is registered or approved.

**Inputs inspected** (the actual images):
- the master reference `../references/momee-soft-storybook-master-reference-v1.png`;
- the new exploration `../references/mom-art-direction-exploration-v1.png` (1536×1024 RGB, SHA-256 `118eca2c…9481`);
- the earlier SVG experiment `../characters/mom/source/mom-head-v1.svg`, with its comparison.

**Evidence labels:**
- **Observed:** seen in the images or measured from the files.
- **Tested:** produced and rendered in this milestone.
- **Assumption:** judgement or experience, not proven here.

## 0. What the exploration image is (observed)

- **Content:** a single flattened sheet with three directions (A, B, C). Each has one head-and-shoulders portrait about 300 px wide, six small expressions (Neutral, Smile, Blink, Talking, Surprised, Happy), four views (front, ¾ left, side left, ¾ right) and four detail tiles (eye, hair, face, shading).
- **A generated sheet:** some captions are garbled (the "Happy (closed)" labels). B's "(recommended)" label and the bullet lists are part of the generated image, so they are claims, not evidence.
- **Not layered:** the expression and view panels are illustrations, not frames or layers.
- **Provenance:** generation details for this file are unknown.

## 1. Candidate comparison

| | A · Faithful Soft Storybook Adventure | B · Simplified Soft Storybook | C · Cozy Adventure (more stylised) |
| --- | --- | --- | --- |
| Character appeal | Warm and charming; the richest finish | Warm and clean; very appealing | Warm and clean; slightly more graphic |
| Adult identity (observed) | **Weakest**: round full face and large round eyes read younger | **Strongest**: longer face, almond-leaning eyes, calmer smile | Close to B; eyes very slightly larger |
| Facial proportions | Round, wide cheeks, small chin | Slightly longer oval, softer jaw | As B, marginally rounder |
| Hair complexity (observed) | High: many layered curls, painted strand texture and paper grain | Medium: large smooth waves, a few strand lines, soft light streaks | Medium-low: as B, with bolder shapes and less texture |
| Animation feasibility | Hardest: textured painterly hair and many curls make hidden overlaps and seams hard to paint consistently | Good: smooth fills hide seams and overlaps can be drawn in the same style | Good: as B |
| Customisation | Hard: recolouring painted texture is lossy and new styles need repainting | Good: fills and gradients recolour cleanly | Good |
| Visual consistency at scale | Risky: hand-painted texture drifts between parts and frames | Good | Good |
| Production effort (assumption) | Highest; probably needs an illustrator or painter | Medium | Medium-low |
| Main risk | Quality depends on painting skill for every hidden piece and frame | Can slide toward flat or "doll-like" if the eyes, shading and hair structure are simplified too far (the v1 problem) | Can read as generic vector art if over-simplified |

**Observed: B and C are closer than their labels suggest.** Their portraits share the face, eyes, hair waves and palette; the main difference is outline weight and a little texture. **A differs most**: more painterly, and younger.

**Compared with the master reference (observed):** all three keep Mom's identity: long reddish-brown waves, side part, warm-brown eyes, peach blouse. B and C are closest to the reference's face shape while reading more adult. A is closest to its painterly finish.

## 2. Pipeline comparison

| | 1 · Pure SVG | 2 · Layered raster (Krita) | 3 · Hybrid SVG + raster |
| --- | --- | --- | --- |
| Visual fidelity | B/C level looks reachable part by part (tested on one eye); **A's painterly texture is not realistic** | Highest ceiling for A, **if** painted by a skilled artist | Close to Pipeline 1, plus some painterly texture; unproven |
| Animation quality | Clean swaps and transforms; hidden overlaps drawn as vectors | Good, but every hidden overlap and frame must be painted by hand; seams are a known risk (legacy M1.0l-A1 showed holes when parts were separated from flat art) | Good; textures must stay aligned when parts move |
| Editing difficulty | Moderate (Inkscape, or code with review) | High for code-driven work; Claude cannot paint convincing raster art (M1.0i, M1.0k-A findings) | High: two sources per part |
| Customisation | **Best**: gradients and fills recolour exactly; parts swap | Weak: tinting painted art is approximate; variants need repainting | Medium |
| Automation (code-assisted) | **Best**: SVG is text; export via Inkscape CLI is proven here | Low: Krita scripting can arrange layers but not paint quality art | Medium |
| Maintenance | Good: small diffable files | Large binary KRA files in LFS | Highest overhead |
| Asset size | Small SVG sources; exported PNG parts sized as needed | Large sources; similar exports | Both |
| Tools | Inkscape (CLI proven), Claude Code | Krita plus a painter | Inkscape, Krita and texture rules |

## 3. Small experiment (tested)

`../experiments/m1.1c-eye-component/` is disposable and isolated. It contains one Candidate-B-style eye as a layered SVG: brow, lid crease, eye white with an under-lid shadow, graded iris, pupil, highlights, upper lash mass and lower lid. It has an open frame and a closed blink frame on the same skin patch, rendered with Inkscape and set beside B's eye tile and the v1 eye.

**Observed result:**
- **Better than v1:** the almond opening, lid crease, under-lid shadow and graded iris remove most of the doll-like look.
- **Short of B:**
  - B's lash mass is smoother and fuller;
  - B's iris has softer, painted-looking banding;
  - our outer lash spikes are still too curly;
  - a soft lid-shade ellipse is visible as a blob, especially on the closed frame.
- **Blink as a frame swap works technically:** open and closed frames share the same canvas, and the closed frame carries its own skin.

**Conclusion:** at the size of one part, pure SVG can get close to B with a few review rounds. It does **not** reproduce A's texture. This is one part only; hair and the whole face are **not** proven.

## 4. Animation feasibility (first: blink, talk, idle, wave)

| Animation | Components needed | Likely problems |
| --- | --- | --- |
| **Blink** | Eye groups per eye: open, half, closed frames, each carrying its own lid skin; brows separate | The skin under the eye must exist in every frame; the lash style must stay identical across frames |
| **Talk** | Mouth group: neutral, small-open and wide-open shapes on a skin patch | Lip colour and line weight must match; a jaw-free approach (shape swap only) keeps it simple |
| **Idle** | Head group (face, features, front hair) over the neck and torso; optional hair-back sway; torso scale for breathing | The neck must extend under the chin and collar (hidden overlap); long hair over the shoulders must not tear when the head bobs |
| **Wave** | Arm split at shoulder, elbow and wrist; an open hand; the sleeve | The shoulder cap and the torso behind the raised arm must be drawn; long hair sits between the arm and the body, which affects draw order and needs a hair-back and a hair-front lock layer |
| Later: smile, walk, look around, sit, interact | Additional frames and views (¾ and side heads, as sketched on the sheet), and leg parts | Turning views need separate head drawings, not rotation; walking needs leg overlap art; sitting needs a different body silhouette |

**Cross-cutting risks:**
- **Hair:** long hair crosses the shoulders and arms, so it needs at least a back mass and one or two front locks.
- **Clothing:** the collar overlapping the neck, and the sleeve cuffs.
- **Joints:** seams at the shoulders, elbows and neck must be hidden by painted or drawn overlaps, never generated automatically.

## 5. Customisation considerations

- **SVG (B/C):**
  - hair colour, eye colour and skin tone become gradient or fill changes;
  - hairstyles are swaps of the `hair-back` and `hair-front` groups on a shared head anchor;
  - outfits and accessories are separate groups.
  - This is the cheapest route for future variants.
- **Raster (A):** recolouring painted texture by tint is approximate, so new hairstyles and outfits need new painting each time.
- **Keep it simple now:** consistent group names and a shared canvas and anchor are enough. A customisation engine is not needed yet.

## 6. Main risks

1. **Artistic:** hand-built vector art landing "close but flatter" than the reference. This happened with v1 and partly in the eye test. Mitigation: work from the larger Candidate portrait, which is about 300 px wide against about 66 px for the old reference face, and review each part with the owner before assembling.
2. **Resolution:** even the B portrait is small for a 4 px/u master, so fine details are reconstruction, not tracing.
3. **Consistency** across many frames and views (blink, talk, turnarounds).
4. **Provenance:** both references are generated images with unknown generation details, and rights are unverified.
5. **Unproven:** hair, the whole head, seams, export sizes and Phaser performance have not been tested.

## 7. Recommendation

**Candidate: B (Simplified Soft Storybook), optionally with C's slightly bolder outline if you want more readability at small sizes.**
- B has the clearest adult identity and the cleanest shapes for parts and animation.
- It stays close to the master reference's face.
- A is the most beautiful finish, but it reads younger and needs painting skill this pipeline does not have.

**Pipeline: 1 (pure SVG) as the default, with Pipeline 3 kept as an optional upgrade.** If B's finish is missed after the next checkpoint, add one restrained raster "finish" layer per part, such as soft shading or grain, rather than painting whole parts. Pipeline 2 is only worthwhile if you commission an illustrator, because direction A depends on painted texture.

These are recommendations from the evidence above, not proven production results.

## 8. Proposed next visual checkpoint (M1.1d, after owner choice)

**Mom face v2, head only (front view), in the chosen candidate's style, using that candidate's portrait as the reference.**
- **Frames:** neutral eyes and mouth, a closed (blink) eye frame, and one open (talk) mouth frame.
- **Detail:** the improved eye construction (fixing the lash spikes and lid-shade blob from the test), a fuller face shape, and hair with two front locks.
- **Stop:** for owner review against the candidate portrait at the same size.
- **Acceptance:**
  - it reads as the same Mom as the chosen portrait, and clearly as an adult;
  - no doll-like eyes;
  - the hair silhouette and gloss are close;
  - the parts swap cleanly.

## 9. Limitations and unknowns

- **One part tested:** only one eye was built. Hair, the full face, seams and Phaser rendering are untested.
- **Judgement-based assessments:** the candidate assessments are visual judgements from a single generated sheet; their small expression and view panels are not verified designs.
- **Effort estimates** are assumptions.
- **Rights:** unverified for both reference images.
- **Not registered:** the exploration image and the experiment are not in the manifest. They are a reference and a disposable test.
