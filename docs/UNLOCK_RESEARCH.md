# Unlock research (Claude, 2026-10-08): what the 16 KiB progression save holds

Method: byte comparison of three saves (no code reverse engineering yet). Labels: CONFIRMED = read directly from the bytes; HYPOTHESIS = my interpretation.
No public format exists for BT3 (PS2) saves (web search found none).

Files compared (all 16384 bytes): `native-port/savedata/BASLUS-21678DBZT3/BASLUS-21678DBZT3` (ACTIVE, sha 86773da7, the one Codex packs),
`repo/build/ps2xRuntime/saves/.../BASLUS-21678DBZT3` ("progress" save, sha eccb2248), `power-scale-trial/save-backups/20261005-104334/...` ("empty" new-game save, sha 68d52bbe).

## CONFIRMED
1. ACTIVE and "progress" differ by only 8 bytes (offsets 4, 0xA0C, 0xC34-0xC38, 0x1694). So the shipped save is essentially the progress save, NOT the empty card.
2. Empty save: 125 non-zero bytes. Progress/active: about 3,640 non-zero bytes (0x0000-0x302A).
3. Bitmap A at 0xC10..0xC33 (36 bytes = 288 bits): empty save has 179 bits set (a default-unlocked pattern `7f f8 ff fe bf ff bf ff 1f e6 ...`), progress/active has ALL 288 bits set.
4. Three dwords at 0xE0C/0xE10/0xE14: empty = 0, progress = 0x1FFF (13 bits), 0x07FF (11 bits), 0x03FF (10 bits): fully filled low-bit masks.
5. Header dwords: progress = 161, 142, 255, 1, 61; empty = 28, 168, 0, 1, 3. 161 equals the stock character count (ids 0..160); 288 bits cover every id up to 287 (the mod's extended ids 161..252 fit inside the bitmap).
6. 0xA08: progress `ff ff ff ff` + dword 11; empty zeros. 0x200-0x20F: progress `1d 14` style counters, empty `05`.
7. 0x1800-0x2D00 (about 5.3 KB, repeating ~0x90-byte records of little-endian 16-bit ids such as 0x143, 0x14A, 0x14F) and the 0x2D58-0x2FFF area (`ff ff ff ff` every 32 bytes then 0x01 bytes) look like per-slot loadouts/Z-item and per-record flags; they are identical in structure in the empty save, so they are not the unlock gates.

## HYPOTHESIS (needs a live check)
- Bitmap A (0xC10, 288 bits) = character/costume/form availability for the select screens; the 0xE0C masks = stage groups (13 + 11 + 10 = 34); 0xA08/0x200 counters = missions/shop/progress counts.
- Because the shipped save already has the whole bitmap set, the player already gets "everything unlocked" for those tables; "Unlock everything" would then be a SETTING that decides which save variant is seeded (progress variant vs the empty/new-game variant) rather than new logic.
- Not proven: whether the extended characters (161+), the mod's own roster pickers and Power Scale custom conditions read this bitmap at all, or are gated by the mod menu independently. The mod roster pickers do not need the save (all ids load via the mod menu today).

## Proposed mechanism (reversible, never touches the real progress without confirmation)
- Keep TWO seeds in the package: `progression` (current active = progress save, everything unlocked as far as the bitmaps show) and `fresh` (the 125-byte new-game save).
- Installer checkbox "Start with a fresh save (normal progression)" OFF by default; later in mod settings: "Unlock everything" = write a small overlay (OR bitmap A to all ones, set the 0xE0C masks, 0xA08 block) into the CURRENT save after a timestamped backup of those exact bytes; turning it OFF restores the backed-up bytes. Needs the game's own save checksum rule if any (none observed: the progress save differs from active in 8 bytes including 0x4 with no check failure) - UNKNOWN, must be tested live.
- Evidence still needed: (a) user report of what is locked with the current save, (b) a live test with a hand-edited save, (c) optional MIPS trace of the reads of the save buffer (heap buffer, address varies; static lui/addiu scan found no fixed references).
