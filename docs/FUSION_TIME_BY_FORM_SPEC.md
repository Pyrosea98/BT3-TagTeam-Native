# Fusion time by transformation (user idea, 2026-10-08)

Owner: Claude (spec), Codex (implementation). Low priority, after the installer. Builds on `FUSION_CONTROL_SPEC.md`. Only Fusion Dance fusions are timed today (`fusion_duration_*`); Potara/preselected fusions (Vegito etc.) stay permanent.

## User idea
A timed fusion (Gogeta, Gotenks, ...) keeps its normal time (default 100 s) in base form; each transformation shortens it: SSJ1 -10%, SSJ2 -20%, SSJ3 -30%, SSJ God -40%, SSJ Blue / SSJ4 -50%. Going SSJ1 -> SSJ3 directly is hard to account for ("how much to take back"). Whatever time is left, the fusion must still be able to transform, even if only 1 s remains.

## Recommended model: a fusion "life" fraction that drains faster per form (no subtraction, no refunds)
- Keep one value `life` from 1.0 (start of the fusion) to 0.0 (defuse). Each second it drops by `rate(form) / T`, T = `fusion_duration_seconds`.
- `rate(form) = 1 / (1 - reduction)`: base 1.00, SSJ1 1.11 (-10%), SSJ2 1.25 (-20%), SSJ3 1.43 (-30%), God 1.67 (-40%), Blue/SSJ4 2.00 (-50%). So a full fusion held in SSJ2 would last 80% of T, in Blue 50% of T, and a mix lasts exactly the weighted sum.
- **Any path works with no extra rule:** SSJ1 -> SSJ3 just changes the rate from then on; reverting (de-transform) lowers the rate again; nothing is "taken back" or refunded. The time already spent stays spent.
- **Always allowed to transform:** the transform is never blocked by the timer. The timer pauses during the transformation cinematic (already the case for cinematics) and after it completes `life` is clamped to at least 1 s worth (1.0/T) so the player gets at least one second in the new form; the fusion then ends normally when `life` reaches 0.
- Permanent fusions (no timer) ignore all of this; characters with no matching form tier use rate 1.00.
- **Form tiers:** map by transformation rank, not by name: tier 1..5 = the game's own transformation steps of the fused character (Gogeta: SSJ, SSJ4, Blue by id; Gotenks: SSJ, SSJ2, SSJ3). A small table `fusion_form_tiers.json` per character id/transformation id -> reduction (default by order: 10/20/30/40/50, configurable). Unknown forms: use the tier by their order of appearance.
- **Settings (Fusion page, EN/ES):** `fusion_time_by_form` On/Off (default Off so current behaviour stays), `fusion_form_penalty` preset: Mild (5-25%), Normal (10-50%, the user's numbers), Heavy (20-70%).
- **HUD:** the existing fusion arc shows `life`; its number (under 10 s) shows projected seconds at the current rate; a small tick/colour on the arc shows the current drain (gold normal, orange when faster); no pop-ups or "-10%" text unless the user asks. Defusion/Fight Again resets.
- **Acceptance:** offline: path tests (base, SSJ1, SSJ3 directly, back to base, Blue with 3 s left, 1 s floor after transform, pause/cinematic, permanent fusion untouched, 2 humans and any seat pair); live later with Gogeta and Gotenks.
