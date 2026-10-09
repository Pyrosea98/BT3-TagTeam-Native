#include "runtime/pad_config.h"
#include "runtime/ps2_host_pad.h"
#include "ps2_host_backend.h"
#include <cassert>
#include <filesystem>
#include <fstream>
#include <vector>
#include <cstdio>

static std::vector<int> slots;
static int pressedSlot=-1,rumbleSlot=-1;
extern "C" bool IsWindowReady() { return true; }
extern "C" bool IsKeyDown(int) { return false; }
namespace ps2x_pad {
bool available(int s) { for (int i:slots) if(i==s) return true; return false; }
bool isController(int s) { return available(s); }
const char *name(int) { return "offline fixture"; }
int axisCount(int) { return 6; }
int buttonCount(int) { return 18; }
bool buttonDown(int s,int b) { return s==pressedSlot && b==GAMEPAD_BUTTON_RIGHT_FACE_DOWN; }
float axis(int,int) { return 0; }
bool rumble(int s,uint16_t,uint16_t,uint32_t) { rumbleSlot=s;return true; }
}
static void neutral(const ps2_stubs::PadPacket &p) {
    assert(p.buttons==0xffff && p.lx==128 && p.ly==128 && p.rx==128 && p.ry==128);
}
int main(int argc,char **argv) {
    using namespace ps2_stubs;
    static_assert(PadConfig::kPlayerCount==4);
    assert(argc==2);
    auto &p=PadConfig::instance();p.setDefaultDir(argv[1]);
    for(size_t i=0;i<2;++i) assert(p.snapshot(i).device.kind==PadDeviceKind::None);
    for(size_t i=2;i<4;++i) {
        assert(p.snapshot(i).device.kind==PadDeviceKind::Gamepad && p.snapshot(i).device.gamepad==int(i));
        assert(p.snapshot(i).binds[size_t(PadAction::Cross)].value==p.snapshot(1).binds[size_t(PadAction::Cross)].value);
    }
    p.load(); // cold config creates all four files
    for(size_t i=0;i<4;++i) assert(std::filesystem::exists(p.playerConfigPath(i)));
    slots={2};pressedSlot=2;
    assert(p.poll(0).buttons!=0xffff);neutral(p.poll(2));neutral(p.poll(3)); // no raw-slot mirroring
    slots={2,4,7,9};pressedSlot=7;
    assert((p.poll(2).buttons&(1u<<14))==0);neutral(p.poll(3));
    padRumblePlayer(3,1,2,50);assert(rumbleSlot==9);
    assert(!p.setDevice(0,{PadDeviceKind::Gamepad,2}));
    assert(p.snapshot(0).device.kind==PadDeviceKind::None && p.gamepadOwner(2)==2);
    assert(p.setDevice(0,{PadDeviceKind::Gamepad,0}));
    p.setBind(3,PadAction::Square,{PadBindKind::Button,6,-1,0.15f});
    assert(p.save());p.resetPlayer(3);p.load();
    assert(p.snapshot(3).binds[size_t(PadAction::Square)].value==6);
    assert(p.snapshot(3).device.gamepad==3 && p.snapshot(0).device.gamepad==0);
    PadConfig::setInputSuspended(true);neutral(p.poll(2));PadConfig::setInputSuspended(false);
    neutral(p.poll(4));assert(!p.setDevice(4,{PadDeviceKind::Keyboard,-1}));
    { std::ofstream f(p.playerConfigPath(3));f<<"player 3 device Gamepad 2\n"; }
    p.load();assert(p.snapshot(3).device.kind==PadDeviceKind::Gamepad && p.snapshot(3).device.gamepad==-1);
    neutral(p.poll(3));assert(p.snapshot(2).device.gamepad==2);
    slots={};p.resetPlayer(3);assert(p.snapshot(3).device.gamepad==3);neutral(p.poll(3));
    const auto legacy=std::filesystem::path(argv[1])/"legacy";
    std::filesystem::create_directories(legacy);
    { std::ofstream f(legacy/"pad.conf");f<<"player 0 device Keyboard\nplayer 1 device Gamepad 0\n"; }
    p.setDefaultDir(legacy.string());p.load();
    assert(p.snapshot(0).device.kind==PadDeviceKind::Keyboard && p.snapshot(1).device.gamepad==0);
    assert(p.snapshot(2).device.gamepad==2 && p.snapshot(3).device.gamepad==3);
    const auto oldTwo=std::filesystem::path(argv[1])/"old-two";
    std::filesystem::create_directories(oldTwo/"savedata");
    { std::ofstream f(oldTwo/"savedata/pad_p1.conf");f<<"player 0 device Gamepad 1\n"; }
    { std::ofstream f(oldTwo/"savedata/pad_p2.conf");f<<"player 1 device Keyboard\n"; }
    p.setDefaultDir(oldTwo.string());p.load();
    assert(p.snapshot(0).device.gamepad==1 && p.snapshot(1).device.kind==PadDeviceKind::Keyboard);
    assert(p.snapshot(2).device.gamepad==2 && p.snapshot(3).device.gamepad==3);
    assert(std::filesystem::exists(p.playerConfigPath(3)));
    std::puts("PASS actual PadConfig: four defaults/files, persisted binds, neutral missing seats, duplicate rejection, rumble routing, suspended/out-of-range input");
}
