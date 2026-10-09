# Overhead HUD and start acknowledgement correction

The 3E64DB6D live test failed: no overhead HUD appeared and the controller
stayed in the intro acknowledgement loop while the fight was playable.
The earlier synthetic checks did not exercise this combination.

## Changes

- The native UI adapter now uses one reentrant lock for Surface operations
  and short-lived PINE connections. Previously the intro callback acquired
  PINE then Surface, while the heartbeat acquired Surface then PINE. That
  inversion can deadlock before the next budget observation. It explains
  why a 90-second active budget cannot protect that blocked operation.
  The exact stalled live thread stacks were not captured; attribution to
  that archived session remains a hypothesis until the new live test.
- HUD capture accepts Ready or Released with a valid generation, matching
  native simultaneous manager/count, verified actors, native fight phase 3
  and cleared preparation holds. It does not acknowledge or release gameplay.
  Vulkan draws the active snapshot in either lifecycle phase, independently
  of the delayed controller callback.
- `--no-overhead-hud` disables head projection and overhead drawing only.
  Zero projected views retain guest health bars. ELF helpers, interpreter
  blocks, cleanup and auxiliary HUD remain enabled for cost comparison.
- Once per second, `[overhead] published views=N detailed=K simple=M` reports
  capture activity, lifecycle phase and projection mean/max milliseconds.
  `[overhead] drawn ...` separately reports submitted panels, bars and arrows.
  Publication alone does not prove rendering or visibility to the player.

## Verification

- Actual Surface heartbeat and PINE-owned intro callback complete concurrently;
  existing settings/publication/late-diagnostic checks pass.
- HUD unit checks accept Ready in a verified native fight, reject active holds,
  non-fight phase, stale ownership and invalid actor data.
- Actual saved 5v5 projection, now with lifecycle Ready rather than Released:
  1 view/6 head points; caller and 4096-byte borrowed stack unchanged.
- Overhead-disabled saved-state check: zero views/points, context/stack unchanged.
- 30 Vulkan render/readback fixtures pass. Six two-fighter fixtures deliberately
  retain Ready without start acceptance/release and verify presented generation.
  One resulting screenshot was visually checked. Fixtures are not live gameplay.

Evidence: `power-scale-trial/codex-overhead-ack-{adapter,hud,projection,disabled,gpu}-check.log`,
`power-scale-trial/overhead-ack-fix-capture/`,
`repo/build/codex-overhead-ack-final-build.log`.

Both launchers select `ps2EntryRunner-overhead-ack-fix.exe`, SHA256
E2EF7910E97668CC928731987E61537B5EC3DD6B65B84E913821F48227EDB35C.
Stable runners are unchanged. No game was launched or controlled.

## Live work remaining

HUD visibility, intro acknowledgement and reported intro slowdown remain
unverified in gameplay. Previous code returned before projection when capture
was inactive, so the 4096-byte stack copy was not executing while gated on
Ready. Do not claim that this correction restores the prior intro speed.
Use the normal profile launcher first; if the slowdown persists, compare the
same roster with `Profile Power Scale 5v5.cmd --no-overhead-hud`.
Inspect both published/drawn lines and projection timing alongside guest_ms.
The performance target of 50 updates/s remains unmet.
