# Upstream Tag Team Mod Version 11 merge (branch upstream-v11-merge)

Three-way merge per module: base = upstream beta.32 as installed, ours = native controller, new = upstream Version 11 (CRLF normalised to LF).

- Added from upstream (new modules): 56 (12 are PCSX2-only and unused by the native build)
- Taken from upstream unchanged (we had not touched them): 72
- Merged cleanly: 9
- Conflicting modules resolved by hand: 18 (see merge/conflicts/*.diff3 and claude_resolve_conflicts.py for the per-hunk choices)
  - ours kept: extra_reload_*, extra_special_pools, fusion_partner_lifecycle, guest_loading_screen, quad_controller, quad_menu_input, team_assignment, native_mode_menu (hunk 1)
  - both sides combined: display_settings, feature_preferences, fresh_team_trainer, localization, controller_assignment, autopilot, mod_settings, game_profile (upstream block plus our POWER_SCALE_* lines), native_mode_menu (hunk 2)

Checks: every module parses; no conflict markers remain; import matrix on the merged tree has no new failures caused by the merge.
The 15 extra import failures versus the baseline are environmental only (the repo has no game-derived `analysis/SLUS_216.78`, and PySide6 is not installed); they are not merge errors.

NOT done: no live run. The merged tree has not been exercised in game, and the live workspace and `main` are untouched.
Before merging to main: run the 20 native checks, then a live match with fusion, lock-on settings and the settings screens (mod_settings was hand-edited).
