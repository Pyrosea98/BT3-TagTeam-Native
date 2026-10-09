# DVCI transition investigation — 2026-10-05

## Confirmed from local source and captured trace

- Capture `power-scale-trial/freeze-captures/20261005-161444/runner.log.tail`
  has RPC 2 followed by four RPC 4 calls at lines 67393–67397, followed by
  the main-loop stall. The same tail has an earlier RPC 4 at line 25495,
  followed by continued normal operation. RPC 4 by itself is not sufficient
  evidence of the freeze cause. No good complete post-match RPC 2/4 sequence
  has been verified yet.
- `repo/games/bt3/work/output/sub_001240B8_0x1240b8.cpp`:
  the RPC 2 wrapper first clears the local 0x184-byte command queue at
  `*(gp-0x50E8)+0x68`, then sends a four-byte request at `0x300EC0`.
  `FUN_00124a28_0x124a28.cpp` invokes it, invokes `0x124520`, then clears
  +0x30/+0x34 in each of eight 0x4C-byte file-slot records.
- `FUN_00124128_0x124128.cpp` places its input argument in request word 0,
  then sends RPC 4 with a four-byte request. Its caller
  `FUN_00124dc0_0x124dc0.cpp` checks a resource, frees and zeroes three
  pointers (+0/+4/+8) in its file-slot record, then invokes RPC 4 with the
  original argument.
- `sub_00123F48_0x123f48.cpp:66` sets RPC mode=0. The receive buffer is the
  client base, size 0x40; callback and callback parameter are zero. These
  calls are synchronous. The nowait-only semaphore signal in
  `Kernel/Syscalls/RPC.cpp` is not the expected completion path for them.
- `ps2_iop.cpp` prefers `ps2xInvokeIopRpc` only if the SID has a registered
  handler. Otherwise its DVCI fallback zeroes the response and writes 1
  (except the opt-in RPC 9 experiment). A native route is not established
  merely because that preferred branch exists. Captured startup logs show
  several missing IRX files; the precise runtime route still needs tracing.

## Hypotheses / unknowns

RPC 2 appears to reset/cancel the disc queue; RPC 4 appears to release a file
resource. These names are inferred from the guest callers, not verified IOP
handler semantics. A missing completion, a wrong response, or a separate main
loop/scene transition failure remain unconfirmed. Do not force a semaphore,
frame or queue completion as a fix based only on the final RPC sequence.

`PS2X_DVCI_DONE=1` changes only the fallback response for RPC 9. It does not
directly repair commands 2/4 and does not affect a successfully handled native
IOP call. Keep it out of the first diagnostic reproduction to avoid changing
two things at once.

## Instrumentation

New executable: `repo/build/ps2xRuntime/ps2EntryRunner-freeze-dvci.exe`.
Build: `codex_build_freeze_diagnostic.cmd ps2EntryRunner-freeze-dvci`.

The existing request/queue probes now execute before preferred native dispatch.
Previously a successful native dispatch returned before those probes. Their
early caps are bypassed with `PS2X_TRACE_CONTINUOUS=1`; queue printing is bounded
by the declared send size. New `[dvci-route]` identifies native versus fallback
handling. New `[dvci-return]` logs the first receive word, selected handling,
mode/callback and internal client busy-clear after `SifCallRpc` finishes.
`returned=1 completion=1` in a route record means the adapter returned handled
and requested completion; it does not establish success of the disc operation.

Coordinate `GAME_LOCK` and preserve old logs before launching. Add
`PS2X_DVCI_PROBE=1` and `PS2X_DVCI_Q=1` to the continuous/thread/scheduler flags,
then use `--renderer vulkan --runner ps2EntryRunner-freeze-dvci.exe`.
Claude owns the gameplay reproduction and capture helper. The build has not
been tested in gameplay yet.
