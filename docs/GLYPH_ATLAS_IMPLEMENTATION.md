# Native glyph assets and layout

Owner: Codex. Implementation started 2026-10-07.

## Current art revision: 2

Claude's05:10 review is implemented under `ui-assets/glyph-atlas-v2/`; initial
assets/previews remain under `glyph-atlas/` for comparison. Body now uses16/12px
ExtraBold with1px additional advance/tracking. Its1px outline is restricted to
the exterior by flood fill; enclosed counters receive no outline. Fill coverage
is preserved. Grey RGB levels raised about15%. Approved title/numeric index
planes are byte-for-byte unchanged. Retained the approved ExtraBold font because
spacing/outline/size changes produced readable1x samples; no Bold download yet.

Preview captions now use the real body atlas. `preview-locales.png` is1x;
`preview-locales-2x.png` is nearest-neighbour pixel doubling. English/Spanish
settings row mocks use extracted `hud-entry5-extracted/plate.png`, generated
glyphs and a value chip: `settings-rows-en.png` / `settings-rows-es.png`, with
matching2x files. These are offline legibility mocks, not working settings UI.

After Claude's06:00 review, row mocks now9-slice the original plate's dark lobe
with source caps retained at1x and flat interior/edge strips stretched. Labels
use the clean area; values use a separate flat slanted chip with a1px light edge.
Title retains the decorated plate; selected row has a gold edge/purple tint;
help has a plate. Generated row/help/chip PNGs and EN/ES1x/2x settings mocks are
under glyph-atlas-v2. These use the locally extracted player's plate; do not
redistribute that game-derived artwork with a release.

Both actual native test suites pass all six revised packs (v2 check logs in
power-scale-trial). Additional check confirms Body advances are exactly the
font advance plus1px; original title/numeric index planes unchanged. New pack
is still compatible with the version1 native metrics parser/draw interface.

## Implemented

`codex_build_glyph_atlas.py` bakes the approved bundled fonts into linear indexed
pages, seven RGBA palettes, metrics and previews. The only font rasterizer is on
the development host. Both OFL licence texts are copied to the generated pack.
`repo/ps2xRuntime/include/runtime/ps2_ui_glyph_atlas.h` reads metrics and lays out
UTF-8 into caller-provided sprite buffers. No Windows APIs, x86 intrinsics, SIMD,
system fonts, file paths or runtime Python are required by that C++ component.

Title: Kanit Black Italic, 26/18 px. Body/Numeric: Barlow Condensed ExtraBold
Italic, 14/11 px. Title26 needs TWO 512x256 pages; each other style needs one.
Each Title/Body pack has 194 glyphs: printable ASCII, printable Latin-1, bullet,
ellipsis and a baked boxed-question replacement. Numeric has 20 glyphs with
equal advances for all digits. Direction arrows and controller icons remain
separate pending sprite assets. No claim of complete runtime-name coverage yet.

## Asset contract, version 1

All integer fields are little-endian. Each `.gatl` has exactly these bytes:

| Offset | Type | Field |
| ---: | --- | --- |
| 0 | 4 bytes | `GATL` magic |
| 4 | u16 | version = 1 |
| 6 | u16 | page count |
| 8,10 | u16,u16 | page width, height |
| 12,16 | i32,i32 | line height, baseline in 1/64 logical pixels |
| 20,24 | u32,u32 | glyph count, kerning pair count |
| 28 | 22 bytes per glyph | sorted glyph records |
| after glyphs | 12 bytes per pair | kerning records |

Glyph record: codepoint u32; page/u/v/width/height five u16; bearingX/bearingY
two i16 (whole logical pixels relative to baseline); advance i32 (1/64 pixel).
Kerning record: left/right u32; adjustment i32 (1/64 pixel). Font and metrics
SHA256 values are recorded in `manifest.json`. Texture/palette authentication
must be added to the production asset loader; the current metrics reader checks
structure and bounds but does not authenticate files.

Each `.indices` is width*height bytes, LINEAR row-major PSMT8 indices. It is not
a ready-made GS CT32 transfer. The GS uploader must swizzle or use WriteP8.
Each `.rgba` has 256 straight RGBA8 entries, host alpha 0..255. A host Vulkan
draw uses straight-alpha blending; a GS uploader must convert alpha to 0..128
once and lay out CSM1. Do not premultiply these assets and also apply straight
blending, or convert alpha twice.

