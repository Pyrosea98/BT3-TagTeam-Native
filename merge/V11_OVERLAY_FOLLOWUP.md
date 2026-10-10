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

## Gate-labelled samples (Claude correction)

The user was losing in every observed failed assist. The lead rule is therefore
not a demonstrated cause. Each actor sample now has sample_gate and
assist_side, evaluated in the upstream gate order: CPU/option/coordinator,
struggler, existing pending/releasing slot, participation/HP, requested/queued
busy actions, unique allied side, free slot, authenticated model, strict flat
range, current busy action, schedule, lead rule, stock, and REGISTER's ally
action. ready-at-sample means these sampled checks passed, not that an assist
was actually requested or confirmed.

human_struggle_sides identifies human participants' side indices. The signed
manager+88 word is the guest tug margin: positive favours side0, negative
favours side1, zero tied. This follows tug_code's side0 strength minus side1
strength and its signed accumulated push, rather than team HP or score.
Counter-after-read and struggle-serial recheck expose sampling limitations;
guest execution telemetry remains authoritative for actual requests/results.

Focused tests cover both sign conventions and range, busy, pending, full-slot,
participation, phase, schedule, stock and registration-action reasons. Private
trial helper updated while GAME_LOCK and runner processes were absent. No
gameplay rule or emitted program changed; no runner rebuild needed.
