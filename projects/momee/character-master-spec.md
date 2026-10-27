# Momee character master specification (M1.0j-C)

**Status:** specification for owner review. A static Mom master candidate exists (v2, M1.0k-A3; visually accepted M1.0k-A4, not production-approved); no layered master has been produced. It extends `app-momee/docs/architecture/asset-pipeline.md` §4 (rig contract, slots) and §9 (density, tiers, formats). Identity comes from the owner-accepted references (`ref.boy.accepted-sheet.v1`, `ref.mom.accepted-sheet.v1-2`) within the Calm Chibi Storybook rules of the Visual Style Bible.

## 1. Stages (keep them distinct)

| Stage | What it is | Boy today | Mom today |
| --- | --- | --- | --- |
| 1 · Accepted reference | Immutable owner-accepted sheet | ✓ | ✓ |
| 2 · Extracted full figure | Non-destructive cutout, static use only | ✓ 2.57 px/u (+ edge-cleaned derivative) | ✓ 1.77 px/u (+ edge-cleaned derivative) |
| 3 · Layered editing source | Krita file organising stage 2 | ✓ | ✓ |
| **4 · Character master** | **Standalone, high-resolution, layered by slot, hidden overlaps painted** | **not yet** | **not yet** |
| 5 · Rig / runtime parts | Trimmed parts, frames, pivots (later milestone) | — | — |

Resampling a stage-2 cutout never produces a stage-4 master.

## 2. Pixel dimensions, bounds and anchors

| | Boy (child rig) | Mom (adult rig) |
| --- | --- | --- |
| World height | 200 u (working value until D2) | 290 u (1.45×) |
| Head proportion | ≈ 2.5 heads (accepted figure 2.47) | 3.2–3.5 heads (bible v1.3; v1.2 figure 3.38) |
| **Master density** | **4 px/u** (pipeline minimum 2.5) | **4 px/u** |
| Figure height in master | **800 px** (minimum 500) | **1160 px** (minimum 725) |
| Master canvas | **640 × 896 px** (= 160 × 224 u) | **800 × 1248 px** (= 200 × 312 u) |
| Feet anchor (master px) | **(320, 864)**: soles end on row 863; the ground line is the top edge of row 864 | **(400, 1216)** |
| @1x / @2x canvas, anchor | 160×224 at (80, 216) / 320×448 at (160, 432) | 200×312 at (100, 304) / 400×624 at (200, 608) |

The canvases and anchors are the same as the current candidate exports, so later masters drop into the same slots.

