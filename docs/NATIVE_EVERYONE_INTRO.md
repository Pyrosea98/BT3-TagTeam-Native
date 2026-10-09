# Everyone overhead HUD, pause hiding and native Ready/FIGHT

## Accepted live evidence

Claude reports the preceding overhead-shapes build successfully displayed Ring,
removed the original HUD in Overhead only, and played a ten-fighter FFA.
Current cinematic fade/shrink is accepted and retained. These are preceding-build
live results; the changes below still need live confirmation.

## Changes

- Guest-thread capture reads the native scene pause bit (scene 0x331DC8,
  flags +0x19F0, mask 0x100). Published snapshots carry paused independently
  of match ownership. Paused rendering draws no overheads, simple bars or
  auxiliary fight HUD; projection work is skipped. Resume restores the normal
  snapshot/render path without changing actor state or settings.
- Detailed overhead HUD adds Everyone / Todos. Every eligible on-screen
  fighter gets the selected shape, independent of friendly/enemy health-bar
  switches, without an additional simple bar. Owner cyan, target orange,
  allies teal/green, other enemies red. Nonfocused Hexagon/Ring diameter is
  capped at 34 logical pixels (27.2 during cinematic fade); focus cap stays 46.
  Names remain Off/Tiny/Normal and focused only. Existing offscreen skipping
  and owner/target arrows remain. Fill remains capped at 45%.
- Native matches without the existing Team Battle dialogue replay use a
  native READY!/FIGHT! banner sequence (LISTOS!/A LUCHAR! in Spanish).
  This reproduces the start banners; it does not invoke another mode's native
  dialogue/phase table. Existing Team Battle dialogue replay is unchanged.
- Native controller writes start request 2, meaning prepared intro pending.
  The guest start gate now releases only for request 1. Runtime validates the
  current generation, native manager/count/actor table, phase 3 and held gate
  before presenting the sequence. READY lasts at least 1500 ms of observed
  unpaused time, FIGHT at least 700 ms. Each stage must first be composed by
  Vulkan. Pausing, missing composition or lost ownership does not advance it.
  Long frame gaps contribute at most 250 ms per observation.
- Only after FIGHT finishes does runtime request the ordinary guarded release.
  That guest gate restores CPU assignments, clears actor/pad input and the
  preparation hold, and publishes its normal ACK. Controller start acceptance
  follows actual guest stage consumption and completion still follows release.
  P3/P4 pad publishing now neutralizes analog/buttons during preparation holds;
  original P1/P2 records clear analog and edge history as well.

## Verification

- Compiled capture/ownership/transport/pause and timer tests PASS: pause and
  absent display acknowledgement preserve the hold, both banner stages require
  their own presentation, new generation/owner resets the countdown, Everyone
  bypasses health-bar switches without duplicating bars.
- Actual settings publisher and concurrency checks PASS, including Everyone
  detail bits, all shape choices and Overhead-only original HUD OFF.
- Actual controller start-loop checks PASS for native FFA/coop/training modes:
  request 2, acceptance from the guest banner stage before ordinary gate ACK;
  existing intro/non-native and identity rejection cases pass.
- Production interpreter on saved 128 MiB 5v5 executes the newly generated
  start gate: requests 0/2 retain all actor holds and clear actor input;
  request 1 restores assignments and clears the hold with ACK. Newly generated
  quad-pad frame code neutralizes P3/P4 analog/buttons while held and restores
  freshly published input after release.
- Saved projection/status checks still PASS: one view/six points, unchanged
  caller/4096-byte borrowed stack, mean 0.0008 ms/max 0.0013 ms; both actual
  original status roots suppressed at zero update scope.
- 90 Vulkan render/readbacks PASS across EN/ES and three aspects, including
  Everyone Hexagon/Ring with ten live actors, pause with zero changed pixels,
  READY/FIGHT presentation acknowledgements, existing HUD and credits cases.
  Relevant Everyone and Spanish FIGHT images visually reviewed.
- Ten-fighter fixtures: 12 samples, CPU compose mean 0.154 ms/max 0.201 ms;
  GPU mean 0.0065 ms/max 0.007 ms. This meets the requested synthetic 0.3 ms
  budget on this computer; it is not a live gameplay performance measurement.

Evidence: power-scale-trial/codex-everyone-intro-{hud,adapter,start,gate-runtime,
projection,gpu}-check.log and everyone-intro-capture/.

## Build / live check

Both root launchers select repo/build/ps2xRuntime/ps2EntryRunner-everyone-intro.exe.
SHA256 5DEA6EA687A90F83C2A9F77427399BDC76D6545F75ECE128D4388903DCBF4DAF.
Build exit 0: repo/build/codex-everyone-intro-build.log.
Stable runners are preserved. No game launched, controlled or stopped.

One combined live test: Everyone with health-bar switches OFF, pause/resume,
FFA Ready/FIGHT with a button/stick held during the banners, then Fight Again;
check coop/training introduction if used. Inspect [native-intro] release and
[overhead] publication/drawing lines. Live pause detection, introduction timing
and these changes across rematch remain unverified. Unsupported-PC capture,
intermittent audio and the 50-update performance target remain outstanding.
