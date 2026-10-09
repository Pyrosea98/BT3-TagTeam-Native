"""Recognize PCSX2's reviewed 16:9 projection patch, including embedded BT4.

The three words are from PCSX2/pcsx2_patches SLUS-21678_428113C2.pnach. The European disc's
SLES-54945_A422BB13.pnach writes two: its native aspect 4/3 at 0x2FF8FC becomes 0x3FE38E34 (16/9) and the
same lui at 0x130D08; its other projection constant (0x2FF9C4, natively 455.11 = 256*16/9) is not patched,
so the European set checks the two words that patch writes, not the USA values moved.
Do not infer aspect from a CRC shared by modified executables. World cameras
inherit these projection values; HUD sprites need matching horizontal scale.
"""
from native_map import A, elf_path
import struct
from prototype import ROOT,elf_reader
from native_map import PAL

WORDS=(((A(0x2FE4CC),0x3FE38E34),(A(0x130BF0),0x3C013F10)) if PAL else
       ((A(0x2FE4CC),0x3FC70FB6),(A(0x2FE594),0x43C70FB6),(A(0x130BF0),0x3C013F10)))


def detected(ram):
    return all(struct.unpack_from('<I',ram,p)[0]==v for p,v in WORDS)


def embedded():
    read=elf_reader(elf_path(ROOT))[2]
    return all(struct.unpack('<I',read(p,4))[0]==v for p,v in WORDS)


def emit_detection(a,output,fail):
    for p,value in WORDS:
        a.li(8,p);a.lw(8,8);a.li(9,value);a.branch(5,8,9,fail)
    a.addiu(output,0,1)
