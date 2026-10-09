#include "repo/ps2xRuntime/src/lib/ps2_hud_upload_trace.cpp"
#include <vector>
#include <stdexcept>
int main() {
    _putenv_s("PS2X_HUD_UPLOAD_TRACE","power-scale-trial/hud-upload-fixture");
    std::vector<uint8_t> packet;
    auto qw=[&](uint64_t a,uint64_t b) { size_t off=packet.size(); packet.resize(off+16); std::memcpy(packet.data()+off,&a,8); std::memcpy(packet.data()+off+8,&b,8); };
    qw((1ull<<60)|2,14); // packed A+D: BITBLTBUF and TRXREG
    qw((10752ull<<32)|(1ull<<48),0x50);
    qw(64ull|(32ull<<32),0x52);
    qw((2ull<<58)|2,0); // IMAGE, two qwords, split across submissions
    qw(0x1111111111111111ull,0x2222222222222222ull);
    const auto original=packet;
    GifArbiterPacket first; first.pathId=GifPathId::Path3; first.data=packet.data(); first.size=packet.size(); first.eeSource=0x100000; first.owner=0x123458;
    ps2xHudObservePacket(first);
    if(packet!=original) throw std::runtime_error("observer changed input");
    uint64_t next[2]={0x3333333333333333ull,0x4444444444444444ull};
    GifArbiterPacket second; second.pathId=GifPathId::Path3; second.data=reinterpret_cast<uint8_t *>(next); second.size=16; second.eeSource=0x200000;
    ps2xHudObservePacket(second);
    uint64_t unknown[4]={(2ull<<58)|1,0,0x5555555555555555ull,0x6666666666666666ull};
    GifArbiterPacket third; third.pathId=GifPathId::Path3; third.data=reinterpret_cast<uint8_t *>(unknown); third.size=32;
    ps2xHudObservePacket(third);
    if(ps2xHudPacketSource()!=UINT32_MAX) throw std::runtime_error("unknown source retained old attribution");
    std::puts("PASS: split IMAGE uploads observed; input unchanged; unknown metadata cleared");
}
