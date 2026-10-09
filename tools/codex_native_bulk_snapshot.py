"""Bounded native bridge reads; caller retains existing frame-boundary hold."""
import struct

RAM_BYTES=0x08000000
CHUNK=0x40000


def read_ranges(p,size=RAM_BYTES):
    if type(size) is not int or not 0<size<=RAM_BYTES:
        raise ValueError('Invalid native RAM capture size')
    result=bytearray(size)
    for address in range(0,size,CHUNK):
        length=min(CHUNK,size-address)
        data=p._exchange(b'\x10'+struct.pack('<2I',address,length),length)
        if len(data)!=length:raise ValueError('Incomplete native bulk snapshot reply')
        result[address:address+length]=data
    return bytes(result)


def read_ram(p):return read_ranges(p)
