# Installer plan: Windows and Android, standalone game

Owner: Claude (plan), Codex (runtime/installer implementation). Written 2026-10-07. Product: a standalone game with the mods
embedded (`ROADMAP.md`, "Product definition"). The installer only places the app and imports the player's own disc.

## What exists today (CONFIRMED from the repo)

The public Windows installer (`Install.cmd`, `setup/`, beta.42 RAR) drives PCSX2: the user picks an ISO, PCSX2 2.6+ and BIOS;
Python and Visual C++ are installed if missing; supported discs are BT3 USA (SLUS-21678), BT3 Europe (SLES-54945), BT4 B14 REV2
(experimental) and the exact Power Scale (Niveles de Poder) BETA 1.5.1 ISO; languages EN and ES. The native port currently runs
only from the derived Power Scale input (`power-scale-input/`: `SLUS_216.78`, `BIN/`, `DATA/`, `DBZP.BIN`, ISO `expanded-2x.iso`
of 4,196,335,616 bytes). That public installer is the model for tone and checks, but the new installer replaces its whole
pipeline (no PCSX2, no Python).

## Install flow (Windows)

1. Installer (NSIS/Inno or MSIX; Codex to choose): per-user install, no admin, bilingual EN/ES, our look (`DESIGN_LANGUAGE.md`).
2. Places the app; shows credits (Power Scale author and Tag Team creator; names must be verified before release).
3. First launch, "Import your disc": file picker, then verify, then extract, then warm-up, then start.
4. Uninstall removes the app and its data folder; never touches the user's disc image.

## Import steps (same code on Windows and Android)

| Step | What | Failure message (plain, one sentence) |
| --- | --- | --- |
| 1 Pick | user chooses the disc image (ISO; later CHD/BIN if wanted) | "Pick the game disc image you own." |
| 2 Identify | SHA-256 against a shipped table of supported discs (hash, title, region, features, build id); unknown hash = refuse with the detected size/hash shown | "That disc isn't supported yet. Supported: Power Scale BETA 1.5.1 (build ...)." |
| 3 Extract | read only the files the runtime needs (ELF, MOD.BIN, MOD/DLC AFS, DATA AFS, UI packages); copy or stream into app storage | "Not enough space: needs N GB." |
| 4 Derive | portrait slot map by disc hash (253 numbers, no art), label table, UI sprites per `UI_ASSET_MANIFEST.md`, character files index | "Couldn't read the interface art." |
| 5 Warm up | pipeline/shader cache, first-frame uploads | skipped silently if it fails |
| 6 Save | write an import receipt (disc hash, tool version, derived-file hashes) so later runs verify instead of re-import | |

Everything derived lives under the platform app-data folder; everything is re-derivable from the disc; nothing game-owned is in the
installer package.

## Android specifics

- ARM64 only; Vulkan present; touch overlay plus gamepad support; haptics optional.
- Storage: the Storage Access Framework picker returns a content URI; seeking/mapping a 4.2 GB ISO through it is slow, so copy the
  needed files (or the whole image if the mod needs it) into app-private storage once, with a progress bar and a space check up front.
- No all-files permission; no network permission required (offline game); logs exportable via the share sheet, sanitised.
- Thermal and battery: frame cap option, performance profile selectable; no speed promise before device tests (`ROADMAP.md`).
- Release channel: signed APK for testers first, AAB later.

## Supported discs table (to fill from the installer's existing checks)

Keep one machine-readable `supported-discs.json` (hash, region, adapter id, feature flags, portrait-map id, label-table id,
build compatibility range). Today's value: Power Scale BETA 1.5.1 only; other adapters (BT3 USA/PAL, BT4) are not part of the native
runtime yet and must not appear in the installer until they pass the same offline checks.

## Safety, privacy, logs

- Never log the disc path, user name, BIOS, saves or keys; log bundle sanitiser removes them (Windows and Android).
- No telemetry. Crash dumps stay local unless the user exports them.
- Show the build number and the disc hash prefix on the About page.

## Credits and legal text

