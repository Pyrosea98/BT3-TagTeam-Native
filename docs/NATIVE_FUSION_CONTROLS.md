# Fusion controls and native indicators — 2026-10-08

The existing **Play Power Scale native UI Slice** launcher selects
`repo/build/ps2xRuntime/ps2EntryRunner-coop-fusion-controls.exe`.
SHA256: `81099D7D7A8067E38D822D6CFDC77D2D5E87F6A7BADBBCC1B2442CB86C38A89D`.

## Implemented

- Six modes, in order: Swap control; P1 attacks/P2 moves; P2 attacks/P1 moves; Swap roles; P1 does everything; P2 does everything.
- P1/P2 in these menu choices mean first/second fuser by consent order. Actual seat icons identify the assigned controllers, including seats 3 and 4.
- Swap interval: 5/10/15/20/30/45/60 seconds, default 20. Both periodic modes use elapsed combat updates since the fusion commit. The first swap waits one full interval. Scene pauses and authenticated shared cinematics stop the clock.
- Native overhead R3 prompt, fusion duration and swap arcs, seat ownership and attack/movement symbols. Prompt queries use the current game recipe eligibility. Hexagon/Ring follow the selected shape; Off uses small bars. Indicator width is capped at 46 logical pixels, opacity at 45%, with cinematic fade and a gentle prompt pulse. English/Spanish labels fit without ellipsis.
- Fixed missing fusion time: the duration record contains an actor pointer at +8 and physical leader at +16. Capture now validates both against the current actor. Previous code mistook the pointer for an index.
- Visibility settings are honored independently of the original guest HUD. Owner/countdown menu labels now describe both control and role swaps.
- Five seconds with an entire team dead/absent while normal team battle remains active creates a diagnostic snapshot. Pauses/loading/cinematics reset the interval; training and FFA are excluded. The capture has its own once flag, independent of scene/exit captures. It does not write guest state or stop gameplay.

## Checks

`codex_check_fusion_controls.py` builds a fixture from actual prepared 5v5 RAM and the current production MIPS code. The native interpreter checks 12 ordered seat pairs × 6 modes, full and split pad routing (buttons and analogs), 5/60-second boundaries, owner/countdown capture, all-seat input restoration after defusion, three/four-seat viewport subjects, and pause/cinematic clocks. Timer pointer identity, hidden settings and real idle eligibility queries also pass. Production cave teardown removes new rows, clocks, interval, prompt and fusion code before the next match while retaining live services.

The fixture models committed fusion metadata and simulated controller input; it does **not** execute every character's native fusion resource transaction. The three-seat projection subset covers ordered pairs among seats 1–3; four-seat projection covers all pairs. No full live 3/4-controller match, USB polling, consent ergonomics, or every character's transform/revert/fusion/defusion resource behavior is claimed.

Actual native current-camera/model replacement projection still agrees with reference anchors within 0.01 pixel. The generated event-tail regression test still preserves stock events and blocks extra-actor scene corruption. These are saved-RAM checks, not new live acceptance.

`codex_check_fusion_ui.py` produces 12 offscreen Vulkan captures: English/Spanish × 16:9/21:9 × Hexagon/Ring/Off. Visual review corrected clipped prompts. The exporter check verifies independent scene/defeat/exit snapshots, 128 MiB RAM, contexts, 200 dispatch records, duplicate suppression and no guest stop. Defeat snapshots include actor pointers/team/HP/action and participation masks; full RAM retains native win-check and fusion inputs.

Logs and images are under `power-scale-trial/codex-fusion-*-check.log` and `power-scale-trial/fusion-native-captures/`.

## Live follow-up

Two-human fusion: choose each control mode, confirm its first interval, owner/role indicators, R3 prompt and timer with the original HUD hidden; defuse, then Fight Again and a second character selection. Seats 3/4 routing is covered offline; hardware acceptance remains unavailable.

The intermittent 5v5 no-win cause remains unknown. If it recurs, relay the new `guest-exit-captures/black-scene-*` folder whose metadata reason is `team-defeat-not-resolved`.

Performance attribution still needs comparable untraced roster runs. The earlier traced 5v5 result is not a baseline and the observed small-roster 60 updates/s is not attributed to this slice. Installer has not been restaged. Stable runners retain SHA256 `4052022DFE11DED8F98A47F8EACEA75D0EEAD9BC87F5F620853461E5CF79756D`.
