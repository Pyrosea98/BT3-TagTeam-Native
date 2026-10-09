# Optimizations from the current fight profile

The 613M-instruction5v5 profile names the next concrete work. It also confirms
that the previous seven helpers did not solve busy-fight performance: about20
fight updates/s and35.2ms guest time remain the latest measured results.

## Corrected mapping and this build

| Profile page | Interpretation | New native work |
| --- | --- | --- |
|070F0000,10.59%|giant model/actor lookup|both helpers translated|
|070F6000,5.89%|giant hurt-box wrapper|its model lookup is native; wrapper remains guest|
|07784000,5.88%|throw resolver/fallback chain|calls translated lookup helpers; wrapper remains guest|
|07788000,4.30%|reciprocal paired/rush lookup|translated|
|07781000,2.99%|throw lookup and expiry|translated, including record expiry writes|
|06944000,5.42%|lock-off QUERY/SET and native tails|QUERY/SET bodies translated; tails remain guest|
|073C6000/073C4000|cinematic contact wrappers/gates|identified; remains guest|
|07400000|effect texture guard|identified; remains guest|

Buu's ultimate lives at070E0000..070F0000. The giant pages must not be labelled
as Buu ultimate work. Percentages are old interpreted instruction volume, not
measured CPU cost or expected FPS gain. A page can contain multiple helpers.

Six new exact-signature generated bodies: giant MODEL/ACTOR, throw LOOKUP/
PAIRED_LOOKUP, lock-off QUERY/SET. Current model size classification, roster
identity, reciprocal partner/action tests and flag5 semantics are unchanged.
Throw expiry clears both records and increments its real counter. Unknown bytes
fall back to interpretation; no poll throttling or gameplay skip is introduced.

## Evidence

-6720 independent MIPS/C++ comparisons across42 variants; full128-bit registers,
 PC,80-byte stack,HUD writes and320-byte throw control/record region compared.
-1088 production adapter/actual-interpreter oracle comparisons on the saved5v5
 roster,17entries,64each, zero signature fallback or mismatch.
-Logs power-scale-trial/codex-profile-hot-leaf-check.log and
 codex-profile-hot-paths-runtime-check.log; build codex-profile-hot-paths-build.log.
-Named old ranking: log-archive/runner-native-leaf-5v5-profile-fight-profile.json.
-Function inventory for hot ELF pages: power-scale-trial/codex-hot-elf-functions.json.

The captured function table has overlapping containing ranges: e.g.1C1B20 spans
78,256bytes over many separately generated functions. A page ranking does not
justify substituting a whole range with an unpatched compiled version. Dirty ELF
work must guard actual installed bytes and retain calls to patched descendants.
That recompile/translation remains outstanding, and still accounts for about37%
of the old interpreted volume. This build does not claim the50-update goal.

## Launch / remaining work

UI Slice and Profile Power Scale5v5 launchers now select
ps2EntryRunner-profile-hot-paths.exe. Generic arena reset and preceding fixes
remain. Profile launcher already runs summarization on a separate command line,
even if the game/controller exits non-zero; there is no && in the saved script.

Test same-roster5v5 steady fighting and compare guest_ms/logicrate. Profiling
should show fewer instructions in the translated helper pages; native cost and
wrapper work still contribute to total frame time. --baseline-native-leaves
disables all added helper translations and resolver tail for comparison.

Live cleanup is now confirmed:5v5 -> Fight Again -> training -> FFA10 all passed.
Busy-fight performance needs the new measurement, then dirty ELF and larger
wrappers/loops. OVERHEAD_HUD_SPEC.md is the new HUD direction, queued separately;
no overhead HUD or audio scheduling fix is claimed by this performance build.
