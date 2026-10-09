# Co-op fusion projection and black-scene investigation

## Trial

The existing **Play Power Scale native UI Slice** launcher selects
`repo/build/ps2xRuntime/ps2EntryRunner-coop-scene-fusion.exe`.
The preceding exit-capture runner and stable runners remain available.

## Fusion overhead correction

Confirmed from the guest renderer: `multiplayer_fusion.SHARED` switches a
two-human fused pair to one native camera and bypasses quad camera preparation.
The native HUD previously continued using the two cached quad cameras.

The HUD now mirrors that authenticated shared-view predicate and projects
through the current camera at `gp-22176`. Three/four-seat sessions retain
their independent cameras. It excludes consumed partners using the match-owned
participation mask. Current actor model and head references are resolved each
frame as before. Defusion removes the shared-view predicate and restores the
partner through the current participation mask.

Checks:

- `codex_check_ui_hud.cmd`: production HUD capture, consumed partner,
  shared-view ownership, three-seat fallback, defusion and stale-owner refusal.
- `codex_check_coop_fusion_projection.py`: actual native projection helpers and
  captured fighter skeletons; two projectable models replace the owner model in
  a controlled shared-view fixture. Each valid anchor agrees with projection
  through the same native camera within 0.01 pixel; caller/context and borrowed
  stack are unchanged. This fixture does not simulate a fusion or match.

Live fusion/defusion with P1 and P2 is pending.

## De-transformation black scene: unresolved

The archived controller log shows a successful extra reload and resource
retirement on revert. The runner keeps drawing 30 swaps/s, but packet output
falls from about 170,000 to 2,000–6,000/s. `cinematic=1` persists afterward.
These logs do not identify the writer or prove that retirement causes the
failure. No failed-frame RAM was provided; no speculative render/cleanup
restoration has been applied.

New production diagnostics:

- A monotonic packet count is published by the Vulkan backend on swap; the
  guest boundary reads it without acquiring a renderer lock. No additional
  atomic operation is added per GIF packet.
- After observing healthy output (at least 20,000 packets/s), output below
  8,000/s for two seconds during an active, unpaused, non-cinematic fight
  triggers a capture.
- A second watch allows ten seconds with cinematic flags present. This catches
  a suspected stale cinematic flag without excluding that condition forever.
  A long legitimate low-output cinematic may also produce this diagnostic;
  the capture itself is not a diagnosis.
- Loading/held-manager and paused states reset the low interval. New match
  generation resets the watch. Counters moving backward reset its sample.
- Capture contains 128 MiB RAM, CPU contexts, the last 200 available main-thread
  dispatch records, layout, cinematic and reload status metadata.
- Output: `power-scale-trial/guest-exit-captures/black-scene-*`. One scene capture
  per process, independent of the existing exit capture. No stop request or
  guest memory mutation; I/O failure is nonfatal.

`codex_check_coop_scene_capture.py` checks the production exporter and independent
exit/scene capture guards. Compiled HUD checks cover the detector thresholds,
generation/pause/reset guards and duplicate trigger prevention.

Next live check: two humans, transform then revert with P2; if the scene blacks
out, leave it running unpaused for at least ten seconds so the capture completes.
Also check fusion and defusion for both players. Use the resulting RAM to audit
cinematic ownership, bound cameras, visibility lists and retained resources.
The installer has not been rebuilt with this trial.

## P2 revert capture audit (2026-10-08)

`black-scene-156042044107000/ram.bin` has scene flags64 `0x2000` at
`0x3337B8`. Native model eligibility (`0x113BA8`) and stage draw
(`0x115950`, `0x115DE0`) suppress world drawing while this bit is set.
All captured actors have left transformation actions; commit and retirement
are both status5, manager reload/hold are zero, and the cinematic camera has
no running track. The native scene-job pool returned by `0x127120`
(`0x301058`, eight64-byte slots) has all eight slots on its free list.
This confirms a retained render-disable flag; it does not identify its writer.
The persistent mod shared-stop value alone is not proof of the original cause.

Next diagnostic launch, using the existing runner:

```powershell
python native-port/codex_ui_slice_trial.py --trace-scene-writes
```

This opt-in uses the existing native address watch on `0x3337B8..0x3337C0`.
Repeated writes are retained, including clears, so a second revert cannot
disappear through deduplication. `[camwrite]` in the runner log includes PC,
RA, stack code words, value and the previous watched bytes. Trace from boot
through P2 transform/revert; compare the last `0x2000` setter with its paired
clear and native job lifecycle. Keep normal launch untraced for performance
measurement. No guest memory repair, forced flag clear or renderer change
has been applied. The launch flag syntax/configuration check passed offline;
this trace still needs a live run.


## P2 revert event-tail correction (2026-10-08)

The subsequent live write trace identifies the setter as the native achievement
sink, rather than a scene-load job. `1296B8` uses the two-row table at
`331DC8+1980=333748`. For physical fighter2 and event77, the address is
`333748 + 2*48 + 8 + (77//64)*8 = 3337B8`; bit77%64 is13 (`2000`).
The captured entry has its correct extra-fighter guard at07382000 installed.
The generated native revert tail at1FE600 called the original C++ sink directly,
bypassing that patched entry. Its containing duplicate and1DB030 have the same
bypass. The stack word201B988 is actor201B040+948, not identified executable code.

The correction routes only native tail jumps targeting1296B8 through runtime
lookup, so they honor the installed guard. The code emitter preserves this rule
on future regeneration; all unrelated tails retain their direct native calls.
No scene-bit watchdog or forced clear is used. The separate trial is
`ps2EntryRunner-coop-event-tail.exe`. Its `--native-event-tail-self-test RAM_PATH`
executes the actual generated tails against captured RAM, without a live game.
Live P1/P2 transform/revert is still required for final gameplay acceptance.

Build/headless result: PASS on black-scene-157233580513900/ram.bin. Actual
unguarded native sink reproduces the corruption; all three corrected generated
tails preserve stock0/1 events and block extras2/3/9 while retaining an unrelated
scene flag. Log: power-scale-trial/codex-coop-event-tail-check.log. UI Slice now
selects the corrected runner by default. Live gameplay acceptance remains open.
