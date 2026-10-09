# Roadmap: embedded Tag Team mod, Windows and Android installers, external testers

Owner of this file: Claude (keeps it current). Decisions come from the user; Codex and Claude
update status in `COLLAB.md`. Written 2026-10-06.

## Goals (from the user)

1. The Tag Team mod is part of the game runtime ("embedded"), not injected by Python through PINE.
2. Our own loading screen now; later, if possible, no loading screen at all because the work
   is done beforehand ("step by step").
3. One installer flow for **Windows and Android**. Once there is enough to test, ask external
   people to try the installer.

## Where we are (2026-10-06)

Working and user-tested on Windows (Vulkan): clean rematch, re-entering the mod menu, extended
roster IDs 161-252 (tested samples load, prepare and rematch; fusion/defusion validated with original partners 3/34, extended Japanese banks unresolved), 5v5 with original IDs.
Open: guest-code interpreter guard (kills sessions after about 6 min in a 5v5), status 173 on one
extended 5v5 roster, portrait order for 64 reordered slots, boot hang (1 in 25), 30 fps menus after
a battle, ki aura on Vulkan, Kaioken tint, loading screen redesign.

## Milestones

| # | Milestone | Done when | Owner |
| --- | --- | --- | --- |
| M1 | Stability and speed baseline | guard fix in; 60 min soak (5v5, rematches, fusion) without a runtime stop; interpreter cost profile by cave; boot hang understood | Codex (runtime), Claude (soak + profile reading) |
| M2 | Roster correctness | runtime labels done; portrait order solved or safe fallback; status 173 explained; extended transformation tested | Codex, Claude |
| M3 | Embedded host (no Python at run time) | lifecycle, preparation transport, rematch, cover control, workers run in-process in C++; PINE bridge only for debugging | Codex |
| M4 | Embedded features | per-frame guest logic no longer runs in the interpreter (route A native C++ or route B frozen cave pack recompiled); oracle comparisons pass per feature | Codex, Claude (oracle harness) |
| M5 | Loading | own cover (art baked at build time, native progress); then overlap preparation with the game's own loading scenes and cache immutable file bytes so most rosters need no extra wait | Codex (runtime), Claude (art/design review) |
| M6 | Windows installer | creates an install from the user's own ISO, verifies hashes, extracts at install time, no Python/PowerShell dependency, uninstall, log export | Codex + Claude |
| M7 | Android port | ARM64 build, Vulkan present, touch/controller input, audio, storage access, JNI lifecycle, APK; same install-from-user-ISO flow | Codex first (proof of concept: stock core boots to title) |
| M8 | External tests | tester channel, build number visible in game, issue template, log bundle that never contains ISO, BIOS, saves or keys | user decides who |

M3 and M4 can overlap with M1/M2. The Python tree stays as the behavioural oracle until M4 is done.

## Loading screen strategy

- Now: keep the Python/art version (Ki Storm today; the game-style design with the real face icons,
  VS, Dragon Ball progress is the target look, see `LOADING_SCREEN_BRIEF.md`). Art assets are
  generated at build/install time from the user's own ISO; nothing is redistributed.
- Next: replace only the run-time part (progress, animation, stage text) with native code; bake the
  pictures.
- Goal ("no loading screen"): the preparation currently takes about 15-20 s after the match
  starts (`19:51:02 -> 19:51:21` for a 1v2). Ways to hide it, in order of effort: start the
  preparation while the game's own loading scenes play; cache decoded character files by
  (ISO hash, file id, costume); prepare the next rematch during the result screen; build only what
  the selected roster needs. Measure first: log each stage's duration.

## Tester-readiness checklist (Windows alpha)

- No Python needed; a clean Windows 10/11 machine installs and plays.
- Installer verifies the exact supported ISO hash and refuses anything else; the user supplies the
  ISO and BIOS; the installer never downloads or ships game data.
- 60 minute soak passes (rematches, fusion/defusion, 5v5, menus).
- Known issues list shipped with the build; version/build number on the title screen.
- One-click log bundle without ISO, BIOS, saves or personal paths.
- Uninstall removes only what the installer created.

## Decisions (user, 2026-10-06)

- **Logo and portraits:** extracted at install time from the user's own disc using our maps; nothing
  is shipped in the installer. The maps are refined later (portrait order for the 64 reordered slots).
- **Power Scale author:** the user is in the author's Discord; the author is only waiting to release a
  new version of the mod, so we work on this beta (1.5.1) with no objection. Credit the Power Scale
  author and the Tag Team mod creator (exact attribution names need verified metadata before release) in the installer, its about screen and the release notes.
  Re-check compatibility when the author's new version is released.

## Remaining risks

- **Android:** a different CPU (ARM64), GPU drivers and thermals; expect long tuning. No speed claim until
  there is a device benchmark. The mod's guest code cannot use x86 SIMD paths there.
