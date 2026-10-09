# Native revive HUD

Implemented in the developer UI Slice runner `ps2EntryRunner-revive-hud.exe`.

- Reads existing revive channel rows; does not change revival rules, costs, timers or CPU pacing.
- Progress arc/hex over the fallen ally, small indicator over the reviver, stock cost pips, recovering/completed/cancelled and stock/distance/admission feedback.
- Uses overhead shape preferences (bar fallback), revive ring visibility, opacity and wave. Existing ground ring remains enabled by its settings.
- Clips to each viewport; at most four plates per viewport. Outcome hints appear only in the reviver's viewport. Free-for-all has no ally revival display.
- Projects retained corpse models with the existing native projection helper.
- Native UI mode disables the legacy guest kill-feed drawer, including the relocated display-settings drawer, at its producer. Death tracking and native kill plates remain active. Legacy mode retains its original drawing.
- Suppresses legacy revive viewport text/bar after drawing its configured ground ring.

## Verification

PASS: native revival channel/half progress/cost/completion/cancel/stock/recovery and stale-manager checks; actual EE kill-feed return without glyph emission; 72 fusion/control cases; production preparation verifies relocated kill drawer no-op; saved 5v5 retained-corpse projection preserves caller and stack; 12 Vulkan captures (EN/ES, 16:9/21:9, hex/ring/bar).

Rendered captures: `power-scale-trial/revive-native-captures/`.
Live acceptance remains pending: revive/cancel/insufficient-stock in a modded match, then defeat a fighter after fusion and confirm only native kill plates appear. Game was not launched for these checks. Installer remains unchanged.

SHA256: D8676D0D141AC2854B4366EF9E3A84CE1679ADB81671CA9C7048C25B7E65050A
