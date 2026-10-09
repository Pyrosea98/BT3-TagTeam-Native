# Interpreter performance and fresh training cleanup

## Ready build

`repo/build/ps2xRuntime/ps2EntryRunner-performance-cleanup.exe`

SHA256 `DD602D0014722169FB60B74711392A28194871B95454FB1D699DA78DA7503669`.

The existing root **Play Power Scale native UI Slice.cmd** selects this build.
The three stable runners retain SHA256 `4052022DFE11DED8F98A47F8EACEA75D0EEAD9BC87F5F620853461E5CF79756D`.

## Performance implementation

The real interpreter caches up to 32 consecutive instructions in patched caves
and hot ELF pages 0x1CE000..0x1DB000. Cached runs avoid repeated dispatch,
native-hook and control-flow decoding checks. Each instruction word is freshly
read before executing: guest stores, PINE writes and rematch replacement can
invalidate code without a write notification. Branches, delay slots and native
entry points retain the existing dispatch path. Active instructions are copied
locally so a yielding guest fiber cannot replace the code being executed.

The headless test executes the actual interpreter. It covers integer, float and
128-bit memory parity, loop/delay slots, self-modification of the next instruction,
return PCs inside blocks and annulled branch-likely delay slots. Cache tests also
check boundaries, collisions and control-flow exclusion.

Five alternating samples of a 690001-instruction loop: baseline median **12.356 ms**,
blocks **6.694 ms**, **1.846x** faster. This is an isolated interpreter benchmark;
live 5v5 update rate and the 50-update/guest-under-60% goal remain unmeasured.
Hot ELF AOT replacement is not implemented in this slice.

For a live comparison, launch the same trial with `--baseline-interpreter` to
disable only the block execution cache. Keep teams, stage and other settings
the same. Existing native target replacements remain enabled in both paths.

## Training cleanup

The actual failed 5v5 -> menu -> training capture has an otherwise unused
expanded heap and an exact copy of 0x0056D350..0x0056D880 at
0x02E03B50..0x02E04080. Recovery requests native mailbox state8 **before** the
original fresh-match snapshot/preparation hold. The guest thread checks:

- Its own completed-teardown receipt and the previous manager mailbox identity.
- A native two-actor manager, ordinary team mode and zero expanded heap bounds.
- Every expanded heap byte outside the known copy is zero.
- The known copy is either zero or byte-for-byte equal to the low-memory source.

Only the 0x530-byte copy is cleared; state9 returns success or a refusal reason.
Success consumes the runtime receipt. Failed checks change no heap data. The
strict unused-heap preparation gate remains. State8/9 are reserved during this
transaction, and a timeout never cancels an in-flight native write.

The host feature flag is set only by this matching trial launcher. Older runner
launch paths make no new request. Seven host tests cover success, refusal,
first match, old runner compatibility, timeout, busy state and snapshot order.

The compiled recovery was tested on the **actual failed 128 MiB capture**:
only the known span changed; every other RAM byte remained identical. Missing
receipt, foreign owner, unknown heap bytes and a changed copy all refused.
The unidentified writer is not repaired; this recovery is intentionally limited
to the observed stat residue. Live 5v5 -> menu -> training still needs confirmation.

## Evidence and next live test

- Build log: `repo/build/codex-performance-cleanup-build.log` (exit0).
- Real runtime checks/benchmark: `power-scale-trial/codex-performance-cleanup-check.log`.
- Cache checks: `power-scale-trial/codex-interp-block-check.log`.
- Host checks: `codex_training_cleanup_check.py` (7 PASS).

Test a 5v5, Fight Again, return to menu, then Modded Training in the same session.
Record steady-fight GAME/logicrate/guest_ms/guest_pct from the runner log, and
check training hits/reset. No game was launched or controlled for these checks.
Transformation changes are excluded per the user's finding that the ISO causes
that error.
