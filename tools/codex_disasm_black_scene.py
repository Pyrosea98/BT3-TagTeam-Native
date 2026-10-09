from pathlib import Path
import struct,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'power-scale-trial/controller/game/tools'))
from prototype import ROOT,elf_reader
from native_map import elf_path
import capstone
read=elf_reader(elf_path(ROOT))[2]
dis=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS64|capstone.CS_MODE_LITTLE_ENDIAN)
data=read(0x100000,0x1C0000)
hits=[]
for offset,(w,) in enumerate(struct.iter_unpack('<I',data)):
    if (w&0xFFFF)==0x19F0 and w>>26 in (43,63):hits.append(0x100000+offset*4)
for at,size in ((0x127120,0x10),(0x1271E8,0xC8),(0x128500,0xC0)):
    print(hex(at))
    for i in dis.disasm(read(at,size),at):print(f'{i.address:08X} {i.mnemonic} {i.op_str}')
