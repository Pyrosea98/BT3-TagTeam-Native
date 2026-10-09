# Native Vulkan text integration

Owner: Codex. 2026-10-07.

## Implemented path

`ps2_ui_vulkan.cpp` implements the actual `TextSpriteSink` using the existing
Granite Vulkan device. Font pages are R8_UNORM indexed images. Each palette is
a256x1 RGBA8 image. The fragment shader fetches the selected palette entry;
changing language or colour does not upload font textures. Straight-alpha
blending uses SRC_ALPHA / ONE_MINUS_SRC_ALPHA for RGB and ONE /
ONE_MINUS_SRC_ALPHA for alpha. Source and palette sampling use nearest clamp.

The paraLLEl-GS swap hook calls the compositor before scanout readback. A
separate RGBA output image receives the game scanout and native UI sprites.
It does not write game GS registers or VRAM. The existing readback/presentation
ring receives the composed image. Game source dimensions remain unchanged;
glyph layout fits the640x448 logical canvas within that image. Output resources
are recreated on size changes. Readback restores the UI output's read-only
layout; dropped/busy readback slots leave that layout intact for the next draw.
Resources are released on PGS shutdown after device idle.

This currently integrates the paraLLEl-GS trial path. The separate seamvk native
renderer, OpenGL and D3D11 paths do not use this compositor. ARM64 compilation
and driver behavior remain unverified.

## Developer trial

Dedicated binary: `repo/build/ps2xRuntime/ps2EntryRunner-native-ui-vulkan.exe`.
`Play Power Scale native UI Vulkan.cmd` selects it, vanilla/controller-free,
with the indexed-font demonstration drawn above the game. Pass
`--ui-language es` or `--ui-language en` to the launcher. This is explicitly a
diagnostic panel, not the final loading/settings screen.

The developer bootstrap sets PS2X_NATIVE_UI_ASSETS to the generated v2 pack,
PS2X_NATIVE_UI_TEST=1 and PS2X_NATIVE_UI_LANGUAGE. When these are absent the
new hook returns the original image without allocating or drawing UI resources.
Ordinary launchers retain their existing binary. Production language/settings
and screen events are not implemented by these developer environment flags.

## GPU verification without a game

The dedicated runner accepts:

```
--native-ui-vulkan-self-test <assets-directory> <output-directory>
```

It creates a real Vulkan device and renders EN/ES from the same indexed assets
onto a640x448 background, reads the GPU output and writes two PNGs. This exits
before loading a game, creating a window, ISO access or opening PINE. The optional
developer harness `codex_ui_vulkan_self_test.py` invokes that native entry point
with correctly quoted Windows paths and captures stdout/stderr. Python only
launches this diagnostic; it does not load fonts, render sprites or read pixels.

Confirmed on this PC's NVIDIA GeForce RTX3080: both GPU outputs rendered and
were visually inspected (Spanish accents, titles, all seven palettes and
numerals). The native test requires successful PNG output, at least1000 changed
RGB pixels and no increase from the initial25 GPU uploads across both frames.
The two renders exercise output-image reuse and layout restoration.

Evidence: `power-scale-trial/codex-ui-vulkan-self-test.log`,
`native-ui-vulkan-capture/vulkan-ui-en.png` / `vulkan-ui-es.png`.
Shader compilation uses the repository's bundled glslang via
`codex_compile_ui_shaders.py`; embedded SPIR-V is included in the runtime build.

## Remaining integration

Native loading/preparation snapshots must select visibility, progress, roster,
error/release state and language. Settings must persist language and select it
at startup. The compositor currently draws a demonstration rather than those
screens. Real game scanout/presentation coexistence still needs one coordinated
trial; the isolated GPU test does not prove the entire game window path.
No match/rematch regression, live draw-cost gate, validation-layer check or
Android performance result is claimed. The current sink emits one draw per
glyph; batching is a later measured optimization, not a proven performance win.

### Live trial follow-up

Claude's07:10/07:25 report confirms native-ui-vulkan3C7B5821 composes text over
the game's live main menu with no corruption/flicker visible in the user
screenshot. User reports no lag in menus. The session is closed and GAME_LOCK
released. No repeat diagnostic-panel run is requested. This is user/screenshot
evidence, not a measured GPU frame-time benchmark. Final overlay aspect after
the host scales scanout to its presentation rectangle remains unverified.

### M5 product screen integration

The dedicated native-ui-slice now consumes real preparation/settings events and
renders loading/settings/About. See NATIVE_UI_SLICE.md for its launcher, actual
GPU/contact-sheet/state/input/language evidence and known gaps. The earlier
Remaining integration section describes the diagnostic3C7B5821 build. The new
slice fixes host-space aspect compensation; isolated ultrawide presentation is
verified. Its actual game/rematch parity still needs the one live session.