- **Interpreter on Android:** the current design (interpreted caves) runs at about 20 fight updates/s in a 5v5 on x86; Android speed is an unbenchmarked risk, and M4 should remove the interpreter from the hot path regardless.
- **New Power Scale version:** a new release will change addresses and files; keep the ISO hash check and
  the per-version maps so the installer refuses unsupported versions with a clear message.

## Priority order (user, 2026-10-06 evening)

Transformation, fusion/defusion and rematches are considered working; stop re-testing them except
where a change touches them. Order from now on:
1. **Remove the Python code** (M3/M4 embedding) and **replace the loading screens** (M5). Top priority.
2. **Portraits** for the whole roster, derived from the game's own data (no per-ID manual checking).
3. **Ki-blast bug:** blasts stop aiming when the locked target dies and the target cannot be changed.
4. **Fusion timer HUD:** replace the 8-bit looking timer with something in the game's own style
   (design brief to follow; must be native, no Python).
5. Standing goal behind all of it: the **Windows installer and the Android APK** for external testers.
   Every new feature must be written for the embedded runtime, not as new Python injection.

## Status log (Claude)

- 2026-10-06: ki-blast aiming fixed and live-passed behind `PS2X_KI_ROUTE=1` (generated selector tail-call bypass); promotion to default pending. Portraits solved (`portrait-slot-map.json`). Defusion, transformation and rematch fixes live-passed. Loading cover direction approved (real game sprites); fusion timer to reuse the game's own clock look; design language written (`DESIGN_LANGUAGE.md`).

## Python elimination (user priority, 2026-10-07)

Rule: no Python on the user's device on Windows or Android. Python may remain only as a developer/build tool. Ledger and
destination of every module: `PYTHON_LEDGER.md` (284 module files including overlay copies, ~67.6k lines): 160 guest-code
generators (41k lines), 65 data/policy tables (8.3k), 20 PINE host-orchestration (7.9k), 20 install-time ISO/art tools (7.2k),
2 host-drawn presentation modules (1.6k), build/dev tools (1.5k). Order: (1) runtime lifecycle/orchestration native (M3),
(2) generators frozen into a cave pack or native C++, hottest first (M4), (3) install-time tools into the native installer (M6),
(4) config menu and loading cover native with a baked glyph atlas (M5), (5) tables to data files shared by build tools and runtime.
Open decision for the user: ship a Windows-only alpha earlier with a bundled portable Python as a stop-gap (Android cannot).

## Product definition (user, 2026-10-07)

The end product is a **standalone game with the mods embedded**, on Windows and Android: one app, double-click or tap to play,
booting straight into the modded Budokai Tenkaichi 3 (Power Scale + Tag Team). Nothing is injected, attached or launched alongside it.
- Single executable/APK: runtime + recompiled game code + the Tag Team mod as native code/data + our UI art code. No Python,
  no PINE controller process, no helper scripts, no `.cmd` launchers or environment flags (today's `PS2X_*` flags become built-in
  defaults; diagnostics stay behind a developer switch).
- The user supplies their own disc image once. First run imports it: hash check, extraction of the assets the game and our UI need
  (art, portraits, labels), caches (including the shader/pipeline cache), then the game starts. Nothing game-owned is bundled.
- Everything the mod needs is inside the game's own menus: mode menu, settings, training, loading, HUD (see `DESIGN_LANGUAGE.md`).
- Settings, saves and caches live in the platform's app-data folder; a normal uninstall removes them.
- Updates ship as a new build number visible in the game; the debug PINE bridge and the logs export remain developer/tester tools only.

## Priority change (user, 2026-10-07)

Graphics work jumps the queue: texture dump and HUD draw trace first, then glyph atlas + native draw layer, then the loading cover,
the settings page, the fusion timer and team HUD plates, the training screen and the lock marker. Embedding continues behind it.

## Platform targets and tester policy (user, 2026-10-07)

- Targets: **x64 and ARM64** (Windows x64, Windows on ARM, Android ARM64). Codex noted x86/SIMD assumptions in the current runtime; the standalone
  build must compile and run on both CPU families. The interim "bundled Python" idea would only ever be Windows x64 (runs on Windows-ARM through emulation) and is
  a stop-gap, not a product.
- Tester policy: send whatever build is the latest STABLE one; today key parts are still missing (embedded host, native HUD/loading/settings, importer), so no
  external build yet.
- Credits (channels given by the user; display names read from the pages, to be confirmed by the user before release):
  Power Scale: https://www.youtube.com/channel/UCXiHmLmbgaSsFGrfejXESYw (page reads "LetsPlayBt3");
  Tag Team mod: https://www.youtube.com/channel/UCY79wsRvOdzBoe8GS77HY0A (page title reads "The Mufti").

