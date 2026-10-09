# Design language: one look for the loading screen, HUD additions, fusion timer, mod menus and installer

Owner: Claude (design), Codex (implementation). Written 2026-10-06. Source of truth for every visual decision.
User direction: "everything has a nice look and feel and is continuous between the elements; Dragon Ball related
or at least Budokai Tenkaichi, but with a cleaner look."

## Principles

1. **Born from the game.** Use the game's own art, shapes, numerals and colour states, extracted from the player's disc at
   install time. New art is only added to join pieces together, drawn in the same style. Never ship game art.
2. **Cleaner, not different.** Same vocabulary as BT3, fewer elements, more space, one accent per screen. Remove
   clutter (second labels, extra bars, decorative noise) before adding anything.
3. **One system.** A loading cover, the fusion timer, a HUD gauge and an installer page must look like they share a kit:
   same plate shape, same numerals, same colours, same motion.
4. **Quiet by default, loud on events.** Idle elements are metal grey and low contrast; important moments use the game's
   own state colours (yellow warning, red critical) and a short punchy animation.

## Kit (all values come from the game's HUD/UI art; confirmed in `hud-reference/bt3-hud-sprite-sheet-user-provided.png`)

- **Plate:** dark slanted parallelogram with a thin metal edge (the Timer/Win counter plate and Team HUD plates). Slant matches
  the ki/health bars. This is the only container shape. No rounded rectangles in game space.
- **Bar:** the HUD bar sprite (slanted metal bar with a coloured fill and a thin lighter edge). Fill colours: orange/gold for
  fusion, blue-cyan for ki/progress, green for health, red for danger. Progress for loading uses the blue wavy Dragon-Ball
  scroll frame (`449.1.10`) because it is the game's own loading bar.
- **Numerals:** the game's italic outlined digits. Grey "Timer (normal)" at rest, yellow at 20 s, red at 10 s (the match
  clock's own state logic). Big gold outlined digits (`450.0.13`) only for counts and menus.
- **Text banners:** the in-game text look (gradient fill, dark outline, slight glow) for words like Fusion, Ready, Fight;
  small caps labels in plain white with a 1 px dark shadow for secondary text.
- **Emblems:** the seven Dragon Balls (`449.1.9`), the VS burst (`455.11`), Z-sword and dragon ornament as rare accents (one
  per screen at most).
- **Glow:** cyan ki glow (the `B.S.C glow` set) for active/selected; gold for fusion; never both on one element.

## Colour roles

| Role | Colour feel | Used for |
| --- | --- | --- |
| Neutral | metal grey, near-black plates | resting UI, plates, bars' empty part |
| Fusion | gold/orange | fusion timer fill, fusion label, fused fighters' names |
| Energy | cyan/blue | ki, progress, selection glow |
| Warning | yellow then red | last 20 s / last 10 s of any countdown |
| Success | green | health, ready/loaded ticks |

## Motion

- Appear: slide in along the plate slant, 8-10 frames. Disappear: fade 6 frames.
- Warning: digits switch colour with a 2-frame flash at 20 s and 10 s; at 5 s a 1 px pulse once per second. No shaking.
- Loading: the Dragon Balls fill one by one as stages complete (7 stages), the wavy bar advances smoothly; VS burst only
  when the match is ready.

## Applying it

- **Loading cover:** left and right fighter portraits (portrait map) on slanted plates, VS burst between them, the wavy
  progress bar under it, seven Dragon Balls above the bar lighting up, mod logo small in the top corner. One background
  tone. No procedural dragon. Goal: no cover at all when preparation finishes before the game's own load (then show nothing).
- **Fusion timer:** a Timer plate under the fused fighter's health area; grey numerals (yellow 20 s, red 10 s), a slanted
  gold bar for remaining time, small "Fusion" banner and the two names only when there is room.
- **HUD additions (target and lock feedback, team gauges):** reuse the team HUD plate and bar sprites; lock-on marker in
  the same glow family as `Lock on`.
- **Mod menus and installer:** same plate/bar/numerals; flat dark background, gold accent, no extra decoration.

## Do and do not

- Do: align everything to the plate slant, keep 8 px (at 640x448) margins, use one accent colour per element.
- Do: reuse existing sprites before drawing new ones.
- Do not: introduce new fonts, rounded boxes, gradients unrelated to the game, 8-bit glyph fonts or neon outlines.

## Implementation notes (for Codex)

- Draw natively in the embedded runtime (M4/M5) with the game's own HUD draw routines where possible; fall back to our
  own sprites built at install time from the disc textures.
