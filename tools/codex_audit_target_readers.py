"""Offline inventory of native actor-manager reads and physical-getter calls.

This inventories candidates; a manager load is not evidence of opponent aiming.
No game connection, memory write or routing patch.
"""
from pathlib import Path
import hashlib
import json
import struct
import sys
import capstone
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(HERE/'power-scale-trial/controller/game/tools'))
from codex_roster_overlay import install
install()
import fresh_team_combat as core

def main():
    path=core.elf_path(core.ROOT);blob,segments,read=core.elf_reader(path)
    dis=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS64|capstone.CS_MODE_LITTLE_ENDIAN)
    dis.skipdata=True
    routed=[(at,at+40) for at,_ in core.selector_sites()]
    rows=[]
    for va,offset,size,_ in segments:
        begin=max(0,(0x100000-va+3)//4*4);end=min(size,0x2B0000-va)
        for i in range(begin,max(begin,end-3),4):
            word=struct.unpack_from('<I',blob,offset+i)[0];pc=va+i
            kind='actor-manager-load' if word&0xFFE0FFFF==0x8F80A8A4 else \
                 'physical-getter-call' if word==(3<<26)|(0x1DC178>>2) else None
            if kind is None:continue
            start=max(va,pc-24);stop=min(va+size,pc+100)
            data=read(start,stop-start)
            instructions=[dict(pc=x.address,text=x.mnemonic+' '+x.op_str) for x in dis.disasm(data,start)]
            rows.append(dict(pc=pc,kind=kind,routed=any(lo<=pc<hi for lo,hi in routed),
                instructions=instructions,
                has_native_stride=any('0x1600' in x['text'] for x in instructions)))
    out=HERE/'power-scale-trial/native-target-readers.json'
    report=dict(elf=str(path),sha256=hashlib.sha256(blob).hexdigest(),
        status='STATIC CANDIDATES ONLY; NOT PROVEN AIM READERS',routed_blocks=[lo for lo,_ in routed],readers=rows)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f'{out}: manager loads={sum(x["kind"]=="actor-manager-load" for x in rows)}, '
          f'physical getter calls={sum(x["kind"]=="physical-getter-call" for x in rows)}')
    print('Native stride candidates:',[hex(x['pc']) for x in rows if x['has_native_stride'] and not x['routed']])

if __name__=='__main__':main()
