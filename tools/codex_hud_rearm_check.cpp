// Actual diagnostic gate: absent trigger, consumption, expiry and second capture.
#include "repo/ps2xRuntime/src/lib/ps2_hud_diagnostic.cpp"
#include <thread>
#include <stdexcept>
#include <fstream>

static uint64_t fixtureTick=10;
uint32_t ps2xHudPacketOwner() { return 0; }
uint32_t ps2xHudPacketSource() { return UINT32_MAX; }
namespace ps2_syscalls { uint64_t GetCurrentVSyncTick() { return fixtureTick; } }
void GSRasterizer::decodeDeferred(const TexDecodeReq &,uint8_t *,size_t,int &,std::vector<uint8_t> &) { throw std::runtime_error("unexpected decode"); }
namespace ps2x::gfx { bool GsWritePngRGBA8(const char *,const uint8_t *,int,int) { throw std::runtime_error("unexpected PNG"); } }
void check(bool value,const char *message) { if(!value) throw std::runtime_error(message); }
int main() {
    const std::filesystem::path root="power-scale-trial/hud-policy-fixture";
    std::filesystem::create_directories(root);
    const auto trigger=root/"capture.trigger";
    std::filesystem::remove(trigger);
    _putenv_s("PS2X_DRAW_TRACE","1");
    _putenv_s("PS2X_GS_DIAG_TRIGGER",trigger.string().c_str());
    check(!ps2xHudDiagnosticActive(),"absent trigger activated capture");
    std::ofstream(trigger)<<"first";
    std::this_thread::sleep_for(std::chrono::milliseconds(110));
    check(ps2xHudDiagnosticActive(),"first trigger not accepted");
    check(!std::filesystem::exists(trigger),"trigger not consumed");
    check(ps2xHudDiagnosticGeneration()==1,"wrong first generation");
    fixtureTick=69; check(ps2xHudDiagnosticActive(),"window closed too early");
    fixtureTick=70; check(!ps2xHudDiagnosticActive(),"window did not close");
    std::ofstream(trigger)<<"second";
    std::this_thread::sleep_for(std::chrono::milliseconds(110));
    fixtureTick=80;
    check(ps2xHudDiagnosticActive(),"second trigger not accepted");
    check(ps2xHudDiagnosticGeneration()==2,"generation did not advance");
    fixtureTick=140; check(!ps2xHudDiagnosticActive(),"second window did not close");
    check(!std::filesystem::exists(trigger),"second trigger not consumed");
    check(!ps2xHudDiagnosticActive(),"capture spontaneously restarted");
    auto *identity=reinterpret_cast<GS *>(uintptr_t(0x1000));
    ps2xHudDiagnosticSetGS(identity);
    check(ps2xHudDiagnosticGS()==identity,"initialized GS identity was not retained");
    ps2xHudDiagnosticSetGS(nullptr);
    std::puts("PASS: actual gate consumes two triggers, expires both windows, retains GS registration");
}
