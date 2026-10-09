# UI asset manifest: what each screen needs from the user's disc (install-time extraction)

Owner: Claude. Written 2026-10-07. Paths are `PZS3US1.AFS` entry.package.sub (decoded with `claude_hud_sheet_lib.py`, PSMT8
GS textures: TEX0 at +0x50, pixels at +0xC0, palette at +0xC0+w*h+0x80). Nothing here is shipped; the installer extracts it from the
player's own disc. Status: CONFIRMED = decoded and viewed; TODO = location unknown or needs the PSMT4 decoder.

## Shared kit

| Asset | Path | Size | Status | Used by |
| --- | --- | --- | --- | --- |
| Big gold numerals 0-9 + player glyph (4x3 grid of 64x64) | 450.0.13 (also 481.0.13) | 256x256 | CONFIRMED | counters, ranks, loading stage count |
| Small italic red/gold numerals 0-9 | 463.0.6, 494.0.6 | small | CONFIRMED | HUD counters |
| Seven Dragon Balls (4+3 grid of 64x64) | 449.1.9 (also 480.1.9) | 256x128 | CONFIRMED | loading stages, sparks |
| Wavy blue progress frame | 449.1.10 (also 480.1.10) | 256x64 | CONFIRMED | loading bar |
| VS burst | 455.11 (456.11, 458.11, 485.11 ...) | 128x64 | CONFIRMED | loading cover |
| Dragon banner band (background) | 450.0.9 (481.0.9) | 512x128 | CONFIRMED | all screens, faint |
| Gold slider knob | 453.0.11 | 128x128 | CONFIRMED | settings sliders |
| Purple slider track (alternative) | 453.0.8 | 512x128 | CONFIRMED | optional |
| "Victory" / "Eliminated" banners | 455.31 | 512x256 | CONFIRMED | optional results |
| 1P/2P/COM tags | 448.1.21 | 128x64 | CONFIRMED | seat colours |
| Team number tabs (1-5, red and green) | 448.1.33 | 256x256 | CONFIRMED | team slots |
| Four-icon set (swap/?/x/x) | 448.1.52.8 | 128x32 approx | CONFIRMED | menu icons |
| Portraits (253, 64x64 PSMT8) | 450.1.31.j via `portrait-slot-map.json` | 64x64 | CONFIRMED | loading, HUD, kill feed, standings |
| Character names/labels | runtime table 0xFD8AD0 (slot order) | UTF-16 | CONFIRMED | all screens |
| Battle HUD plates, bars, Timer normal/yellow/red numerals, damage/hit counters | AFS1 entry 2 (battle) PSMT4, resident from ~0x573B00 | various | TODO (PSMT4 decode or runtime dump) | team HUD, fusion timer, training counters |
| In-game text banners (Boost!, Counter!, Lock on, Ready, Fight...) | unknown | various | TODO | lock marker, labels |

## Per screen

| Screen | Needs | Native work |
| --- | --- | --- |
| Loading cover | portraits, 449.1.9, 449.1.10, 455.11, 450.0.9 | upload once; per-frame only sprite/UV/colour; 7 stage balls; VS pop; bar wave scroll |
| Settings page | 450.0.9, 453.0.11, glyph atlas, row/chip plates | native list widgets (select, toggle, slider, choice), no PIL |
| Training | 450.0.13, portraits, HUD plates (TODO) | counters from the game's own damage/hit values |
| Team HUD / viewport panels | HUD plates and bars (TODO), portraits, glyph atlas | reuse `viewport_hud` geometry |
| Fusion timer | Timer numerals normal/yellow/red (TODO), HUD bar (TODO) | reuse the game's clock draw if found |
| Kill feed | glyph atlas, portraits optional | replace the 5x7 glyph font |
| Lock-on marker | text banners / glow (TODO) | small marker on target change |

## Glyph atlas (needed by every screen)

Build one atlas at install time: Latin set (A-Z, a-z, 0-9, punctuation, Spanish accents used by Power Scale names), two styles:
(1) title (large, gold gradient, dark outline, slight glow), (2) body (italic, white-lavender, dark outline). Source font must be
free to redistribute (the atlas is generated from a bundled open font, not from the game). Kerning table + fixed line height;
the same atlas serves menus, HUD labels and the kill feed.

## (Historical, superseded by the entry-5 section below) Battle HUD identified from the first runtime capture (2026-10-07; vanilla 1v1, `log-archive/hud-native-capture-1v1-vanilla/`, contact sheet `contact-sheet-00.png`)

Decoded by the runtime's own GS decoder from the GS VRAM during a battle; all CONFIRMED visually against `hud-reference/bt3-hud-sprite-sheet-user-provided.png`.
EE source addresses are not known yet (the capture reads GS VRAM; provenance is the next step).

| HUD part | GS TBP | PSM | Size | CLUT (CBP) | Note |
| --- | ---: | --- | --- | ---: | --- |
| HUD base plate (grey metal, the large slanted frame) | 10752 | PSMT8 | 256x64 | 11392 | the Team/Timer plate family |
| HUD glow (white silhouette of the base) | 10816 | PSMT8 | 256x64 | 11396 | glow mask, same shape |
| Max Power lightning | 10992 | PSMT8 | 256x128 | 11432 | |
| Health/ki bar sprites, green | 10880 | PSMT8 | 256x64 | 11404 | same texture, different palettes |
| Health/ki bar sprites, grey (empty) | 10880 | PSMT8 | 256x64 | 11400 | palette swap |
| Health/ki bar sprites, red (danger) | 10880 | PSMT8 | 256x64 | 11408 | palette swap |
| Blast-stock numerals 0-7 (gold) | 10944 | PSMT8 | 128x64 | 11424 | |
| **Timer (normal) numerals 0-9 + infinity (grey outlined italic)** | 10752 | PSMT4 | 128x128 | 11392 | the match clock font |
| "READY" banner | 10752 | PSMT8 | 512x64 | 11392 | in-game text style |

