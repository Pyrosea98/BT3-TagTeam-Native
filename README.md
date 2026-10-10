# BT3 Tag Team Native

A standalone Windows build of **Dragon Ball Z: Budokai Tenkaichi 3 (Power Scale BETA 1.5.1)** with the **Tag Team mod** built in. It runs on a native static-recompilation runtime instead of an emulator, with the mod's logic embedded, a native Vulkan interface (overhead HUD, fusion and revive indicators, menus, credits), up to five fighters per side, free-for-all, co-op and Modded Training, native CPU tactics, and an installer that imports **your own** disc image.

## Download v0.2 preview

Get the Windows installer package from the [v0.2 preview release](https://github.com/Pyrosea98/BT3-TagTeam-Native/releases/tag/v0.2-preview). It includes English/Spanish release notes, checksums and matching source code. You must supply your own supported Power Scale BETA 1.5.1 disc image.

This update includes the Version 11 integration, wider beam assist range and CPU transformation fixes. Mega Instinct Vegeta is restricted for extra fighters; complete roster memory coverage and safe recovery after destructive reload failures remain unfinished. See [the v0.2 changelog](docs/V02_PREVIEW_CHANGELOG.md).

## Built on The Mufti's Tag Team Mod

This project exists because of **[The Mufti's Tag Team Mod](https://github.com/tehmufti/Budokai-Tenkaichi-3-Tag-Team-Mod-PCSX2-)** (GPL-3.0), which adds simultaneous fighters, teams, free-for-all, split screen and much more to Budokai Tenkaichi 3 on PCSX2. The game logic in `controller/` comes from that mod and is adapted here to run natively with the Power Scale BETA 1.5.1 roster. If you want the original emulator-based mod, an experimental online mode, Linux builds or the Workbench tools, use the upstream project: [releases](https://github.com/tehmufti/Budokai-Tenkaichi-3-Tag-Team-Mod-PCSX2-/releases) and [channel](https://www.youtube.com/channel/UCY79wsRvOdzBoe8GS77HY0A). Please send gameplay credit and thanks there.

> Unofficial fan project. Not affiliated with or endorsed by the owners of Dragon Ball or Budokai Tenkaichi.
> **No game files are included in this repository** (no disc images, executables, game archives, extracted art, saves or captures). You must supply your own Power Scale BETA 1.5.1 disc image.

## Repositories

| Repository | What it holds |
| --- | --- |
| **BT3-TagTeam-Native** (this one) | The embedded controller and mod logic (`controller/`), the installer sources (`installer/`), the player manual (`manual/`), project tools and tests (`tools/`), design specs and notes (`docs/`). |
| [BT3-TagTeam-Runtime](https://github.com/Pyrosea98/BT3-TagTeam-Runtime) | The native runtime: a branch (`tagteam-native`) of [z3xox/BT3-Recomp](https://github.com/z3xox/BT3-Recomp) with the Tag Team bridge, the native UI and four-seat pads. |

## Credits

- **Power Scale:** LetsPlayBt3 (https://www.youtube.com/channel/UCXiHmLmbgaSsFGrfejXESYw)
- **Tag Team mod:** The Mufti (https://www.youtube.com/channel/UCY79wsRvOdzBoe8GS77HY0A), upstream project [tehmufti/Budokai-Tenkaichi-3-Tag-Team-Mod-PCSX2-](https://github.com/tehmufti/Budokai-Tenkaichi-3-Tag-Team-Mod-PCSX2-). The code in `controller/` is derived from that GPL-3.0 project (base version 0.1.0-beta.32) and adapted to the native runtime; see `docs/UPSTREAM_V11_REVIEW.md` for the comparison with upstream Version 11.
- **Runtime:** [z3xox/BT3-Recomp](https://github.com/z3xox/BT3-Recomp) and PS2Recomp.
- **Special thanks** to RidJuampa for helping me understand the code.

## Licence

GPL-3.0-only, see `LICENSE`. Third-party components keep their own licences, see `THIRD_PARTY_NOTICES.md` and `NOTICE`. Distributed builds must offer the corresponding source of this repository and of BT3-TagTeam-Runtime.

## Where to start

- Player manual: `manual/BT3-TagTeam-Manual-EN.pdf` and `-ES.pdf`.
- Roadmap and status: `docs/ROADMAP.md`, `docs/NATIVE_PORT_ASSESSMENT.md`.
- Installer design and checklist: `docs/INSTALLER_PLAN.md`, `docs/PUBLIC_RELEASE_CHECKLIST.md`.
- Feature specs: `docs/FUSION_CONTROL_SPEC.md`, `docs/CPU_TACTICS_SPEC.md`, `docs/OVERHEAD_HUD_SPEC.md`, `docs/MODE_SCREENS_SPEC.md`.

This is a preview: many checks in `tools/` replay captured game states or test isolated pieces, and several features are not yet live-validated on every character and mode. Live gameplay status is tracked in the docs.
