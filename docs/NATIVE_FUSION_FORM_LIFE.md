# Fusion time by form — implemented 2026-10-08

## Try it

Use `Play Power Scale native UI Slice.cmd`. It now selects
`repo/build/ps2xRuntime/ps2EntryRunner-fusion-form-life.exe`.
In Settings → Fusion, enable **Timed fusion and automatic defusion** and
**Fusion time drains faster in stronger forms**, then select a drain strength.
Start a newly prepared match. Fight Again retains that match's settings.
The new option defaults **Off**; the existing configured time limit is retained.
The frozen Initial 0.1 installer does not contain this new slice.

## Behavior

The production guest clock keeps remaining life in Q16 units. The native Vulkan
HUD reads this clock directly; no new host polling worker is added. Each combat
update consumes `rate(form) = 100 / (100 - penalty)` base updates. Changing forms
changes future drain, without resetting the time already spent. The existing
authenticated expiry and serial defusion resource service remain in charge.

| Form | Mild | Normal | Heavy |
|---|---:|---:|---:|
| Base | 0% | 0% | 0% |
| SSJ1 | 5% | 10% | 20% |
| SSJ2 | 10% | 20% | 35% |
| SSJ3 | 15% | 30% | 50% |
| God | 20% | 40% | 60% |
| Blue / SSJ4 | 25% | 50% | 70% |

Percentages describe a full fusion held in that form: Normal Blue lasts half the
configured base duration. A mixed path consumes the same shared life budget.
Direct jumps and reversions read the active model's current runtime character ID.
Unknown forms use base drain. Native Dance receipts (kind 241) are required;
preselected fusion fighters and permanent Potara are unaffected. Optional legacy
timed Potara, if admitted by another configuration, retains its old clock.

Battle pauses, shared cinematics and the actor's transform actions 236–243 pause
drain. A completed form change grants at least 30 combat updates at the new rate;
the completion boundary itself does not consume an update. This grace is the
exception to the no-refund rule. A separate grace counter preserves that second
even for a one-second configured duration, while life stays within its original
budget. Busy moves still finish before the existing defusion hold is requested.
The timer never changes transformation eligibility.

The native arc shows the remaining life fraction. The under-ten-second number
projects time at the current rate, including remaining grace; the existing
under-three-second warning is retained. A tiny orange marker indicates faster
drain. Hexagon, Ring and Off layouts, EN/ES and timer-hide settings are supported.

## Form table

`power-scale-trial/controller/game/tools/fusion_form_tiers.json` uses expanded
runtime IDs: Gotenks 48 base, 49 SSJ1, **50 SSJ3**; Gogeta 110 base, 53 SSJ1,
59 SSJ2, 58 SSJ3, 62 God, 54 SSJ4, **219 Blue**. It is loaded when the controller
starts and compiled into that match's guest clock. Restart after editing it.
Gotenks' second listed transformation is SSJ3; ordinal guessing would be wrong.
These IDs follow the expanded roster identity evidence. Actual live transformation
chains for each form still require the checks below.

## Evidence

- Isolated build SHA256: `9F5FCC162022BE247DBD4D0E11E1E278AC2924D72EB73C37C5BEABF937EA95E8`.
- `codex_check_fusion_form.py`: actual EE interpreter executes current production
  TICK and expanded ROW helper on captured native actor/model resources. All 18
  tier/preset combinations, 12 ordered allied actor pairs, Gotenks direct SSJ3 and
  revert, Blue with three seconds left, one-second grace, one-second total budget,
  transform/shared/scene pauses, Off/Potara/permanent/unknown guards, stale actor
  cancellation, HI/LO preservation and projected native HUD pass. Actual production
  cleanup removes timer code and all life/rate/grace fields.
- Existing fusion controls: 12 ordered seat pairs × 6 modes = 72 cases pass on the
  new runner, with PAD/FOLLOW, input merges, interval boundaries, all-seat defusion
  input, projection, prompt, text suppression and hide guards.
- `codex_check_quad_rematch_cleanup.py --fusion-form`: real consecutive captured
  co-op matches produce a fresh 891-block preparation with the feature enabled.
  Current timer/quad code authenticates; changing options in an existing prepared
  match is rejected. Defusion ownership receipt regression passes separately.
- `codex_check_fusion_ui.py`: 12 offscreen Vulkan captures EN/ES × 16:9/21:9 ×
  Hexagon/Ring/Off pass, with visual review. Existing independent exit exporters pass.
- Settings: default Off, six enabled/preset combinations, invalid values rejected,
  current Python sources compile. Future installer staging includes the JSON table.
- No live game was launched. No runner/Python process or GAME_LOCK remained.
  Stable three runners retain `4052022D...`; frozen installer retains `DB41AB29...`.

Logs: `power-scale-trial/codex-fusion-{form,controls,visual}-check.log`.
Images: `power-scale-trial/fusion-native-captures/`.

## Remaining live checks

Gogeta and Gotenks: fuse, transform directly to a higher form, revert, check native
arc/projected number, finish defusion, Fight Again and select a new match. Try a
transformation near expiry. Confirm permanent/preselected fusions stay permanent.
The offline tests seed committed receipts and real model identities; they do not
replace live native fusion/transform resource transactions or physical 3/4-pad tests.
