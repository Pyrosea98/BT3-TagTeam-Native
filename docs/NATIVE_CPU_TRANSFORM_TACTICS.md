# CPU transformation tactics — first slice

Implemented 2026-10-08. Live animation/resource completion is not yet accepted.

## Try it

Use the existing `Play Power Scale native UI Slice.cmd` launcher. It selects
`repo/build/ps2xRuntime/ps2EntryRunner-cpu-transform-diagnostics.exe`.
SHA256: `6c8b08a5a947e2ba475463a65ac63519e827ea3e4dfa800ef65587c406f8dfa0`.
The installer has not been restaged. Stable original/OpenGL/Vulkan runners are unchanged.

Settings → CPU tactics / Tácticas de CPU:

- Allied CPU transformations: Native / More often / When outmatched.
- Enemy CPU transformations: Native / More often / When outmatched.
- CPU tactics difficulty: Native / Aggressive / Relentless.

Both scopes default to Native, leaving existing AI unchanged. The preset alone
never enables assistance. Allies are the first seated player's team; FFA CPUs
are enemies. A takeover immediately excludes the human-controlled fighter.
Settings apply to a newly prepared match; Fight Again retains its match settings.
Training emits no planner and retains `training_cpu_behavior`.

## Native decision and execution

Native input dispatch201CFC calls2034F0 only after the transform-input bit is
present. The existing2033C8 chance policy is a veto, not an eagerness mechanism.
The new bounded EE planner executes after the existing match frame continuation.
It scores at3Hz, uses actual actors, HP rows and CPU flags, excludes absent or
consumed fighters, and only attempts at authenticated idle11/15 with no pending
hits/actions. It pauses with preparation, battle pause and shared cinematics.

Selection calls the exact installed eligibility wrapper with `(actor,slot,1,1)`.
Only an accepted slot goes through the exact installed initiation wrapper.
This follows the ordinary2033C8/203610 path, including native stock checks,
NPC exceptions/chance/giant policy, cinematic admission and serial reloads.

**Runtime finding:** invoking the low native entry directly in the diagnostic
interpreter could take compiled dispatch without executing its installed NPC
wrapper. The planner therefore binds the authenticated jump destination present
in each native entry at preparation, rather than relying on low-entry dispatch.
Those targets and the complete planner are authenticated by dependency checks.
No generic change to existing native dispatch was made in this slice.

The scripted20AB60 request uses eligibility with stock checks disabled and can
increase stocks to the requested cost. It is not used. The planner never writes
stocks, actor models or transformation actions.

## Outmatched score

- +2: target's remaining HP percentage exceeds CPU's by at least25 points.
- +1: CPU below50% HP.
- +1: target has at least20000 more ki units.
- +1: CPU lost HP since its previous evaluation.
- +2: target has a higher reviewed form tier, only when both IDs are known.

Native/Aggressive/Relentless thresholds are3/2/1; successful-start cooldowns
are nominally8/5/3 combat seconds. One accepted start per evaluation preserves
resource serialization. Pauses stop evaluation and cooldowns.

The reviewed tier table includes Gotenks/Gogeta plus captured Power Scale Goku
(Fin), Vegeta, kid Trunks and Goten forward forms. Unknown IDs contribute no tier
score. Positive-cost forms rank by reviewed same-family tier where known,
otherwise by native stock requirement. Zero-cost forms are allowed only for a
reviewed same-family tier increase; unknown zero-cost forms and reverts are
excluded. All candidates still need native eligibility and initiation approval.
More often does not use the outmatched score threshold.

## Diagnostics update

The native runner reads guest telemetry at3Hz, logging each actor on observed
reason/start changes and every3s. Lines show scope, score components, unknown
tier status, slots/costs, native candidate eligibility, stocks and rejection
reason. Per-match summaries count starts by side (FFA counts all as enemies).
Policy hints only refine native vetoes where current authenticated policy or
stocks support that explanation. Successful initiation is not proof of animation
or resource completion. Native fusion commits are observed separately; this
slice has no fusion-choice planner.

The kids' live captures have zero-cost SSJ slots (46→47 and44→45), explaining
why the earlier slice excluded them. Goku/Vegeta also have free SSJ1/2; the old
slice considered their cost-bearing SSJ3. Existing logs cannot explain the exact
delay or the autonomous Vegito choice. This update adds evidence for future runs.

Exact guest mod text now also uses the released prepared-match/core/feed lease,
so temporary invalid actor HUD snapshots or missing presentation acknowledgement
do not restore scrambled text. Full byte guards remain required. Offline CPU/
human combinations and both styles pass; visual live confirmation remains open.

## Evidence

`codex_check_cpu_tactics.py` / `power-scale-trial/codex-cpu-tactics-check.log`:

- Actual production MIPS scoring/selection: best known eligible form, fallback,
  veto, human/takeover exclusion, allies/enemies, HP/ki/tier/recent loss,
  3Hz cadence, cooldown, pause, consumed/dead/stale actors and manager leases,
  prior frame continuation and HI/LO. Native boundaries are explicitly stubbed
  for these deterministic decision checks.
- Separately executes actual installed native eligibility: no-stock refusal,
  funded acceptance, per-character/global/chance/giant-policy vetoes.
  Giant-policy case deliberately classifies the fixture destination; it does
  not claim new expanded-ISO giant classification evidence.
- Actual production planner → installed guards → native initiation selects
  Goku's permitted slot1. Animation/resource completion needs live play.
- Native defaults and Training exclusion; setting validation and EN/ES page;
  actual production rematch cleanup clears the new reservation.

`codex_check_quad_rematch_cleanup.py --cpu-tactics --fusion-form` /
`power-scale-trial/codex-cpu-tactics-preparation-check.log`:

- Actual second co-op preparation,905 blocks, with CPU settings, existing NPC
  giant restrictions and timed form-life enabled.
- Existing quad/fusion dependency validators accept the exact CPU wrapper and
  reject changed planner code. Current timer/quad programs remain authenticated.

No game boot, PINE connection or live controller simulation was used.

## Live checklist for Claude/user

1. New2v2 or3v3, one human plus CPUs with available ordinary transformations.
   Set both scopes More often, Aggressive. Check ally and enemy transformations
   complete with normal costs and all actors remain interactive.
2. Set one scope Native and the other More often; check scope isolation.
3. New match: When outmatched, Aggressive. Damage a CPU or give its target a
   clear HP/ki advantage; check it prioritizes an eligible form at a safe idle.
4. Verify Fighters restrictions/chance still veto; then restore usual settings.
5. Fight Again, then return to selection and prepare another match. Check CPU
   settings retained on rematch, fresh actors on selection, no normal-tag fallback.
6. Training remains unchanged. Normal close should finish quietly (source fix).

CPU revive/navigation and autonomous fusion are the next separate slices.
