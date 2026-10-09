#include "runtime/ps2_ui_transport.h"
#include <cassert>
#include <cstdio>
using namespace ps2x::ui;
int main() {
    std::array<uint8_t,UiPacketBytes> packet{};
    auto put=[&](size_t i,uint32_t v){std::memcpy(packet.data()+i*4,&v,4);};
    put(0,1);put(1,1);put(2,42);put(6,1);put(7,5);
    for(unsigned i=0;i<6;++i)put(8+i,i==5?252:i);
    put(21,2);put(22,1|(2u<<3)|(3u<<6));put(23,3);put(24,7);
    assert(uiPublish(packet));auto& l=uiStore().lifecycle;
    assert(l.snapshot(uiNow()).mode==BattleMode::FreeForAll && l.snapshot(uiNow()).seats[2]==3);
    assert(l.snapshot(uiNow()).humans==3 && l.snapshot(uiNow()).hudOptions==7);
    put(21,5);assert(!uiPublish(packet));put(21,2);
    put(22,7);assert(!uiPublish(packet));put(22,1|(2u<<3)|(3u<<6));
    put(24,8);assert(!uiPublish(packet));put(24,7);
    put(1,2);put(4,100);put(5,6);assert(uiPublish(packet));
    assert(l.snapshot(uiNow()).screen==Screen::Loading);
    put(1,4);assert(!uiPublish(packet)); // percentage is not readiness
    put(1,8);assert(!uiPublish(packet)); // modal cannot steal held match
    put(1,11);assert(!uiPublish(packet));
    put(1,3);assert(uiPublish(packet));put(1,11);assert(uiPublish(packet));assert(uiPublish(packet));
    assert(l.snapshot(uiNow()).startAccepted && l.snapshot(uiNow()).phase==PreparationPhase::Ready);
    put(1,8);assert(!uiPublish(packet));put(1,4);assert(uiPublish(packet));
    put(1,1);put(2,43);assert(uiPublish(packet));
    put(2,42);put(1,5);assert(!uiPublish(packet));
    put(2,43);assert(uiPublish(packet));put(1,4);assert(!uiPublish(packet));
    put(1,6);assert(uiPublish(packet));put(1,10);assert(uiPublish(packet));
    put(18,3);assert(!uiPublish(packet));put(18,1);
    std::memset(packet.data()+128,'x',128);assert(!uiPublish(packet));
    assert(l.snapshot(uiNow()).screen==Screen::Settings);
    assert(!uiPacketValid({packet.data(),packet.size()-1}));
    std::puts("PASS native UI framing, stale generation, error hold, release and modal ownership");
}
