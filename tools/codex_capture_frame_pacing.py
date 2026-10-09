"""Take one read-only RAM/log capture at a user-selected menu boundary."""
import argparse
import json
from pathlib import Path
import struct
import time

import capture_freeze


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('label', choices=('pre-match-select', 'post-match-select'))
    args = parser.parse_args()
    folder = Path(__file__).resolve().parent/'power-scale-trial/frame-pacing-captures'/(
        time.strftime('%Y%m%d-%H%M%S')+'-'+args.label)
    capture_freeze.capture(folder)
    ram = (folder/'ram.bin').read_bytes()
    u = lambda address: struct.unpack_from('<I', ram, address)[0]
    manager = u(0x2ff10c)
    fields = {hex(address): hex(u(address)) for address in
              (0x333700, 0x333704, 0x3337b8, 0x3337c0, 0x2feb14, 0x2c9fc8)}
    summary = {'label': args.label, 'scene_manager': hex(manager), 'globals': fields,
               'note': 'RAM is read live, without a guest hold. IO registers such as VIF1_STAT are not part of this RAM capture.'}
    if 0x100000 <= manager < 0x2000000-0x690 and manager % 4 == 0:
        summary['scene'] = hex(u(manager+0x18))
        summary['manager_fields'] = {hex(offset): hex(u(manager+offset)) for offset in
                                     (0x14, 0x624, 0x68c)}
    (folder/'pacing-boundary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(folder)


if __name__ == '__main__':
    main()