Confirmed (user, 2026-10-07): credit names Power Scale = "LetsPlayBt3", Tag Team mod = "The Mufti". Fonts: Kanit Black Italic (titles) + Barlow Condensed ExtraBold Italic (body/numeric).

Decided (user, 2026-10-07): the About page and installer credits show both the names AND the channel links (LetsPlayBt3: https://www.youtube.com/channel/UCXiHmLmbgaSsFGrfejXESYw ; The Mufti: https://www.youtube.com/channel/UCY79wsRvOdzBoe8GS77HY0A). On Android and Windows the link opens the system browser only on an explicit tap.

Special thanks (user, 2026-10-07): a person who helped the user understand the code, Discord profile https://discord.com/users/747155705303400528.
Display name and exact wording are NOT known yet: do not invent them. Ask the user (name as they want it shown, wording, whether the Discord link is shown,
and that the person agrees to be named/linked) before it ships. Placement: the About page and the boot credits as a third block, "Special thanks: [name]".

Special thanks FINAL (user, 2026-10-07): display name "RidJuampa" (Discord handle ridjuampa, shown in the profile screenshot the user sent). Wording approved by the user:
EN "Special thanks to RidJuampa for helping me understand the code." ES "Agradecimiento especial a RidJuampa por ayudarme a entender el codigo."
Show the name only (no Discord link) unless the user later asks for the link; the Discord URL stays out of the UI by default.

## Future idea (user, 2026-10-08): online play
Not scheduled. First finish the installer and local co-op. When we get there: netplay needs deterministic lockstep or rollback on top of the static recompilation (fight update determinism, input exchange, desync detection), plus lobbies/NAT traversal; the 30-50 updates/s performance goal and the removal of Python come first.

### Online plan (Claude, 2026-10-08, after the user asked about 3 remote + 1 local host without split screen)
- **Phase A (recommended first): "remote seats"**: host-authoritative. The host runs the game and renders each remote seat's viewport (we already have seat input plumbing for P2-P4 and the quad viewports), hardware-encodes one video stream per remote seat (NVENC/AMF/Media Foundation H.264) plus shared audio, and receives each friend's pad input over an encrypted channel. Lobby code plus NAT traversal (ICE/STUN) with an optional relay; max 3 remote seats + the local host. Friends need no ISO; Android can be a thin client (decode + input). Costs: about 100-150 ms round trip on good links (casual/co-op, not competitive), about 8 Mbps upload per friend, host GPU/CPU load of 4 viewports + 3 encodes (UNMEASURED: first prototype must measure it on the Ryzen 5700G, also at 5v5 speeds).
- **Phase B (long term): deterministic lockstep/rollback** with everyone running the game: requires native de-Python (no asynchronous PINE state injection), deterministic FP/RNG across x64/ARM64, fast delta snapshots (current full snapshots are 128 MiB) and the same ISO build on every peer.
- Prerequisites for both: installer gate, de-Python slices, performance goal; security: encrypted transport, lobby codes, relay option to hide host IP.

### CORRECTION to the online plan (Claude, 2026-10-08): the BT3-Recomp runtime ALREADY has P2P netplay
- Found in `repo/ps2xRuntime/include/runtime/ps2_netplay.h` and `ps2_statesync.h` (impl `src/lib/ps2_netplay.cpp`, about 1,070 lines): host/join over UDP/TCP (`ps2NetHost(port, player)`, `ps2NetJoin("ip:port", player)`), 6-byte input packets, input delay, lockstep and ROLLBACK (`PS2X_NET_ROLLBACK=<window>`, needs `PS2X_FIBERS` + frame stepping; predicts missing remote inputs and re-simulates from a snapshot), portable STATE SYNC at connect (guest memory, devices, kernel records, every guest thread's R5900 context), per-N-frame checksums with desync detection (`ps2NetDesyncFrame`), a Netplay tab in the overlay, auto-jump to character select. The old "Dragon Net" main-menu page was retired 2026-09-25 (docs/NEW-NETMENU.md), the transport stayed.
- So "phase B" is NOT from scratch. Open questions for our build: it is 2-player (`ps2NetLocalPlayer()` is 1 or 2; we need up to 4 seats, 3 remote + 1 host, each peer with its own single view), whether the Power Scale/Tag Team build keeps determinism (the Python controller writes state asynchronously over PINE, injected caves and our native helpers must be inside the snapshot, per-boot RNG seed and host-time dependencies must be synced), whether our interpreter/fibers/native-leaves mode is snapshot-safe, and whether re-simulation fits the CPU budget (5v5 runs at 20-30 updates/s; small matches reach 60). Remote-seats streaming (phase A) stays as the fallback when determinism cannot be guaranteed.
