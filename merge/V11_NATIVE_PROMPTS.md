# v11 native prompt audit

The v0.2 local merge can reuse the existing native UI design. This audit does
not change the published v0.1 installer or enable new gameplay features.

| Surface | Current route | Native adaptation |
| --- | --- | --- |
| Beam-assist hint, multiplier and failure captions | Upstream draw gates publish their selected localized text slot | Native glass/gold caption chip per human viewport. Eligibility, assist count, caption lifetime and EN/ES text remain upstream-owned. |
| Attacker warnings and target marks | Upstream camera gates publish admitted masks and marker style | Native overhead ring/hexagon, chevrons and border warnings. Guest rendering stays available when native projection coverage is incomplete. |
| Settings/menu rows | Existing native menu adapter | Reuse the current menu layout; unsupported emulator-only controls remain hidden. |
| Structured preparation failures | v11 passes `error=(first, second)` to `Presentation.show` | Adapter now accepts the argument and selects the existing native failure cover even for localized messages. Detailed text is logged; the cover still displays its existing generic localized failure message. |

## Implementation boundaries

- Read beam/target state from its gameplay owner; preserve upstream conditions
  rather than infer eligibility from a displayed caption.
- Route battle prompts to the correct human and viewport, including co-op.
- Suppress the old guest emitter only when the native renderer supports that
  prompt, so fallback builds do not lose it and supported builds do not duplicate it.
- Keep native panel scale/opacity and EN/ES selection consistent with the existing HUD.
- A late preparation diagnostic must not reopen a loading cover over an accepted
  or released match. The structured-error adapter preserves that guard.

## Verification

`tools/codex_check_v11_error_cover.py` exercises the real presentation adapter
with a localized structured failure and confirms that accepted/released matches
remain uncovered.

Rendering is implemented on runtime branch `v02-v11-native-hud` with isolated
runner `ps2EntryRunner-v02-v11-hud.exe`. The local merged controller branch is
`v02-v11-local`. Pair these sources: the released v0.1 runner does not implement
the new presentation probes.

- `codex_check_v11_prompt_emission.py`: both actor capacities assemble; code and
  presentation allocations do not overlap; original fallback stub ABI retained.
- `--native-v11-prompts-self-test`: manager/actor ownership, stale rows, exact
  draw-code authentication, projection fallback, and interpreted fallback PASS.
- Eight Vulkan captures reviewed: EN/ES, full/split/quad views, off-screen
  warnings and ultrawide layouts. Private output is under
  `experiments/v11-local-validation/hud-captures`.
- No live beam-assist/targeting gameplay acceptance yet. New gameplay options
  remain off by default; native rendering does not enable them.

Local trial: `experiments/v11-local-validation/Play v0.2 native HUD.cmd`. It uses
the merged sandbox controller and the new runner, with the shared game lock and
existing read-only disc/native UI assets. Installed/released launchers are unchanged.
