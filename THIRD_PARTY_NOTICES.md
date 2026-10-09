# Third-party notices

This project's own code is GPL-3.0-only (see `LICENSE`). The components below keep their own licences. This list covers what this repository and the preview installer use; the installer package also ships the licence texts of its bundled libraries in its `notices` folder.

## Derived from
- **Tag Team Mod** by The Mufti, GPL-3.0-only: https://github.com/tehmufti/Budokai-Tenkaichi-3-Tag-Team-Mod-PCSX2- (the code in `controller/`, base version 0.1.0-beta.32, modified).
- **BT3-Recomp** by z3xox, GPL-3.0, and **PS2Recomp**: the native runtime in the companion repository BT3-TagTeam-Runtime keeps its own `THIRD-PARTY-NOTICES.md` (including paraLLEl-GS, Granite and other libraries).

## Fonts (in `fonts/`, each with its licence file)
- Barlow Condensed, Kanit and Exo 2: SIL Open Font License 1.1.
- Liberation Sans: SIL Open Font License 1.1.

## Python runtime and libraries bundled in the preview installer
CPython (PSF licence), Pillow (HPND), NumPy (BSD), pycdlib (LGPL-2.1), psutil (BSD-3-Clause), Capstone (BSD), pyelftools (public domain), zstandard (BSD), comtypes (MIT), pycaw (MIT), and the Microsoft Visual C++ runtime redistributables. Exact versions and licence texts are in the installer's `notices` folder. Source for pycdlib and the other copyleft or attribution-required components is available from their upstream projects; the versions used are listed in the installer inventory (`installer/package-inventory.json` is generated at build time).

## Tools used to build the installer
Inno Setup (Jordan Russell and contributors) for the installer; its runtime files are not part of this repository.

## Not included
Game disc images, PS2 BIOS files, game executables and archives, extracted game art, saves and RAM captures are never part of this repository.
