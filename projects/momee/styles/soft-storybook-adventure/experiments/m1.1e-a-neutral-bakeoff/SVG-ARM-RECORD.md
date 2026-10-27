# SVG arm record (artwork removed 2026-11-16)

> The SVG candidate artwork was rejected and deleted. This is the arm's own README, kept unedited below as a historical record. Image, SVG and sheet files it names no longer exist.

---

# M1.1e-A Gate A: neutral Mom, SVG arm (EXPERIMENTAL)

**Status: not visually successful yet.** These files are ready for the owner to compare. They are not accepted, approved or production-ready, and the rights are unverified.

- **Target:** Candidate B (`references/mom-art-direction-exploration-v1.png`, middle column), one step more mature.
- **Method:** a new SVG built from scratch with the `momee-character-art` skill. `mom-head-v1.svg` was not copied or modified.
- **Reference crop:** B's main portrait at `541,191,294,351`. I checked it visually: an enlarged crop shows the panel's rounded border at about x 541–836 and y 191–541. The B eye tile is at `541,730,112,109`.
- **Input hashes:** both reference SHA-256 prefixes matched (`118eca2c`, `907a9bd8`).

## Files

| File | What it is |
| --- | --- |
| `mom-neutral-svg-v1.svg` / `.png` | Final (pass 2). viewBox `0 0 1024 1280`, exported at 96 dpi to 1024×1280 with alpha |
| `check-svg.txt` | `check-svg.mjs` output with `--groups` for the 18 named groups: **OK**, 0 warnings |
| `review/sheet-256.png`, `review/sheet-144.png` | Primary sheets: B portrait crop, Mom v1, SVG candidate |
| `review/sheet-720.png` | Secondary detail sheet |
| `review/eye-detail.png` | B eye tile beside the candidate's left and right eyes, enlarged. Crops: `296,520,204,198` and `590,520,204,198` |
| `iterations/` | `pass0-build`, `pass1` and `pass2` as `.svg` and `.png`, plus each pass's 256 and 144 sheets |
| `construction/build-mom-neutral-svg.mjs` | Drafting script that writes the SVG. All anchors are hand-placed. Only the outlines of tapered features (lashes, crease, brows, strands, gloss) are computed from 3–6 point spines |

**Ids:** "left" and "right" mean the viewer's left and right, as in Mom v1.

**Group order:** `hair-back > outfit-top-back > neck > outfit-top > head (ears, face-base, shading, blush, nose) > facial-features (brows, eye-left, eye-right, mouth) > hair-front (hair-front-cap, hair-front-lock-left, hair-front-lock-right) > highlights`.

There are no frames, rig or animation.

## Passes used: 1 build + 2 visual (the cap)

| Pass | File | What changed and why |
| --- | --- | --- |
| 0 | `iterations/pass0-build.png` | Complete first build: almond clip-path eyes, tapered lashes and crease, side-part hair cap, back hair, two front locks over the shoulders, coral blouse with collar. **Judged:** the eyes were too pale and small at 256 and 144, the hair read as a straight helmet with hard horizontal trough bands, and too much forehead showed |
| 1 | `iterations/pass1.png` | Eyes about 8% larger with a darker iris, a thicker lash mass and a higher, darker crease. Wavy, asymmetric hair silhouette and lock edges. The trough rectangles were replaced by curved tapered separations. Fringe edge lowered and a part notch added. Hair value lifted toward B's caramel. Blush stronger, ears smaller. **Technical fix in the same export:** the fringe shadow showed a grey blob, so I rebuilt it as tapered bands |
| 2 | `iterations/pass2.png` = final | Right face-edge lock widened and fringe edge made fuller, to reduce the exposed forehead. Broad low-opacity sheen bands on the crown, sweep and right mass. The outer cap edge became a tapered line instead of a hard stroke, because it read as a hood seam. Softer lash flick. Slightly warmer top of the eye white |

**Honesty notes:**
- During pass 1 I made one intermediate check render before the saved pass-1 export.
- I first cut the eye-detail sheet too tight. I deleted it (my own file) and regenerated it with full-eye crops.

**Session size:** about 50 tool calls. That is roughly 150–200k tokens of context, including reading the skill files and viewing about 15 images.

## Visual-review checklist (final, judged at 256 and 144 first)

1. **Identity: partly.**
   - *Observed:* The same reddish-brown, long, wavy, side-parted hair, the coral collar and the warm palette. She reads as an adult rather than a child, so she is more mature than B.
   - *Observed:* The charm and softness are weaker than B. The face is a large, pale, smooth area, so at 144 she reads as a generic vector woman rather than clearly "Momee Mom".
2. **Eyes: mostly yes.**
   - *Observed* (eye-detail sheet): an almond opening with a flatter lower lid, a visible upper-lid crease, the iris cut by the upper lid, a lash mass with one soft outer flick and no spike rows, and no circular sticker opening.
   - *Observed:* Two weaknesses remain:
     - the main highlight is still a round white blob;
     - the crease is a little heavy.
   - *Assumption:* Size compared with B. I estimated it from coordinates in the enlarged crop, because no script measures it. The opening is about 8% narrower than B's, short of the 10–15% target. Including the lash it is about equal. At 256 the eyes still look smaller than B's (*Observed*), because more white shows and the iris is lighter.
