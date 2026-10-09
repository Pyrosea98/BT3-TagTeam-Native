# Native screen lifecycle component

Owner: Codex. 2026-10-07. Header: ps2_ui_screen_lifecycle.h.

Implemented a thread-safe typed snapshot/state controller for Hidden, Loading,
Settings and About. The preparation owner publishes a strictly increasing match
generation, two rosters (1..5 per side, fighter IDs0..252), monotonic progress,
stage0..7, ready/failure/release/teardown and a monotonic-clock heartbeat.
Language is retained between generations. Snapshots copy fixed-size data; there
are no dynamic strings or allocations during publication/snapshot reads.

Loading ownership takes priority over settings/About. A new generation cannot
replace an owned loading/error screen until the current owner releases or tears
it down. Stale generations cannot change progress or clear a newer error. A100%
progress update is not readiness and does not hide the cover. Ready is a distinct
event; released is accepted only after Ready. Failure remains visible until
explicit teardown, and never becomes Ready/Released automatically.

The heartbeat lease flags stale ownership in snapshots; it does NOT infer actor
state, close errors or release gameplay. Lease clocks must come from one shared
monotonic source. Heartbeats can refresh Ready/Failed states as the owner waits.
Settings/About close events also reject backwards timestamps.

The component is presentation state only. It does not mutate guest memory,
consume gamepad input, acknowledge a presented frame, restore a match, or release
fighters. Those responsibilities remain with the match lifecycle owner and
renderer/presentation callback. No guessed legacy RAM/control addresses are
used. The M5 trial connects actual worker progress/rosters/release acknowledgement
through the bounded UI bridge to the real Vulkan screen views. The development
producer remains Python; lifecycle ownership migration is a later milestone.
Language persists through the existing settings model. See NATIVE_UI_SLICE.md.

`codex_check_ui_lifecycle.cmd` compiles the actual header and verifies generation
ownership, roster validation,100%-versus-ready-versus-release, stale update/
teardown rejection, error persistence, menu priority, heartbeat expiry/refresh,
clock regressions and cancellation teardown. PASS logged in
`power-scale-trial/codex-ui-lifecycle-check.log`. No runtime executable or live
screen behavior changed by this component alone.
