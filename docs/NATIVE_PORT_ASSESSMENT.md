# BT3-Recomp integration assessment (2026-10-05)

Update: an actual Power Scale/expanded-2x native trial is now built. Binary
comparison established that the overlay is an exact stock body preceded by a
2 KiB initializer, and the ELF keeps its loaded layout with 31 byte changes.
The executable was regenerated and a PINE bridge reuses the installed Python
Tag Team hooks. The earlier stock-only limitations below describe the original
upstream checkout; current implementation/test status is in
`power-scale-trial/README.md`. No native mod DLL is required by this trial.

Source examined: z3xox/BT3-Recomp at `e22a34beb564e2d0f32bd60b02f0a95d9645ddcc`.
Local checkout: `native-port/repo/`. The existing PCSX2 installations and both ISOs were not modified.

## Architecture

BT3-Recomp statically translates the USA `SLUS_216.78` EE executable and the
`BIN/DBZP.BIN` gameplay/menu overlay to C++ during setup. It runs translated
guest code with PS2 memory and device services supplied by `ps2xRuntime`; it is
not a clean-room rewrite of BT3 gameplay. The graphics backend is a separate
choice and does not remove the guest address and resource-layout assumptions.
The front-end extracts data from the user's ISO after verifying the boot ELF.

The runtime has a versioned DLL/SO mod API (`ps2x_mod_api.h`) with guest-function
lookup/replacement, frame and pad access, frame callbacks and host HUD feeds.
Replacement supports both the main executable table and the DBZP overlay table.
The default CMake setting backs guest RAM with 128 MiB while exposing the native
32 MiB size to ordinary game code. This matches Tag Team's extended heap and
code-cave ranges. The repository's README and mods README claim a shipped Tag
Team mod, but this checkout contains neither `ps2xRuntime/mods/tagteam/` source
nor a `tagteam.dll`/`.so`. It must be obtained from its author or independently
ported; the API alone is not the gameplay implementation.

## Power Scale compatibility gate

The port hardcodes stock USA boot ELF SHA-256
`811188ba9b416500d921cd4d9514df0cbf42f3a41a99cf5aac5a3da37171bf99`.
The stock ISO in this workspace has that hash and DBZP hash
`30f61f9c78c3859e5dd4fcfd8df6753b0f2d2c64beb924b92da5b2eaaa5e09cc`.
Power Scale BETA 1.5.1 instead has boot ELF
`b8ac3756da720f8a6fa3f9ab77a3c54f13f0735b159ad9098860e744dd9732f7`
and DBZP `038c002ad24dcbd88ae6e8868006fe2eb7cdab06f482525514fef3e708b205f7`.
These hashes are from the existing installer profiles. `PS2X_SETUP_FORCE=1`
only bypasses a refusal; it does not repair function maps, overlay entrypoints,
generated patches, or runtime hooks. The front-end independently verifies the
stock ELF, so a forced developer build would still not make a normal Power Scale
install work. No Power Scale build is attempted here.

## Concrete integration path

1. Build an isolated stock USA BT3-Recomp tree from the stock ISO. Confirm a
   stock 1v1 first, then get the actual Tag Team DLL/source matching API v1.
   If unavailable, port the smallest working PCSX2 path to a new DLL: detect
   menu/selection, create one extra fighter, then 1v2. Keep all writes in the
   new tree. Do not copy PCSX2's Python process-watcher and MIPS code caves
   blindly: move equivalent logic to host C++ function/frame hooks, with guest
   memory bounds and lifecycle checks.
2. Reproduce stock Tag Team stages incrementally: selection capture, extra
   resource ownership, spawn/AI/targeting, uneven-team parity, camera, HUD,
   defeat, transformations/fusion, and cinematics. Preserve the guest game's
   selected roster rows and HP, as the current installer does. Validate each
   stage with a short match before adding the next.
3. Add a separate Power Scale target profile keyed by **both** exact ELF and
   DBZP hashes. Diff the two binaries' code and data layout, regenerate or
   review the main and overlay function maps, VU1 offsets/hashes and every
   source-patch anchor, and audit runtime overrides keyed by guest addresses.
   Verify in-game resources and AFS extraction with the Power Scale ISO. Any
   address that moved needs a profile-specific mapping; any changed function
   needs review, not a hash-gate bypass.
4. Run Power Scale native 1v1, then 1v2 and uneven 1v5 with the audited 0–160
   IDs. Keep direct 212, 186, 194 and other 161–252 extra-fighter selections
   gated until independently loaded resource ownership/bounds are established.
   ID 83 native-leader transformation to 212 is a separate observed path.
   Compare native HP (including Cell Jr's 150,000), attacks, costume reload,
   transformations, and fusion with the PCSX2 baseline.
5. Triage cinematic freezes independently. The beta.36 Power Scale ultimate
   rush freeze has a RAM snapshot but no CPU PC/registers; it does not establish
   the same defect in BT3-Recomp. Capture a native stack/guest PC and recent
   hook events if it recurs.

The isolated stock Windows runner and portable tree are now built in
`native-port/stock-deploy/`. The remaining stock gate is an actual front-end
ISO install and 1v1 gameplay test. Access to the separately shipped Tag Team
native mod source/binary remains a second gate. A Power Scale native build
would have two unproven layers until those checks are complete.

## Read-only preflight

`python native-port/native_port_preflight.py PROFILE_JSON native-port/repo`

Exit code 0 means the profile's boot ELF matches this source tree's stock gate;
2 means it does not. This checks recorded profile metadata, not the ISO bytes
or gameplay. It also reports whether the checkout includes the mod API,
Tag Team source, and default 128 MiB RAM setting.
