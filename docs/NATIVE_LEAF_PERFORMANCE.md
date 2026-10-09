# Native hot helpers and current profiling

This performance slice retains the generic arena cleanup and previous UI fixes.
It replaces guest interpretation for seven more audited helper functions:

| Entry | Helper |
| --- | --- |
| 077C4000 | Inactive-actor update eligibility |
| 070B0400 | Revival lifecycle/eligibility gate |
| 070B1000 | Revival actor/HP-row lookup |
| 07260000 | Watched-fighter HUD resolver, standard and quad variants |
| 071A0000 | Multi-contact eligibility gate |
| 07243000 | Beam-clash eligibility gate |
| 07180000 | Dash-clash eligibility gate |

It also handles the combat resolver continuation at07368808. The actual5v5
capture has a contact-wrapper jump at07368800, so the earlier full-body native
resolver signature does not match. The continuation is unchanged and matches
its generated body exactly. Native handling begins only when those wrappers
have reached the continuation; their collision/clash/context semantics remain.

All bodies are generated C++ control flow from the existing Python byte emitters.
Every selected body is checked against actual guest code bytes. Unknown bodies
remain interpreted. Live manager/participation/HP/action/HUD state is read on
each call. No poll throttling, approximate proximity filter or feature skipping
is introduced. New instruction support includes variable shifts, signed compare,
AND/NOR, signed32addition,32-bit stores and full128-bit stack saves/restores.

## Checks

- 4800 independent MIPS/Python-vs-generated-C++ comparisons across30 capacity3/5
  variants: full128-bit registers, return PC, stack bytes and HUD control writes.
  Changed code and interior PCs refuse without execution.
- Production native adapter oracle uses the actual runtime interpreter, including
  full register/stack/HUD comparisons. The headless --native-leaf-self-test route
  applies this to704 cases/11 entries on a real saved5v5 roster.
- Runtime builds use a separate ps2EntryRunner-native-leaf-performance.exe.
  Evidence logs: codex-native-leaf-check.log and codex-native-leaf-runtime-check.log
  under power-scale-trial; build log under repo/build.

Live improvement is unmeasured. Previous block-cache live results were only
about22 fight updates/s; the50-update/guest-under60% goal is not met or claimed.

## One profiling run

Double-click root **Profile Power Scale 5v5.cmd**, prepare the same5v5 roster and
stage, then fight for2–3 minutes with ordinary attacks, movement and ki blasts.
Close normally. The launcher enables fight-only interpreted-page profiling and
summarizes the current log into runner-fight-profile.json. Rankings also print
every20seconds, so analysis can begin while a fight is running.

Use **Play Power Scale native UI Slice.cmd** for normal play without profiling.
Append --baseline-native-leaves to either launcher to disable these seven new
helpers and the resolver continuation, retaining existing target getters and
block caching. --baseline-interpreter independently disables block caching.

The fresh profile determines the next native/algorithmic work. Instruction
counts measure work volume, not time per instruction. Larger collision/pair,
revival-channel, special-move and dirty ELF routines remain guest interpreted.
They need their actual control/ownership side effects audited before skipping
loops or translating them. Safe native helper work can proceed before a new
profile; choosing the largest next bottleneck needs current fight evidence.
