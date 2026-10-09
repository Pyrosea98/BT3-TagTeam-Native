// Offline conversion of a saved texture's CT32 upload using the runtime GS layout.
#include "runtime/ps2_gs_memory.h"
#include <fstream>
#include <vector>
#include <iterator>
#include <cstring>
#include <cstdio>
#include <cstdlib>
int main(int argc,char **argv) {
    // Optional explicit raw IMAGE mode: input output psm w h tbw upload_w upload_h.
    if(argc!=3 && argc!=9) return 2;
    GSMem::InitLookupTables();
    std::ifstream file(argv[1],std::ios::binary);
    std::vector<uint8_t> b((std::istreambuf_iterator<char>(file)),{});
    if(argc==3 && b.size()<0xc0) return 3;
    auto word=[&](size_t off) { uint64_t value; std::memcpy(&value,b.data()+off,8); return value; };
    const auto tex=argc==3?word(0x50):0,trx=argc==3?word(0x90):0;
    unsigned psm=(tex>>20)&63,w=1u<<((tex>>26)&15),h=1u<<((tex>>30)&15),bw=(tex>>14)&63;
    unsigned uw=trx&4095,uh=(trx>>32)&4095;
    size_t pixels=argc==3?0xc0:0;
    if(argc==9) {
        psm=std::strtoul(argv[3],nullptr,10); w=std::strtoul(argv[4],nullptr,10); h=std::strtoul(argv[5],nullptr,10);
        bw=std::strtoul(argv[6],nullptr,10); uw=std::strtoul(argv[7],nullptr,10); uh=std::strtoul(argv[8],nullptr,10);
    }
    if((psm!=19&&psm!=20)||!bw||bw>63||!w||!h||w>512||h>512||!uw||!uh||uw>512||uh>512||size_t(uw)*uh*4> b.size()-pixels) return 4;
    if(size_t(uw)*uh*4!=size_t(w)*h/(psm==20?2:1)) return 5;
    std::vector<uint8_t> vram(4*1024*1024),indices(w*h);
    for(unsigned y=0;y<uh;++y) for(unsigned x=0;x<uw;++x) {
        uint32_t c; std::memcpy(&c,b.data()+pixels+4*(size_t(y)*uw+x),4);
        GSMem::WriteCT32(vram.data(),0,(uw+63)/64,x,y,c);
    }
    for(unsigned y=0;y<h;++y) for(unsigned x=0;x<w;++x)
        indices[size_t(y)*w+x]=psm==20?GSMem::ReadP4(vram.data(),0,bw,x,y):GSMem::ReadP8(vram.data(),0,bw,x,y);
    std::ofstream out(argv[2],std::ios::binary);
    out.write(reinterpret_cast<const char *>(indices.data()),indices.size());
    return out?0:6;
}
