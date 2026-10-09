#include "runtime/ps2_interp_decode.h"
#include <cassert>
#include <cstdio>
#include <memory>
int main() {
    Ps2InstructionDecodeCache cache;
    uint32_t random=0x4927abcd;
    for(unsigned i=0;i<100000;++i) {
        random=random*1664525u+1013904223u;
        uint32_t pc=(i%6000)*4, word=random;
        const auto check=[&](Ps2DecodedInstruction d) {
            assert(d.op==word>>26 && d.rs==((word>>21)&31) && d.rt==((word>>16)&31));
            assert(d.rd==((word>>11)&31) && d.sa==((word>>6)&31) && d.funct==(word&63));
            assert(d.imm==uint16_t(word) && d.simm==uint32_t(int32_t(int16_t(word))));
        };
        check(cache.get(pc,word));check(cache.get(pc,word));
        word^=0xffff0001;check(cache.get(pc,word)); // same PC modified without notification
        check(cache.get(pc+4096*4,word)); // colliding address, e.g. another overlay
    }
    assert(cache.hits==100000 && cache.misses==300000);
    Ps2GeneratedPresenceCache presence;unsigned calls=0;
    auto lookup=[&](uint32_t pc){++calls;return pc==0x100000;};
    assert(presence.get(0x100000,lookup));assert(presence.get(0x100000,lookup));assert(calls==1);
    assert(!presence.get(0x104000,lookup));assert(presence.get(0x100000,lookup));assert(calls==3);
    std::puts("PASS decode fields, immediate sign, raw-word invalidation, address collisions (400000 accesses)");
    auto ownedBlocks=std::make_unique<Ps2StraightBlockCache>();auto& blocks=*ownedBlocks;
    std::array<uint32_t,64> words;words.fill(0x24420001);
    auto fetch=[&](uint32_t at){return words[(at>>2)&63];};
    auto boundary=[](uint32_t at){return at==40;};
    auto& first=blocks.get(0,fetch,boundary);assert(first.count==10);
    assert(&blocks.get(0,fetch,boundary)==&first && blocks.hits==1);
    words[3]=0x24420009; // execution must detect a changed word within the hit
    assert(first.code[3].word!=fetch(first.code[3].pc));blocks.invalidate(first);
    assert(blocks.get(0,fetch,boundary).code[3].word==words[3]);
    blocks.get(4096,fetch,boundary);assert(blocks.get(0,fetch,boundary).pc==0);
    words[0]=0x03E00008;assert(blocks.get(0,fetch,boundary).count==0);
    assert(!ps2StraightInstruction(0x54000001) && !ps2StraightInstruction(0x45010000));
    std::puts("PASS block boundaries, mid-block mutation, collisions, control-flow exclusion");
}
