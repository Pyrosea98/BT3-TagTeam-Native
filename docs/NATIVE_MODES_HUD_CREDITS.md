# Native modes, HUD and credits: M5.2

Current launcher update: `ps2EntryRunner-live-mode-fixes.exe` (0590F845).
See `NATIVE_LIVE_MODE_FIXES.md` for live follow-up fixes and remaining blockers.
The original all-mode build record below is retained as evidence.

## Build and launch

`Play Power Scale native UI Slice.cmd` now selects
`repo/build/ps2xRuntime/ps2EntryRunner-modes-hud-credits.exe`.
SHA256: `9F2B5C11C5556AFA05A587BA0AB7A29307E5DD69832780EC9E1A72D2A7156EFD`.
The three stable runners remain `4052022DFE11DED8F98A47F8EACEA75D0EEAD9BC87F5F620853461E5CF79756D`.

## Implemented

- Loading covers consume the real mode and physical controller assignments:
  25 team combinations, co-op Allies/Enemies, FFA 2–10, training, training
  co-op and exhibition. COM/1P/2P/3/4 labels come from the player's ISO.
- The frame/caps stay fixed; only the inner blue wave scrolls. Display labels
  remove power tags without changing roster IDs. Leader names wrap.
- The cover fades when Ready plus actual guest start acceptance is observed,
  allowing entrance dialogue to be seen. Actual actor release still waits for
  its existing acknowledgement. Error and stale-generation guards remain.
- Native game-thread HUD capture validates manager, phase, actor identities,
  roster slots, HP/ki, target, transformation model, fusion and killfeed owners.
  The renderer receives immutable snapshots and does not read guest RAM.
- Team watched/target plates, FFA ten-fighter list, native clock glyphs in
  grey/yellow/red, gold timer bars, three killfeed entries, head marker and
  training refill/idle/counter panel render in English and Spanish.
- Training counters observe actual damage before/after the patched damage
  function, from generated and interpreted callers. Select resets counters.
- Replaced guest panel/feed/timer drawing is suppressed only after native HUD
  drawing, with exact full-body byte guards. Unknown patches fall back to
  guest drawing. Timer save/chained render owner/restore and viewport camera,
  scissor and gameplay work remain. No guest control/options are overwritten.
- Nonblocking startup credits, any-key/pad skip, full names/plain channel URLs,
  first-import credits and persisted default-on startup preference. Off uses
  a short strip. About is second in the actual mod menu and first in settings;
  browser links still require explicit confirmation.
- Bridge packet/operation/service/send/byte counters in `[fps]`; no guest-lock
  wait exists in this bridge. This does not exclude CPU/memory contention.
  Native target getters default on; interpreter count atomics are batched;
  immutable generated-function presence is cached, with live dirty/override
  decisions retained. Raw-word guarded instruction predecode is opt-in.

## Acceptance evidence

- Build exit 0: `repo/build/codex-modes-hud-credits-build.log`.
- 130 actual RTX3080 Vulkan render/readback cases PASS, unchanged 359 uploads:
  `power-scale-trial/codex-modes-hud-credits-gpu.log`.
- All-family English/Spanish review sheets and HUD captures at 16:9/21:9:
  `power-scale-trial/native-ui-modes-capture/`. Timer digits, training counters,
  co-op, FFA, credits and ultrawide captures visually reviewed.
- Native lifecycle/transport/HUD capture and exact draw guard checks PASS.
  Real settings adapter persistence and mode/seat publication PASS.
  Actual assembled menu replacement/readback and start-acceptance loop PASS.
  Instruction decode invalidation/collision test: 400000 accesses PASS.

Reproduce GPU acceptance with `codex_modes_hud_credits_check.py`. Recreate
the exact guest drawing guards with `codex_native_hud_draw_pack.py`.

## One coordinated live session

No game was started, stopped or controlled during this implementation.
The new build still needs live validation:

1. Boot credits skip; Mod menu second About; language/startup preference save.
2. 5v5: visible entrance dialogue, watched/target HP/ki, target change,
   transformation/fusion timer, killfeed, clean Fight Again.
3. Co-op 2P, FFA four contestants, training: controller labels, HUD ownership,
   damage counters and Select reset; no leaked loading/menu input.
4. Same-roster 5v5 ordinary polling 0.2s versus `--controller-poll 2.0`.
   Collect `[fps]` bridge service/guest utilization/fight-update statistics.

## Limits

Gameplay behavior of the new HUD/menu patch is not yet live-confirmed.
Fixtures validate capture/ownership guards and rendering, not gameplay parity.
No measured speedup or 50-fight-updates/s result is claimed. A block execution
cache and hottest dirty ELF AOT functions remain performance work; the current
field decode cache is not a block executor. The Python controller still owns
orchestration/settings actions. APK/ARM64 and a platform importer remain later
work. The local ISO art cache must not be redistributed.