3. **Proportions: partly.**
   - *Assumption* (estimates from crop coordinates, not script-measured):
     - eye line at about 50.6% of the canvas height, against about 49.7% in B;
     - eye-to-chin distance about 10% longer than B's;
     - face width about the same.
   - *Observed:* The longer lower face does read more adult, but the face as a whole reads larger and longer than B's. The exposed forehead triangle is still bigger than B's.
4. **Hair: partly.**
   - *Observed:* The silhouette is asymmetric (larger, lower left mass; waves peak at different heights), and the side part sits right of centre.
   - *Observed:* There are overlapping masses (cap, fringe sweep, right mass, back hair, two front locks) with curved shadow separations. Gloss follows the wave direction.
   - *Observed:* But the crown is still a smooth even dome, the upper sides read as a straight curtain, and the front locks have heavy, tube-like outlines on both edges.
   - *Observed:* Varied ends are not visible, because the bottom is cropped like B's.
5. **Shading: partly.**
   - *Observed:* Every area has gradients, with a soft hair interior behind the neck and a face-edge vignette.
   - *Observed:* Some edges are visible at 720 and in the eye detail:
     - the right-forehead lock-shadow band;
     - the fringe shadow bands;
     - the crown sheen bands.
   - *Observed:* The hair highlights are not plastic. The eye highlight is borderline.
6. **Line: partly.**
   - *Observed:* Lines are warm brown and never black. From the source, the silhouette is heavier (hair 4–4.5) than the inner lines (2.4–3.2).
   - *Observed:* The front-lock inner edges carry silhouette weight across the blouse and look mechanical.
7. **Generic-vector test: no.**
   - *Observed:* At 144 and 256 it looks closer to clean stock vector art than to B's soft painted storybook finish.
   - *Observed:* It is better than Mom v1 in eye shape, adult read, hair waves and framing.
8. **Structure: yes.**
   - *Measured:* `check-svg.mjs` reports OK with all 18 required groups and 0 warnings. `xmllint` is clean. The export is 1024×1280 with alpha.
   - Frames: none, by brief.

## Gaps vs Candidate B, most visible first

1. **Face area too large and flat.** The forehead triangle shows too much, cheek and side modelling is weak, and the skin is paler and less peach than B's.
2. **Hair lacks B's painterly volume.** The crown is an even dome without B's broad glossy crown highlight. There are too few fine strand lines, the upper sides are curtain-like, and the lock outlines are tube-like.
3. **Eyes read lighter and smaller at small sizes.** More sclera shows, the iris is less saturated amber, and the highlight is a plain round blob.
4. **Visible gradient and band edges.** These are the lock shadow on the right forehead, the fringe shadow bands and the sheen bands.
5. **Ears are more prominent** and lack B's hair shadow.
6. **Blouse is simplified.** It has no collar band, flatter collar points and narrower shoulders than B.
7. **Overall "generic vector" finish.**

## Skill-effect notes

**Known failures it helped avoid (observed against Mom v1):**
- circular eye openings: almond clip path;
- sharp or curly lash spikes: one soft flick;
- mirrored hair curtains: deliberate asymmetry;
- the doll look and weak adult identity, partly: longer lower face, crease, closer brows;
- plastic circular glints in the hair: long tapered gloss instead.

The eye construction order in `facial-design.md` was the most directly useful guidance.

**Not avoided:**
- the generic vector look;
- flat shading on large skin areas;
- a slightly sticker-like round eye highlight.

**Gaps or problems in the skill:**
- **Soft-edged shading:** there is no technique for soft shading shapes on non-elliptical paths without filters. "Fade gradients to 0" works for radial blobs, but tapered bands at a uniform opacity give hard edges. That is the source of gap 4.
- **No measurement script:** `visual-review.md` asks for "Measured" evidence on proportions, but no script prints eye width, eye line or face length. All proportion claims here are therefore Assumptions.
- **Brow colour conflict:** `facial-design.md` says brows are "hair colour, slightly lighter", but the B sample is darker (`#944f2e` against hair `#a15733`). I used the sample.
- **Front-lock tops:** `hair-design.md` doesn't cover how to blend the top of a `hair-front-lock-*` (in front of the body) into `hair-back` without a seam.
- **check-svg blind spot:** `check-svg.mjs` skips every gradient-filled ellipse in its sticker warning. Iris and blush pass, which is correct, but sticker-like highlights are never flagged.
- **Canvas size:** `svg-techniques.md` says Mom head sources use 780×880. This brief required 1024×1280. No conflict in practice.
- **Workflow step not followed:** the SKILL workflow's "build part by part" step was not literally followed. I built everything in one generated pass, then judged.
- **Skill listing:** the Skill tool did not list `momee-character-art` at session start. It appeared after I read the folder, and I then invoked it.
- **Tools:** `export-png.sh` (no hang) and `compare-sheet.mjs` worked first time.
