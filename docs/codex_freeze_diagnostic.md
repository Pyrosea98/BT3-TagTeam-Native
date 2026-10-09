# Freeze diagnostic runner

Build with `native-port\codex_build_freeze_diagnostic.cmd`. The CMake target
remains `ps2EntryRunner`, but its output name is
`repo/build/ps2xRuntime/ps2EntryRunner-freeze-diagnostic.exe`. The build script
does not copy or replace a stable executable. The shared build cache retains
this diagnostic output name; use this script for subsequent diagnostic builds.

Coordinate through `COLLAB.md`, check/create `GAME_LOCK`, and preserve existing
logs before launching. No automatic game launch is part of the build.

From the workspace root, in PowerShell:

```powershell
$env:PS2X_TRACE_CONTINUOUS = '1'
$env:PS2X_THREADLOG = '1'
$env:PS2X_SCHED_DEBUG = '1'
& 'experiments/.full-install/.venv/Scripts/python.exe' 'native-port/run_power_scale_native.py' --renderer vulkan --runner ps2EntryRunner-freeze-diagnostic.exe
```

`PS2X_TRACE_CONTINUOUS=1` removes the scheduler, RPC-loop, thread-spin and wake
event caps, and emits uncapped sleep-block/sleep-wake/wake records directly to
stderr, including when `RUNTIME_LOG` is compiled out. Scheduler output also
requires `PS2X_SCHED_DEBUG=1`. Normal cap behavior remains when the continuous
flag is absent. Launch selection via `--runner` is restricted to a filename in
the existing build output directory.

Output goes to `power-scale-trial/runner.log`; controller messages go to
`power-scale-trial/controller.log`. Preserve their tails at a stall and use
Claude's freeze capture helper. This is uncapped file logging, not a ring
buffer. Use short diagnostic runs: extra logging can alter timing and generate
large files. A successful build alone does not confirm a freeze reproduction.

## Dispatch-history diagnostic

Build: codex_build_freeze_diagnostic.cmd ps2EntryRunner-freeze-history.
Select --runner ps2EntryRunner-freeze-history.exe and set PS2X_STALL_HISTORY=1.
At each guest dispatch loop's same-PC threshold2000, emits [stall-history] and [stall-state]. State includes requested globals and scene manager scene/+14/+624/+68C fields. Dispatch ring is host-thread-local; guest fibers sharing a host thread share this history. Current tid is logged, but this is not a guaranteed exclusive per-guest-thread trace. An interpreter-internal spin may never reach this dispatch threshold.

User-visible launch: double-click root Play Power Scale diagnostic.cmd from Explorer. Tool-parent launches and shell launches were invisible in the user's latest tests. This diagnostic does not change game behavior or claim to fix the freeze.

## Interpreter diagnostic

Select --runner ps2EntryRunner-freeze-interp.exe with PS2X_STALL_HISTORY=1 and PS2X_STALL_INTERP=1, plus existing continuous/DVCI flags. Play Power Scale diagnostic.cmd selects these. Dumps active interpretUntil entries, last entry/return/exit/RA, count of calls entering at their stop PC, and last16 executed interpreter instructions per guest context (including delay slots). Prints six requested function lookup/dirty results after the dispatch history, so diagnostic lookups are distinguishable. Patched function lookups now enter the dispatch ring too. No interpreter return semantics changed. Capture helper must be started separately by the capture owner.

## Patched interpreter resume fix

Runner: ps2EntryRunner-interp-fix.exe. No fix environment switch is required: the patched interpreted stub opts into executeEntry. Ordinary interpretUntil call sites keep the default pre-entry stop check. On a patched resume, the first iteration runs even when entry equals returnPc; all later stop checks and the runaway guard remain. This addresses the empty-dispatch loop confirmed in capture20261005-171356; gameplay validation is pending. Keep both diagnostic flags for validation. The legacy equal_entry_returns diagnostic counts equal-PC entries, not whether they now execute instructions; after the fix that number alone does not indicate an empty return.
