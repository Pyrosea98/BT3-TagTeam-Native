# Native indexed texture discovery (developer trial)

This first diagnostic dumps textures actually sampled by the GS stream using the
runtime's existing deferred PSMT4/PSMT8 decoder. It does not decode arbitrary EE
texture containers yet. EE source addresses and CPU caller PCs are explicitly
unknown: queued GIF packets do not preserve that provenance. A draw census is
not an identified HUD pass or a confirmed match-clock routine.

Coordinate GAME_LOCK before launch. Use `Play Power Scale HUD diagnostic.cmd`.
After entering a battle, create
`power-scale-trial/hud-native-capture/capture.trigger` (no PINE client).
The new hud-rearm runner polls the trigger at most10 times per wall second.
Exclusive Vulkan skips the shadow parser outside the capture. On arming, it
imports current Vulkan VRAM/register state once before processing the next packet.
Capture stops after60 vsync ticks; at most32 draws per texture/palette identity,
1024 identities and32768 total rows. A changed CLUT is a distinct identity.
Draws exceeding those limits are suppressed without ending the window early.
The trigger is removed when consumed. Create a new trigger after the window
closes to capture again in the SAME game session; import state is renewed.
Logs identify arming, first packet, baseline import success/failure, output start
and window closure. A failed import cannot silently look like a successful capture.
Each attempt writes under capture-1, capture-2, etc. Archive the output root
before another launch; generation numbering starts over in a new process.
Maximum128 distinct indexed texture register identities, dimensions <=512x512.
Each capture subdirectory writes PNGs, textures.jsonl and draws.jsonl; run
`codex_hud_contact_sheet.py <capture-subdirectory>` with the development Python to
make numbered contact sheets. Archive the folder and remove the trigger before
another launch. This tool does not modify the production default launcher.

The Vulkan trial retains the reference GS parser in state-only mode DURING the
capture window. It adds CPU cost and file IO then; capture timings are not
production performance. Outside the window the Vulkan parser bypass is restored.
Normal runs keep the parser bypass and diagnostics off. Decoder receives an owned
4MiB VRAM copy; no guest memory, palette, target or rendering state is rewritten.
Rendered-to-VRAM textures may be stale in the shadow parser; indexed upload-fed
atlases are the initial discovery scope, not a Vulkan readback guarantee.

Draw metadata: global vsync tick, GIF path, primitive, FST/STQ inputs, vertex
positions after XYOFFSET, fixed-point UV (divide by16), STQ, vertex RGBA, blend
register, framebuffer, texture TBP/PSM and CLUT. Every primitive kind is retained
within the bounded window, with only32 samples per identity; this is a sample,
not a complete per-frame command listing. The first partial primitive at the
import boundary can lack vertices from preceding packets; later draws remain.
Texture dimensions come from TEX0. One image per register identity: subsequent
contents or palettes at the same addresses are not new captures. Repeat a new
capture for normal/yellow/red timer states; this version does not prove all those
variants appeared. Source-address correlation and producer-PC transport are next.

Build and live verification are recorded in COLLAB.md. Do not interpret an empty
capture as absent HUD art or claim native UI integration from diagnostic output.

## Upload provenance trial

`Play Power Scale HUD provenance.cmd` uses a separate runner, vanilla/controller-free,
with PS2X_KICKPROBE=2 (existing light PATH2 builder attribution). The normal HUD
diagnostic launcher remains on the live-passed rearm runner.
PS2X_HUD_UPLOAD_TRACE=<directory> observes the ordered GIF stream from startup,
without enabling shadow GS parsing until the usual capture trigger. It saves
at most256 distinct IMAGE chunks targeting DBP10752/10880 or CLUT11392..11424,
at most64KiB per saved chunk, plus uploads.jsonl and [hudupload] log markers.

Metadata includes destination format/stride/transfer dimensions, packet offset,
saved/chunk lengths, original RAM source where known, and builder_ra from existing
PATH2 allocation attribution. A draw trace adds builder_ra and
last_packet_ee_source; caller_pc remains unknown. A builder return address is
not an authenticated clock entry point or a capture of all its arguments.

Sources are retained before arena copying for direct RAM submissions, or resolved
from the existing PATH2 chain map. Unmapped copied PATH3 chains/jobs, scratchpad
and VU packets remain null. Do not treat zero builder_ra as a real caller. IMAGE
chunks can span packets; saved bytes are upload bytes, not unswizzled indices.
Dimensions describe the transfer and can differ from sampled TEX0 dimensions.
The first observed source is a submission-time address; the guest can reuse it.
Use saved bytes rather than reading that address later and assuming it is unchanged.

Archive hud-upload-capture and hud-native-capture before launch. After a vanilla
battle loads, trigger a short draw/texture capture. Match HUD upload chunks with
disc files and preceding [cdread] destination ranges. Copy/decompression and
buffer reuse may prevent direct range correlation; raw-byte matches are a separate
route. Upload tracing/light attribution adds diagnostic cost: verify unarmed speed
early and stop if it is slow. Live source recovery is not yet established.
