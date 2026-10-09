#include "runtime/ps2_interp_budget.h"
#include "runtime/ps2_bulk_read.h"
#include <cassert>
#include <cstdio>
int main() {
    Ps2InterpreterBudget healthy(10);
    for (unsigned frame=0; frame<1000; ++frame) {
        for (unsigned instruction=0; instruction<10; ++instruction) assert(healthy.instruction());
        healthy.nativeProgress();
    }
    assert(healthy.total==10000 && healthy.nativeDispatches==1000 && healthy.uninterrupted==0);
    Ps2InterpreterBudget runaway(10);
    for (unsigned i=0;i<10;++i) assert(runaway.instruction());
    assert(!runaway.instruction());
    runaway.nativeProgress();
    assert(runaway.instruction());
    assert(ps2BulkReadValid(0,262144,0x08000000));
    assert(ps2BulkReadValid(0x07ffffff,1,0x08000000));
    assert(!ps2BulkReadValid(0,0,0x08000000));
    assert(!ps2BulkReadValid(0,Ps2BulkReplyLimit+1,0x08000000));
    assert(!ps2BulkReadValid(0x07ffffff,2,0x08000000));
    assert(!ps2BulkReadValid(0xffffffff,2,0x08000000));
    std::puts("PASS: healthy cumulative work survives; uninterrupted runaway still stops");
    std::puts("PASS: bulk read range, reply cap and integer overflow guards");
}
