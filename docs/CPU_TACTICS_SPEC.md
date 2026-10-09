# CPU tactics: transform more, fuse, revive (user request 2026-10-08)

Owner: Claude (spec), Codex (feasibility + implementation). After the installer restage. For BOTH allied CPUs and enemy CPUs (separate scopes).

## What exists today (from `mod_settings.py` and the page help text)
- Fighters page: CPU transformations can be disabled globally, into giants disabled, a chance limit, and per-character exceptions. "Humans, fusion and Body Change are unaffected": CPUs do NOT fuse today.
- Revival page (`revive_enabled`, cost in blast stocks, channel seconds, radius, ring): teammate revival is a HUMAN mechanic (stand near the fallen ally and channel). CPUs do not revive anyone as far as we know (UNKNOWN: please check).

## Requested behaviour
1. **Transform more often / smarter:** when the CPU's opponent looks stronger (higher transformation tier, more HP/ki, or the CPU is losing), it should prioritise transforming (and use the best available form) instead of waiting for the native random chance. Options: Native (today) / More often / As soon as possible when outmatched.
2. **Fuse:** a CPU with a valid Fusion Dance partner (ally CPU, or an ally human who accepts) should fuse when conditions are met (partner alive and near, ki available, fusion allowed for that pair, not already fused), preferably when outmatched. Options: Off (today) / Allies only / Allies and enemies.
3. **Revive allies:** a CPU should walk to a fallen teammate and revive them with the same rules as humans (stock cost, channel time, radius, safety), when the area is safe enough. Options: Off / Allied CPUs / Enemy CPUs / Both.
4. Each behaviour has separate toggles for allied CPU and enemy CPU, a "difficulty" preset (Native / Aggressive / Relentless) that tunes thresholds, EN/ES strings, a new "CPU tactics" settings page, applies at the next match. Training mode keeps `training_cpu_behavior`. Never break native move rules, transformation exceptions or giant restrictions (they still override).

## Work plan for Codex (feasibility first)
A. Report how the game's CPU AI decides to transform today (guest code, state machine, the "chance limit" hook) and where a priority/force hook can be attached safely; same for starting a fusion and a revive for a non-human actor (what inputs do humans' R3/revival produce and can the mod inject the same for a CPU actor).
B. Implement in this order: (1) transform eagerness + outmatched trigger, (2) CPU revive, (3) CPU fusion, each behind its own default-Off setting, with offline tests on captured states and a live checklist.
C. Keep performance within the budget (no per-frame heavy scans; compute the "outmatched" score at most a few times per second).

## Addendum (user, 2026-10-08, live observation)
- Enemy CPUs Goku + Vegeta fused on their own into **Vegito** (Potara/permanent fusion). The user would like the CPU to pick **either** Vegito (Potara) **or** Gogeta (Fusion Dance) for the same pair, not always the same one. It is UNKNOWN whether the game's native pick is fixed; Codex to check the native choice code.
- Slice 3 requirement: when a CPU pair has more than one fusion option, choose among the valid options randomly or by preset (setting `cpu_fusion_choice`: Native / Random / Prefer timed Dance / Prefer permanent Potara). Respect fusion exclusions per character pair; HUD indicators follow the fusion type: timed Dance fusions show the fusion arc (and form-drain), permanent fusions show no timer by design.
