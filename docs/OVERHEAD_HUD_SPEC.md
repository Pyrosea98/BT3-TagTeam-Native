# Overhead HUD: a detailed mini-HUD over 1P and the target, simple bars over everyone else

Owner: Claude (design), Codex (implementation). Written 2026-10-07. Reference render: `loading-mockups/overhead-hud-mock.png`
(`claude_overhead_hud_mock.py`, drawn on the user's own 21:9 screenshot). Builds on `MODE_SCREENS_SPEC.md` (HUD options) and `DESIGN_LANGUAGE.md`.

## Why (user, 2026-10-07)

- The corner panels are hard to align on 21:9 and, in a 10-fighter free-for-all, there are far too many names on screen.
- Direction from the user: focus the HUD on the **health and ki bars**; show a **small detailed HUD over the fighter you target and over your own
  fighter (1P)**; everyone else gets the **simple life bar we already have** (the overhead health bars). With that, the game's original HUD can be hidden
  ("the original hud can disappear"). Some of the extra info must remain switchable in Mod settings.

## What is drawn

1. **Detailed mini-HUD over 1P and over the current target** (two at most per viewport). Anchored to the fighter's head with the game's own projection
   (`1210D8`, as `guest_healthbars` does), a small pointer at the bottom. Contents, left to right: optional portrait 36 px square, name (Body 12-14, one line,
   ellipsis), HP bar (slanted, green, red under 25%), ki bar (slanted, blue), ki stocks as small pips, "1P" tag for the owner; transformation/charge state as a
   small icon when active. Plate: dark slanted plate with a 2 px light edge (same plate language as the settings rows); accent edge cyan for 1P, orange for the target.
2. **Simple bar over everyone else:** the existing overhead health bars restyled to the kit: slanted 64x7, green, red under 30%, no name, no portrait. Optional
   tint by relation (allies cyan edge, enemies orange edge) when "friendly/enemy bars" are enabled. Dead fighters show nothing.
3. **Names:** only inside the two detailed HUDs by default. Setting `hud_overhead_names`: Off / 1P and target (default) / All.
4. **Corner panels are removed** (user decision). The contestant list is optional and defaults to Off, kill feed and fusion timer remain independent toggles.

## Behaviour rules

- Scale with distance, clamped to 70-130% of the base size (never smaller than Body 11); fully clamped to the viewport edges: if the 1P or target fighter is off-screen
  show a small edge arrow with a two-letter abbreviation of the name instead of the full HUD.
- If the two detailed HUDs would overlap, push the target's HUD up by its own height; never cover the other fighter's head.
- Hide all overhead elements during cinematics (ultimates, transformation scenes, fusion dance, intros) using the existing cinematic/pause flags; fade in 6 frames after.
- Split-screen and 3-4 player modes: each viewport draws its owner's detailed HUD and that owner's target; other fighters get the simple bar; every viewport is scissored.
- Changing target (L3) moves the detailed HUD to the new target immediately; the old target falls back to the simple bar.
- Free-for-all with up to 10 fighters: at most 2 detailed + 9 simple bars; no contestant list unless the user turns it on.
- Fusion: the fused fighter shows the fusion name once and the fusion timer plate underneath its detailed HUD when it is 1P or the target.
- Performance: one projection call per drawn fighter, one sprite batch per frame; stay under 0.3 ms per frame at 10 fighters.

## Settings (page "HUD", all with EN/ES strings, applied at the next match)

- `hud_style` (DECIDED by the user 2026-10-07: the misaligned corner panels are REMOVED, no Classic style): **Game HUD + overhead** (default) / **Overhead only** (game HUD hidden). The game's own HUD simply stays, or is disabled by `show_native_hud`.
- `hud_overhead_names`: Off / 1P and target / All. Default: 1P and target.
- `hud_overhead_detail`: 1P only / 1P and target / 1P, target and allies. Default: 1P and target.
- `hud_overhead_portraits`: On/Off (default On for detailed HUD).
- `hud_panel_scale_percent` and `hud_panel_opacity_percent` (from the previous spec) apply to the overhead plates.
- `show_native_hud` keeps working independently, and the native-HUD toggle must really hide the game's own HUD (known bug: it is ignored today).

## Acceptance

1. Capture sheets at 21:9, 16:9 and 4:3 for 2, 6 and 10 fighters in Classic, Compact and Overhead-only styles; text only on plates; no overlap between the two detailed HUDs; off-screen arrow case.
2. Target switching, fusion, transformation, cinematic hide and split-screen behave as above (one live session).
3. Native HUD OFF really hides the game's HUD; the overhead HUD alone carries all the information the player needs (HP, ki, stocks, name of 1P and target).
4. No measurable frame-time regression (log the median/max compose time).

## Addendum (user idea, 2026-10-07): the frame itself is the gauge (hexagon / ring), translucent

Instead of a plate with two bars, draw a small portrait inside a frame whose BORDER is the life and ki gauge: no plate, so the HUD is smaller and naturally translucent. Reference render
`loading-mockups/hex-hud-mock.png` (`claude_hex_hud_mock.py`): **A** flat-top hexagon (top three edges = life, bottom three edges = ki, both filling left to right), **B** double hexagon
ring (outer = life, inner = ki), **C** round ring (outer 270 degree arc = life, inner arc = ki). Size about 40-46 px for 1P/target on a 640x448 grid scale (about 3x smaller than the plate), fill alpha about 40-45%,
border track 1 px light edge, gauge colours as the kit (life green, red under 30%, ki blue), accent edge cyan for 1P and orange for the target. Name: small Body 11 label under the shape for 1P and target only
(setting), ki stocks as up to 6 tiny pips around the lower edge when there is room, "1P" tag as a small chip at the lower-left. New setting `hud_overhead_shape`: Plate (current) / Hexagon A / Double hexagon B / Ring C
(default after the user's pick). Simple bars for other fighters stay as they are.

## Decision (user, 2026-10-07): shapes A and C, selectable; names optional/tiny
- `hud_overhead_shape` = **Off / Hexagon (A) / Ring (C) / Plate** (the user picked A and C; B is dropped; Plate stays as the classic alternative). Default: Hexagon (A). "Off" removes the detailed overhead HUD for 1P/target (simple bars for the others remain governed by the existing bar toggles).
- Names: `hud_overhead_names` default **Off**; options Off / Tiny (Body 10-11 under the shape, 1P and target only) / Normal. The cleaner look does not need names.
- Everything else (size 50-120%, opacity 30-100%, cinematic fade, ki pips as an option) as in the earlier entries.

## Clarification (user, 2026-10-07)
- ONE shape at a time (Hexagon or Ring); the focused target uses the SAME shape and look as the owner (no separate styling), only the accent colour differs.
- The game's original HUD must be able to DISAPPEAR completely ("Overhead only"): the overhead HUD then has to carry every fight-critical piece the original shows for the watched fighter: life, ki, ki stocks (pips), transformation/charge state, and the fusion timer when active.
- Size and opacity are capped: gameplay over look and feel (Rule 0 in `DESIGN_LANGUAGE.md`).
