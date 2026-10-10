# Live trial follow-up

## Restored native overlay checks

Compared the native overlay additions at released commit 7c23afa against all
18 changed merged overlays. Three authenticated Power Scale IO call sites had
reverted to strict original-disc comparisons: extra_reload_service,
extra_reload_preload, and body_swap_resources. Restored their shared
native_io_helper_matches check. It accepts only the reviewed Power Scale
profile, exact jump/delay instruction, original helper tail, and target header.

All other native overlay additions remain present after whitespace
normalization. Two exceptions were reviewed: fresh_team_trainer now reports
the same guest failure with v11's structured reason; mod_settings retains all
native display/HUD fields while adding v11 target/threat controls. The
selected_resource_queue transport loop uses captured_transport authentication.
viewport_hud's DRAW relocation and beam extension are upstream changes.
This comparison checks preservation of native patches, not every v11 behavior.

## Diagnostics and trial preparation

Beam-assist read-only logging now records observed start/end, guest telemetry
(human/CPU confirmations, triggers, stock failures and busy/blocked/hit), and
sampled CPU flag, action fields, stock, manager counter, schedule and side word.
Reads/logging are bounded to twice per second during observed struggles.
Match-end output retains the last sampled counters; transitions shorter than
the sampling interval are labelled as counter changes between samples.

The emitted-code fixture executes ASSIST, REGISTER, FREE and SYNC with a
controlled ELIGIBLE boundary. Valid scheduled CPU requests register; rejection,
busy, insufficient stock, wrong schedule and a winning side do not. The
upstream code helps only tied/losing sides. Actual ELIGIBLE range/admission and
live transition/confirmation are not established by this fixture.

Existing battle history now also records ki and blast stocks beside human
actions, stop flags, inputs and shared hold state when battle diagnostics are
enabled. It does not infer that a button was refused.

Private trial launcher fills missing required artwork from native-port before
imports, under its game lock. Existing art/settings/player saves are preserved.
Controller fixes are staged in the private v11 sandbox; runner unchanged.

## Still unresolved

Live CPU assist nonparticipation, absent CPU tactic starts, and blocked
specials after Goku reaches SSJ God are not claimed fixed. Do not bypass
no-slot, zero-cost/revert, or action/ownership gates without captured evidence.
No v0.1/v0.2 roster control run has been performed here. Released installer
and binaries are unchanged.
