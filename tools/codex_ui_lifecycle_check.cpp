#include "runtime/ps2_ui_screen_lifecycle.h"
#include <cassert>
#include <cstdio>
using namespace ps2x::ui;
int main() {
    ScreenLifecycle ui;
    const std::array<uint16_t,1> one{0}; const std::array<uint16_t,3> two{161,202,252};
    assert(ui.snapshot(0).screen==Screen::Hidden);
    ui.language(Language::Spanish);
    assert(ui.open(Screen::Settings,10));
    assert(ui.open(Screen::About,11)); assert(ui.close(12));
    assert(ui.begin(1,20,one,two));
    auto s=ui.snapshot(20);
    assert(s.language==Language::Spanish && s.teamOneCount==1 && s.teamTwoCount==3 && s.fighters[3]==252);
    assert(!ui.begin(2,21,one,two)); // no replacement of an owned cover
    assert(!ui.open(Screen::Settings,21) && !ui.open(Screen::About,21));
    assert(!ui.close(21));
    assert(ui.progress(1,100,7,22));
    assert(ui.snapshot(22).phase==PreparationPhase::Preparing); // progress is not readiness
    assert(!ui.released(1,23));
    assert(!ui.progress(1,99,6,23));
    assert(!ui.progress(0,100,7,23));
    assert(ui.ready(1,24));
    assert(!ui.startAccepted(0,25));
    assert(ui.startAccepted(1,25));
    assert(ui.snapshot(25).startAccepted && ui.snapshot(25).phase==PreparationPhase::Ready);
    assert(!ui.open(Screen::Settings,26)); // intro does not relinquish owner
    assert(ui.snapshot(10000).ownerExpired);
    assert(ui.snapshot(10000).screen==Screen::Loading); // stale heartbeat cannot release game
    assert(ui.heartbeat(1,10000)); assert(!ui.snapshot(10001).ownerExpired);
    assert(ui.released(1,10002)); assert(ui.snapshot(10002).screen==Screen::Hidden);
    assert(!ui.begin(1,10003,one,two)); // stale generation
    assert(ui.begin(2,10003,one,two)); assert(ui.progress(2,30,2,10004));
    assert(ui.fail(2,10005));
    assert(!ui.released(2,10006));
    assert(!ui.open(Screen::About,10006));
    assert(!ui.progress(2,50,3,10006));
    assert(ui.snapshot(20000).phase==PreparationPhase::Failed);
    assert(!ui.teardown(1,20000)); // old owner cannot close the current error
    assert(ui.teardown(2,20000)); assert(ui.open(Screen::About,20001));
    assert(!ui.close(19999)); assert(ui.close(20002));
    const std::array<uint16_t,1> bad{253};
    assert(!ui.begin(3,20003,bad,two)); assert(!ui.begin(3,20003,{},two));
    assert(ui.begin(3,20003,one,two));
    assert(!ui.progress(3,101,1,20004)); assert(!ui.progress(3,10,8,20004));
    assert(ui.progress(3,10,1,20004)); assert(!ui.progress(3,20,2,20000));
    assert(ui.teardown(3,20005));
    assert(ui.begin(4,20006,one,two));assert(!ui.startAccepted(4,20007));
    assert(ui.ready(4,20007));assert(ui.startAccepted(4,20008));
    assert(!ui.fail(4,20009));assert(ui.snapshot(20009).startAccepted);
    assert(ui.released(4,20010));
    std::puts("PASS native UI lifecycle: generation/lease/progress/ready/release/error/menu priority");
}
