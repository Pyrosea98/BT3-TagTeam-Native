"""Read real extended-character PAK bounds from their owned native allocation."""
import struct


def allocation_capacity(ram, pointer):
    u = lambda at: struct.unpack_from('<I', ram, at)[0]
    if not 0x100100 <= pointer <= len(ram)-8 or pointer & 3:
        raise ValueError('Invalid loaded PAK pointer')
    capacity = None
    for header in range(pointer-0x100, pointer-31, 4):
        if u(header) == 0x53484254 and u(header+4) == 1 and u(header+20) == pointer:
            candidate = u(header+24)
            if 0 < candidate <= len(ram)-pointer and u(header+16) >= candidate+32:
                capacity = candidate
                break
    if capacity is None:
        raise ValueError('Loaded PAK has no live owning heap allocation')
    return capacity


def pak_extent(ram, pointer):
    u = lambda at: struct.unpack_from('<I', ram, at)[0]
    capacity = allocation_capacity(ram, pointer)
    count = u(pointer)
    table_bytes = 4*(count+2)
    if not 1 <= count <= 4096 or table_bytes > capacity:
        raise ValueError('Loaded PAK offset table exceeds its allocation')
    offsets = [u(pointer+4+4*i) & ~3 for i in range(count+1)]
    end = offsets[-1]
    if not table_bytes <= offsets[0] <= end <= capacity:
        raise ValueError('Loaded PAK extent exceeds its allocation')
    if any(a > b for a,b in zip(offsets, offsets[1:])):
        raise ValueError('Loaded PAK offsets are not ordered')
    return end

