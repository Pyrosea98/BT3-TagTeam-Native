# M5.2 live follow-up fixes

The UI Slice launcher selects `ps2EntryRunner-live-mode-fixes.exe`.
SHA256: `0590F845FCE3B6EF766D07E0AA43EB933BBAFAD117DAFCD1FC2FA08DD4A0A849`.

## Implemented and checked

- Replay intro is restricted to Team Battle; FFA, co-op and training request
  their prepared start gate directly. Start wait logs mode and human count.
- If a mode omits the acknowledgement, release requires the same manager,
  generation marker/count, fight phase 3, disabled start gate, cleared input
  hold, every captured actor pointer/physical identity and restored CPU seats.
  Merely being in phase 3 while still held cannot complete release.
- Late diagnostic strings after accepted/released start are logged with mode,
  phase, acceptance and exact text. They cannot create/reopen a failure cover.
  Native lifecycle rejects failure after start acceptance. Lease expiry cannot
  bring the cover back over an accepted intro/match.
- A real preparation failure replaces the stage/percentage line. Its labels
  sit below the clean progress bar, with no Ready/100% underneath.
- HUD geometry and text now anchor to presentation edges while preserving
  glyph/sprite proportions. Watched/target plates sit below the stock top HUD;
  training stays bottom-left; feed stays right. Loading covers stay centred.
  FFA rows fit below the stock bars. Flat HUD caps remove the grey fragments
  from training, FFA, killfeed and fusion plates. They are display-only.
- Training counters recognize the actual revival -> killfeed damage chain
  (`1CE630 -> 070B7000`, magic `52565631`, previous `07411000`), as well as the
  direct damage hook. They do not wrap damage in other modes or when disabled.

Evidence: build exit 0 in `repo/build/codex-live-mode-fixes-build.log`;
140 actual Vulkan render/readback cases PASS in
`power-scale-trial/codex-live-mode-fixes-gpu.log`; EN/ES captures and contact
sheets in `power-scale-trial/native-ui-live-fixes-capture`, including HUD
16:9/21:9/4:3. English/Spanish ultrawide and 4:3 captures visually checked.
Native lifecycle, HUD/hook guards and settings/late-diagnostic checks PASS.
The actual start-wait loop passed Team Battle, exhibition, FFA 0/1/2 players,
co-op and training cases with/without ACK and changed-identity rejection.

## Cleanup and transformation audit: unresolved

`codex_m52_live_failure_audit.py` produces the archived RAM audit
`power-scale-trial/codex-m52-live-failure-audit.json` without game writes.

The training failure capture has zero extended heap bounds. Only 771 bytes
are nonzero, on pages `02E03000`/`02E04000`. The entire affected span
`02E03B50..02E04080` is an exact copy of `0056D350..0056D880`. Teardown was
logged complete before this capture. Who writes/owns this later stat copy is
unknown; it has not been blindly cleared or classified as leaked allocations.
Self-healing cleanup/Retry is not implemented until ownership is established.

Frozen `250570..2505A8` is a packet-list search: object+44 supplies the list,
halfword+10 identifies type, halfword+6 ends search, word+0 advances to the
next packet. A nonmatching node with flags=0 and next offset=0 never advances.
The freeze's packet pointer/requested type is absent from the capture, so
NULL vs malformed packet is not proven. Other forms also log failed file loads
(99/103, 111/115, 123/127); 291/295 alone do not prove a missing form bundle.
Runtime names and ISO names differ: a name such as Nail does not establish
the model family for a Power Scale slot. No name-based rejection was added.

No loader-recovery, transformation watchdog or performance improvement is
claimed. Claude's steady-fight bridge measurements make the preparation burst
an unsuitable performance comparison; the poll-slowing A/B is withdrawn.
Fresh interpreter profile and native/block/AOT work remain the performance
path after these gameplay blockers. Stable three runner hashes are unchanged.

## Live check

No game was launched/stopped. Use the UI Slice launcher for one coordinated
FFA start and training counter test; check HUD positions on the user's 21:9
screen. The 5v5-to-training cleanup and Goku GT fourth-costume transformation
freeze remain open and should not be treated as fixed by this build.
