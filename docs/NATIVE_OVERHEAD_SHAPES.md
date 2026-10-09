# Native overhead shapes and original HUD suppression

## Implemented

- Original status rendering now uses a native wrapper for 0x2188B8, covering generated calls as well as interpreter calls. Suppression checks the live simultaneous manager, fight phase, authenticated HUD subject, known code and exact health/ki/stocks or portrait/name root. It no longer requires an update-scope counter during rendering.
- Other prompt nodes use the original generated renderer, bypassing the guest shim that could suppress gameplay prompts along with status panels. The snapshot lock is released before callbacks. FIGHT/clash/dialogue rendering still requires live verification.
- Show native HUD OFF and Overhead only publish original-HUD suppression while retaining overhead rendering. Once-per-second [native-hud] lines report suppressed status roots and retained prompt nodes.
- Shape choices: Off / Hexagon / Ring / Plate. Hexagon is default; owner and target use the same selected shape with different accents. Names default Off, with Tiny and Normal available only on focused actors. Names are clipped to the reserved frame width.
- Hexagon and Ring use one shader quad with masked portraits, perimeter life/ki gauges and no new shape textures. Diameter is capped at 46 logical pixels regardless of maximum scale settings; cinematic shapes shrink to 80%. Fill alpha is capped at 45%, with cinematic fill approximately 28% at default opacity. Plate alternative is also capped in size and fill.
- Ki stocks/pips, transformation/charge indication and active fusion timer accompany focused gauges. Original HUD OFF forces critical pips and fusion time visible even when their optional display preferences are disabled.
- EN/ES settings are exposed through the actual roster-tools overlay. Legacy saved names/size/opacity values remain accepted. Existing glass styling, approved RidJuampa credits, performance translations, cleanup and rematch handling remain.

## Verification

- Actual settings-to-native publisher: four shapes, Tiny names, original-HUD OFF transport; concurrent PINE/UI acknowledgement checks PASS.
- Compiled HUD checks: status-only roots, stale ownership/code/phase refusal, zero update-scope compatibility, transport limits, diameter caps, cinematic and capture guards PASS.
- Actual saved 128 MiB 5v5: native status wrapper suppresses both real status roots with update scope zero; other prompt root is not classified as a status root. Projection yields one view/six points, preserving caller and borrowed 4096-byte stack; mean 0.0016 ms, maximum 0.0184 ms. This is offline evidence, not a live match.
- 60 Vulkan render/readbacks PASS: EN/ES, 16:9/21:9/4:3, single/two/four viewports, Hexagon/Ring/Plate/Off, cinematic, maximum settings with critical pips/timer forced, and credits/About. Relevant captures visually reviewed. Readbacks use a fixed 640x448 output and can stretch virtual presentation aspect; they do not establish live ultrawide appearance.
- Synthetic compose CPU median 0.159 ms, maximum 43.183 ms including cold setup; GPU median 0.007 ms, maximum 0.014 ms. These are offscreen UI timings, not measured gameplay speed.

Evidence: power-scale-trial/codex-overhead-shapes-{adapter,hud,runtime,gpu}-check.log;
power-scale-trial/overhead-shapes-capture/.

## Build and live follow-up

Both root launchers select repo/build/ps2xRuntime/ps2EntryRunner-overhead-shapes.exe.
SHA256 AD012D6769E51ACE775B0CCBFE2CF7FC6CE6D4C97DC1C29A8BD6C9C90FF24DD4.
Build exit 0: repo/build/codex-overhead-shapes-final-build.log.
Three stable runners retain SHA256 4052022DFE11DED8F98A47F8EACEA75D0EEAD9BC87F5F620853461E5CF79756D.
No game launched, controlled or stopped; no process or GAME_LOCK at final check.

First live check: Show native HUD OFF or Overhead only must remove original status panels while overhead gauges and Ready/FIGHT/clash prompts remain. Verify Hexagon/Ring, cinematic fade, critical stocks/fusion timer, target switching and Fight Again in the same coordinated session. Original-HUD disappearance and live shape appearance are not yet confirmed.

The 50-update performance target remains unmet. Previous ~30 FPS fight sessions need a same-roster native-leaves baseline comparison before attributing recovery. Non-team intro sequencing, unsupported-PC capture and intermittent audio are separate outstanding items.
