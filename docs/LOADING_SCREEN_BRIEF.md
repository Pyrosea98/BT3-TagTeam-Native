# Tag Team loading screen: brief for Codex (workstream G)

Owner: Codex (lead). Claude supports with review and the mockup scripts. Coordinate in `COLLAB.md`.
Written 2026-10-05 after user feedback on two mockups.

## What the user wants (their words, summarised)

- The loading screen of the Tag Team mod must not break the look and feel of
  Budokai Tenkaichi 3. Not generic, not a neon sci-fi HUD.
- Show the **character select images of every participant**, a big **VS**, and a
  **progress bar**.
- Show the **game logo** (`power-scale-trial/controller/game/Tag Team Mod Logo.png`,
  the BT3 logo with "TAG TEAM MOD").
- **Dragon Balls on the progress bar: approved** (seven balls that light up as
  loading passes each seventh).
- **Dragon art: rejected.** Claude's procedurally drawn Shenron "looks like it
  was drawn by a 3 year old". The colour palette (green, red, gold) was right.
  Do not ship a hand-coded dragon. Use real art or leave it out (see "Art").
- BT3's own loading screens are interactive mini scenes (Vegeta doing
  push-ups, Gohan pulling out many Z swords, Goku eating, split screens). The
  user would like something interactive while loading. **Z swords is the
  preferred mini game.** Other ideas they mentioned from other DB games:
  growing Saibamen with the analog stick, climbing Korin's Tower.
- Fighters must stay idle: input pressed during the mini game must not make the
  background fighters act or leak into the match when it starts.

## Mockups (reference only, not production)

- `claude_loading_mockup.py` -> `loading-mockups/1_2v2.png`, `2_1v3.png`,
  `3_5v5.png`: layout that scales 1..6 fighters per side, real portraits,
  blue (P1) and red (P2) frames, name plus power string banners, VS, bar.
- `claude_loading_mockup_v2.py` -> `loading-mockups/v2_2v2.png`, `v2_1v3.png`: adds
  the logo, a dragon (rejected) and the Dragon Ball progress row (approved).
- Facts learned while drawing: the 161 portraits are 64x64 with the real art in the
  box (8,10)-(56,53) (48x43); crop to it and scale, or the faces look tiny.
  `characters.json` `base_name` is the name with the Power Scale `[n]` suffix,
  `form` is the power string. Fonts are Windows system fonts (Arial Black,
  Arial Bold Italic); the game's own font is not available to us.
- Do not treat the mockup as the design. Improve it: closer to the game's own UI
  (look at the select screen and native loading scenes), better typography,
  better frame art.

## Art (the open problem)

Options, best first. Please evaluate and report before building:
1. Real game art from the user's ISO (user-owned files, extracted locally like
   `extract_loading_assets.py` does for portraits): Shenron, Dragon Ball, Z
   sword, tower, background textures, the native VS or menu frames. Needs a
   survey of which textures exist and where (menu overlay `DBZP.BIN` textures,
   `PZS3US*.AFS` UI packages).
2. Hand-authored raster/vector art supplied by the user (ask them).
3. No dragon: logo + aura + Dragon Balls only.
Never redistribute extracted art in the repo or installer; extract at install time.

## Technical constraints (what exists today)

- Pipeline: `guest_loading_screen.py` installs a PNACH hook late in the native
  frame (before the battle loop submits its GIF arena). The controller writes
  double-buffered packets over PINE. Protocol v4 "Ki Storm": packet A (GS
  setup, PSMT8 background/foreground/atlas uploads with CLUTs), packet B
  (foreground registers), then a 4 KiB descriptor with the animation plan
  (`loading_lights_a/_b`, `loading_protocol.py`, `loading_art_v4.py`). Native frame
  is 512x448, drawn at 2x and resampled; images are PSMT8 (256 colours).
- Progress and messages come from the preparation stages in the controller
  (`autopilot.py`, `loading_presentation.py`, `guest_loading_screen.py`).
- A legacy rectangle-only packet without a descriptor is still accepted.
- **Current regression (must be fixed first, see COLLAB Request 2):**
  `guest_loading_screen.sync()` disables the cover because the Power Scale module
  now overwrites the Tag Team duplicate-selection patch at `0x261650`
  (`loading hook out of date`). Nothing here will display until that is fixed.
- Frame rate: a full picture per update is heavy over PINE; expect roughly 5-10
  updates per second unless a guest-side sprite/animation routine is added
  (the v4 descriptor already animates ribbons, sparks, gauge digits at 60 Hz in the
  guest; reuse that model for an animated bar, Dragon Ball glow, embers).

## Interactive mini game (Z swords), staged

Do not start it before the static screen works.
1. Static screen with logo, portraits, VS, Dragon Ball progress driven by the real
   preparation percentage.
2. Ambient guest-side animation (embers, ball glow).
3. Prototype Z-sword mini game: read the pad (see `controller_mailbox.py`, pad
   input helpers) at about 30 Hz, draw sword-pull progress/score. Design it so it
   never affects loading: no waiting on input, no extra heap, bounded work per frame.
4. Input isolation: fighters have CPU/input disabled during preparation; also
   flush any buffered pad edges when the match is released, and ignore held
   buttons for a short grace window.
5. Research item, separate and optional: whether the game's native loading
   scenes can be invoked during preparation. UNKNOWN; not verified.

## Acceptance

- Appears during preparation in Vulkan native runs, for 1v1..5v5 and uneven teams.
- No "hook out of date" message in `controller.log`.
- No effect on loading time or stability; two consecutive matches both show it.
- Uses only the user's own game data for art; no third-party downloads.
