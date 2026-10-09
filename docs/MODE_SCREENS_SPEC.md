# Every mode, every screen: one build spec

Owner: Claude (design), Codex (implementation). Written 2026-10-07. Builds on `LOADING_COVER_SPEC.md` (done and live-tested),
`DESIGN_LANGUAGE.md`, `GLYPH_ATLAS_SPEC.md`, `UI_ASSET_MANIFEST.md`. User direction: tackle all mode/team-size combinations at the same time now
that the logic exists.

## Key fact (CONFIRMED in the code)

Every mode uses the same two-column selection (`battle_mode_policy`: up to 5 fighters per column, physical actor order). Team size combinations
(1v1 ... 5v5, 1v5, 2v3, 3v2 ...) are already covered by the 25 layouts of the native cover. Modes differ only in WHAT the columns mean and in who is human:
`teams` (Team 1 vs Team 2), `ffa` (every fighter against all others), `coop` (allies on column 1 vs CPU on column 2), `training` and `training_coop` (practice), plus
2-4 human variants through team assignment (`human_seats`). So the screens need MODE VARIANTS of one layout engine, not new engines.

## Modes (mod menu `OPTIONS`) and what each shows

| Mode | Humans | Columns mean | Loading cover variant |
| --- | --- | --- | --- |
| Team battle | 1-4 (team assignment) | Team 1 vs Team 2 | current cover: two plates "Team 1"/"Team 2", VS burst |
| Co-op | 2-4 | allies (column 1, all human seats) vs CPU enemies | plates "Allies" (cyan) and "Enemies" (orange); a seat tag P1..P4 on each human portrait; VS burst |
| Free-for-all (1 or 2 players, or all CPU) | 0-4 | every fighter vs everyone | ONE wide plate "Free-for-all" holding every contestant (up to 10) in a 5x2 grid, no VS burst, a small "FFA" burst top centre instead; humans get a seat tag, CPUs a grey "COM" tag |
| Modded training | 1-2 | you (column 1) vs the practice dummy/opponent | plates "You" / "Practice partner", title "Modded Training" under the mod logo, no VS burst, balls and bar as usual |
| Training co-op | 2 | two humans vs dummy | like co-op with title "Modded Training" |
| Exhibition (all CPU) | 0 | like team battle | team plates, title "Exhibition" |

Seat tags use the game's own `1P/2P/COM` sprite (`448.1.21`) and team number tabs (`448.1.33`) for 3P/4P; all sizes at the 1x grid scale used by the cover.
Costume/form are never shown on the cover; names use the cleaned base name (no `[nn]` tags), Body 12 for non-leaders, Body 16 for the leader.

## In-battle screens per mode (same big step, after the cover variants)

Use the HUD sprites from AFS1 entry 5 (plate, bars, Timer numerals with the three palettes) through the native draw layer.

| Element | Modes | Behaviour |
| --- | --- | --- |
| Team plates and bars (watched fighter + its target) | teams, coop, training | the game's HUD plate language; bar colours green/blue/grey/red from the extracted palettes; fighter name Body 12 |
| Contestant list | ffa | compact vertical list at the screen edge: portrait 24 px, name Body 12, thin slanted HP bar (green, red under 25%), seat tag for humans; dead fighters fade to grey |
| Fusion timer | teams, coop, ffa (if enabled) | Timer plate under the fused fighter's health: numerals grey, yellow under 10 s, red at 3 s (game's own thresholds), gold bar, "Fusion" label in the Title style when there is room |
| Kill feed | teams, ffa, coop | right-top stack of 3 entries on slanted plates: killer portrait, arrow, victim portrait; Body 12 names |
| Lock-on marker | all | small marker on the locked target's head position for 20 frames when the target changes (L3), in the `Lock on` colour family (cyan) |
| Training panel | training, training_coop | left-bottom plate: toggles (Refill HP, Idle CPU, Show counters), HITS and DAMAGE numerals in the gold numerals, reset hint |

## Settings and other menus

All 16 settings pages are already native. Per-mode additions: mode names in the mode menu use the Title style; the "Modded Training" entry and the co-op / FFA explanatory help line (Body 12) use the catalogue (EN/ES). Add catalogue strings for every new label (plates, tags, titles, help lines).

## Acceptance (Codex's own checks before reporting once)

