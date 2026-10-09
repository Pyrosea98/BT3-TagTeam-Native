# Why the 2-player setup screen is invisible and the "loading hook out of date" warning (Claude, read-only, 2026-10-09)

Nothing was edited and no game was touched. Source: `guest_loading_screen.py`, `team_assignment.py`, `native_menu_services.py`, `native_menu_loading.py`, live `controller.log` files and the generated `tagteam-bootstrap.pnach`.

## The causal chain (CONFIRMED by reading the code)
1. The **2-player team setup screen** (`team_assignment.Controller`) and the **controller assignment wizard** do not draw themselves. They call `GuestLoadingScreen().show_picture(self.picture(), surface='menu', client=p)` and wait for `self.screen.presented(p)` (team_assignment.py lines about 133-165). Same machinery as the loading cover.
2. `GuestLoadingScreen.sync()` (guest_loading_screen.py lines about 719-737) first verifies the COMPLETE machine code of every hook piece: `any(p.read(address,len(expected)) != expected for address,expected in code_pieces())`. On any difference it prints `loading hook out of date: restart the emulator` ONCE, sets `self.available=False` and returns False.
3. While `available` is False nothing is published: the picture never reaches the guest, so the screen is invisible. Input still reaches the menu logic, which explains "I cannot see it but Triangle works" and the blind "Selected teams: 1 human player(s)" confirmations.
4. So **the invisible setup screen and the stale warning are the same bug**, not two. (The live warning appears 20 s after the first blind confirms in the 02:13 dev run and in the installed run at 01:07.)

## What is NOT the cause (CONFIRMED by an offline probe)
`code_pieces()` has 24 pieces and 41,222 words. I recomputed them in five environments and compared with the words in the freshly generated `tagteam-bootstrap.pnach` (the file that boot loads into guest RAM):

| Environment | Mismatching words vs the pnach |
| --- | --- |
| base (`PS2X_NATIVE_UI_SLICE=1`, cover 0, en, credits on) | 0 |
| language es | 0 |
| menu credits off | 0 |
| boot credits off | 0 |
| `PS2X_NATIVE_MODE_COVER=1` | **132 words, all in piece 0x07697400** (the cover code) |

So language, credits and the other launcher flags cannot cause it; the only environment value that changes the expected machine code is `PS2X_NATIVE_MODE_COVER` (guest piece 0x07697400 emits JR/NOP when it is not `1`, see `native_menu_loading.py:123`). That variable is read once, from `mod-settings.json`, when the launcher starts (`run_power_scale_native.py:91`), so toggling "Decorative mode loading cover" inside the game does NOT change the running guest code until the next launch. Note for the user: that is why enabling the cover in the Menus page appeared to do nothing.

## What it could still be (needs the live evidence below)
(a) **Guest RAM at one of the verified pieces is overwritten after boot.** Candidates: the team/mode areas that are also used by other features: `0x06911000/0x06911800` (team_assignment CODE/RESOLVE), `0x06930000`, `0x06912000-0x06913000`, the quad hooks `0x06C30000/0x06C31000`, `0x07691000`, `0x07698000-0x0769A000`, the cover data `0x076F6000`, and the overhead/CPU/fusion installs (`extra_reload_forms`, CPU tactics at preparation time) that share the 0x069xxxxx and 0x074xxxxx regions. The warning fires after the first team selection, which is when preparation code starts installing.
(b) **A different process or helper computes `code_pieces()` with another environment**, for example a restart helper or the installed `app.pyw` path launching the controller with a different `PS2X_NATIVE_MODE_COVER`/slice environment than the one that generated the pnach.

## Recommended fixes (for Codex, in order of value)
1. **Log the first mismatch** when the warning fires: piece address, first differing word offset, expected and actual words, plus which module owns that address. One line, then the investigation is trivial.
2. **Do not let any unrelated piece disable the dialogs.** The setup screens only need the loading/menu pieces; verify just those pieces (or compare against the pnach file, the real source of truth, instead of regenerating Python), and treat a mismatch in an unrelated feature piece as a non-fatal log.
3. **Self-heal instead of giving up:** if a verified piece differs and the region is not in active use by a prepared match, write the expected words back (the bootstrap is the known-good image) and retry once; only latch `available=False` after that fails.
4. **Make the cover independent of the dialogs:** the cover must never be able to take down `show_picture`. If the cover is enabled it should have its own piece list.
5. **Make `native_mode_cover` live (or say "restart required"):** either flip the guest code at runtime, or show the standard "Restart required" notice when it is toggled.
6. **Acceptance:** a Vulkan readback with non-black pixels where the setup screen must be, in a 2-human flow and with `native_mode_cover` on and off; a boot-to-setup-screen automated check; and a check that after preparing one match the pieces still compare equal.
