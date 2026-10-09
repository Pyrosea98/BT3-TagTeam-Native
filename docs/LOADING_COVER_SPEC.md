# Loading cover: complete build spec (no further design rounds needed)

Owner: Claude (design), Codex (implementation). Written 2026-10-07. Reference render: `loading-mockups/v3-real-sprites.png`
(`claude_loading_mockup_v3.py`). Language/kit: `DESIGN_LANGUAGE.md`. Text: glyph atlas (`GLYPH_ATLAS_SPEC.md`). Sprites: `UI_ASSET_MANIFEST.md`.
All coordinates are in the 640x448 logical grid (origin top-left), mapped through the presentation rectangle.

## When it shows

- Shown only while a match is being prepared AND the game's own loading is not already covering the screen. It appears at match-preparation start
  (lifecycle state Loading) and stays until the lifecycle publishes Ready AND the owner observes Released. Never hide at 100% progress.
- If preparation finishes before the cover has been visible for 12 frames, never show it at all (the goal is no cover when loading is fast).
- Fade in 8 frames (alpha 0 to 1 on the whole cover), fade out 10 frames after release. During the cover the fighters stay idle and input is
  isolated (native match owner responsibility).
- Failure: keep the cover, replace the stage line with the error text (Title 18, red palette) plus "Close and reopen the game" (Body 16, white) and
  hold until explicit teardown.

## Layers (back to front)

1. Background: vertical gradient, top (14,20,40) to bottom (24,54,70); over it the dragon banner `450.0.9` stretched to 640 px wide, y = 134, alpha 0.30,
   scrolling left at 8 logical px/second (wrap), no other motion.
2. Fighter plates: left team plate and right team plate, each a slanted dark plate with the game-metal edge (see Plate below).
3. Portraits inside the plates (see Layout by team size). Idle: portraits do not animate except the active-ready pulse.
4. VS burst `455.11` centred at (320, 150) scaled 2.0.
5. Names: Body 16 white under each portrait (side 1 left-aligned, side 2 right-aligned), max width = plate width, ellipsis if longer.
6. Dragon Balls row: seven balls from `449.1.9` (4+3 grid of 64x64 cells), scaled to 56 px, centred at y = 292, x spacing 66 px starting at x = 88.
7. Progress frame: the wavy blue scroll `449.1.10` (256x64) scaled 1.5, centred x = 320, y = 340..372; fill inside is its own blue wave, animated by scrolling the wave
   texture horizontally 24 px/s; the fill width = progress * inner width.
8. Stage line: Body 16, white, centred, y = 384: localized stage text (below). Percentage: Numeric 14, gold, centred y = 404 ("37%").
9. Mod logo: small, top-right corner (590, 22) right-aligned: "TAG TEAM MOD" Title 18 gold; nothing else on the screen.

## Plate

Slanted plate, slant 20 px (top edge shifted right), fill (24,28,40) alpha 0.92, 2 px edge (190,198,215), outer 1 px glow in the fighter side's accent
(left team = cyan (90,208,255), right team = orange (240,162,74)). Reuse the 9-sliced HUD plate language (left cap, flat middle, right cap) from the settings rows.

## Layout by team size (each side up to 5 fighters, up to 10 total)

Left plate region x 24..296, right plate region x 344..616, both y 70..250.
- 1 fighter: one portrait 128x128 at the plate centre.
- 2: two portraits 96x96 side by side. 3: three 80x80. 4: 2x2 grid of 72x72. 5: one 80x80 leader on top row left + 2x2 grid of 56x56 (leader larger).
- The leader's name uses Body 16, other fighters Body 12 under their portraits.
- Portraits come from the portrait map: `portrait-slot-map.json[slot]` indexes the ISO UI portrait list (`PZS3US1` entry 450, package 1, ui[31]); scaled with bilinear filtering and a 1 px dark inner border.
- Costume/transformation form is not shown; show the base name from the runtime label table.

## Stage mapping (seven Dragon Balls)

The preparation phases in `[prepare-timing]` are 0..6 ("Preparing team battle", "Loading fighters" x2, "Preparing arena" x2, "Getting ready", "Ready"). Ball k lights when phase k completes
(ball 7 lights when Ready is published, not before). Phase texts (EN / ES), one catalogue entry each: "Preparing teams" / "Preparando equipos"; "Loading fighters" / "Cargando luchadores";
"Creating fighters" / "Creando luchadores"; "Preparing the arena" / "Preparando la arena"; "Setting up combat" / "Preparando el combate"; "Getting ready" / "Listo en un momento"; "Ready" / "Listo".
Progress = completed weight / total, using the measured phase durations as weights (so the bar advances smoothly rather than by seventh).

## Animation numbers (30 updates per second logic, drawn each display frame)

- Ball light-up: unlit alpha 0.35 grey tint; on completion scale 1.0 to 1.25 to 1.0 over 8 frames, plus a 6-frame white flash at 60% opacity; spark = 4 small star sprites flying out 16 px over 10 frames (reuse effect sprite from entry 2 if found, else a 2x2 white pixel diamond).
- VS burst: pops in once: scale 0.6 to 1.1 to 1.0 over 10 frames when the cover first shows; then static (no loop, no flicker).
- Progress wave: scrolling as above; fill eases to the target (ease-out, 12 frames) so jumps look smooth.
- Portraits: on ready, a single 6-frame brighten pulse on every portrait, then they stay.
- Dragon banner scroll: constant.

## Data the cover needs from the lifecycle

Generation id, phase (0..6), stage progress 0..1, rosters (two arrays of up to five engine slots), language, state (Loading/Ready/Failed/Released), error id. Nothing is read from legacy RAM fields.

## Acceptance (Codex runs these before reporting; the user tests only when all pass)

1. Offline: layout for every team size 1v1..5v5 and 1v5 stays inside its plate with no overlap (rendered contact sheet of all 25 combinations, 1x), names with 24 characters ellipsis correctly, ES and EN catalogues complete.
2. State machine: fast preparation never shows the cover; slow preparation shows it, never hides at 100%, hides only after Released; failure holds; stale generation ignored; rematch shows again.
3. GPU: the cover renders on the real Vulkan path over the game with no upload after the first frame, no frame-time spike over 2 ms in steady state (log it).
4. Live: one 5v5 mod match and one rematch with the new cover, fighters idle during preparation, input isolated, no regression versus the current loading time.
5. Art: side-by-side render against `v3-real-sprites.png`; Claude reviews the screenshot once.