1. Contact sheet of every mode x team-size layout at 1x (teams 25, coop 4 sizes x 3 enemy sizes, ffa 2..10 contestants, training 1v1 and 2v1, exhibition) in EN and ES: no overlap, no clipped names, seat tags present.
2. State machine unchanged from the cover spec (never at 100%, hide on Ready + accepted start request, failure hold, stale generations).
3. HUD: render captures of team plates, FFA list with 10 contestants, fusion timer in the 3 colour states, kill feed, lock marker, training panel at 16:9 and 21:9, one frame each, text only on plates.
4. Live: one match per mode family (team 5v5, coop 2P, FFA 4 contestants, training) with fighters idle during loading, no input leak, no frame-time regression (log the median and max compose time).

## Credits visibility (user request, 2026-10-07: "credits at the start of the game; About is too hidden; it should be one of the first options")

1. **Boot credits splash (every launch):** right after the runtime starts, before the game's own logos, a native credits screen in the design kit: dark background with the faint dragon banner, mod logo (Title 26, gold) centred at y = 120, one line "A Budokai Tenkaichi 3 mod project" (Body 16), then two credit blocks centred: "Power Scale: LetsPlayBt3" and "Tag Team mod: The Mufti" (Body 16, names in gold, Body 12 below each with the full channel URL, plain text, NOT clickable at boot), build number bottom-left (Numeric 11), "Press any button" bottom-right fading in after 1.5 s (Body 12). Shows for 4 seconds, any button skips, fades in 8 frames and out 10 frames; never delays or blocks the game's loading (it overlays the boot logos). Setting "Show credits at startup" (default ON) on the first page of the Mod settings; when OFF show a 1.5 s strip only.
2. **First-run importer:** the same credits screen appears once at the end of the first import.
3. **Menu placement:** About/Credits is no longer the last settings category. (a) Mod menu (mode menu): add the entry "ABOUT / CREDITS" as the SECOND item (after TEAM BATTLE, so Team Battle stays the default choice), opening the About page; (b) Mod settings category index: About first; (c) the About page keeps names, full links and the build number; browser links open only on an explicit confirm.
4. **Catalogue:** add EN/ES strings for the splash lines, "Show credits at startup", "Press any button", and the menu entry names.

## HUD options in Mod settings (user, 2026-10-07: "the extra info should be enabled through the mod settings; a 10-character free-for-all is big")

Every extra element the native layer draws must be switchable from Mod settings (page "HUD"; persisted in `mod-settings.json`, EN/ES strings, readable live by the native HUD each time the match starts). REUSE the existing keys first (they already exist in `mod_settings.py`): `show_native_hud`, `show_friendly_healthbars`, `show_enemy_healthbars`, `show_kill_feed` (default false), `show_kill_score`, `show_hud_portraits`, `split_hud_scale_percent`, `split_hud_style`, `coop_hud_layout`, `show_fusion_timer`, `fusion_duration_enabled`. The native panels must honour them (today they ignore them). NEW keys to add to the HUD page:
- `hud_watched_panels` (On/Off, default On): the watched fighter + target panels.
- `hud_contestant_list` (Off / Compact / Full, default Compact): FFA and large matches; Compact shows the watched fighter, then up to 4 more rows (nearest alive first, humans pinned), 3 px thinner rows, no portraits; Full shows every contestant (up to 10) at the standard row height; Off hides it. Auto-compact when more than 6 contestants.
- `hud_kill_feed_rows` (1 / 3 / 5, default 3) in addition to the existing on/off.
- `hud_lockon_marker` (On/Off, default On).
- `hud_training_panel` (Full / Counters only / Off, default Full).
- `hud_panel_scale_percent` (80 / 100 / 120, default 100): scales Body text and plates of every native panel; the layout re-anchors to the screen edges.
- `hud_panel_opacity_percent` (60 / 80 / 100, default 100) for plate backgrounds.
Each toggle must take effect without restarting the game (re-read at match start is fine; menu changes apply on the next match).

Special thanks (user, 2026-10-07): a person who helped the user understand the code, Discord profile https://discord.com/users/747155705303400528.
Display name and exact wording are NOT known yet: do not invent them. Ask the user (name as they want it shown, wording, whether the Discord link is shown,
and that the person agrees to be named/linked) before it ships. Placement: the About page and the boot credits as a third block, "Special thanks: [name]".

Special thanks FINAL (user, 2026-10-07): display name "RidJuampa" (Discord handle ridjuampa, shown in the profile screenshot the user sent). Wording approved by the user:
EN "Special thanks to RidJuampa for helping me understand the code." ES "Agradecimiento especial a RidJuampa por ayudarme a entender el codigo."
Show the name only (no Discord link) unless the user later asks for the link; the Discord URL stays out of the UI by default.
