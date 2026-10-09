# Mode/performance batch — work in progress

2026-10-07. Latest handoffs read: 11:50 cover bugs, 12:30 mode/HUD
specification, 13:10 measured 5v5 interpreter bottleneck, and 13:50 startup
credits/About visibility request.

## Implemented and checked internally

- Cover presentation now has `startAccepted`, separate from actor release.
  The actual Session loop observes guest intro CONTROL+20 = 1/2 after existing
  manager/count/marker checks. Presentation fades over ten 30 Hz frames;
  the original start-gate ACK still owns actor release. Intro waiting sends
  a presentation heartbeat once per second. Failure clears startAccepted.
- Protocol action 11; op18 capability version 2. Adapter skips action11 for
  the retained M5 capability-version1 runner, preserving its compatibility.
- Separate stationary wave frame/cap and scrolling interior, wider bar.
  Import cache version3; display-only numeric-tag cleanup, two-line leader.
- Bridge FPS counters: packets/operations/rejections, worker service time,
  socket-send time, RX/TX bytes. Receive idle time is excluded. This bridge
  has no guest mutex or synchronous guest acknowledgement: guest wait is
  reported as `none_no_guest_lock`, NOT a measured claim of zero indirect
  CPU/memory contention.
- Existing exact-signature native target getters default enabled; explicit
  PS2X_NATIVE_TARGETS=0 and oracle remain available.
- Bounded instruction field decode cache, opt-in PS2X_INTERP_PREDECODE=1.
  Every execution compares the freshly fetched effective word, including
  delay slots, so arbitrary guest/PINE/DMA replacements cannot leave a stale
  decode. This is an instruction cache, NOT a basic-block executor or a
  demonstrated speedup. Default disabled pending measurement.
- --controller-poll 2.0 enables a 10x slower ordinary-poll comparison;
  pending transformation/fusion worker acknowledgement polling is retained.
- About/Credits is now displayed FIRST in the native settings category index
  and initially selected. Base category IDs remain unchanged; the display
  rotation preserves page/help/restore/back navigation. About includes the
  M5.1-dev UI build label. Its two URLs still open only on explicit Cross.
  Actual settings-model check covers initial placement, Down -> first real
  category, open/back, Up -> About, build label and existing save/link gates.

## Evidence

Internal build: repo/build/ps2xRuntime/ps2EntryRunner-mode-performance-work.exe
SHA256 8238D21E5452FF79E6484725E1392D0CBB4CE0FAC7FB25CA76A3726221F4AF8A.
Build log repo/build/codex-mode-performance-work-build.log, exit0.
Stable three runners retain 4052022D SHA. Existing user launcher is retained.

Native lifecycle and transport suites PASS. codex_start_accept_check.py tests
the actual Session release loop (intro acceptance BEFORE actor release,
no-intro ACK, changed-identity rejection). Real settings adapter test PASS.
Decode checker: 400000 accesses, field/sign-extension parity, changed-word
and colliding-address rejection, PASS.

58 RTX3080 GPU render/readback cases PASS, including actual intro-acceptance
fade while phase remains Ready, old release/failure/menu guards, EN/ES team
layouts and ultrawide fixture. 318 uploads remain fixed. Captures:
power-scale-trial/native-ui-mode-work-capture. GPU log:
power-scale-trial/codex-mode-performance-gpu.log. 5v5 capture visually checked.

## Follow-up: M5.2 implementation completed

All-mode covers, controller seat art, native HUD capture/views and startup/menu
credits below are now implemented and built in `ps2EntryRunner-modes-hud-credits.exe`
(9F2B5C11). The user UI Slice launcher selects this build. 130 GPU cases and
the protocol/model/capture/menu/start checks passed. See
`NATIVE_MODES_HUD_CREDITS.md` for current evidence and the single live test.
Generated-function presence caching and batched instruction counters are also
implemented. No measured gameplay speedup is claimed; block execution/hot ELF
AOT and the same-roster live performance gate remain open.

## Original outstanding list (superseded by the update above)

All-mode cover variants/seat art, complete mode catalogue and native HUD data
publication/views from MODE_SCREENS_SPEC.md; block execution cache or another
measured interpreter optimisation; hottest dirty ELF functions; same-roster
live bridge/polling A/B and performance gates. No game started, no live
speedup claim, no final user test requested for this partial build.
Startup credits splash/short strip and any-button skip, first-import credits,
startup preference persistence and second entry in the mod mode menu are also
pending from the 13:50 handoff. The settings placement change above does not
claim these are implemented.
