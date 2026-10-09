# Guarded native ELF leaves

The October 7 latest profile attributes 42.7% of interpreted instructions to
patched ELF pages. This first ELF slice translates small integer leaves;
it does not translate those whole pages or claim to eliminate that percentage.

## Implementation

15 original functions in the ranked pages are emitted as C++ (see
codex_target_pack_oracle.json for addresses and exact bytes). Two additional
entries are the intact tails at 001DAC80 and 001DACF0. Their patched headers
continue through the lock-off/extended-flag wrappers first; those wrappers
replay the first two original instructions before reaching the native tail.

An exact comparison of every function/tail byte is required on each call.
Changed bodies remain interpreted. No calls, writes or stack adjustments
are accepted by this first ELF audit; supported branches only move forward.
Interpreter dispatch and block boundaries recognize the new entries. There is
no blanket bypass of the overlapping dirty-function ranges.

## Verification

- 9440 independent MIPS/C++ comparisons across59 total variants (existing
  helper pack plus17 ELF variants), including code-mutation refusal.
- Real128MiB prepared5v5 capture20261007-131331-1c7a1b67/16-ready-held.bin:
  15 eligible installed ELF entries x64 samples =960 production-vs-interpreter
  comparisons PASS; two changed original headers correctly rejected.
- Existing17 helper entries x64 =1088 production comparisons PASS.
- Logs: power-scale-trial/codex-native-elf-independent-check.log and
  codex-native-elf-runtime-check.log; build repo/build/codex-native-elf-leaves-build.log.

## Build / live limits

Both UI Slice and Profile5v5 use ps2EntryRunner-native-elf-leaves.exe.
Generic arena cleanup and prior fixes remain. --baseline-native-leaves
turns off all added leaves including ELF; it is not an ELF-only comparison.
Stable runners remain unchanged. No game was launched by this verification.

Busy fighting remains about20updates/s in the preceding live build.
New-build FPS gain is UNKNOWN. Larger patched ELF routines and wrapper loops
remain interpreted. Overhead HUD, native HUD suppression, audio investigation,
non-team intro and unsupported-PC capture are not delivered in this build.

SHA256: 79B16A12EE978A7626E6CE8A815C5F0D86EBD14E4BDBAEC2D06D2DDC680CF966