- Keep geometry in one table (plate, bar, margins, colours) so loading, HUD and installer pull from the same constants.
- Textures: entry 2 (battle) and the UI archives; see `FUSION_TIMER_HUD_BRIEF.md` for locations.

## Screen and mode inventory (Claude, 2026-10-06; read from the mod's own modules)

Every screen below must adopt the kit. "Today" is what the Python mod draws now; all of it must end up native.

| Screen / element | Module(s) | Today | Target look |
| --- | --- | --- | --- |
| Mode menu (Modded Modes: team, FFA, co-op, training...) | `mode_menu`, `native_mode_menu`, `native_menu_assets` | animated grouped menu on the game's menu plates; labels are replaced atlas bitmaps | keep the game's plates and motion; labels in the in-game text style (same atlas look as the stock menu), icons from the 4-icon set |
| Mod settings / config menu | `ingame_settings`, `mod_settings` | host-drawn pages rendered with Arial/Liberation in Python (PIL), uploaded as images | native pages built from plates, bars, toggles in the kit; game numerals; no system fonts; (also removes a Python dependency) |
| Loading cover | `guest_loading_screen`, `loading_lights_a/b`, `native_menu_loading`, `native_menu_texture` | "Ki Storm" cover with a PSMT8 background, foreground atlas and light emitters | real-sprite cover (v3 mockup): portraits on plates, VS, Dragon Balls, wavy bar |
| Team battle HUD | `viewport_hud`, `guest_healthbars` | two compact panels per viewport (watched fighter + its target); overhead health bars | the game's team HUD plates and bar sprites, same slant, same state colours |
| Kill feed and kill counts | `guest_killfeed`, `display_settings` | compact 5x7 uppercase glyph font | game text look (small outlined italic), names from the label table, feed on a plate |
| Fusion timer | `fusion_duration`, `multiplayer_fusion` | 5x7 glyphs + flat bar | Timer plate, game numerals (grey/yellow/red), gold bar, "Fusion" banner |
| Free-for-all ("one for all") | `ffa_targeting`, `battle_mode_policy`, `four_player_mode` | targeting only; HUD reuses team panels | same panels; per-contestant colour from the game's six bar colours; OPTIONAL (not in the mod today, user has never seen one): final-standings banner in the Victory/Eliminated style |
| Co-op and 3/4-player | `coop_character_select`, `coop_controller`, `quad_menu_input` | native select flow + mod HUD | same kit; seat colours from the 1P/2P/COM tags and team-number tabs |
| Modded Training | `modded_training`, `fresh_team_trainer` | practice with refill/idle CPUs, no dedicated HUD | training panel on a plate: refill, idle CPU, hit/damage counters using the game's own counters |
| Lock-on feedback | `lockon_switch`, `lockon_queue` | none visible | small lock marker in the `Lock on` glow style when the target changes |
| Installer | (new) | none | same plates/bars/numerals, flat dark background, gold accent |

Open design needs: a settings page template (title plate, list rows with a slanted highlight, toggle/slider widgets,
help line), a training HUD template, and a final-standings screen. I will draw these as reference renders from the real
sprites (like `loading-mockups/v3-real-sprites.png`) before Codex implements them.

Correction (2026-10-07): the final-standings screen shown in `loading-mockups/v3-standings.png` is a design idea for FFA only. The mod
has no ranking screen today (`result_presentation.py` only hands camera/winner animation back to the game's own result). Low
priority; do not build it before the loading cover, settings page, training screen and HUD.

Correction (2026-10-07, from the user): in the game's own clock the digits turn RED only at 3 seconds, not at 10. Use the game's real
thresholds for the match clock look; for the fusion timer choose our own warning steps deliberately (yellow at 20 s, red at 10 s is a
design choice, not copied from the game). Yellow threshold of the game's clock: ask/measure.

The game's match clock states (user, 2026-10-07): grey normally, YELLOW under 10 seconds, RED at 3 seconds. The fusion timer should
use the same three states and thresholds (grey, yellow under 10 s, red at 3 s) so it reads exactly like the game; this replaces the
earlier 20 s / 10 s idea. Keep an optional extra cue (pulse) only in the last 3 seconds.

## Rule 0 (user, 2026-10-07): gameplay over look and feel, always
Anything we draw during a fight must be small and see-through enough that it never hides the action: overhead shapes about 40-46 px on the 640x448 grid, fill alpha at most about 45%, thin borders, no plates larger than needed,
names off by default, and a hard cap on size/opacity even at the maximum setting. When a nicer look and playability conflict, playability wins. The game's own HUD must be removable (setting) so the overhead HUD can replace it.
