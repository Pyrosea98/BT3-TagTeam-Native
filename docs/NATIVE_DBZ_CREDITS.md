# Dragon Ball credits and boot health check

## Credits update

The full credits screen no longer reuses the battle status title frame (including
its empty portrait/scroll cap), menu help frames or the stretched banner. It uses
seven Dragon Balls from the existing game assets, a gold title, subtle stars,
flat dark blue credit panels and thin gold rules. The development badge is
removed. Power Scale / LetsPlayBt3, Tag Team / The Mufti and the approved
RidJuampa acknowledgement remain in that order, with the existing author links.
The short credits strip also uses flat panels.

The full-screen background stays opaque while text fades. This prevents a boot
image underneath from showing through and resembling a character placeholder.
Exact attribution of the user's artifact to the old frame versus background
bleed-through is unconfirmed; both paths are removed from the full credits view.

92 Vulkan render/readbacks PASS, including EN/ES full and short credits, first
fade frame requiring at least 90% background replacement, skip/fade lifecycle,
and the preceding Everyone/pause/intro/HUD fixtures. EN/ES full credits visually
reviewed. Actual saved 128 MiB projection/status checks also pass.
Evidence: power-scale-trial/codex-dbz-credits-{gpu,runtime}-check.log and
power-scale-trial/dbz-credits-capture/.

## Boot investigation stopped at the user's request

The archived everyone-intro failure is real: game FPS and swaps approached zero,
while host repaints stayed near 60. It was not reproduced in the controlled
comparison. Current everyone-intro cold boot reached game-frame 2798 with tail
median 59.79 game FPS / 59 swaps/s; previous overhead-shapes reached frame 2196,
60.14 game FPS / 59 swaps/s. The subsequent boot-isolated build reached frame
2130, 60.03 game FPS / 59 swaps/s in its bounded 40-second check.

Startup isolation now explicitly excludes all new intro polling/reads/writes
outside the prepared Ready lifecycle. New guest start/quad modules are absent
from the boot bootstrap and are installed during match preparation; pause
capture already returns before reading its flag in inactive lifecycle phases.
This is isolation, not a proven root-cause repair for the intermittent stall.

codex_boot_check.py uses the actual UI Slice launcher, controller and settings,
keeps per-run logs/JSON, and requires real game-frame advancement plus sustained
swaps above 30 in the first thirty roughly one-second samples and at the end.
It rejects the archived failure and accepts the successful comparisons. Menu
wait-PC samples are reported separately; this does not prove menu navigation.
The first sandboxed diagnostic could not initialize loopback PINE and was
excluded. Valid runs used working loopback access. No settings, resolution or
input were changed by the diagnostic. No further boot retries after the user's
instruction to treat this as an edge case.

## Selected build

Both launchers select repo/build/ps2xRuntime/ps2EntryRunner-dbz-credits.exe,
SHA256 4E1400AA1A22C1BEB2D4468069C1360A450FCA465EB8CAAC3581855E7BEF74E6.
Build exit 0 in repo/build/codex-dbz-credits-build.log.
Includes Everyone, pause hiding, held Ready/FIGHT and explicit startup isolation.
The credits changes were checked offscreen; the final credits build was not
cold-booted again after the user requested no more reproduction attempts.
Stable runners remain untouched. No game/process/GAME_LOCK at handoff.
Live Everyone/pause/FFA intro/rematch verification is still pending.
