#include "ps2_runtime_macros.h"
#include <cassert>
#include <algorithm>
#include <vector>
#include <fstream>
#include <iterator>
extern void ps2xTagteamTraceKiBranch(uint8_t *,R5900Context *,uint32_t,uint32_t);
int main() {
    _putenv_s("PS2X_KI_TRACE","1");
    std::freopen("power-scale-trial/codex-ki-trace-check.log","w",stderr);
    std::vector<uint8_t> ram(PS2_RAM_SIZE);
    auto put=[&](uint32_t p,uint32_t v){std::memcpy(ram.data()+p,&v,4);};
    const uint32_t m=0x180000,actor=0x190000,sp=0x300000,effect=0x400000,payload=0x410000;
    put(0xD8080,1);put(0xD8084,4);put(0xD8088,m);put(0xD808C,4);put(0x2FEB14,m);put(m,2);
    for(uint32_t i=0;i<4;++i){put(0xD8040+4*i,actor+i*0x2000);put(actor+i*0x2000+12,i);}
    put(0xD8000,3);put(actor+0x948,218);put(sp+0xA0,0x1769ec);
    put(sp+0x78,payload);put(sp+0x88,effect);put(effect+0x38,payload);
    R5900Context ctx{};SET_GPR_U32(&ctx,29,sp);SET_GPR_U32(&ctx,16,0);SET_GPR_U32(&ctx,4,1);
    const auto before=ram;std::array<unsigned char,sizeof(ctx)> cpu{};
    std::memcpy(cpu.data(),&ctx,sizeof(ctx));
    ps2xTagteamTraceKiBranch(ram.data(),&ctx,0x2058e0,0x1310bc);
    ps2xTagteamTraceKiBranch(ram.data(),&ctx,0x2058e0,0x1310bc); // rate suppressed
    if(ram!=before||std::memcmp(&ctx,cpu.data(),sizeof(ctx))!=0){std::puts("FAIL: observer mutated state");return 1;}
    SET_GPR_U32(&ctx,4,3);put(0x073D680C,1);
    ps2xTagteamTraceKiBranch(ram.data(),&ctx,0x2058e0,0x1310bc); // target change immediate
    put(sp+0xA0,0xDEADBEEF);
    ps2xTagteamTraceKiBranch(ram.data(),&ctx,0x2058e0,0x1310bc); // unrelated caller rejected
    std::fflush(stderr);
    std::ifstream input("power-scale-trial/codex-ki-trace-check.log");
    const std::string log((std::istreambuf_iterator<char>(input)),{});
    assert(log.find("selected_physical=3 used_model=1 used_physical=1")!=std::string::npos);
    assert(log.find("selected_physical=3 used_model=3 used_physical=3")!=std::string::npos);
    assert(std::count(log.begin(),log.end(),'\n')==2);
    std::puts("PASS: actual steering operand, changed target, caller filter, rate limit, RAM/CPU unchanged");
}
