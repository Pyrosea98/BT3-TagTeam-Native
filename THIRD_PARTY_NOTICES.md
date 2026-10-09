# Third-party notices

This project's own code is GPL-3.0-only (see `LICENSE`). The components below keep their own licences. This list covers what this repository and the preview installer use; the installer package also ships the licence texts of its bundled libraries in its `notices` folder.

## Derived from
- **Tag Team Mod** by The Mufti, GPL-3.0-only: https://github.com/tehmufti/Budokai-Tenkaichi-3-Tag-Team-Mod-PCSX2- (the code in `controller/`, base version 0.1.0-beta.32, modified).
- **BT3-Recomp** by z3xox, GPL-3.0, and **PS2Recomp**: the native runtime in the companion repository BT3-TagTeam-Runtime keeps its own `THIRD-PARTY-NOTICES.md` (including paraLLEl-GS, Granite and other libraries).

## Fonts (in `fonts/`, each with its licence file)
- Barlow Condensed, Kanit and Exo 2: SIL Open Font License 1.1.
- Liberation Sans: SIL Open Font License 1.1.

## Native runtime libraries shipped in the installer
Checked against the files in the preview payload (2026-10-09).
- **FFmpeg 7.1** (`avcodec`, `avformat`, `avutil`, `avfilter`, `avdevice`, `swresample`, `swscale` DLLs): built as **LGPL-3.0-or-later** (`--enable-version3`, no GPL or non-free parts; the DLLs report "LGPL version 3 or later"). They are loaded as separate DLLs, so you can replace them with your own build. Source: https://ffmpeg.org (the version is in the DLL names; the exact source archive is available from the runtime repository's build notes or on request through an issue).
- **Microsoft Visual C++ runtime** (`msvcp140*.dll`, `vcruntime140*.dll`): Microsoft redistributable.
- **paraLLEl-GS** (LGPL-3.0-or-later), **Granite** (MIT), SDL2 (zlib), raylib (zlib), Dear ImGui (MIT), rcheevos (MIT), nlohmann/json (MIT) and the other native libraries are compiled into `ps2EntryRunner`. Their licences are listed in the runtime repository's `THIRD-PARTY-NOTICES.md`: https://github.com/Pyrosea98/BT3-TagTeam-Runtime

## Python runtime and libraries bundled in the preview installer
CPython 3.11 (PSF licence) with its standard extension modules, which include OpenSSL 3 (Apache-2.0), libffi (MIT), SQLite (public domain), Tcl/Tk (BSD-style) and bzip2/xz (BSD/public domain); Pillow 12 (HPND) with the image libraries its wheel bundles (libjpeg-turbo, FreeType, LittleCMS, libwebp, OpenJPEG, libtiff, zlib; licences in the wheel's own files); NumPy 2.4 (BSD-3-Clause) with OpenBLAS (BSD-3-Clause) and the GCC runtime libraries it bundles (GPL-3.0 with the GCC Runtime Library Exception); pycdlib 1.20 (LGPL-2.1); psutil 7 (BSD-3-Clause); Capstone 5 (BSD); pyelftools 0.33 (public domain); zstandard 0.25 (BSD-3-Clause); comtypes 1.4 (MIT); pycaw (MIT). pycdlib is pure Python, so it can be replaced or modified by editing the installed `Lib/site-packages/pycdlib` folder. Source for each is available from its upstream project at the version above.

## Still to do before a signed or wider release
- The installer's `notices` folder carries only the BT3-Recomp, Python and font licence texts today. The licence texts of FFmpeg, pycdlib, Pillow, NumPy (and its bundled libraries), OpenSSL and the other items above should be added to it.
- `background.png` and `icon.png` in the runtime repository must be confirmed as original or freely licensed art (the runtime notices already flag this).

## Tools used to build the installer
Inno Setup (Jordan Russell and contributors) for the installer; its runtime files are not part of this repository.

## Not included
Game disc images, PS2 BIOS files, game executables and archives, extracted game art, saves and RAM captures are never part of this repository.
