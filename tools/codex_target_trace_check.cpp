#include "runtime/ps2_target_trace.h"
#include <vector>
#include <string>
#include <cassert>
#include <cstring>
#include <iostream>
static std::vector<std::string> logs;
static void output(const char *line) {logs.emplace_back(line);}
int main() {
    std::vector<uint8_t> ram(0x8000000);
    auto put=[&](uint32_t at,uint32_t value){std::memcpy(ram.data()+at,&value,4);};
    auto has=[](const char *s){for(const auto &line:logs)if(line.find(s)!=std::string::npos)return true;return false;};
    const uint32_t manager=0x180000,human=0x190000,enemy=0x1A0000,cpu=0x1B0000,pad=0x333800;
    put(0xD8080,1);put(0xD8084,4);put(0xD8088,manager);put(0xD808C,4);put(manager,2);put(0x2FEB14,manager);
    put(0x073D6800,1);put(0x073D6804,manager);put(0x073D6808,2);
    put(0xD8040,human);put(0xD8044,enemy);put(0xD8048,cpu);put(0xD8000,1);
    put(enemy+0x1278,1);put(cpu+0x1278,1);put(enemy+0x9AC,1);put(enemy+0x9E4,80000);
    ps2x::tagteam::TargetTrace trace(output);
    trace.sample(ram.data(),ram.size());
    const auto untouched=ram;
    put(pad+328,2);
    trace.input(ram.data(),ram.size(),0,human,pad,0x073D6820);
    assert(has("event=press-edge")&&has("bound_button=0x2")&&has("l3_edge=1"));
    // Guest switch result, not a trace write.
    put(0xD8000,3);put(0x073D6860,1);put(0x073D680C,1);
    trace.sample(ram.data(),ram.size());
    assert(has("event=target-change")&&has("outcome=switch-counter-advanced"));
    // Correct zero=human predicate: CPU action/pending words never produce events.
    put(cpu+3480,999);put(human+3480,123);put(0x073D680C,2);trace.sample(ram.data(),ram.size());
    for(int i=0;i<100;++i)trace.sample(ram.data(),ram.size()); // getter calls are not updates
    assert(!has("blocker-over-30-updates"));
    put(0x073D680C,33);trace.sample(ram.data(),ram.size());
    assert(has("blocker-over-30-updates"));
    for(const auto &line:logs)assert(line.find("physical=2 ")==std::string::npos);
    put(human+3480,0);put(0x073D680C,34);trace.sample(ram.data(),ram.size());assert(has("blocker-cleared"));
    // Read-only proof, malformed pointers, stale manager, lifetime/reset and ring cap.
    const auto before=ram;trace.sample(ram.data(),ram.size());assert(ram==before);
    put(0xD8044,0xFFFFFFF0);put(0xD8000,1);put(0x073D680C,35);trace.sample(ram.data(),ram.size());
    const auto n=logs.size();put(0x073D6804,manager+16);trace.sample(ram.data(),ram.size());assert(logs.size()==n);
    put(0x073D6804,manager);put(0x073D680C,0);trace.sample(ram.data(),ram.size());
    for(unsigned i=1;i<300;++i){put(0x073D680C,i);put(0xD8000,i%2?1:3);trace.sample(ram.data(),ram.size());}
    assert(trace.retainedEvents()==256);
    put(0xD8044,enemy);put(0xD8000,3);put(0x073D680C,400);put(0x073D6850,600);put(0x073D6900,600);
    const auto readonly=ram;
    trace.consumer(ram.data(),ram.size(),0,human,0x073D6900,0x073D7200);
    assert(has("actual_pending_address=0x73d6900 pending=600"));
    put(enemy+0x994,5);trace.candidate(ram.data(),ram.size(),0,1,enemy,0x073D7500,false);
    assert(has("candidate=1 slot=5 reason=invalid-slot-or-pointer"));
    put(enemy+0x994,0);put(enemy+0x9E4,0);trace.candidate(ram.data(),ram.size(),0,1,enemy,0x073D7520,true);
    assert(has("candidate-hp-read")&&has("reason=hp<=0"));
    trace.nativePhysicalRead(ram.data(),ram.size(),0x1DB010,1,enemy);
    assert(has("caller_site=0x1db010 getter_argument=1"));
    const auto rate=logs.size();
    for(unsigned i=0;i<1000;++i)trace.nativePhysicalRead(ram.data(),ram.size(),0x1DB010,1,enemy);
    assert(logs.size()==rate); // bounded lookup/rate gate before human scans
    put(0x073D680C,480);trace.sample(ram.data(),ram.size());assert(has("event=periodic"));
    const auto finalBefore=ram;trace.sample(ram.data(),ram.size());assert(ram==finalBefore);
    trace.resolverRead(ram.data(),ram.size(),0x1DB100,human,enemy,0x7784500);
    assert(has("resolved-target-read")&&has("table_match=0"));
    std::cout<<"PASS: L3/pad edge, actual switch-counter outcome, human/CPU distinction, update-based blocked duration, stale pointers/manager, read-only observer, ring bounds\n";
}
