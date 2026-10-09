# Fresh-match arena reset

This supersedes the fixed-span recovery described in NATIVE_PERFORMANCE_CLEANUP.md.
Live tests found the same residue at three different heap addresses. Comparing
it with a changing live stat source is not a valid ownership test.

The guest thread now clears 0x02000000..0x06000000, the exact arena reset by
nativeMatchBoundary. Conditions required before any write:

- Runtime-only completed native teardown receipt and matching previous-owner mailbox.
- Fresh native two-actor manager and ordinary mode, with zero expanded heap bounds.
- Both native actors occupy low-memory storage with identities0/1; no expanded actor storage.

The host requests this before capturing the fresh match. Successful reset
consumes the receipt. Missing/foreign ownership, live bounds, expanded manager
or expanded actor storage refuse without modifying RAM. The strict fresh-memory
precheck remains. No heap-address or stat-content assumption remains.

Actual 128MiB captures tested:

1. prepared-states/20261007-130820-72065da3/00-original-selected-match.bin
2. freeze-captures/20261007-144700-cleanup-refused-3/ram.bin
3. freeze-captures/20261007-150400-cleanup-refused-3-third-match/ram.bin

All recovered; every byte outside the expanded arena remained identical.
All ownership/live-storage rejection checks passed. Evidence:
power-scale-trial/codex-arena-cleanup-check.log; seven host tests also pass.
The later stat-copy writer remains unidentified. Live third-match recovery
still needs confirmation; offline captures establish recovery coverage.

## Launch and performance profile

Root **Play Power Scale native UI Slice.cmd** selects
`repo/build/ps2xRuntime/ps2EntryRunner-arena-cleanup.exe`.
Build log: repo/build/codex-arena-cleanup-build.log.

Append `--profile-interpreter` to this launcher for current hot-page ranking.
Profiling is opt-in and restricted to prepared simultaneous fight phase3 with
input/combat gates cleared, excluding preparation/menu interpreter work. It
prints cumulative per-host-thread rankings about every20seconds and at thread
exit. Close normally to retain final output. Counts identify busy pages, not
CPU cost per instruction; no frame-rate claim follows from them alone.

The new profiling flag does not add another optimization. Live DD602D00 results
were only a modest improvement (whole-fight GAME22, logicrate21.9, guest32.8ms),
far short of50updates/guest<60%. Current ranking is needed to choose safe native
replacements or algorithmic gates; the earlier histogram included obsolete
guest loading code. Baseline comparison remains `--baseline-interpreter`.

Next live sequence:5v5 -> Fight Again -> menu -> training -> menu -> FFA in one
process, checking successful arena cleanup for each fresh match. HUD settings,
the FFA Ready/Fight sequence and extended-character crash diagnostics are
separate outstanding requests from the latest COLLAB notes.
