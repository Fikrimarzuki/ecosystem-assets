# Mom visual specification v1 (Soft Storybook Adventure)

**Status:** specification for owner review (M1.1a). Source of truth: the registered master reference `references/momee-soft-storybook-master-reference-v1.png` (manifest id `ref.momee.soft-storybook-master-reference.v1`, SHA-256 `907a9bd8…dd36`, 1536×1024). Everything below was read from that image. Where the image is silent or unclear, this document says so instead of inventing a feature.

**The reference is a flattened concept illustration.** Its "Character Components (SVG layers)" panel and the animation strips (Idle, Blink, Talk, Wave, Walk) are pictures, not editable layers or verified production assets. Mom is only about 190 × 380 px in the full-figure view, so all measurements are approximate (±3 px on the sheet) and colours are single-region averages.

## 1. Whole-sheet findings

| Element | Observed design |
| --- | --- |
| Boy | Short tousled brown hair, large brown eyes, open smile, cream hoodie with blue collar and pocket patch, navy shorts, navy sneakers, one hand waving; reads as a young child |
| Girl | Long wavy brown hair with a pink bow, pink pinafore dress (small star or flower motif) over a white top, pink shoes with white socks, hands up in a wave |
| Mom | See §2 |
| Dad | Short dark-brown hair, olive/sage overshirt open over a cream tee, tan chinos, brown shoes, hands in pockets; slightly taller than Mom |
| Expressions | Mom and Boy each show five heads: Neutral, Smile, Closed Eye (Wink), Talking, Surprised. Heads are bust crops with a shoulder and collar. |
| Component examples | One Mom figure beside separated pieces (back hair, front hair locks, blank head, three face-feature rows, trousers, torso/arms, shoes). It is a layout illustration; the pieces are not guaranteed to match the full figure (see §7). |
| Environments | Bedroom (wood bed with a blue star quilt, dresser, shelves, toys, sunny window with cream curtains, plants, round rug), kitchen (wood cabinets, table, light), bathroom (pale blue tile, white sink), entrance/hallway (wood doors, coat hook), outside (garden fence, flowers, trees) |
| Palette | Eight swatches (sampled): brown `#996953`, sand `#f3dabc`, coral `#fdbca7`, white `#fffeff`, butter `#fae2ae`, sage `#a4ae7c`, sky `#b0cde1`, lavender `#bfabe1`; the sheet background is `#f8f0e5` |
| Tone words on the sheet | Warm, Friendly, Safe, Playful, Storybook, Interactive |

Note: Girl and Dad are shown here for the first time; no legacy artwork exists for either.

## 2. Mom: character identity

