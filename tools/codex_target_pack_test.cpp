// Test ABI for the same generated C++ bodies used by the production adapter.
#include "runtime/ps2_tagteam_target_pack.h"
#include <cstring>
struct Ops {
    uint8_t *ram;uint64_t *regs;
    uint32_t u32(unsigned r) const { return uint32_t(regs[2*r]); }
    uint64_t u64(unsigned r) const { return regs[2*r]; }
    void s32(unsigned r,uint32_t v) { if(r)regs[2*r]=uint64_t(int64_t(int32_t(v))); }
    void u64(unsigned r,uint64_t v) { if(r)regs[2*r]=v; }
    uint32_t read32(uint32_t p) { uint32_t v;std::memcpy(&v,ram+(p&0x7ffffff),4);return v; }
    uint8_t read8(uint32_t p) {return ram[p&0x7ffffff];}
    uint64_t read64(uint32_t p) { uint64_t v;std::memcpy(&v,ram+(p&0x7ffffff),8);return v; }
    void write64(uint32_t p,uint64_t v) { std::memcpy(ram+(p&0x7ffffff),&v,8); }
    void write32(uint32_t p,uint32_t v) { std::memcpy(ram+(p&0x7ffffff),&v,4); }
    void load128(unsigned r,uint32_t p) {if(r)std::memcpy(regs+2*r,ram+(p&0x7ffffff),16);}
    void store128(unsigned r,uint32_t p) {std::memcpy(ram+(p&0x7ffffff),regs+2*r,16);}
};
extern "C" __declspec(dllexport) int run_targets(uint8_t *ram,uint64_t *regs,uint32_t entry,uint32_t *exit) {
    Ops ops{ram,regs};return ps2x::tagteam::frozen::execute(ram,entry,ops,*exit);
}
