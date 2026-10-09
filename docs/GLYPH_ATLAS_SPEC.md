# Glyph atlas spec: one text system for every mod screen

Owner: Claude (spec), Codex (implementation). Written 2026-10-07. Used by: settings pages, mode menu labels, training panel,
team HUD names, kill feed, fusion timer label, loading cover names, installer. Replaces the Python PIL pages of
`ingame_settings.py` and the 5x7 glyph font of `guest_killfeed.py`.

## Why an atlas

The game draws all text as pre-baked sprites (every label, banner and numeral is a texture). We do the same: a baked indexed
atlas plus a draw call that emits sprites. No system fonts, no runtime font rasteriser, no Python. Because the game itself
recolours HUD bars and numerals with palette swaps, our atlas is 8-bit indexed with a small CLUT per colour state; colour changes
are a CLUT choice, not new art.

## Rights

The atlas is generated from an open-licensed font (SIL OFL), not from the game, so it can be baked at BUILD time and shipped.
Candidates (italic, heavy, readable at 12-24 px): Exo 2 Black Italic, Barlow Condensed Bold Italic, Saira Condensed ExtraBold Italic.
Pick one by looking at renders next to the game's own labels; keep its licence file in the credits screen.

## Styles

| Style | Look | Sizes (px at 640x448) | Use |
| --- | --- | --- | --- |
| Title | heavy italic, gold-to-orange vertical gradient, dark purple outline 2 px, 1 px inner highlight, soft outer glow baked in | 26 and 18 | screen titles, banners |
| Body | italic bold, near-white lavender fill, dark navy outline 1.5 px | 14 and 11 | rows, labels, names, help text |
| Numeric | tabular digits only (0-9 : . % + - x /), same look as Body | 14 and 11 | timers, counters, values |

Palette (CLUT) variants per style, all drawn from one index texture: gold, white, grey (disabled), cyan (energy/selection),
yellow (warning), red (critical), green (ok). The state colours must match the HUD kit in `DESIGN_LANGUAGE.md`.

## Character set

ASCII 0x20-0x7E, Latin-1 accents used by Power Scale names (a e i o u with acute/grave/diaeresis, n with tilde, c with cedilla,
inverted ? and !), plus symbols: arrow left/right/up/down, bullet, multiplication sign, ellipsis, circled-button letters
(cross, circle, square, triangle drawn as sprites, not glyphs). Names in the label table are Latin only (UTF-16 slots, FFFE marker).
Unknown code points draw a boxed question mark; never crash.

## Atlas layout

- One or MORE PSMT8 pages per style and size (amended 2026-10-07: Title 26 needs two pages for the full charset; the metrics carry a page index), each at most 512x256, power-of-two sides, 1 px padding between glyphs, premultiplied edges.
- Metrics table per font: advance, bearing x/y, width, height, UV rect, kerning pairs for the 40 most common pairs, line height,
  baseline. Stored as a small binary blob next to the texture (versioned, little-endian, hashed).
- Uploaded ONCE into VRAM when a screen opens; text drawing emits only sprite packets (position, UV, CLUT, colour, alpha).

## API (native)

`DrawText(style, size, palette, x, y, utf8, flags)` with flags: left/centre/right, max width with ellipsis, scale (1.0 or 0.75),
shadow on/off. `MeasureText(...)`. All coordinates in the 640x448 logical grid; the draw layer applies viewport scissor so split
screens work (the mod already supports 4 viewports).

## Acceptance

1. Side-by-side render of the same label in the game's own atlas and ours looks like the same family (user reviews).
2. Every name in `portrait-slot-map.json`/the label table renders without fallback boxes in Spanish and English.
3. A full settings page redraws without any texture upload after the first frame.
4. No allocation per frame; draw cost for 200 glyphs under 0.3 ms on the reference PC.

## Candidate fonts downloaded for preview (2026-10-07, user approved)
`font-candidates/`: Kanit Black Italic, Barlow Condensed ExtraBold Italic, Exo 2 Italic variable (all SIL OFL 1.1, licence files alongside, from github.com/google/fonts).
Side-by-side render: `loading-mockups/font-candidates.png`.
**DECIDED (user, 2026-10-07): Title style = Kanit Black Italic; Body and Numeric styles = Barlow Condensed ExtraBold Italic.** Exo 2 is not used. Ship both OFL licence files in the credits/third-party notices.
