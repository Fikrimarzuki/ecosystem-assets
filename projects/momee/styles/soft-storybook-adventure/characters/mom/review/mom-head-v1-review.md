# Mom head v1: review notes (M1.1b-1)

**Status:** candidate for owner review. **Not visually accepted, not production-approved.** A valid render is not the same as visual acceptance.

| File | Purpose |
| --- | --- |
| `../source/mom-head-v1.svg` | Editable source (780×880 viewBox, 59 paths, 8 ellipses, 2 circles, 11 gradients, no filters, no images, no text, no external references) |
| `../exports/mom-head-v1.png` | Inkscape export at 192 dpi: 1560×1760, transparent background |
| `mom-head-v1-comparison.png` | Reference crops beside the prototype at a comparable size, plus an enlarged detail |
| `../source/construction/` | Drafting aid: the template and the script that smooths the hair silhouette, wave troughs and glints from hand-placed points. Not needed to edit the SVG. |

## Reference findings used

The full figure and the Neutral expression bust agree on these points:
- **Face:** wide and soft, with full cheeks and a small rounded chin.
- **Eyes:** large round warm-brown irises with a top-left highlight, and a dark tapered upper lash with a small outer flick.
- **Small features:** short, thin, gently arched brows; a tiny nose; a small closed smile; lateral peach blush.
- **Hair:** a side part right of centre and a broad fringe sweeping to the viewer's left; a short lock at the right temple; both ears visible in front of the side hair; long reddish-brown waves with a glossy crown.
- **Detail available:** the face is only about 66 px wide on the sheet, so the fine details are informed reconstruction, not copying.

## Fidelity assessment (critical)

| Criterion | Assessment |
| --- | --- |
| Face likeness | Recognisably the same character: eyes, smile, blush, ears and part all match. The face reads slightly **younger and rounder** than the reference, and the cheeks lack the reference's soft modelling. |
| Eye shape | Close in size, colour and highlight. The **lash flicks are sharper** and the eyes slightly more "sticker-like" than the soft painted eyes in the reference. |
| Facial proportions | Eye spacing and height match within a few pixels at the sheet's scale. The face is slightly wider at the jaw. |
| Hair silhouette | Side part, sweep and long waves are present. The silhouette is **simpler**: fewer layered locks and flyaways, and the waves are smoother than the reference's flowing, overlapping waves. |
| Hair colour | Close (warm reddish-brown). The reference has **richer gloss bands** and depth; ours is flatter. |
| Storybook shading | Gentle gradients and soft outlines, but **flatter and more vector-like** than the reference's painterly finish |
| Adult identity | Acceptable but borderline: it could still read a little young (big eyes, round face) |
| Overall appeal | Clean and friendly, but **not yet at the reference's quality**. |

**Verdict:** a promising first candidate, not visually successful yet. It needs owner review and at least one more art pass.

## Editability and animation readiness

- **Groups** (every element has an id; no element is merged into the face):
  - `hair-back`: silhouette, troughs, strands, glints;
  - `neck-preview`;
  - `head`: ears, face base whose top edge is the hairline, shading, blush, nose;
  - `facial-features`: eyebrows; eyes, with clipped iris groups; mouth;
  - `hair-front`: fringe sweep, temple lock;
  - `highlights`.
- **Blink:** each eye is its own group, so a closed or half eye can replace it. The skin under the eyes is the face base, so nothing has to be repainted.
- **Talk and expressions:** the mouth group and the brows are separate, so new shapes can be swapped in.
- **Head movement:** the hair-front and the head move together. The hair-back is one mass, so a simple sway is possible, but there are no per-lock parts.
- **Customisation:** hair colour lives in gradients (`hairBase`, `hairFringe`, `glint`, streaks); skin in `skin`, `neck` and the ear fills; eye colour in `iris`.
- **Candidate pivots, as guides only (no rig):**
  - head joint about (387, 470);
  - eye centres (321, 337) and (454, 339);
  - mouth (387, 410).

## Known deviations

1. **Hair:** less layered and glossy than the reference, and the waves are simplified.
2. **Eyes:** sharper lash flicks.
3. **Face shape:** slightly rounder and younger.
4. **Forehead:** the sweep leaves a little more forehead visible in the centre than the reference does.
5. **Hair length:** stops at chest length for this head prototype; it continues in the full body.
6. **Neck:** a preview only; no collar or shoulders, which belong to the torso.

## Suggested next iteration (after owner feedback)

- **Eyes:** soften and shorten the lash flicks.
- **Face:** slightly narrower jaw and softer cheeks, for a more adult read.
- **Fringe:** bring the sweep lower across the centre of the forehead.
- **Hair:** add two or three overlapping front locks over the shoulders, broader gloss bands and a little more wave definition, without splitting the hair into many parts.
