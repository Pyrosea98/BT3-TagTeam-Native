# CPU tactics — initial source audit, 2026-10-08

Requested order: transformation eagerness, revival, fusion. No CPU tactics are
enabled or packaged yet. This report distinguishes verified entry points from
the native decision logic still needing analysis.

## Transformations

`npc_transform_policy.py` wraps native eligibility **0x2033C8** and initiation
**0x203610**, through the existing ordinary-form/cinematic admission chain.
It authenticates the actor and its current CPU flag at actor+0x1278, preserves
human control/takeovers, applies global and per-character restrictions, then
either rejects or continues into the native routine. The chance setting is
already 100% by default: it is an admission throttle, not an AI action weight.
Raising it cannot make a CPU initiate more transformations.

The throttle holds its roll stable for 64 combat updates, so repeated native
eligibility retries cannot defeat a low configured chance. Ordinary commands
99–103 and actions 236–240 follow this form chain. Fusion commands use a different
chain and must remain separate.

A scan of direct JALs in the original ELF finds eligibility callers at
0x2035C0, 0x208E5C and 0x20ABC4, and initiation callers at 0x204990/0x2049C0/
0x2049F0/0x204A20. Disassembly verifies that 0x208E5C obtains a form slot through
0x20E158 before checking eligibility; 0x20ABC4 searches up to four destinations
through 0x20E180 and then checks eligibility. The 0x2049xx callers check and
consume native commands 0x116–0x119 before initiating slots 0–3. These are useful
entry candidates; their callers and AI scheduling semantics are not yet proven.

Next implementation should bias/request an available native form at a bounded
decision cadence, while retaining eligibility, stock costs, action/scene guards,
reload ownership and user restrictions. It must not write a transformed model or
force a resource swap. The active roster overlay already supports 253 current IDs,
destinations and override/giant table slots. The original fallback module supports
161; it is not the module used by the roster launcher. The giant classification
entries themselves still derive from the original USA size-class audit; expanded
destination classification needs checking before extending automatic tactics.

## Revival

`teammate_revive.py` explicitly excludes CPU-driven actors from starting a
channel and requires current human seat ownership (including takeovers). CPUs
therefore cannot initiate this mod's revival today. The retained native KO/get-up
dispatcher performs the revival once its request is accepted; no native CPU
revival planner has been identified.

A CPU planner needs approach/navigation and a safe channel intent, sharing the
existing proximity, stock cost, interruption, retained-corpse, recovery and
double-charge guards. Removing the human check alone would let passing CPUs
channel indiscriminately and would not implement deliberate movement or safety.
Keep CPU control ownership unchanged. Inspect movement/command scheduling before
choosing a hook; do not give CPUs synthetic human-seat ownership.

## Fusion

`multiplayer_fusion.py` already resolves eligible native recipes and permits a
CPU partner through the ordinary native fusion path. A human partner requires
the existing R3 consent edge. Its timer/commit pipeline authenticates both actor
identities, life, idle actions, current resources, eligibility, and consumption.
Thus CPU participation is supported; autonomous eagerness is not implemented.
The broad statement “CPUs cannot fuse today” in the spec needs this qualification.

The planner can request a reviewed recipe through this existing path. It must
never invent a committed row, consume a partner without native acceptance, or
replace human consent with a CPU timeout. The source requires a real initiating
human pad when establishing a human consent request; CPU-initiated requests to
humans therefore need a dedicated authenticated request entry that retains the
recipient's R3 confirmation. CPU/CPU requests can retain native eligibility and
BEGIN/COMMIT. Actual native autonomous fusion decision timing remains unproven.

## Implementation scope

- Default Off, independent allied/enemy scopes, Native/Aggressive/Relentless
  presets, EN/ES CPU tactics page, settings captured at preparation.
- Training retains its existing CPU behavior settings.
- Evaluate outmatched/nearby-corpse/partner decisions at a few Hz with bounded
  actor scans. Recheck native safety immediately before committing a request.
- Test human/takeover exclusion, expanded forms and giant/character restrictions,
  paused/cinematic states, stock costs, refusal/consent, corpse ownership, and
  rematch cleanup on actual captures before live acceptance.

Feasible through the current authenticated action services, with additional AI
planning hooks. Native decision scheduling and CPU navigation require further
analysis; this initial audit is not an implemented behavior change.

## Implementation review update

The current production preparation chain installs `cpu_retaliation` for bounded
damage-driven target switching, and optionally installs `npc_transform_policy`
and `teammate_revive`. The roster overlay, not the original fallback copies, is
authoritative. CPU retaliation observes actual CPU flags and opposing damage;
it is not transformation, revive, or fusion planning. Transform policy applies
globally to current CPU actors on either side; it has no allied/enemy tactics
scopes or difficulty preset. Revival still requires current human ownership.
No `cpu_tactics` module/page/settings or action planner is wired into preparation.
The requested three behaviours therefore remain unimplemented. No CPU behaviour
changes were made during this review.
