"""Exclude verified native audio ring bytes, retaining their object/header pointers."""
import struct
from native_map import A, elf_path
from prototype import ROOT, elf_reader
from codex_roster_resources import allocation_capacity


def audio_data_literals(ram, addresses):
    if not addresses:
        return set(), []
    native = elf_reader(elf_path(ROOT))[2]
    # The allocator call and stream constructor define precisely which bytes
    # are ring data. Modified/unsupported implementations receive no exception.
    for start, length in ((0x264CE4,0x64),(0x272930,0x1F0)):
        at=A(start)
        if ram[at:at+length] != native(at,length):
            return set(), []
    table=A(0x2C7060)
    original=native(table,6*20)
    u=lambda at:struct.unpack_from('<I',ram,at)[0]
    verified,receipts=set(),[]
    for index in range(6):
        desc=table+20*index
        owner,size,kind=struct.unpack_from('<3I',original,20*index)
        if (u(desc),u(desc+4),u(desc+8)) != (owner,size,kind):
            continue
        buffer,state=u(desc+12),u(desc+16)
        if not 0x100100<=buffer<=len(ram)-size or not 0<size<=0x100000:
            continue
        state_base=A(0x2C9288)
        if not state_base<=state<=state_base+15*0xC8 or (state-state_base)%0xC8:
            continue
        if ram[state]==0 or ram[state+3]!=2:
            continue
        try:
            capacity=allocation_capacity(ram,buffer)
        except ValueError:
            continue
        if capacity!=size:
            continue
        aligned=(buffer+63)&~63
        # Native272930: two channel workspaces, then a sector-aligned ring.
        ring=aligned+2*0x40C0
        length=((size-(aligned-buffer)-2*0x40C0-0x124)//2048)*2048
        if length<=0 or ring+length>buffer+capacity:
            continue
        if (u(state+0x2C),u(state+0x20),u(state+0x24),u(state+0x28))!=(aligned,ring,length,0x24):
            continue
        found={at for at in addresses if ring<=at and at+4<=ring+length}
        if found:
            verified.update(found)
            receipts.append(dict(descriptor=desc,state=state,allocation=buffer,capacity=capacity,
                                 data_start=ring,data_bytes=length,literals=sorted(found),
                                 evidence='Exact native constructor + live SHBT owner + stream ring fields'))
    return verified, receipts
