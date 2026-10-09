# Native loading, settings and About trial

Historical M5 acceptance record. The root UI Slice launcher now selects M5.2
`ps2EntryRunner-modes-hud-credits.exe`; see `NATIVE_MODES_HUD_CREDITS.md` for
the current build, all-mode HUD/credits changes and live test sequence.

## Launch and one live acceptance session

Open the root `Play Power Scale native UI Slice.cmd`. It selects the dedicated
`ps2EntryRunner-native-ui-slice.exe`, Vulkan, expanded roster, clean native
rematches and the real mod controller. This launcher acquires GAME_LOCK and
releases its own lock after the game closes. It refuses another owner's lock.

1. Open Modded Modes, then Settings. Existing settings navigation/edit/save
   behavior is retained. Language is staged; Square saves it. Close and reopen
   Settings to verify persistence. Triangle returns to the mod menu.
2. The last Settings category is About. Cross opens it. The two author names
   and full channel links are displayed. Up/Down selects a link; Cross opens
   that selected link in the system browser. Nothing opens on page entry.
3. Choose a modded mode and a valid 5v5 roster. The game's ordinary disc-load
   picture remains during native disc loading; the native preparation cover
   starts at the worker's actual preparation event. Check selected portraits,
   language, progress, held fighters, visible failure handling and final fade.
4. Finish the match and choose Fight Again once. Check that the selected
   simultaneous roster rebuilds and the new preparation cover completes.

Do not run a separate PINE probe during this session. Existing controller
clients are serialized, and UI events inside a poll reuse that poll's client.

## Implemented integration

- C++ owns the loading/settings/About snapshots and Vulkan presentation.
  Versioned bounded bridge messages use existing PINE opcodes17/18; no guest
  address, executable command or file path is accepted by the UI protocol.
- The existing preparation worker publishes actual phase boundaries and the
  selected roster. Stages0..6 are mapped by completed phase, including creating
  fighters and combat setup. Completion weights are medians from eight
  successful native preparation captures:750/1672/711.5/1484.5/1039/2249.5ms.
  Intro/release acknowledgement time is excluded from the completion weights.
- Ready and Released are separate. The adapter publishes Released only after
  StreamingSession.release_start returns from its identity checks and the
  game's start-gate acknowledgement. Retried Ready/Released messages are
  idempotent.100% cannot hide the cover; errors require owner teardown.
- Native GPU readback carries the exact UI generation/revision; menu input
  waits for that revision to return through the real readback path. Existing
  guest input isolation and its180-frame lease are retained. Menu presentation
  also expires after a missing5-second owner heartbeat; loading errors stay.
- Preparation under12 logic frames produces no cover. Entrance/exit fades,
  VS pop, seven balls/pop/flash/particles, scrolling banner/wave,12-step bar
  easing and ready portrait pulse run from a30Hz timebase. Language changes
  use existing textures and the complete native EN/ES catalogue.
- The640x448 layout is fitted in the actual host presentation rectangle, then
  mapped back to the scanout. Fonts/portraits/balls retain their proportions
  when the host stretches the game scanout to an ultrawide destination.
- All1v1..5v5 layouts use selected native roster IDs0..252, the audited portrait
  permutation and runtime base labels. Native text ellipsizes at UTF-8 boundaries.
  A24-character test label and all253 character names are covered by the atlas.
- Settings use the existing complete mod preference model, with native title,
  flat rows, separate value chips, selection and help. Save/discard/repair,
  per-character exceptions and About remain available. Graphic preference rows
  in the GPU template fixture are sample data, not new native graphics controls.

## Local assets and reproducibility

`codex_import_native_ui.py` reads the player's expanded ISO and caches extracted
sprites/253 portraits alongside generated fonts. The developer app-data override
is `power-scale-trial/app-data/native-ui`; this is not the final platform importer.
The cache records ISO size/mtime and roster-map hash. These derived game assets
must not be redistributed. The importer reuses the decoded portrait package
instead of decompressing the full UI package for every portrait.

Native headless GPU acceptance:

```
experiments\.full-install\.venv\Scripts\python.exe native-port\codex_ui_slice_check.py
```

No game, ISO execution, window, PINE connection or user input is involved in
this test. The native executable loads actual assets, renders/readbacks PNGs
on Vulkan and verifies unchanged upload counts. Python assembles contact sheets.

Other checks: `codex_check_ui_transport.cmd`, `codex_check_ui_lifecycle.cmd`,
`codex_ui_adapter_check.py`. The adapter check uses the real preference model
and an isolated temporary settings file; it never rewrites the player's settings.

Evidence: `power-scale-trial/codex-ui-slice-self-test.log`,
`codex-ui-transport-check.log`, `repo/build/codex-ui-slice-build.log`, and
`power-scale-trial/native-ui-slice-capture/`. Both contact sheets contain all25
team layouts. Additional captures cover EN/ES settings/About/failure,24-character
ellipsis and the simulated2560x1080 host presentation.

## Limits of this milestone

The native screen renderer/state is implemented; semantic preparation and
settings orchestration still use the Python development controller. This is
not the Python elimination milestone or an Android APK. Windows ARM64/Android
builds and graphics backends besides paraLLEl-GS Vulkan are unverified.

Isolated warmed CPU/GPU timings are measured separately. First-use shader
compilation causes an approximately18ms CPU hitch; this is not a live gameplay
frame-time measurement. Live5v5/rematch/input/loading-time parity and Claude's
single visual review remain UNKNOWN until the coordinated session. Existing
stable runners and ordinary launchers are preserved.

Build SHA256: `E0CE05C8990C638AAEE14E712014F875C917A128EC3598058846121AF1A2CE5F`.
