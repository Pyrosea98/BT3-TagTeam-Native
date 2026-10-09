# Combined ELF performance and overhead HUD trial

## Implemented

The verified ELF leaf slice and overhead HUD are in one executable:
ps2EntryRunner-elf-overhead-hud.exe. Both root UI Slice and Profile5v5
launchers select it. The stable runners remain unchanged.

The old host corner fighter panels are removed. Each active native viewport
projects live model heads on the guest thread using121ED8/1210D8 and the
native camera matrices. The GS thread receives an immutable snapshot; it
never reads RAM or calls guest code. No new PINE client is created.

Owner and target receive detailed overhead plates: live character name,
optional portrait, health, ki, blast-stock pips, viewport player tag and fusion
time. Stock units are100000, matching the native accessor. Ordinary form
236..240 and Sparking accumulator status provide small state indicators.
Other living fighters get simple health bars with relation accents.

Every viewport is scissored. Off-screen front-facing owner/target points
receive edge arrows and short names. Plates clamp to viewport bounds; target
plates separate from owner plates; simple bars avoid detailed plates.
Fighter status has draw priority over auxiliary panels. Behind-camera or
failed projections are omitted. Authored camera flags and shared stops hide
overheads; their return fades over6guest frames.

Original game HUD is enabled by default. Its setting is independent of
capturing overhead stats. Overhead only also writes the guest display HUD
control OFF. The runtime suppresses only the authenticated status roots in
the scoped native draw traversal; node updates, dialogue/clash/FIGHT roots,
camera wrappers and gameplay continue. Existing game-style split panels are
retained when the original game HUD is enabled. Guest health-bar drawings are
replaced only with exact code signatures and available projected coverage;
unknown bodies retain their normal path.

## Settings

Under HUD, next-match preferences with EN/ES labels:
- HUD style: Game HUD + overhead / Overhead only.
- Names: Off / Player and target / All.
- Details: Player only / Player and target / Player, target and allies.
- Portraits, optional contestant list (default OFF), scale70..130%, opacity20..100%.
- Existing original HUD, friendly/enemy bars, kill feed and fusion timer controls.

These are staged native-controller tools; installer/PCSX2/ISOs were untouched.

## Verification and limits

- Actual prepared RAM20261007-131331-1c7a1b67/16-ready-held.bin:
  head projection produces6valid points in1view; caller context and borrowed
 4096-byte stack preserved. Mean0.0013ms/max0.0020ms across120headless calls.
  Held-preparation gate is cleared and fight phase reproduced for this test;
  actors/models/camera matrices remain captured data.
- HUD capture, actual stock units, scoped status-root suppression, foreign or
  altered code refusal, aspect/split clipping and overlap checks PASS.
- Actual adapter consumes validated preferences; captured display installer
  writes original-HUD control OFF for Overhead only, retaining executable programs.
- Final ELF helper regression:2048 production-vs-interpreter comparisons PASS;
  prior independent9440MIPS/C++ comparisons remain applicable.
-30real Vulkan render/readback captures: EN/ES,2/6/10fighters, single/two/four
  viewport fixtures, portrait/scale/opacity variations, off-screen arrow and
  overlap cases across16:9/21:9/4:3. In elf-overhead-hud-capture/.
-CPU compose median0.206ms; single-view10-fighter fixture max0.211ms;
  warm worst0.454ms across all fixtures (including four views); initial cold
  pipeline preparation19.212ms. GPU median0.008ms/max0.011ms. The0.3ms budget
  is not established for four-view or live play. These are synthetic render
  fixtures, not a real battle measurement.

Logs: power-scale-trial/codex-elf-overhead-projection-check.log,
codex-elf-overhead-elf-check.log, codex-elf-overhead-gpu-check.log.
Build: repo/build/codex-elf-overhead-hud-final-build.log, exit0.

Live target switching, cinematic hide/fade, current split cameras, native HUD
visibility and rematches need one combined gameplay session. FPS improvement
is UNKNOWN; busy fighting in the preceding live build remains~20updates/s.
This does not translate the larger dirty ELF callers or all cave loops.
Audio scheduling, non-team Ready/Fight, unsupported-PC capture and special
thanks remain outstanding; no fix for those is claimed here.

## Test

Use Play Power Scale native UI Slice.cmd for this combined build, or Profile
Power Scale5v5.cmd for busy-fight metrics and the automatic profile summary.
Verify heads/target on one modded match, target switching and a cinematic,
then Fight Again. Change original HUD visibility before a fresh match to
verify that overheads remain available. Existing resolution settings remain.

SHA256: 3E64DB6D63DE8B954D4A21E8126D04FB1B1232A85BA82F5E236213F891106093

## Live regression and corrective build

Claude's live test of the above build showed no overhead HUD and a stuck
intro acknowledgement despite a playable fight. Treat live delivery as failed.
The selected corrective build and its evidence/remaining limits are recorded
in NATIVE_OVERHEAD_ACK_FIX.md. It removes the controller-release dependency,
fixes the UI/PINE lock inversion, and adds projection/rendering diagnostics
and an overhead-only disable switch. Live visibility and speed remain unverified.
