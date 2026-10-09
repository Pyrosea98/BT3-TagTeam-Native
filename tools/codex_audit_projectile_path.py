"""Preserve local ELF evidence for projectile tracing; no game connection.

Function names are investigation labels, not established gameplay semantics.
In particular, the generic effect initializer is not a ki-specific spawn.
"""
from pathlib import Path
import hashlib
import json
import struct
import sys
import capstone

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / 'power-scale-trial/controller/game/tools')]
from codex_roster_overlay import install
install()
import fresh_team_combat as core

RANGES = {
    'generic_effect_allocate': (0x1AD7B8, 0x1AD988),
    'generic_effect_initialize': (0x1AD988, 0x1AD9F8),
    'contact_update_dispatch': (0x1AF9C0, 0x1AFA10),
    'effect_record_update': (0x12E160, 0x12E258),
    'record_effect_flags': (0x12E9B0, 0x12EA10),
    'record_effect_emit_a': (0x12F1A8, 0x12F328),
    'record_effect_emit_b': (0x12F328, 0x12F54C),
    'secondary_effect_allocate': (0x187BE0, 0x187C50),
    'contact_block': (0x1B0030, 0x1B0238),
}

def main():
    path = core.elf_path(core.ROOT)
    blob, segments, read = core.elf_reader(path)
    dis = capstone.Cs(capstone.CS_ARCH_MIPS,
                      capstone.CS_MODE_MIPS64 | capstone.CS_MODE_LITTLE_ENDIAN)
    dis.skipdata = True  # R5900 extensions can appear as undecoded bytes.
    report = dict(elf=str(path), sha256=hashlib.sha256(blob).hexdigest(),
                  status='STATIC EVIDENCE ONLY; KI SPAWN/AIM NOT IDENTIFIED', functions={})
    for name, (lo, hi) in RANGES.items():
        calls = []
        for va, offset, size, _ in segments:
            for i in range(0, size - 3, 4):
                pc = va + i
                if not 0x100000 <= pc < 0x2B0000:
                    continue
                word = struct.unpack_from('<I', blob, offset + i)[0]
                if word >> 26 in (2, 3) and ((word & 0x3FFFFFF) << 2) == lo:
                    calls.append(dict(pc=pc, kind='jal' if word >> 26 == 3 else 'j'))
        report['functions'][name] = dict(begin=lo, end=hi, callers=calls,
            instructions=[dict(pc=x.address, bytes=x.bytes.hex(),
                               text=x.mnemonic+' '+x.op_str)
                          for x in dis.disasm(read(lo, hi-lo), lo)])
    output = HERE / 'power-scale-trial/native-projectile-path.json'
    output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(output)
    print(report['status'])

if __name__ == '__main__':
    main()
