#include "runtime/ps2_ui_hud.h"
#include "runtime/ps2_ui_overhead_layout.h"
#include "runtime/ps2_ui_transport.h"
#include "runtime/ps2_ui_fight_intro.h"
#include "runtime/ps2_scene_packet_watch.h"
#include <cassert>
#include <vector>
#include <cstdio>
int main(){
    using namespace ps2x::ui;
    ScenePacketWatch watch;
    assert(!watch.sample(1,1000,0,true));assert(!watch.sample(1,1500,50000,true));
    for(unsigned t=2000;t<4000;t+=500)assert(!watch.sample(1,t,50000,true));
    assert(watch.sample(1,4000,50000,true));assert(!watch.sample(1,4500,50000,true));
    assert(!watch.sample(2,5000,50000,true)); // no healthy baseline in new match
    assert(!watch.sample(2,5500,50000,true));
    assert(!watch.sample(2,6000,100000,true));assert(!watch.sample(2,6500,100000,true));
    assert(!watch.sample(2,8000,100000,false)); // pause/cinematic cancels low interval
    assert(!watch.sample(2,8500,100000,true));assert(!watch.sample(2,9000,1,true)); // counter reset
    std::puts("PASS scene watch: sustained collapse after healthy baseline, once per generation, pause/cinematic/new-match/counter-reset guards");
    std::vector<uint8_t> ram(0x08000000);
    auto put=[&](uint32_t p,uint32_t v){std::memcpy(ram.data()+p,&v,4);};
    ScreenSnapshot s;s.generation=42;s.phase=PreparationPhase::Released;s.teamOneCount=2;s.teamTwoCount=2;
    s.fighters={1,202,161,252};s.seats={1,2,0,0};s.mode=BattleMode::Training;
    put(0x2FEB14,0x100000);put(0xD8080,1);put(0xD8084,4);put(0xD8088,0x100000);put(0xD808C,4);
    put(0x2FEB38,0x110000);put(0x110000,3);
    for(unsigned i=0;i<4;++i){uint32_t p=0x120000+i*0x2000;put(0xD8040+4*i,p);put(p,i);put(p+8,i&1);put(p+12,20);put(p+0x9E4,10000);put(p+0x9E8,40000);put(p+0x9F0,100);put(p+0x9F4,1000);}
    put(0x073AF108,2);put(0xD8008,3);
    put(0x070CF000,0x54524E31);put(0x070CF004,0x100000);put(0x070CF008,4);put(0x070CF00C,1);put(0x070CF018,1);
    put(0x07416000,1);put(0x07416004,0x100000);put(0x07416008,4);put(0x0741600C,100);
    put(0x07416200,80);put(0x07416204,252);put(0x07416208,202);put(0x0741621C,1);
    auto h=captureHud(ram,s);assert(h.active && h.subject==2 && h.target==3 && h.training && h.refill && h.idle);
    put(0x331DC8+0x19F0,0x100);auto paused=captureHud(ram,s);assert(paused.active && paused.paused);
    assert(overheadCounts(paused).detailed==0 && overheadCounts(paused).simple==0);
    put(0x331DC8+0x19F0,0);assert(!captureHud(ram,s).paused);
    FightIntro intro;assert(!intro.advance(42,0x100000,100,false,false));
    for(unsigned tick=200;tick<=2100;tick+=100)assert(!intro.advance(42,0x100000,tick,true,true));
    assert(intro.stage==1 && intro.elapsed==0);
    for(unsigned tick=2200;tick<=4200;tick+=100)assert(!intro.advance(42,0x100000,tick,false,false));
    assert(intro.stage==1 && intro.elapsed==0);
    for(unsigned tick=4300;tick<=5700;tick+=100)assert(!intro.advance(42,0x100000,tick,false,true));
    assert(intro.stage==2 && intro.elapsed==0);
    for(unsigned tick=5800;tick<=6400;tick+=100)assert(!intro.advance(42,0x100000,tick,false,false));
    assert(intro.stage==2 && intro.elapsed==0);
    for(unsigned tick=6500;tick<=7000;tick+=100)assert(!intro.advance(42,0x100000,tick,false,true));
    assert(intro.advance(42,0x100000,7100,false,true));
    assert(!intro.advance(43,0x100004,7200,false,true) && intro.stage==1);
    assert(h.actors[2].character==202 && h.actors[2].seat==2 && h.actors[1].character==161);
    assert(h.kills[0].active && h.kills[0].known && h.kills[0].killer==202 && h.kills[0].victim==252);
    put(0x077CF000,5);put(0x077CF004,h.manager);put(0x077CF008,4);put(0x077CF010,4);
    auto fused=captureHud(ram,s);assert(fused.active && !fused.actors[2].present && !fused.actors[2].alive && fused.actors[0].present);
    put(0x06C0F000,0x51564131);put(0x06C0F004,h.manager);put(0x06C0F024,2);
    put(0x06C0F040,0);put(0x06C0F044,0);
    put(0x06BCA000,0x4D465531);put(0x06BCA004,h.manager);put(0x06BCA008,4);
    put(0x06BCA100,3);put(0x06BCA124,0);put(0x06BCA128,1);
    uint8_t shared=255;assert(sharedFusionView(ram,fused,shared) && shared==0);
    put(0x06C0F024,3);assert(!sharedFusionView(ram,fused,shared));put(0x06C0F024,2);
    put(0x06BCA004,h.manager+4);assert(!sharedFusionView(ram,fused,shared));put(0x06BCA004,h.manager);
    put(0x06BCA100,0);put(0x077CF010,0);auto defused=captureHud(ram,s);
    assert(defused.actors[2].present && defused.actors[2].alive && !sharedFusionView(ram,defused,shared));
    std::puts("PASS co-op fusion HUD: consumed partner excluded, authenticated shared-camera selection, defusion restores partner, stale and 3-seat fallback");
    put(0xD8088,0x100004);assert(!captureHud(ram,s).active);put(0xD8088,0x100000);
    put(0x124994,5);assert(!captureHud(ram,s).active);put(0x124994,0);
    put(0xD8048,0xfffffff0);assert(!captureHud(ram,s).active);put(0xD8048,0x124000);
    put(0x1209E8,0);assert(!captureHud(ram,s).active);put(0x1209E8,40000);
    s.phase=PreparationPhase::Ready;assert(captureHud(ram,s).active);
    put(0x120948,301);assert(captureHud(ram,s).actors[0].cinematic);put(0x120948,11);
    put(0x0711F000,0x43504F31);put(0x0711F004,0x100000);put(0x0711F008,4);put(0x0711F03C,1);
    auto cinematic=captureHud(ram,s);assert(cinematic.active && cinematic.cinematic);
    put(0x0711F004,0x100004);assert(!captureHud(ram,s).cinematic);put(0x0711F03C,0);
    put(0x073E1C00,1);assert(!captureHud(ram,s).active);put(0x073E1C00,0);
    put(0x110000,2);assert(!captureHud(ram,s).active);put(0x110000,3);
    s.phase=PreparationPhase::Preparing;assert(!captureHud(ram,s).active);
    assert(!captureHud({ram.data(),1024},s).active);
    for(const auto& guard:hudDrawGuards){
        std::memcpy(ram.data()+guard.base,guard.bytes,guard.size);
        assert(guestHudDrawBoundary(guard.pc));
        assert(replacementHudDrawPc(ram,guard.pc,0x123456)==(guard.next?guard.next:0x123456));
        ram[guard.base]^=1;assert(!replacementHudDrawPc(ram,guard.pc,0x123456));
        assert(!replacementHudDrawPc({ram.data(),1024},guard.pc,0x123456));
    }
    assert(!replacementHudDrawPc(ram,0x072D0000,0x123456)); // camera/render wrapper is retained
    put(0x1CE630,(2u<<26)|(0x07411000u>>2));assert(trainingDamageHook(ram));
    put(0x1CE630,(2u<<26)|(0x070B7000u>>2));assert(!trainingDamageHook(ram));
    put(0x070BF000,0x52565631);put(0x070BF028,0x07411000);assert(trainingDamageHook(ram));
    put(0x070BF028,0x07411004);assert(!trainingDamageHook(ram));
    s.phase=PreparationPhase::Released;s.hudOptions=6;
    put(0x1209F8,250000);auto off=captureHud(ram,s);
    assert(off.active && !off.showGameHud && off.actors[0].stocks==2);
    const uint32_t gp=0x304270;put(gp-22324,0x170000);put(0x170000,0x171000);put(0x170008,0x172000);
    put(0x726F000,0x48554431);put(0x726F008,off.manager);put(0x726F01C,1);
    put(0x2188B8,(2u<<26)|(0x07276000u>>2));
    assert(hideGameHudNode(ram,off,gp,0x171000) && hideGameHudNode(ram,off,gp,0x172000));
    assert(!hideGameHudNode(ram,off,gp,0x173000)); // dialogue/clash/FIGHT roots
    off.showGameHud=true;assert(!hideGameHudNode(ram,off,gp,0x171000));off.showGameHud=false;
    put(0x726F01C,0);assert(hideGameHudNode(ram,off,gp,0x171000)); // render is independent of update scope
    off.active=false;assert(!hideGameHudNode(ram,off,gp,0x171000));off.active=true;
    put(0x110000,2);assert(!hideGameHudNode(ram,off,gp,0x171000));put(0x110000,3);
    put(0x2188B8,0);assert(!hideGameHudNode(ram,off,gp,0x171000));
    for(float width:{640.f,1062.f,597.f})for(float factor:{1.f,.5f}){
        OverheadBox bounds{30,20,width*factor,448*factor};
        auto owner=overheadPlace(bounds.x,bounds.y,156,54,bounds);
        auto target=overheadSeparate(overheadPlace(bounds.x,bounds.y,156,54,bounds),owner,bounds);
        assert(!overheadOverlap(owner,target));
        const OverheadBox details[]={owner,target};auto bar=overheadAvoidDetails(overheadPlace(bounds.x,bounds.y,64,7,bounds),details,bounds);
        assert(!overheadOverlap(bar,owner) && !overheadOverlap(bar,target));
        for(auto box:{owner,target,overheadPlace(-1000,5000,156,54,bounds)})
            assert(box.x>=bounds.x && box.y>=bounds.y && box.x+box.width<=bounds.x+bounds.width && box.y+box.height<=bounds.y+bounds.height);
    }
    std::array<uint8_t,UiPacketBytes> packet{};auto word=[&](unsigned n,uint32_t v){std::memcpy(packet.data()+n*4,&v,4);};
    word(0,1);word(25,0x800001d5);word(26,100);word(27,80);assert(uiPacketValid(packet));
    word(25,0x800001df);assert(!uiPacketValid(packet));word(25,0x800001d5);
    word(26,65);word(27,50);assert(uiPacketValid(packet));
    word(28,0x80000102);assert(uiPacketValid(packet));word(28,0x80000104);assert(!uiPacketValid(packet));word(28,0);
    word(26,49);assert(!uiPacketValid(packet));word(26,100);word(27,101);assert(!uiPacketValid(packet));
    HudSnapshot telemetry;telemetry.viewCount=1;telemetry.views[0].valid=true;telemetry.views[0].target=1;
    for(unsigned i=0;i<4;++i){telemetry.actors[i].present=telemetry.actors[i].alive=true;telemetry.views[0].points[i].valid=telemetry.views[0].points[i].onScreen=true;}
    telemetry.preferences.friends=telemetry.preferences.enemies=false;
    auto counts=overheadCounts(telemetry);assert(counts.detailed==2 && counts.simple==0 && counts.filtered==2);
    telemetry.preferences.detail=3;
    counts=overheadCounts(telemetry);assert(counts.detailed==4 && counts.simple==0 && counts.filtered==0);
    telemetry.preferences.detail=1;
    telemetry.preferences.friends=telemetry.preferences.enemies=true;
    counts=overheadCounts(telemetry);assert(counts.simple==2 && counts.filtered==0);
    telemetry.views[0].points[2].onScreen=false;telemetry.views[0].points[3].valid=false;
    counts=overheadCounts(telemetry);assert(counts.offscreen==1 && counts.invalid==1 && counts.simple==0);
    telemetry.preferences.shape=0;assert(overheadCounts(telemetry).detailed==0);
    for(unsigned setting:{50u,65u,80u,100u,120u,130u})for(float distance:{.7f,1.f,1.3f}){
        assert(overheadDiameter(distance,uint8_t(setting),false)<=46.f);
        assert(overheadDiameter(distance,uint8_t(setting),true)<=36.8f);
    }
    std::puts("PASS overhead: HUD-off snapshot and stocks, status-only scoped suppression, code-change refusal, aspect/split bounds and overlap, transport limits");
    std::puts("PASS actual HUD capture: physical/roster mapping, live stats/target, training, killfeed, stale identity/range/phase guards");
}