Index roles: 0 transparent; 1..15 outline; 17..31 subdued glow; 33..47 title
highlight; 48..255 fill (13 gradient levels x16 coverage levels). Outline/glow
are identical across palettes; highlight/fill follow the selected colour.
Unused 16/32 are transparent. Edges have quantized four-bit coverage. One role
is stored per pixel; the layers are not independently composited at runtime.

## Native API available now

`GlyphAtlas::load(span)` validates version, lengths, page/UV bounds, sorted
codepoints and fallback availability. Loading allocates; `measure`/`layout`
do not allocate. `layout(utf8,x,baselineY,output,scale)` returns written count,
total advance and buffer-capacity status. Each output quad includes page, source
UV/size, destination x/y and scale. Scale must be positive and at most16.
Unsupported codepoints and malformed UTF-8 use the boxed-question glyph.
The bounded layout continues measuring when the output buffer is full.

Pending API features: maximum width/ellipsis policy, multiline, optional shadow
and an actual renderer backend for texture upload/draw submission.
This header is not connected to a gameplay UI yet. No runtime executable changed.

### Native draw interface and languages

`ps2_ui_text_draw.h` now connects the layout to `TextSpriteSink`. The sink
implements upload/release, begin/end graphics state and sprite submission on
the renderer thread. `NativeTextFont` uploads each indexed page and each of
seven palettes only when loaded, owns the returned handles, releases partial
uploads on failure, and releases all handles on reset/destruction. The sink
must outlive the font. Per-frame drawing changes palette handles, not textures.

Draw supports left/centre/right alignment, scale, 640x448 canvas fitting into
an arbitrary viewport, scissor and proportional UV clipping at viewport edges.
Insufficient caller scratch space rejects the entire label before beginning a
draw batch. Sink begin/end must restore the renderer's prior graphics state.
This implements alignment and viewport handling previously listed as pending;
ellipsis, multiline and optional shadow remain pending.

`ui-assets/ui_strings.json` is the single source for31 complete EN/ES labels.
`codex_build_ui_strings.py` emits portable native UTF-8 byte literals in
`ps2_ui_strings.h`. `Localizer::select` sets the active language; unsupported
tags are rejected without changing it. There is no per-label fallback to another
language. Each catalogue entry must provide both languages before generation
succeeds. Selection is not yet connected to settings persistence or game UI.

`codex_check_ui_text_draw.cmd` compiles and exercises the actual native draw
code against a recording sink for all six packs. Checks: both languages/all31
keys, invalid language/key, alignment, four viewport clipping bounds/UVs, fully
clipped label, buffer exhaustion, palette changes over120 simulated frames with
no new uploads, and complete cleanup after success or failed partial upload.
Results: `power-scale-trial/codex-ui-text-draw-check.log`, six PASS rows.
The sink is a test implementation, not a Vulkan backend: actual GPU upload,
game screen visibility and performance remain unverified.

Previews now use the same catalogue: `preview-en.png`, `preview-es.png`, and
`preview-locales.png` (side-by-side panels with explicit language headings).
JSON is explicitly decoded as UTF-8 on Windows, including accents.

## Verification

`codex_check_glyph_atlas.cmd` compiles the actual header with clang C++20 and
checks all six generated packs: successful load, UTF-8 sequence counting,
invalid/overlong/unsupported codepoints, scaling, bounded writes, measure/layout
agreement, empty text, corrupt version, truncated file and invalid page index.
Results: `power-scale-trial/codex-glyph-atlas-check.log`, six PASS rows.
`codex_glyph_atlas_preview.py` reads generated metrics/indices/palettes to render
`ui-assets/glyph-atlas/preview.png`; it does not rasterize fonts. Visually reviewed
titles, Spanish labels, numeric rows and all seven colour states.

Live draw performance, ARM64 compilation, full settings-page rendering and
upload-once behavior are not tested yet. Next: native texture ownership/upload
and sprite draw submission, then use this layout in the loading cover.
