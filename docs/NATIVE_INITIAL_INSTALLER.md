# Initial Windows installer — fusion form/text release, 2026-10-08

## Current artifact

`installer/output/BT3-TagTeam-Fusion-0.1-Setup.exe`

- Size: 70,795,554 bytes.
- SHA256: `ed287512e548dc2a7003202a69bf8c47b7dbcc0eab4acf36989c2d1c0fcd06ec`.
- Packaged `ps2EntryRunner-standalone.exe`: 103,407,616 bytes, SHA256 `6f037206514122d42848448cf181abe905ae0ebcf141dcd95f75ed2608460bc3`.
- Runner matches the checked `ps2EntryRunner-fusion-text-release.exe` exactly. Stable developer runners remain unchanged.

Windows x64, per-user, EN/ES, one Play shortcut, hidden embedded CPython and native Vulkan runner/importer. System Python, PCSX2 and BIOS are not required. Player discs and derived interface art are not packaged. This is ready for installed-build live acceptance; no game was launched during these checks.

## Included changes

Latest rematch teardown/rebuild, second-match controller cleanup, giants preparation, co-op ownership, P2 revert event-tail fix, transformation/defusion handoff, expanded roster, native overhead HUD/credits/special thanks, six fusion control modes and configurable swap interval.

The R3 chip appears only over the fighter whose player is being asked to accept fusion. Idle/defused fighters get no native fusion chip. Both sizes of the shared guest mod-text renderer are suppressed during an authenticated native HUD match in either HUD style. Native kill plates/timers/ownership remain; ordinary game menus and legitimate game prompt roots remain functional. Exact code guards reject changed guest code.

Installed Play uses pythonw and CREATE_NO_WINDOW, redirects output to logs and reaps its runner on all controller exit paths. The developer CMD closes silently after normal/forced runner exit and runtime errors. Only startup/setup errors show the log tail with an eight-second timeout; there is no indefinite pause. Android will require an in-process lifecycle; this Windows change does not implement an APK.

Fresh settings: expanded maps ON, six fusion choices (P2 everything last), swap interval20s, show_fuse_prompt ON, Game HUD + overhead, credits ON. Existing preferences remain on source refresh/upgrade. Map changes use the existing Restart now/Later flow.

Progression save is seeded only when absent, independently of imported ELF:
`%LOCALAPPDATA%/BT3TagTeam/saves/progression/BASLUS-21678DBZT3/BASLUS-21678DBZT3`.
Packed save SHA256: `86773da7dd5f355455b3f397784a3b8aec18558c2c5ac878c26317b85eab7b54`.
Unlock everything remains on hold and is not included.

## Offline installer gate — PASS

1. Actual silent installation into an isolated workspace app/profile; embedded runtime resolves223 modules with PATH limited to System32, no external Python. Packed progression save seeded only when absent.
2. Original Power Scale BETA1.5.1 ISO imported through the installed embedded app/native importer into a new profile. Original SHA256 `f3e495b8eb2269c2808f00352058d0be6facf3db4bf1c013f2d78ea2a531c6d3`; prepared expanded SHA256 `e26dbbe6cfb75d7e407f7d197330b270de47b50ac83920ba435f946868a0390e`. Full importer verification, derived art receipt and fresh combat code generation PASS. Source disc is not written.
3. Upgrade from preceding installed revision to final package; deliberately changed Spanish/maps-OFF/45s settings and distinct save preserved byte-for-byte. Private sources refreshed; installed runner equals final checked runner.
4. Actual silent uninstall of final upgraded package removes app/private sources/import and preserves the distinct progression save unchanged. Test profile override supports isolated uninstall without touching the player's default data.
5. Clean install of the final package into a second fresh profile; embedded runtime/save check and a second actual original+expanded import/code-generation check PASS.
6. Offline actual MIPS matrix72 ordered-pair/control cases, pending-recipient/idle/defused prompt guards, both text sizes through the actual interpreter in both HUD styles, pointer timer and pause/cinematic clocks, production cave cleanup PASS. Compiled29 exact draw-variant/code-mutation guards PASS. Vulkan12 EN/ES/aspect/shape captures PASS. Giants, co-op rematch ownership, consecutive-match cleanup and transform/defusion receipt checks PASS.
7. Real hidden child-process normal/crash/killed/setup-failure/restart cleanup PASS. No remaining app/runner processes or GAME_LOCK after headless checks. A live game quit was not performed.

Evidence: `installer/fusion-release-{build,install,import-check,upgrade,uninstall,match-checks}.log`, `installer/fusion-final-fresh-{install,import}.log`, isolated `package-check.json` files, and `power-scale-trial/codex-fusion-*-check.log`.

## Morning live checklist

- Install this Setup and open installed Play; confirm no console appears.
- Import first-run original ISO through the UI; check EN/ES, expanded-map preference and Restart now/Later.
- Play5v5, FFA and two-human co-op; transform/revert, fuse/defuse, correct recipient prompt, native kill plates, no garbled guest banners; Fight Again and new character selection.
- Save, quit and relaunch; confirm progress/settings persist and no launcher/controller/console remains after quit or crash.

Three/four-seat routing/projection is checked offline with captured resources and simulated input. Full physical3/4-controller polling and every character's native resource transaction remain outside offline acceptance. Performance attribution still needs comparable untraced live runs. Fusion time by form is included, default Off, with Mild/Normal/Heavy EN/ES settings. Live higher-form/revert/near-expiry/defusion acceptance passed on the preceding form-life build. Native HUD ownership now remains acknowledged between frames; both text helpers are also block-cache boundaries. Cleaned native kill plates omit form/costume annotations. These text corrections still need live confirmation in co-op requests, refusals/timeouts, owner/countdown/first swap, and kills in both HUD styles.

## Current restage gate (fusion form + text)

Actual clean install into `installer/fusion-text-installed`, 224 embedded modules
with System32-only PATH, fresh `fusion-text-profile` original/expanded import:
PASS. Actual installation of the prior Initial package into a separate profile,
then upgrade to this package preserved Spanish/maps-OFF/45s preferences and a
distinct save byte-for-byte. Actual uninstall removed app/private sources and
retained the save. Inno's temporary uninstall process finished asynchronously;
completion was verified against its final log and absent files. No game booted.

Current evidence: `installer/fusion-text-gate.json`, `fusion-text-gate.log`,
`fusion-text-{build,install,prior-install,upgrade,uninstall,uninstall-finish}.log`.
The older numbered gate above records preceding-release checks; the current
form/text restage adds actual EE form clock and life/grace cleanup, 72 control
cases, 12 Vulkan captures including acknowledgement retention between frames,
quad preparation, giants and receipt regressions. A separate diagnostic executable
adds the straight-block fall-through text-boundary regression; the packaged and
developer release runners remain identical at the SHA above.

`codex_check_launcher_exit.py` executes a real hidden controller/runner/cmd chain,
forces child termination through Windows TerminateProcess, and verifies controller
and shell exit within five seconds with no child/owner remaining. Installed Play
has no CMD/pause path and uses hidden Python/child processes. Physical live console
observation remains part of the checklist.

Original Initial installer retained as the preceding artifact. The updated Fusion
installer has a distinct filename because Windows held the old installer open.
CPU tactics are not included; see `NATIVE_CPU_TACTICS_FEASIBILITY.md`.
