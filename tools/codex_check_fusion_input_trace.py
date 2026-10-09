"""Seed original native eligibility plus actual emitted tracing wrappers.

No live guest: native targets are deterministic EE boundary stubs; the actual
native branching/search instructions execute between those boundaries.
"""
from pathlib import Path
import os,struct,subprocess,sys,tempfile
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE/'power-scale-trial/controller/game/tools')]
from codex_roster_overlay import install
install()
from prototype import Assembler
import fusion_input_trace as t
ram=bytearray((HERE/'power-scale-trial/controller/game/analysis/prepared-states/20261007-201319-d7ac1d61/16-ready-held.bin').read_bytes())
u=lambda at:struct.unpack_from('<I',ram,at)[0]
put=lambda at,v:struct.pack_into('<I',ram,at,v)
PROBE=0x06FE0400
# Restore only the audited original eligibility body in this offline fixture.
ram[t.A(0x203788):t.A(0x203900)]=t.abi.NATIVE(t.A(0x203788),0x178)
ram[t.CODE:t.CODE+len(t.code())]=t.code()
put(t.CONTROL,t.MAGIC);put(t.CONTROL+4,0)
for i,(site,target,offset) in enumerate(t.CALLS):
    base,body=t.wrapper(i);ram[base:base+len(body)]=body;put(t.A(site),(3<<26)|(base>>2))
# Preserve native callees' saved registers; deliberately disturb HI/FPU and
# caller temporaries so trace logging cannot accidentally hide ABI changes.
COUNTER_ENTRIES=(0x1CF0C8,0x1DAC78,0x1DC348,t.abi.SIDE,0x1CED60,0x20E340,0x20E3E8,0x20E3A0,0x1CE108,0x1CE198)
def boundary(entry):
    # Avoid crossing another compiled ELF entry with a long synthetic stub.
    a=Assembler(PROBE+0x6000+0x200*COUNTER_ENTRIES.index(entry))
    a.boundary_entry=entry
    return a

def finish(a):
    counter=4*COUNTER_ENTRIES.index(a.boundary_entry)
    a.li(10,PROBE+0x100);a.lw(11,10,counter);a.addiu(11,11,1);a.sw(11,10,counter)
    a.li(10,0x13579);a.r(24,0,10,10);a.emit((28<<26)|(10<<21)|(10<<16)|24)
    a.li(10,0x3F012345);a.emit((17<<26)|(4<<21)|(10<<16)|(7<<11))
    a.jr();body=a.finish();ram[a.base:a.base+len(body)]=body
    struct.pack_into('<2I',ram,a.boundary_entry,(2<<26)|(a.base>>2),0)
for entry,refusal in ((0x1CF0C8,1),(0x1DAC78,2),(0x1DC348,3),(t.abi.SIDE,4),(0x1CED60,5)):
    a=boundary(entry);a.li(9,PROBE);a.lw(2,9);a.addiu(10,0,refusal);a.r(0x26,2,2,10);a.i(11,2,2,1)
    if refusal in (4,5):a.i(14,2,2,1)
    finish(a)
for entry,value in ((0x20E340,195),(0x20E3E8,300000)):
    a=boundary(entry);a.li(2,value);finish(a)
a=boundary(0x20E3A0);a.addiu(2,6,100);finish(a)
a=boundary(0x1CE108);a.li(9,PROBE);a.lw(10,9,8);a.addiu(11,10,100);a.addiu(2,0,-1)
a.branch(5,5,11,'end');a.move(2,10);a.label('end');finish(a)
a=boundary(0x1CE198);t.abi.row_address(a,2,4,5,10);a.addiu(2,2,0x40);finish(a)
# build_memory guards must accept only the owned SIDE predecessor and preserve
# every native delay slot; occupied or unknown callsites are rejected.
check=bytearray(ram)
check[t.BASE:t.END]=bytes(t.END-t.BASE)
check[t.HOOK:t.HOOK+8]=t.abi.NATIVE(t.HOOK,8)
for site,target,_ in t.CALLS:
    expected=t.abi.NATIVE(t.A(site),8)
    if site==0x203830:expected=struct.pack('<I',(3<<26)|(t.abi.SIDE>>2))+expected[4:]
    check[t.A(site):t.A(site)+8]=expected
