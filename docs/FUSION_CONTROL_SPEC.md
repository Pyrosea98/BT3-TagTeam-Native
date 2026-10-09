# Co-op fusion: control modes, swap seconds and the fusion/swap indicators (user request 2026-10-08)

Owner: Claude (spec), Codex (implementation). Builds on `OVERHEAD_HUD_SPEC.md`, `FUSION_TIMER_HUD_BRIEF.md`, Rule 0 in `DESIGN_LANGUAGE.md`.

## User findings (live)
- Mod menu lists only: "swap every 20 s", "P1 attacks / P2 moves", "P1 does everything".
- Missing: "**P2 attacks / P1 moves**", and a mode that **swaps the move/attack roles every X seconds**.
- The swap interval is fixed at 20 s: it must be configurable. The **first swap must happen exactly after X seconds** from the moment the fusion starts (aligned with the option).
- During the match the user does NOT see: the "PRESS R3 to fuse" prompt, the **seconds left of the fusion**, nor the **seconds until the next control swap** (all three settings are ON in mod-settings.json: `show_fusion_timer`, `show_fusion_control_owner`, `show_fusion_control_countdown`, `fusion_duration_enabled`, `fusion_duration_seconds` = 100). In "Overhead only" the game's own status/prompt text is suppressed, so the mod's guest-drawn texts (`guest_killfeed.TEXT`) may be hidden or never reach the screen. Cause UNKNOWN.

## Control modes (`coop_fusion_controls`, EN/ES labels)
1. **Swap control** (full control passes P1 <-> P2 every X s). Legacy `swap_20s` maps here.
2. **Split: P1 attacks / P2 moves** (existing).
3. **Split: P2 attacks / P1 moves** (NEW).
4. **Swap roles** (NEW): the move/attack split alternates every X s (P1 moves + P2 attacks, then P1 attacks + P2 moves ...).
5. **P1 does everything** (existing). Optional: **P2 does everything**.
New `coop_fusion_swap_seconds`: 5 / 10 / 15 / 20 (default) / 30 / 45 / 60, used by modes 1 and 4. The first swap occurs X s after the fusion starts; a defusion resets; swap timers pause with the game pause and cinematics.

## On-screen indicators: reuse the overhead HUD language (small, translucent, Rule 0 caps)
All drawn natively over the FUSED fighter (the 1P/target focus style), independent of the game HUD (they must show in Overhead only and in Game HUD + overhead):
- **Fuse prompt:** a small chip "R3  FUSE" (Body 11, translucent plate, about the size of a name label) over the fighter that can fuse when the fusion condition is met and the setting for prompts is on; hides when the player fuses or the condition ends; pulses gently, no big text.
- **Fusion time left:** a thin ring/arc (or short bar) of the fusion time, gold -> yellow under 10 s -> red under 3 s (the game's thresholds), with the number in tiny Numeric type only under 10 s.
- **Swap countdown:** a second, smaller arc/bar next to it filling toward the next swap, plus an owner marker "P1"/"P2" (cyan/magenta) that flips at the swap; in split modes show two tiny role icons (move / attack) with the seat tags and flip them at each role swap.
- Shape follows `hud_overhead_shape` (Hexagon edge or Ring arcs); if the shape is Off, fall back to small bars. Max about 46 px, fill alpha <= 45%, fade during cinematics like the other overhead elements.
- Settings: `show_fusion_timer`, `show_fusion_control_countdown`, `show_fusion_control_owner` keep their meaning; add `show_fuse_prompt` (default On).

## Acceptance
Offline: all five modes with seat/role logic for P1/P2 (and P3/P4 neutral), first swap at X s for X in {5, 60}, legacy value migration, EN/ES strings, render captures of the three indicators (16:9 and 21:9, Hexagon, Ring, Off shape). Live: 2 humans fuse, check prompt, both timers, owner/role flips, defusion reset, pause behaviour.

## Addendum (user, 2026-10-08)
1. **"P2 does everything" is a required mode, listed LAST** in `coop_fusion_controls` (order: Swap control, P1 attacks/P2 moves, P2 attacks/P1 moves, Swap roles, P1 does everything, P2 does everything).
2. **Any seat pair in 3-4 player split screen.** The two humans that fuse can be any pair: P1+P2, P1+P3, P1+P4, P2+P3, P2+P4, P3+P4, and each ORDERED both ways (who pressed R3 / which seat is first of the pair, i.e. P1+P3 and P3+P1, etc.: 12 ordered pairs). Define the roles by the two seats of the pair, not by literal "P1/P2": in the menu the words stay P1/P2 and mean "the first fuser / the second fuser" (document this in the help line, EN/ES); the mode "P1 attacks / P2 moves" means first-fuser attacks / second-fuser moves. Everything must hold for every pair: input routing (attack/move/all), the swap and role-swap timers, the owner marker colours (use each seat's colour), the camera/viewport the fused fighter is watched in, the split-screen layout after the fusion (the freed viewport/seat), the defusion handoff, the fusion HUD indicators over the right fighter in the right viewport, and the second-match cleanup.
3. **Acceptance:** an offline matrix, 6 seat pairs x 2 orders x 6 modes (72 cases), using real captured 3-4 seat states (or fixtures built from them) with simulated pad input: after fusion the correct seat(s) control the correct actions, the swap fires at X s, defusion restores each seat's own fighter and input, no seat is left without a viewport, indicators anchor to the fused fighter in its viewport. Report what cannot be verified without extra controllers.