| Aspect | Reference |
| --- | --- |
| Pose | Front-facing, standing, weight even. Her right hand (viewer's right) is raised in an open-palm wave; her left hand rests low at the waist. Feet apart, shoes pointing slightly out. Warm, gentle, calm ("Warm, gentle" on the sheet). |
| Head | Round, soft, slightly broader at the cheeks, with a small chin. A large head relative to the body, but less extreme than the Boy's. |
| Eyes | Large, dark-brown irises with a darker pupil and a white highlight, a thin darker upper lash line, no heavy outline; set wide apart |
| Eyebrows | Thin, softly arched, brown, close above the eyes |
| Nose | Minimal: a faint small mark or none |
| Mouth | A small, gentle closed smile in the neutral pose |
| Blush | Soft peach blush on both cheeks |
| Skin | Warm light peach (sampled about `#fedebf`) |
| Hair silhouette | Long and wavy, falling past the waist, with a side part (at the viewer's right of centre), a soft swept fringe across one side of the forehead and locks framing the face. Volume is wide at the shoulders and tapers into curling ends. |
| Hair colour and shading | Mid reddish-brown (sampled `#84442d`) with a glossy lighter highlight band (about `#c5704d`) near the crown and on waves, darker inner shadows between waves |
| Proportions | About 3.5 heads tall (estimated by eye; ±0.3). Slim body, narrow shoulders, long wide-leg legs. Hands are small and simple. |
| Outfit | Coral-peach button blouse with a pointed collar, sleeves gathered at the forearm, tucked into a high-waisted waistband; cream wide-leg trousers with a waistband and side pockets; white low sneakers |
| Personality | Warm, gentle, welcoming, relaxed |

## 3. Rendering style

- **Outlines:** soft, warm brown, thin, fairly consistent; no black.
- **Palette:** warm pastels (coral, peach, cream, brown), no saturated primaries.
- **Shading:** gentle gradients and one soft shadow tone per area, with a light highlight; a subtle painterly finish rather than flat vector fills.
- **Shapes:** rounded, with softly tapered curves; no sharp geometric edges.
- **Contact shadow:** a faint soft ellipse under the feet on the sheet. In production it belongs on a separate shadow layer.

## 4. Animation-aware construction (proposed components)

Draw order, back to front. Names follow the slot convention (`slot/attachment`).

| Component | Contents | Likely pivot |
| --- | --- | --- |
| `shadow` | soft ellipse | none |
| `hair-back` | the long wavy mass behind head, shoulders and back | head joint (so it follows the head) |
| `arm-back` (her left) | upper arm, forearm, hand resting at the waist | shoulder, elbow, wrist |
| `leg-back`, `shoe-back` | trouser leg and shoe | hip, knee, ankle |
| `body-skin` | neck, hands, wrist skin | neck base |
| `leg-front`, `shoe-front` | trouser leg and shoe | hip, knee, ankle |
| `outfit-bottom` | trousers with waistband (one piece, or two legs plus a waist piece) | hip |
| `outfit-top` | blouse body and collar | waist, neck base |
| `head-skin` | face, ears, neck overlap | neck |
| `face-blush` | cheek blush | head |
| `face-eyes` | open eyes; later half, closed and happy frames | eye centres |
| `face-brows` | brows (neutral; raised later) | brow centres |
| `face-mouth` | neutral smile; later small and wide open | mouth centre |
| `hair-front` | fringe and face-framing locks | head joint |
| `arm-front` (her right, waving) | upper arm, sleeve, forearm, hand | shoulder, elbow, wrist |

**Likely joint overlaps and hidden artwork** (not visible in the reference; they must be newly drawn and are not present in the sheet):
- **Head and neck:** the neck extending up under the chin and down under the collar; the skull behind the front hair.
- **Hair-back:** the whole mass behind the body, and the shoulders behind the hair.
- **Shoulders and sleeves:** shoulder caps under both sleeves and the torso side behind the raised arm (needed for waving).
- **Elbows and wrists:** a forearm overlap under the gathered sleeve; wrist continuing into the sleeve cuff; fingers of both hands.
- **Waist and hips:** blouse hem under the waistband, thighs under the trousers, ankles and shoe tops under the hems.
- **Face:** eyelid skin under the eyes for blink frames; skin under the mouth.

## 5. Fidelity priorities

**1. Identity-critical (keep faithful):** the face proportions and eye size; the gentle smile and soft brows; the long wavy side-parted hair silhouette and its reddish-brown colour; the coral blouse, cream wide-leg trousers and white sneakers; the warm palette; the soft brown outline and painterly finish; the overall proportions (about 3.5 heads); the warm, gentle personality.

**2. May be simplified for animation (carefully):** individual hair strands and flyaways (keep the main waves); small fold lines around the gathered sleeves, elbow and waist; the exact finger shapes while keeping the open-palm wave; fine texture in the hair; the contact shadow's softness; hidden joints (painted simply).

**3. Needs owner review before changing:**
- front versus ¾ view (the reference shows a front view; the legacy Mom master was a left-facing ¾);
- hair length and volume, if the animation needs it shortened;
- blouse sleeve length and gathering;
- shoe colour (white in the full figure, brown in the component panel);
- proportions (head count);
- any change to the colour palette or outline weight;
- whether the waving arm is the neutral pose or a separate pose.

## 6. What the reference does not show

Do not assume these exist: Mom's back, side or ¾ views; the unclasped lower arm and hand details; ears (hair hides them); closed-mouth profile; teeth and tongue detail; a full-resolution face (the face is about 70 px wide on the sheet); a neutral resting pose with both arms down; shading direction beyond a soft top-left tendency (not verified).

## 7. Discrepancies inside the reference (flag for the owner)

- **Shoes:** white sneakers in the full figure, brown shoes in the component panel.
- **Trousers:** a cream colour in the figure, a darker beige in the component panel.
- **Pose:** the full figure waves, while the component panel's figure stands with both arms down.
- **Components panel:** the pieces are sketches rather than a measured breakdown, and the back-hair piece looks like a ponytail shape unlike the free-flowing hair.
- **Animation strips:** Mom's Idle, Blink, Talk, Wave and Walk frames are pictures of the same character; they are not verified production assets.