About page and installer: "Power Scale: [author, verified]. Tag Team mod: [creator, verified]." Channels supplied by the user: Power Scale https://www.youtube.com/channel/UCXiHmLmbgaSsFGrfejXESYw (reads "LetsPlayBt3"); Tag Team mod https://www.youtube.com/channel/UCY79wsRvOdzBoe8GS77HY0A (reads "The Mufti"); display names CONFIRMED by the user (2026-10-07): Power Scale = "LetsPlayBt3", Tag Team mod = "The Mufti". DECIDED (user, 2026-10-07): the About page shows BOTH the names and the channel links. plus third-party notices (open font
licence for the glyph atlas, runtime dependencies). Do not invent names; resolve them with the user before the first external build.

## Testing plan (before external testers)

- Clean Windows 10/11 VM, no Python/VC runtime: install, import, play, uninstall.
- Wrong disc, truncated disc, disc moved after import, low disk space, cancel and resume during import.
- Spanish and English UI; keyboard, XInput and DualShock pads.
- Android: two real devices (one mid-range), install from APK, import from internal storage and SD, rotate, background and resume.

## Answers from the user (2026-10-07)

1. `expanded-2x.iso` = the disc with the maps expanded to twice their size; it is produced by an executable that comes with the Tag
   Team mod and takes the user's ISO as input. So the importer can rebuild it from the user's own disc; the map-expansion step must
   become part of the import (native code, not that executable), or the runtime must read the expanded layout directly.
2. A BIOS is needed by the PCSX2 version of the mod; the native runtime probably does not need one (to be confirmed by Codex).
3. Windows installer technology and signing: no preference; Codex to choose.

## Open questions

1. How exactly is `expanded-2x.iso` produced from the user's Power Scale disc (what does the "expanded" map change), and can the
   installer reproduce it from the original disc alone? (Codex / Tag Team creator.)
2. Does the native runtime need a PS2 BIOS at all? The PCSX2 flow required one; the recompiled runtime may not. Confirm before
   telling testers what to bring.
3. Which installer technology on Windows (MSIX vs NSIS/Inno) and signing plan.
4. Distribution channel and who may receive builds (user decision).

Special thanks (user, 2026-10-07): a person who helped the user understand the code, Discord profile https://discord.com/users/747155705303400528.
Display name and exact wording are NOT known yet: do not invent them. Ask the user (name as they want it shown, wording, whether the Discord link is shown,
and that the person agrees to be named/linked) before it ships. Placement: the About page and the boot credits as a third block, "Special thanks: [name]".

Special thanks FINAL (user, 2026-10-07): display name "RidJuampa" (Discord handle ridjuampa, shown in the profile screenshot the user sent). Wording approved by the user:
EN "Special thanks to RidJuampa for helping me understand the code." ES "Agradecimiento especial a RidJuampa por ayudarme a entender el codigo."
Show the name only (no Discord link) unless the user later asks for the link; the Discord URL stays out of the UI by default.

## Android input plan (user, 2026-10-08)
- **Two input families, any mix per seat:** (1) an **on-screen PS2 pad** replicating the DualShock layout and (2) **1-4 Bluetooth/USB gamepads connected at once**.
- **On-screen pad:** two analog sticks (left + right), D-pad, four face buttons (Triangle/Circle/Cross/Square), L1/L2/R1/R2, L3/R3 (stick clicks), Start/Select; real multi-touch (both sticks and several buttons together), translucent and resizable with Rule 0 caps (never cover the fight), repositionable per player/orientation, optional haptics, auto-hides when a physical controller is assigned to that seat; a few optional shortcut buttons (e.g. L1+R1 combos) but the base layout stays a faithful PS2 pad because BT3 uses many chords.
- **Bluetooth/USB gamepads:** up to 4 simultaneously via Android `InputDevice` (SDL2 game controller layer, hot-plug, controller database), "press any button to join" seat assignment, persistent per-device mapping (vendor/product/descriptor), reassign from the Controllers tab, per-device rumble, disconnect handling (seat pauses with an on-screen prompt instead of dropping the player).
- **One shared input model for all platforms:** `InputSource -> Seat (1..4)`; sources are keyboard, SDL gamepad, touch pad, and later network seats; every seat produces the same native pad record (buttons + 4 axes), so Windows P3/P4 (see the native-pad request in COLLAB 15:05), Android and netplay share one path and no Python is involved.
- **Display notes:** one phone/tablet screen is small for split screen; plan for external display output (USB-C/Chromecast/Android TV) and a per-seat viewport choice; no speed promise before ARM64 device tests.