Key finding: the bar colours (green / grey / red) are PALETTE SWAPS of one texture (same TBP 10880, CLUT 11400/11404/11408). So the clock's
yellow and red states are very likely palette swaps of the grey numeral texture too: the native timer should reuse one numeral texture
and select a palette per state (grey, yellow at 20 s, red at 10 s), exactly as the game does. To confirm, capture once with the clock
under 20 s and under 10 s (not yet done).

## Battle clock location (found 2026-10-07 by a paused/unpaused RAM diff, vanilla Duel)
The displayed seconds are stored in THREE words that all drop 57 -> 56: `0x188876C`, `0x1888770`, `0x188B0B4` (near the battle manager 0x1880F80).
The game's own states (user): grey normally, yellow under 10 s, red at 3 s. `claude_clock_watch.py <n>` triggers the HUD capture at a clock value.

## (Historical, superseded) Match clock palettes CONFIRMED (2026-10-07, hud-rearm build, captures at clock 8 and clock 2; `log-archive/hud-native-capture-clock8-clock2-success/`)

The clock numerals are ONE PSMT4 128x128 texture at GS TBP 10752 (digits 0-9 plus the infinity sign) drawn with three palettes:
- normal (grey outlined italic): CLUT 11392 (first capture, before the 60 s mark)
- **yellow (under 10 s): CLUT 11396** (capture at clock 8)
- **red (at 3 s): CLUT 11400** (capture at clock 2)
Other HUD palette swaps seen: bar texture TBP 10880 PSMT8: green 11404, blue 11420, grey 11400, red 11408 (the blue bar is the ki/second player). Blast-stock numerals (gold) TBP 10944 CLUT 11424.
So the native timer needs ONE numeral texture and three 16-colour palettes (or the three CLUT ids if drawn through the game's own HUD pass). Source provenance on the disc is still unknown (the capture reads GS VRAM): next step is matching these textures against AFS1 entry-2 sub-entries by bytes.

## HUD source on the disc FOUND (2026-10-07, hud-provenance build; `log-archive/hud-upload-capture-vanilla-1v1/`, map `power-scale-trial/hud-entry5-map.json`)

All battle HUD textures come from ONE file read: **`PZS3US1.AFS` entry 5** (701,856 bytes), read whole at LBN 0x5FDBB (343 sectors) into EE 0x17BCE00.
29 of the captured GS uploads have EE sources inside that buffer and are byte-identical to the disc data at the offsets below (verified).
Offsets are relative to the start of AFS1 entry 5; data is the GS transfer form (the same swizzled/CT32 layout as the other textures; palettes are CT32 16x16 = 256 colours, or 8x2 = 16 colours for PSMT4).

| Piece | GS dest (DBP) | Entry-5 offset | Bytes | Note |
| --- | ---: | ---: | ---: | --- |
| Timer digits 0-9 + infinity (PSMT4 128x128, 64x32 CT32 transfer) | 10752 | 2528 (0x9E0) | 8192 | palette normal grey: DBP 11392 @10848 (0x2A60), 64 B |
| Timer palette yellow (under 10 s) | 11396 | 11040 (0x2B20) | 64 | 8x2 palette; CORRECTED by Codex's pixel match (my 501856 was another grey palette) |
| Timer palette red (at 3 s) | 11400 | 11232 (0x2BE0) | 64 | 8x2 palette (the 1024-byte entry at 71840 is the bars' grey palette, not the clock's red) |
| HUD plate (PSMT8 256x64 as 128x32 CT32) | 10752 | 20000 (0x4E20) | 16384 | |
| Bars atlas (PSMT8 256x64) | 10880 | 55328 (0xD820) | 16384 | |
| Bar palettes: grey 11400 | | 71840 (0x118A0) | 1024 | bars only (the timer's red palette is the 64-byte one at 11232) |
| green 11404 | | 72992 (0x11D20) | 1024 | |
| red 11408 | | 74144 (0x121A0) | 1024 | |
| blue 11420 | | 77600 (0x12F20) | 1024 | |
| Blast-stock numerals palette | 11424 | 87072 (0x15420) | 1024 | |
| More plate/overlay uploads (256x32 CT32, 32 KB each) | 10752 / 10880 | 232544, 266592, 300640, 400864, 468960 | 32768 | other HUD atlases (glow, lightning, READY ...) |

Install-time extraction: read AFS1 entry 5, slice these ranges, decode with the PSMT4/PSMT8 + CLUT layouts (Codex's `codex_decode_disc_indices` tool has the layout code). Nothing is shipped; the player's disc provides it.


## Extractor status (Codex, 2026-10-07)
`codex_extract_battle_hud.py` reads AFS1 entry 5 from the player's ISO, pins its SHA-256 (`019665de20c36caeff3d25d2b1f40e76cf549f1df122955cf3274c3cf9a822c3`),
and writes the 29 raw slices plus 8 named decoded assets (digits in all 3 states, plate, 4 bar colours), verified against the runtime captures. It is a
development prototype (Python + small native helper), not the production importer. Manifest: `power-scale-trial/hud-entry5-extracted/manifest.json`.
