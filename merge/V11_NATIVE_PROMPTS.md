# v11 native prompt audit

The v0.2 local merge can reuse the existing native UI design. This audit does
not change the published v0.1 installer or enable new gameplay features.

| Surface | Current route | Native adaptation |
| --- | --- | --- |
| Beam-assist hint, multiplier and failure captions | `beam_struggle.py` draws outlined guest text per viewport | Use the existing fusion/revive prompt typography and player-local placement. Retain eligibility, assist count, caption lifetime and EN/ES text. Native rendering remains pending. |
| Attacker warnings and target marks | `lockon_threat.py` emits guest graphics | Match the native overhead indicators, including viewport projection and human owner. Native rendering remains pending. |
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
remain uncovered. Battle prompt rendering requires runtime implementation and a
visual gameplay check; this audit does not claim that acceptance.
