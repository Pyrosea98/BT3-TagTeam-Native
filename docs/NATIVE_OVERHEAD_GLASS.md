# Compact translucent overhead HUD

## Live evidence accepted

Claude's E2EF7910 session confirms intro acknowledgement, visible overheads,
target switching and Fight Again. Two recorded fights have segment medians
28.8–29.7 FPS, guest 16.3–20.8 ms and guest share 38–58%. That is this
session's measurement, not a controlled attribution to the ELF leaves or
lock correction. The 50-update performance target remains unmet.

## Implemented

- Detailed panels default to 65% size (about 101 x 33 logical pixels before
  distance scaling). Portraits are about 23 pixels; names retain an 11-pixel
  minimum, HP bars are about 5 pixels and ki bars about 4 pixels.
- Dark blue glass fill defaults to 50% alpha, with a thin 70% light edge.
  Text and coloured bars retain their colour; bar backing is 70% alpha.
  Owner/target accent edges remain. Simple bars retain their prior size,
  independent of the detailed-panel scale setting.
- Size presets 50/65/80/100/120; opacity presets 30/50/70/100. Previously saved
  scale 130 and opacity 20 remain valid. The active roster-tools/mod_settings.py
  overlay now includes the HUD keys; the underlying controller copy alone was
  insufficient to expose them in the real native trial menu.
- Authenticated shared cinematic stop, member-mask ownership, actor authored
  flags and known cinematic participant actions reduce panels to 80% size and
  approximately 28% default fill alpha. They remain visible. Names retain
  their minimum size. These are display-only changes, not game action changes.
- SpecialThanks EN/ES catalogue entry with the user-approved RidJuampa wording.
  It is the third block in full and short boot credits and in About, following
  Power Scale and Tag Team. No Discord link. About retains only the two existing
  link actions.
- Publication logs explain simple bar counts using filtered/offscreen/invalid
  projection/absent-or-dead counters plus friendly/enemy preferences.

## Why the recorded simple count was zero

Current saved mod-settings.json has both show_friendly_healthbars and
show_enemy_healthbars false. Those preferences force all otherwise eligible
simple bars off. They are preserved. Enable the desired switches to show simple
bars; the new one-line diagnostics reveal any additional projection exclusions.
This is not evidence that every extra fighter was off-screen.

## Verification

- Actual native adapter/settings model checks pass, including credit text,
  preset stepping, default 65/50, older saved values and concurrent intro/UI
  heartbeat. Active overlay HUD keys are exercised by the settings model.
- Compiled HUD tests pass: cinematic signals do not deactivate capture, foreign
  cinematic ownership is ignored, filtering/offscreen/invalid projections are
  counted separately, 65% transport accepted and below 50 rejected.
- Actual saved 5v5 projection still passes: 1 view/6 points, caller and borrowed
  stack preserved, mean 0.0008 ms/max 0.0011 ms. This is an offline saved state.
- 42 Vulkan render/readback checks pass, including default/min/max styles,
  cinematic fixture, Ready without ACK, single/two/four viewports, EN/ES,
  16:9/21:9/4:3, full/short boot credits and About. Relevant captures reviewed.

Evidence: power-scale-trial/codex-overhead-glass-{adapter,hud,projection,gpu}-check.log
and power-scale-trial/overhead-glass-capture/.

Both root launchers select ps2EntryRunner-overhead-glass.exe, SHA256
41585B15CC1CDDC088FFE9014571A4BE014F5F4C24F4C40D0A8D11348173CB50.
Build exit 0: repo/build/codex-overhead-glass-final-build.log.
Existing interpreter/ELF helpers, cleanup and rematch fixes are retained.

## Remaining live checks

Compact size/translucency, cinematic fade and original-HUD OFF with overheads
still visible need gameplay verification. Same-roster native-leaves comparison
is required before attributing the measured 30 FPS session to a particular
performance change. Non-team Ready/Fight, unsupported-PC capture and audio
health remain outstanding. This build does not claim those fixes.