- **One fixed canvas and anchor per character** for every view, expression and part. Nothing may be cropped differently per expression.
- Hair top at the stated height: Boy 200 u (800 px) and Mom 290 u (1160 px) above the ground line, ±1 %.
- Clear space above the hair is fixed by the box: **Boy 16 u (64 px), Mom 14 u (56 px)**; 8 u (32 px) below the soles. (Corrected in M1.0k-A: the earlier text said 16 u for both, but Mom's 312 u box with a 290 u figure leaves 14 u.) Raised-arm poses may later need a taller box, decided once per character.
- **Transparent background:** RGBA, straight alpha, no matte, no panel colour, no text, labels or decorations. The ground/contact shadow goes on the `shadow` layer only.
- Colour: sRGB, 8-bit per channel at export (a 16-bit source is fine). No embedded profile in exports.

## 3. Views

| View | Requirement | Notes |
| --- | --- | --- |
| **¾** | **Required for the first master** | Rig contract: authored facing right, flipped for left. Boy's accepted figure faces right ✓. **Mom: native left-facing ¾** (owner decision in the M1.0k-A brief, 2026-10-24), matching v1.2 and keeping her side part and hair sweep as accepted. At runtime a left-facing master is flipped to face right, and only when she must face right. |
| Front | Planned (dialogue portraits, UI) | Same canvas, anchor and identity checks |
| Side, back | Later | Not needed for Morning Routine v1 |

## 4. Expressions (face slots on one shared head per view)

| Slot | Attachments required | Why |
| --- | --- | --- |
| `face-eyes` | `open`, `half`, `closed`, `happy` (closed arcs) | Blink, sleepy wake-up (the Boy sleeps in bed in S1), happy |
| `face-brows` | `neutral`, `raised` | Happy and talking emphasis |
| `face-mouth` | `neutral`, `happy` (open smile), `talking-a`, `talking-b` | Two talking shapes for simple lip flap |
| `face-blush` | `default` | Kept separate for skin-tone work |

The named expressions are combinations of these:

- **neutral** = open + neutral + neutral
- **happy** = happy + raised + happy
- **talking** = open + raised + talking-a/b

The talking frame keeps open eyes (an M1.0i decision; the owner can revisit it). Head shape, hair and line weight must be **pixel-identical** across expressions: only face-slot layers differ.

## 5. Hidden joint overlaps (must be painted, never inferred)

Every movable part extends **≥ 6 u (24 master px)** beyond its visible seam, under the covering part, in the same rendering style. Based on the M1.0j-B gap analysis:

| Region | Boy | Mom |
| --- | --- | --- |
| Neck under the chin / collar | Neck extension (none drawn today) | Neck behind the hair and collar |
| Shoulders | Shoulder caps under the sleeves | Shoulder caps under the rolled sleeves |
| Hair | `hair-back` skull mass behind the head; fringe overlap on the forehead | `hair-back` long-hair mass behind the body; blouse and back painted behind the front locks |
| Arms | Upper/lower arm split at the elbow, with an overlap | Forearms and hands **unclasped** (or a dedicated `hand-front/clasped` attachment over a complete torso) |
| Hands | Wrist overlap | Wrist overlap |
| Legs and feet | Upper thighs under the shorts; ankles under the socks | Trouser legs as `outfit-bottom` parts that swing; shoes under the hems |
| Face | Eyelid skin under each eye attachment; skin under the mouth | Same |

## 6. Layer naming and Krita source structure

- **Document:** one character per `.kra`, RGBA, sRGB, canvas and anchor as in §2. A guides group (hidden) holds the ground line, anchor and height lines.
- **Groups, back to front, named by slot** (asset-pipeline §4):
  - `shadow`
  - `hair-back`
  - `arm-back-upper`, `arm-back-lower`, `hand-back`
  - `leg-back-upper`, `leg-back-lower`, `shoe-back`
  - `body-skin`
  - `leg-front-upper`, `leg-front-lower`, `shoe-front`
  - `outfit-bottom`, `outfit-top`
  - `head-skin`, `face-blush`, `face-eyes`, `face-brows`, `face-mouth`
  - `hair-front`
  - `arm-front-upper`, `arm-front-lower`, `hand-front`
- **Layers inside a group** are attachments named `slot/attachment` (e.g. `face-eyes/half`, `hand-front/open`). Clipped shading or line sublayers are allowed inside an attachment group. Each attachment must render correctly on its own.
- **Reference:** a locked, hidden `00 reference` group holds the accepted figure (stage 2) at master scale, for comparison only. It is never exported and never painted on.
- **Not allowed in export-relevant layers:** filter or transform masks left unapplied, non-normal blend modes at group level, or text.

## 7. Export tiers

From the master, by **uniform premultiplied area-average downscale only** (the M1.0j-B `tiers.mjs` method):

| Output | Content | Tiers |
| --- | --- | --- |
| Full-figure composites | Per view × named expression, for review and static use | @1x (1 px/u), @2x (2 px/u) |
| Part PNGs plus frame JSON | Trimmed attachments with 2 px padding and extrusion | Rig milestone, not now |

Pages are ≤ 2048². Never enlarge. File names: `<who>-<view>-<expression>.v<N>.@<tier>.png`. Every file is hashed into `manifest.json` under the approval contract (`visualAcceptance` / `productionApproval` / `rights`).

## 8. Visual-fidelity checks (all must pass before owner review)

1. **Identity side-by-side:** the master, at equal head height, beside the accepted reference figure. Owner judgement of face, eyes, hair, outfit, palette and posture.
2. **Silhouette agreement:** the neutral ¾ composite at @1x against the accepted extraction at @1x. Alpha-mask IoU ≥ 0.90 (same pose), same anchor, height within ±1 %.
3. **Palette:** mean colour of hair, skin, shirt/blouse, shorts/trousers and shoes within ΔE₀₀ ≤ 5 of the accepted figure.
4. **Proportion:** head count within the §2 range; eye line within ±2 % of the accepted figure.
5. **Expression alignment:** identical alpha outside the face slots across expressions.
6. **Edge QC:** 0 halos and 0 paper specks with `candidates/m1.0j-c-construction/edges.mjs`; no detached components.
7. **Overlap QC:** every slot reaches its §5 overlap; the pose-sheet gap check (`app-momee/scripts/assets/pose-sheet.mjs`) shows no new enclosed gaps for the neutral pose.
8. **Provenance and rights:** illustrator agreement or tool, model, prompt and terms recorded. Rights stay `unverified` until evidence exists.

## 9. Boy and Mom specifics

**Boy: is the accepted illustration sufficient?**

- **Initial production work:** yes. At 514 px (2.57 px/u) it meets the 2.5 px/u minimum.
- **Static use:** the stage-2 and edge-cleaned cutouts serve development previews at @1x and @2x.
- **As a base for animation work:** an illustrator can paint the §5 hidden overlaps and §4 face attachments as new layers on top of the Boy working KRA at its native density.

**Boy: what is missing for animation?**

- The hidden overlaps (§5).
- Every face attachment except the drawn open-smile state.
- An elbow split.
- A `hair-back` layer.

A 4 px/u repaint is preferred long-term but not required to start.

**Mom v2 (M1.0k-A3, A4): visually accepted, static only.** The owner accepted Mom v2's appearance on 2026-10-24: `source/characters/mom/mom-three-quarter-master-candidate.v2.master.png`, about 3.42 heads, native left-facing ¾. It is **not production-approved** and its rights are **unverified**. It is a flat illustration, so animation still needs the §4–§6 layers; see [the M1.0l-A handoff](m1.0l-a-mom-animation-handoff.md).

**Silhouette exception (§8.2), Mom v2 only:** IoU 0.884 against the accepted v1.2 extraction at @1x, accepted by the owner because the difference is primarily slightly fuller hair and wider trousers. The global ≥ 0.90 guideline is unchanged. Layered Mom composites should be compared with v2.

**Mom: a genuinely higher-resolution standalone illustration is required.** (Met by v2; the brief below is kept as the record.)

- **Resolution:** the current figure is 514 px (1.77 px/u), below the 2.5 px/u minimum and the @2x tier.
- **Brief:** one new standalone ¾ illustration of Mom v1.2 at **≥ 1160 px figure height** (4 px/u; absolute minimum 725 px) on a transparent or flat background, native **left-facing** ¾ (§3).
- **Pose:** relaxed caring stance; hands unclasped or provided as a separate layer.
- **Identity, preserved from v1.2:** slightly longer face with a gentle chin; slightly smaller, soft brown eyes with two highlights and a small outer lash flick; long, full, soft waves with a side part, reaching mid-back, with locks over the shoulders; coral-pink rolled-sleeve button blouse; beige wide-leg trousers; white shoes; 3.2–3.5 heads.
- **Acceptance:** it passes §8, with the identity side-by-side taken against the v1.2 sheet's main figure. Upscaling or redrawing the current cutout procedurally does not qualify.
