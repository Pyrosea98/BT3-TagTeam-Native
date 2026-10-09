# Native P3 and P4: implementation brief (Claude, read-only analysis, 2026-10-09)

User request: the native runtime and its Shift+Tab overlay only know two players. Add **P3 and P4** to the native options so they can be mapped (device, buttons, sticks), copying the P2 behaviour, and stop depending on the Python SDL capture for seats 3 and 4. Nothing below was edited by me; it is a map for Codex.

## Where the "2 players" limit lives (CONFIRMED by reading the source)
| What | File and line | Today |
| --- | --- | --- |
| Player count constant | `repo/ps2xRuntime/include/runtime/pad_config.h:101` | `static constexpr size_t kPlayerCount = 2;` (comment: "BT3 is a 1v1 fighter"); `m_players` is `std::array<PadPlayerConfig, kPlayerCount>` (line 141) |
| Per-player config files and loop bounds | `src/lib/pad_config.cpp` lines about 626-1072 (`load`, `save`, `snapshot`, `setDevice`, `setBind`, `resetPlayer`, `playerConfigPath`) | `savedata/pad_p1.conf`, `pad_p2.conf`; every loop is bounded by `kPlayerCount` (the `player N` index in the file is validated against it, lines about 772 and 900) |
| Overlay Controllers tab | `src/lib/ps2_settings_overlay.cpp` lines about 907, 1068, 1083, 4049 | loops and bounds use `kPlayerCount` |
| Overlay/launcher player combo | `src/frontend/fe_pages.cpp:598-607` | `static const char *const kPlayers[] = {"Player 1", "Player 2"}` and `fe::comboRow("Player", &player, kPlayers, kPlayerCount)` |
| Debug panel names | `src/lib/ps2_debug_panel.cpp:1482-1486` | `playerNames[] = {"Player 1", "Player 2"}` |
| Guest pad ports | `src/lib/Kernel/Stubs/Pad.cpp:29-30` (`kPadPortCount = 2`, `kPadSlotCount = 2`), `padPlayerForPortSlot` near line 296 | stock BT3 only polls ports 0 and 1 |

## Important design point
The stock game only reads **ports 0 and 1**, so P3 and P4 must NOT be added as guest pad ports. The mod already has a private path for seats 3 and 4 (Python today, `quad_controller.py`). The native option for P3/P4 should therefore: (a) extend the CONFIG layer (devices, binds, UI, files) to 4 players, and (b) feed seats 3 and 4 into the same private mailbox from C++, replacing the Python SDL capture.

## The private mailbox protocol (CONFIRMED from `quad_controller.py`, `Bridge.poll`)
- Addresses (EE): `BASE=0x06C10000`; `PADS=BASE+0x4000`; `MAILBOX=BASE+0x5000`; `CONTROL=BASE+0xF000`; `MAGIC=0x51494E31`.
- Seat record = **32 bytes** each, two records (seat 3 then seat 4) at `MAILBOX` and `MAILBOX+32`: `struct '<I4f12x'` = one 32-bit digital word, then four floats (left X, left Y, right X, right Y, each normalised to -1..1, 18% dead zone, circular clamp), then 12 zero bytes.
- Digital word bits (from `input_binding.BUTTONS`, `MASKS = 1<<index`): select 0, l3 1, r3 2, start 3, up 4, right 5, down 6, left 7, l2 8, r2 9, l1 10, r1 11, triangle 12, circle 13, cross 14, square 15. The poller also publishes dominant-axis direction bits: left stick into bits 16-19 and right stick into bits 20-23 (up 4 / down 8 vs left 1 / right 2 nibble per stick, see `encode_pad`). Triggers count as l2/r2 above 10000/32767.
- Publication handshake (all inside one frame boundary so the guest never sees a torn pad): read `CONTROL` first 16 bytes `(magic, owner_a, owner_b, active)`; require `magic==MAGIC` and `active!=0`; remember the owner pair and fail if it changes; require `read(core.ACTORS)==owner_a` and `core.MODE == (1, owner_b, owner_a, owner_b)`; then write `CONTROL+28 = 1` (writer flag), write the 64-byte mailbox, bump the sequence (non-zero, wraps to 1), write it at `CONTROL+16`, write `CONTROL+28 = 0`. The guest copies the mailbox, checks writer flag and sequence, and falls back to neutral if stale.
- SDL device indices used today: seats 3 and 4 = gamepad indices (2, 3) (`Bridge(devices=(2,3))`). In the native config these become the per-player `Gamepad N` device or `Keyboard`.

## Work items
1. `kPlayerCount = 4`; `pad_p3.conf` and `pad_p4.conf` created from the P2 defaults on first run (same bind table; default device `None` for P1/P2 as today, and for P3/P4 default to the next free gamepad or none); migrate nothing (old files stay valid); keep reading `player N` indices up to 3.
2. Overlay Controllers tab and `fe_pages.cpp` combo: four entries (Player 1..4) with the same device picker, bind capture, test area and rumble per player; update the debug panel names; make sure "hold the button or key to capture" works for the new rows.
3. Device assignment: two players must not claim the same gamepad index; show "(in use by Player N)"; hot-plug rescan; per-device persistence by vendor/product id if cheap.
4. Native mailbox writer: a C++ function called at the frame boundary (where the pad override already runs) that implements the handshake above for seats 3 and 4 using the per-player config, so Python no longer needs SDL for seats 3 and 4. Keep P1/P2 on the existing guest ports. Only active when the quad controller is installed and the owner/mode checks pass (otherwise write nothing).
5. Remove or bypass the Python `ControllerCapture`/`Bridge` for seats 3-4 once the native writer works (keep it behind a fallback env var for one release); migrate any existing mod-side P3/P4 bindings.
6. Tests: unit test of the encoder against `encode_pad` output for sample button/axis sets; offline replay on a saved four-seat state proving the guest reads the native record (the existing quad checks); overlay screenshot with four players; a loopback fixture that simulates seats 3 and 4 buttons.
7. Android/netplay hook: the same function should accept a seat record from any source (touch pad, remote peer) so `InputSource -> Seat` stays platform-neutral (see `INSTALLER_PLAN.md`).

