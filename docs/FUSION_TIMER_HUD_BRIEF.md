# Fusion timer HUD: brief for the native version

Owner: Claude (design), Codex (implementation). Written 2026-10-06. Status: concepts shown to the user,
choice pending.

## What exists today (CONFIRMED from `fusion_duration.py:165-200`)

- Drawn by guest MIPS code per viewport: the countdown text through `guest_killfeed.TEXT` (the mod's own
  compact 5x7 bitmap glyph atlas, drawn as GS rectangles) and a 3 px bar through `guest_healthbars.RECT`.
- Colour 0x80A0FFFF (light blue, half alpha), anchored under the fighter's health area:
  `screen_y(232)` stacked or `screen_y(168)`, x from the viewport at actor+512 + 1800.
- Remaining time is `seconds * ACTOR_HZ` (default 40 s); the bar total comes from the record or CONTROL+16.
- Extra CPU fusions only show their timer when watched (camera successor or viewport owner).
- Settings: `show_fusion_timer` (bool) and `fusion_duration_seconds` in Mod settings. Keep both.

## Why it looks 8-bit

The glyphs are 5x7 pixel blocks and the bar is a flat rectangle; nothing uses the game's own HUD art.

## Goals

1. Looks like it belongs to Budokai Tenkaichi 3: same numeral style as the match clock, the same slanted bar
   shape as the ki/health gauges, the game's own colours and fade timing.
2. Readable at a glance in split-screen / 4-player viewports (smaller scale, same layout).
3. Warns the player before defusion (colour change at 10 s, pulse at 5 s, short sound cue if one exists).
4. Shows who is fused (portrait pair or two names) only when there is room; never covers the fighters' health.
5. Native only: no new Python/PINE injection. Draw from the embedded runtime (or from the frozen cave pack) using
   textures extracted at install time from the user's disc (no game art shipped).

## Concepts shown to the user (mockups in chat)

- A: large italic match-clock numerals over a slanted gauge (cheapest, closest to the game).
- B: split gauge in the two fighters' colours with a round numeral emblem and the fused names.
- C: draining ring that turns red under 10 s (best warning, needs more art).

## Open decisions (user)

- Which concept (or mix), and whether to show names/portraits.
- Warning behaviour: colour only, or colour plus sound.

## Data needed by the implementation

- The game's numeral font/atlas for the match clock (find in the UI/HUD packages; Claude to locate by RAM scan
  like the portrait block) and the gauge frame sprites.
- Per-viewport anchor and scale rules (reuse `viewport_hud.py` geometry).

## Game art located on the user's disc (2026-10-06, Claude; CONFIRMED by decoding to PNG)

Decoder: PSMT8 GS textures (TEX0 at +0x50, pixels at +0xC0, palette at +0xC0+w*h+0x80), the same layout as the
portraits (`claude_hud_sheet.py`, contact sheets in `power-scale-trial/hud-sheets/sheet0..5.png`, index of all
3,975 PSMT8 textures in `power-scale-trial/psmt8-textures-afs1.json`). Paths are AFS1 (`PZS3US1.AFS`) entry.package.sub.
- Big gold/orange outlined numerals `0-9` plus the player-count glyph: `450.0.13` (same art repeats in `481.0.13`).
- Small slanted red/gold numerals `0-9`: `463.0.6` (candidate for the in-match clock; to be confirmed against a battle screenshot).
- Seven Dragon Balls: `449.1.9` / `480.1.9`; the blue wavy progress frame: `449.1.10` / `480.1.10`; VS burst `455.11`/`456.11`;
  "Victory"/"Eliminated" banners `455.31`/`455.36`; team-number tabs `448.1.33`; 1P/2P/COM tags `448.1.21`; flame-car
  loading art `449.1.21`/`480.1.12`; dragon banner `450.0.9`; the 4-icon set `448.1.528` / `450.1.38.8`.
- Not found yet: the battle HUD (health/ki gauges, match clock). Probably another archive (`PZS3US0.AFS`, `PZS3US2.AFS`) or
  a non-PSMT8 format (PSMT4/PSMCT32); scan next. A user screenshot of the in-match HUD would confirm which numerals the clock uses.
- Art stays on the user's disc: extract at install time, never ship.

## Reference from the user: the full BT3 HUD sprite sheet (2026-10-06)

Saved as `hud-reference/bt3-hud-sprite-sheet-user-provided.png` (a ripped sheet; reference only, never ship it). It shows the real
HUD set: HUD base/glow, team HUD plates, "Timer/Win counter" plate, blast-stock bar and counters, **Timer (normal) = grey outlined
italic numerals 0-9 + infinity, Timer (in yellow), Timer (in red)**, damage/hit counters, Dragon Balls (skill list), health/ki bar
sprites in six colours, teammate stats bars, switch-gauge glow, R3 alarm arrows, and the in-game text banners.

### Design consequence (replaces the generic concepts)
- Use the game's own clock look: numerals from the "Timer (normal)" set, switching to the "Timer (in yellow)" set at 20 s and
  "Timer (in red)" at 10 s, exactly like the match clock's state logic; sits on a "Timer/Win counter" style dark plate.
- The bar uses the HUD bar sprites (the slanted metal ki/health bar shape), in the fusion colour.
- "Fusion" label as in-game text style (same family as "Boost!/Counter!/Lock on"), small, only when it fits.
- Both partners' mini names/portraits optional, using the portrait map.

### Where the sprites are (CONFIRMED / UNKNOWN)
- The battle HUD textures are NOT among the 3,983 PSMT8 textures I decoded (those are menu/loading art). The 97 PSMT4 textures
  (AFS1 entries `0`, `1`, `2.x`, `450.0.5/6`, `453.0.21`, `455.4/32`, ...) are the likely HUD atlases; decoding needs a PSMT4
  unswizzle (not implemented yet).
- Better route for the NATIVE version: do not decode art at all. During a battle the HUD textures are already resident in GS
  VRAM and the game's own clock code draws them. Embed by calling/reusing the game's clock/gauge draw routine (find it from the
  match-clock counter in a battle RAM dump) with the fusion value and position, so the timer is pixel-identical to the game's HUD
  and needs no extracted art. Codex: this belongs with the M4 embedded draw layer.

## (SUPERSEDED: the HUD is in AFS1 entry 5, see UI_ASSET_MANIFEST.md) Where the battle HUD art lives (Claude, 2026-10-06 22:55; matched against `16-ready-held.bin` of a 1v3 match)
- 276 of the disc's textures are present VERBATIM in the battle-ready RAM. They come from AFS1 **entry 2** (the battle resource
  package: effects/auras 2.9..2.628, and the 64x64 PSMT4 textures `2.1`, `2.7`, `2.566`), loaded contiguously from about
  0x573B00 (e.g. 2.1 at 0x573B00, 2.7 at 0x57DEC0, 2.566 at 0x684400; 2.39 at 0x59FA80). The HUD digit atlases are almost certainly
  the PSMT4 ones among them; PSMT4 decoding is still missing in my scripts (PSMT8 and PSMCT32 decode fine).
- Cheapest way to see them: ask the runtime's own GS texture decoder (it already decodes PSMT4 for rendering) to dump a given TBP /
  RAM address to PNG in a debug mode. That also validates my reading against the user's reference sheet.
