# First native feature trial

Build: `repo/build/ps2xRuntime/ps2EntryRunner-native-targets.exe`

SHA256: `D232093AE09E1B3AD19F0005A2FCC7908B7AA46176EF729B16876ED5FC85E48C`

Launch **Play Power Scale native targets test.cmd** after the current Claude
session closes. It selects Vulkan, bulk snapshots, roster/rematch support,
`PS2X_NATIVE_TARGETS=oracle` and interpreter profiling. Do not connect an
additional PINE client during preparation or gameplay.

## What moved

Four leaf functions: COUNT07368000, PHYSICAL07368200, LOGICAL07368600 and
RESOLVER07368800. Their guest bodies are compiled into ordinary C++ branches
at developer build time. There is no runtime opcode decoder or compilation.
Reviewed capacities3/5 and team/FFA resolver variants are frozen. Every entry
requires exact agreement with its entire guest code body; changed/unsupported
code follows the original interpreter. Live MODE/PAIR/POINTERS/TABLE data,
GP/registers and native fallback destinations are preserved.

This is the first M4 feature. Python still prepares the match and supplies the
remaining guest features. No claim of M3 completion or a Python-free installer.
Dead-target selection behaviour is intentionally the existing oracle behaviour;
Claude's diagnosis must inform a separate native behaviour change.

## Evidence

`codex_check_target_pack.cmd` compiles the same generated pack into a test DLL.
An independent Python MIPS executor compares1600 randomized cases: all128-bit
GPR contents, exit PC and stack writes, gate publication/manager mismatch,
capacity bounds, both pair aliases, logical lookup and native fallback.
Altered bytes and an interior entry reject without execution effects.

Live oracle mode runs the first64 calls of each entry through native C++ on a
copied CPU context, restores its only written RAM area (three temporary stack
words), and executes the original body through the real interpreter. It compares
GPRs, exit PC and those stack bytes. A mismatch logs `ORACLE MISMATCH` and stops
the trial. Subsequent calls use native code. This bounded sample is NOT full
coverage of all match states. Normal mode `PS2X_NATIVE_TARGETS=1` omits comparison;
`0` disables the feature. It is disabled by default in all runners.

Expected logs: `oracle PASS entry=N samples=64; continuing native`, and shutdown
`[native-targets] entry=N native=... oracle=... signature_fallback=...`.
Compare equivalent fight `[logicrate]` and interpreter histogram windows with
bulk748AF28E; do not infer a speedup from the15% instruction share alone.

## First live comparison requested from Claude

After your portrait/target diagnosis session ends, run one ordinary simultaneous
match with this launcher. Confirm menus/selection/preparation, targeting/melee/ki
behaviour and the oracle messages, then close normally for counters/profile.
Because getter alias semantics are touched, include a pair-scoped interaction
only if convenient; no new exhaustive rematch/defusion campaign requested.
Keep existing same-roster bulk logs as the baseline. Any target probe must share
the controller connection or use captured state; no second live socket.

## Next migration

### Target reader diagnosis v2 (after Claude20:10)

**Play Power Scale target readers test.cmd** selects the new
`ps2EntryRunner-native-target-readers.exe`. It preserves the first trace executable
and adds queue-at-press (wide AND legacy arrays explicitly labelled), timeout,
periodic human snapshots each60 lock-on updates, candidate inventory and actual
consumer pointer/HP-read observations. Snapshot rejection reasons are labelled
as predictions; the instruction-level consumer observations identify the actual
candidate inspected. No retarget policy changed.

`native-leader-getter-read` logs physical-getter caller sites requesting a leader
while a human table selects an extra. Those calls also serve rendering/iteration;
they are candidates, NOT proof of an aim reader. A bounded hash table rate-limits
them before scanning human state. `resolved-target-read` observes the actual
return from the relocated base resolver at07784400 beneath the contact/throw/
beam/dash wrappers; includes returned actor, original caller site, table agreement
and contact-context activity. This does not trace all direct inline manager reads
or prove that paired participant IDs3732/3736 are a generic cached lock pointer.

`codex_audit_target_readers.py` inventories103 manager loads and236 native physical
getter calls from the local ELF, with disassembly and27 routed block spans in
`power-scale-trial/native-target-readers.json`. Manager reads can access stats,
resource tables and iteration; do not route all of them as opponents.

First trace live logs: all four initial64-sample oracle checks passed. The three
getter entries recorded millions of native calls and zero signature fallbacks.
The base resolver entry recorded556141 signature fallbacks because multi_contact
replaces07368800 with a jump; extra_throws keeps the base body at07784400.
The wrapper chain remains interpreted and was not migrated by the initial pack.

### Target diagnosis trial (added after Claude19:40)

Use **Play Power Scale target trace test.cmd** after the previous session closes.
It selects the separate `ps2EntryRunner-native-targets-trace.exe`, retains native
oracle mode and sets `PS2X_TARGET_TRACE=1`. No additional PINE client. The original
native-targets and bulk executables are preserved. See the latest COLLAB entry
for this build's hash.

The C++ observer retains the last256 event lines and emits each event immediately
to runner.log. It reads only bounded guest data and never changes target selection,
input or damage. Human means actor+0x1278 is ZERO. Target/blocked-state snapshots
are sampled once per installed lock-on update counter, not per getter invocation;
transient changes between those samples may be missed.

`press-edge` observes the actual `LW t4,328(t1)` after the guest's real pad resolver,
including co-op/quad routing. Logs raw/previous inputs, configured button mask,
L3/bound edges, source PC, hold timing, paired/pending and camera observations.
It does not assume R3, a15-update gesture, or which variant the user's settings
selected. `press-outcome` reports the target and per-actor switch-counter change
at the next observed update. No immediate switch is not proof of rejection: the
request may remain queued. `target-change` includes new target HP/present/action;
`blocker-over-30-updates` reports persistent paired/pending values, once per episode.

First test: fire at a living locked opponent, kill that opponent, tap your configured
L3 switch, then fire at the next opponent. Preserve the trace lines and say whether
the displayed lock changed and whether blasts recovered. Native baseline oracle
and this trace may share one game session. Trace-on performance is diagnostic;
do not use it as the native speed benchmark. Trace is OFF by default.

`codex_check_target_trace.cmd` validates actual edge/outcome records, zero=human,
30-update duration rather than call count, stale pointers/manager/reset handling,
read-only memory and the256-event ring bound.

Native lifecycle observation and the native loading cover. Publish a versioned
generation/phase/progress/roster snapshot at a game-thread boundary, consume it
through the existing host UI renderer, and extract logo/portrait art locally at
install time. Reuse the renderer UI path used by `PS2SettingsOverlay::draw`,
which already participates in native Vulkan presentation. The cover must retain
release acknowledgement and error/lease semantics before replacing the guest
cover; no independent renderer-thread reads of mutable actor objects. Approved
layout: game logo, all portraits, VS and seven Dragon Balls on the progress bar.
The cover is not implemented in this trial.

Regenerate developer artifacts with `codex_freeze_target_pack.py` when reviewed
oracle generators change; unsupported opcodes fail generation. Build through
`codex_build_freeze_diagnostic.cmd ps2EntryRunner-native-targets` into this
dedicated output. Existing bulk and stable executable hashes are unchanged.