## ADDENDUM 2026-10-09 (Claude, investigation only): what the Python path REALLY is, and the staged plan

User decision: "investigate only"; Codex implements. Findings from reading `quad_controller.py`, `quad_menu_input.py`, `controller_assignment.py`, `controller_mailbox.py`:

### Three separate Python input paths feed seats 3 and 4 (all encode with `quad_controller.encode_pad`, 32 bytes per seat `<I4f12x`)
| Path | Used when | CONTROL / MAILBOX / TOKEN (EE) | MAGIC | Poll preconditions |
| --- | --- | --- | --- | --- |
| In-match quad pads (`quad_controller.Bridge`) | 3-4 human fights | `0x06C1F000` / `0x06C15000` / `+0x80` | `0x51494E31` | control `(magic, owner_a, owner_b, active!=0)`; `read(core.ACTORS=0x2FEB14)==owner_a`; `core.MODE==(1,owner_b,owner_a,owner_b)`; owner pair must not change |
| Character-select quad menu (`quad_menu_input.Bridge`) | 3-4 humans choosing fighters | `0x06C3F000` / `0x06C3F100` / `0x06C3F080`; code at `0x06C30000`, pad stride `0x1C0` | `0x514D4931` | `Mailbox.identity`: code unchanged, scene manager at `mode_menu.SCENE_MANAGER` with `scene+0x18 == 40`, native menu guard magic present; writes control `(MAGIC, scene, 2, 1)` |
| Controller-assignment wizard (`controller_assignment.Bridge`) | the "Assign controllers" screen | `0x06933000` / `0x06933100` / `0x06933080`; code at `0x06930000` | `0x43415331` | only the magic at CONTROL |

All three write `CONTROL+28=1` (writer flag), the 64-byte mailbox, a non-zero wrapping sequence at `CONTROL+16`, then `CONTROL+28=0`. The transport that moves the bytes (`controller_mailbox.py`) is the PCSX2-era "narrow authenticated mailbox" (Read/WriteProcessMemory or /proc fd mapping, token written through PINE). **UNVERIFIED: whether this transport has ever worked with the NATIVE runner for 3-4 humans; no live 3-4 human match exists in the logs (all live co-op tests were 1-2 humans).** So 3-4 player play may not work natively at all today, independent of the missing UI.

### Native conversion (what the C++ writer must do)
- Source of the seat state: `PadConfig::instance().poll(2)` and `poll(3)` giving `PadPacket{buttons (active-low 16 bit), lx,ly,rx,ry (0x80 centre)}`.
- The PS2 pad bit order equals the mod word's low 16 bits: select 0, l3 1, r3 2, start 3, up 4, right 5, down 6, left 7, l2 8, r2 9, l1 10, r1 11, triangle 12, circle 13, cross 14, square 15. So `word = (~buttons) & 0xFFFF`. Floats: `(byte-128)/127` clamped to -1..1; add the dominant-axis direction bits exactly as `encode_pad` does (left stick bits 16-19, right stick bits 20-23: up 4 / down 8 / left 1 / right 2 nibble per stick, dominant axis only, threshold 0.5).
- Write all three CONTROL blocks from ONE service called from `ps2xTagteamFrame` (`ps2x_tagteam_bridge.cpp:543`, direct `ram` access, same thread as the guest so no tearing), each only when its own preconditions in the table hold, never when the magic is absent. Disable the Python bridges when `PS2X_NATIVE_SEAT_PADS=1` (the launcher sets it) by making the three `Bridge.poll` return False immediately; keep them as a fallback for one release.

### Defaults and device assignment
`kPlayerCount=4`; P1 and P2 keep today's defaults. P3 and P4 must default to explicit devices (`Gamepad 2` and `Gamepad 3`, "N-th controller"), NOT `None`: `None` means "any pad + keyboard" and `pollLegacyAuto` would make P3 mirror pad 0 when fewer than 3 pads exist. A missing pad gives a neutral seat. Two players must never own the same gamepad index; show "(in use by Player N)". Config files `pad_p3.conf` and `pad_p4.conf` from the P2 defaults. UI changes: `fe_pages.cpp:606` `kPlayers[]` (4 names), `ps2_settings_overlay.cpp` (about lines 907, 1068, 1083, 4049), `ps2_debug_panel.cpp:1486` names.

### Staged plan (suggested)
1. **Stage 1 (config + UI, low risk):** `kPlayerCount=4`, defaults, files, UI rows; the poll generalises already (`PadConfig::poll` is player-agnostic except `pollLegacyAuto`).
2. **Stage 2 (native writer):** the three-block service above plus the env switch; offline test against a saved four-seat state with synthetic `PadPacket`s (assert the exact 64 bytes, handshake order and that a stale owner writes nothing).
3. **Stage 3 (live):** needs 3-4 controllers (or a keyboard device on P3 and virtual pads) for one real 4-human match; until then label 3-4 player as experimental.
