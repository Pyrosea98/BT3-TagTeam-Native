# Range fix and CPU transformation review

## Implemented for the isolated trial

Beam assist base range defaults to 300 and accepts 30..1500. expanded_maps
multiplies the guest distance by two before squaring it. Default effective
range is 600 on expanded maps; maximum is 3000. Existing saved base values
remain valid. The private trial's selected value was explicitly changed from
150 to 300 for the requested wider-range test.

Revival base radius similarly doubles on expanded maps. Its settings cap stays
200 base units; guest validation and native HUD admission now allow 400
effective units. EN/ES help puts effective range and map scale first so the
native help's eight-line limit cannot hide it. No guest code program changed:
only configuration data and the native renderer's radius bound changed.

The live 244..265-distance misses are inside even 150*2; 448 is inside the new
default 600. The 1385..1468-distance samples still exceed the default but fit
the configurable maximum. Wider range does not guarantee assistance while
busy, ahead, unstocked, or outside the scheduling/admission gates.

No start latch was added: widening range directly addresses the user's choice
without changing assist timing or accepting an ally that has left range.

## Other distance consumers reviewed

- Spectator/takeover uses ownership and selected teammate identity, no world
  proximity setting.
- Outnumbered "ganged up" counts living enemies targeting the actor through
  the target table; there is no radius to multiply.
- Lock-on nearest uses distance ranking; uniform map scaling preserves the
  order. Its markers/rings use projected pixel size, not a world-distance cap.
- Fusion control/lifecycle has no configurable mod proximity radius. Native
  eligibility is retained; no arbitrary native assembly limit was patched.
- Camera distance percentages, HUD ring pixels and beam formation spacing are
  not configurable world-unit reach thresholds and are not doubled.
- Expanded ISO builder scales stage geometry/collision/bounds/spawns. It does
  not change the beam struggle executable. Live separation is about 240..253;
  these captures do not establish a 1x/2x change to native clash separation.

## CPU planner: confirmed policy and observed cast

Positive-cost native transformations can be candidates even without a reviewed
tier. Zero-cost candidates require reviewed same-family tiers and strictly
upward progression. Reviewed same-family reverts are rejected even with a
positive cost. Therefore "unreviewed ID" does not mean "CPU can never use it."

| Source | Captured destinations/cost | Result before native admission |
| --- | --- | --- |
| 31 Vegeta | 32:0, 33:3 | 32 blocked by zero-cost review; 33 candidate requiring 3 stocks |
| 34 Vegeta | 35:0, 36:0, 20:1 | reviewed upward candidates; successful live starts reported |
| 60 Vegeta (Super, identified by its Super slots) | 181:0,183:0,184:0,72:0 | all blocked by missing family/tier review |
| 119 Goku (Super) | 76:0,167:0,179:0,83:1 | three zero-cost forms blocked; 83 can be a paid candidate |
| 108 Cell Super Perfecto, 117 Kid Buu | all four destination IDs 255 | no ordinary transformation slots in observed tables |

31/34 labels in the captured Power Scale menu both read "Vegeta[7]"; the era
names "mid/end" are not separately authenticated by that table. Do not swap
them based on their numeric IDs or the user's observed speed of transformation.

Private complete inventory: experiments/v11-local-validation/
cpu-form-review-inventory.json: 30 IDs with reviewed tiers, 223 without, and 48
observed source/destination slots. These are coverage counts, not 223 broken
characters. Full-roster forward-slot census has not been captured.

## CPU family trial implementation after the ranges live test

Beam assist was confirmed live twice by Claude: each struggle recorded one
trigger, confirmation, CPU assist, pose and release, with no busy/blocked/hit
failure. Multiplier effect and further repetition still need acceptance.

Implemented three explicit trial families in cpu_tactics.tables(), scoped to
the exact Power Scale runtime profile: (31,32,33), (60,181,183,184,72), and
(119,76,167,179,83). Runtime names and captured forward slots establish the
proposed upward order. Native admission, stock/chance/giant checks, cooldowns,
reverse-form refusal and cross-family refusal are retained. This activates
the candidates only in the isolated next-version trial, not the public release.
Each family still needs live transform/hold/revert/stock-cost acceptance.

Focused profile/tier checks pass; the production EE planner fixture now tests
free upgrades and reverse/cross-family refusals for the new families as well
as the earlier Black/Vegito cases. The captured native admission/stock/chance
and guarded initiation checks also pass. Actual animation/resource completion
and concurrent actor behavior are not proved by this offline fixture.

The UI catalogue matches portraits/031.png to ID31 and the full label
"8.4M-30M-25M-100M", and portraits/060.png to ID60 and "110.000M". ID34
has "85M-1.250M-100M". ID60's existing mapping is based on name match and
consistent RAM ordering, while ID31's portrait was found verbatim in RAM.
The reported screenshot's "120M" differs from the catalogue's "25M";
the match log establishes the helper's runtime ID31. Era names still are
not explicit in the captured menu strings.