old=t.game_profile.installed;t.game_profile.installed=lambda:{'runtime_variant':t.game_profile.POWER_SCALE_VARIANT}
try:
    plan=t.build_memory(check);assert len(plan['blocks'])==24
    for site,_,_ in t.CALLS:assert not any(b['address']==t.A(site)+4 for b in plan['blocks'])
    for site,_,_ in t.CALLS:
        bad=bytearray(check);bad[t.A(site)+4]^=1
        try:t.build_memory(bad)
        except ValueError:pass
        else:raise AssertionError('changed native delay accepted')
    installed=bytearray(check)
    for b in plan['blocks']:
        value=bytes.fromhex(b['data_hex']);installed[b['address']:b['address']+len(value)]=value
    side=t.A(0x203830);prior=struct.pack('<I',(3<<26)|(t.abi.SIDE>>2))+t.abi.NATIVE(side+4,4)
    for active in (0,t.ROWS,t.ROWS+9*t.STRIDE):
        struct.pack_into('<I',installed,t.CONTROL+4,active)
        assert t.dependency_override(installed,side,prior)==installed[side:side+8]
        assert t.dependency_override(installed,side,prior[:4])==installed[side:side+4]
    for address in (t.CODE+12,t.HOOK+4,t.CONTROL,*[t.wrapper(i)[0]+12 for i in range(len(t.CALLS))],*[t.A(site)+4 for site,_,_ in t.CALLS]):
        installed[address]^=1
        try:
            accepted=t.dependency_override(installed,side,prior)
            assert accepted!=installed[side:side+8], 'unauthenticated trace accepted'
        except ValueError:pass
        finally:installed[address]^=1
    struct.pack_into('<I',installed,t.CONTROL+4,t.ROWS+1)
    try:t.dependency_override(installed,side,prior)
    except ValueError:pass
    else:raise AssertionError('unaligned active row accepted')
    struct.pack_into('<I',installed,t.CONTROL+4,0)
    try:t.dependency_override(installed,side,t.abi.NATIVE(side,8))
    except ValueError:pass
    else:raise AssertionError('withdrawn native bitmap target accepted')
    print('PASS strict installed-trace dependency: mutable valid active row, full entry/gate code, hooks/delays, magic, predecessor')
    bad=bytearray(check);bad[t.BASE]=1
    try:t.build_memory(bad)
    except ValueError:pass
    else:raise AssertionError('occupied trace reservation accepted')
finally:t.game_profile.installed=old
print('PASS exact gate predecessor/delay/reservation manifest guards')
if '--emit-only' in sys.argv:
    destination=HERE/'analysis/fusion-input-gate-fixture.bin';destination.write_bytes(ram)
    print('Emitted offline fixture:',destination);raise SystemExit(0)
runner=HERE/'repo/build/ps2xRuntime'/os.environ.get('BT3_TEST_RUNNER','ps2EntryRunner-branding-fusion-review.exe')
with tempfile.TemporaryDirectory(prefix='fusion-input-',dir=HERE/'power-scale-trial') as temp:
    fixture=Path(temp)/'ram.bin';fixture.write_bytes(ram)
    result=subprocess.run([runner,'--native-fusion-input-self-test',fixture],capture_output=True,text=True,timeout=60)
    output=result.stdout+result.stderr+'\nEXIT '+str(result.returncode)+'\n'
    (HERE/'power-scale-trial/codex-fusion-input-check.log').write_text(output,encoding='utf-8')
    print(output,end='');assert result.returncode==0
