"""Read-only compatibility check for a BT3-Recomp checkout and Tag Team disc profile.

Usage: python native-port/native_port_preflight.py PROFILE_JSON RECOMP_DIR
The profile is an existing Tag Team installer game-profile.json. No ISO is opened.
"""

import argparse
import json
import re
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path)
    parser.add_argument("recomp", type=Path)
    args = parser.parse_args()
    profile = json.loads(args.profile.read_text(encoding="utf-8"))
    root = args.recomp
    setup = (root / "games/bt3/setup.py").read_text(encoding="utf-8")
    match = re.search(r'^ELF_SHA256\s*=\s*"([0-9a-f]{64})"', setup, re.M)
    if not match:
        parser.error("BT3-Recomp expected ELF SHA-256 was not found")
    expected = match.group(1)
    members = profile["members"]
    actual = members["/SLUS_216.78;1"]
    overlay = members["/BIN/DBZP.BIN;1"]
    mod_source = root / "ps2xRuntime/mods/tagteam/tagteam.cpp"
    api = root / "ps2xRuntime/include/ps2x_mod_api.h"
    runtime = root / "ps2xRuntime/src/lib/ps2x_mods.cpp"
    cmake = (root / "ps2xRuntime/CMakeLists.txt").read_text(encoding="utf-8")
    result = {
        "disc_variant": profile.get("runtime_variant"),
        "disc_iso_sha256": profile.get("iso_sha256"),
        "boot_elf_sha256": actual,
        "recomp_expected_elf_sha256": expected,
        "boot_elf_matches_recomp": actual == expected,
        "disc_overlay_sha256": overlay,
        "mod_api_present": api.is_file() and runtime.is_file(),
        "tagteam_source_present": mod_source.is_file(),
        "default_128_mib_ram": bool(re.search(r'set\(PS2X_RAM_MB\s+"128"', cmake)),
    }
    print(json.dumps(result, indent=2))
    return 0 if result["boot_elf_matches_recomp"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
