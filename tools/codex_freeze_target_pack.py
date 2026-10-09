"""Developer-only AOT compiler for audited leaf getter/guard/resolver caves.

Emits ordinary C++ control flow, not a runtime decoder/cache. Unknown instructions
or control flow fail generation. Original generators remain the byte oracle.
"""
from pathlib import Path
import json
import struct
import sys
import csv

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(HERE/'power-scale-trial/controller/game/tools'))
from codex_roster_overlay import install
install()
import fresh_team_combat as combat
import battle_mode_policy as policy


def instruction(w):
    op=w>>26;rs=(w>>21)&31;rt=(w>>16)&31;rd=(w>>11)&31;sa=(w>>6)&31
    imm=w&65535;simm=imm if imm<32768 else imm-65536
    addr=f'(o.u32({rs})+uint32_t({simm}))'
    if w==0:return ''
    if op==0:
        fn=w&63
        if fn==0:return f'o.s32({rd},o.u32({rt})<<{sa});'
        if fn==2:return f'o.s32({rd},o.u32({rt})>>{sa});'
        if fn==3:return f'o.s32({rd},uint32_t(int32_t(o.u32({rt}))>>{sa}));'
        if fn==4:return f'o.s32({rd},o.u32({rt})<<(o.u32({rs})&31));'
        if fn==33:return f'o.s32({rd},o.u32({rs})+o.u32({rt}));'
        if fn==36:return f'o.u64({rd},o.u64({rs})&o.u64({rt}));'
        if fn==37:return f'o.u64({rd},o.u64({rs})|o.u64({rt}));'
        if fn==38:return f'o.u64({rd},o.u64({rs})^o.u64({rt}));'
        if fn==39:return f'o.u64({rd},~(o.u64({rs})|o.u64({rt})));'
        if fn==42:return f'o.u64({rd},int64_t(o.u64({rs}))<int64_t(o.u64({rt})));'
        if fn==43:return f'o.u64({rd},o.u64({rs})<o.u64({rt}));'
        if fn==45:return f'o.u64({rd},o.u64({rs})+o.u64({rt}));'
    if op==9:return f'o.s32({rt},o.u32({rs})+uint32_t({simm}));'
    if op==11:return f'o.u64({rt},o.u64({rs})<uint64_t(int64_t({simm})));'
    if op==12:return f'o.u64({rt},o.u64({rs})&{imm}u);'
    if op==13:return f'o.u64({rt},o.u64({rs})|{imm}u);'
    if op==15:return f'o.s32({rt},{imm}u<<16);'
    if op==35:return f'o.s32({rt},o.read32({addr}));'
    if op==36:return f'o.u64({rt},o.read8({addr}));'
    if op==43:return f'o.write32({addr},o.u32({rt}));'
    if op==30:return f'o.load128({rt},{addr}&~15u);'
    if op==31:return f'o.store128({rt},{addr}&~15u);'
    if op==55:return f'o.u64({rt},o.read64({addr}));'
    if op==63:return f'o.write64({addr},o.u64({rt}));'
    raise ValueError(f'Unsupported frozen instruction {w:08x}')


def compile_body(name,base,data):
    words=struct.unpack(f'<{len(data)//4}I',data)
    end=base+len(data)
    def jump(target):
        if base<=target<end:
            if target%4:raise ValueError('Unaligned target')
            return f'goto L{target:x};'
        return f'return 0x{target:x}u;'
    lines=[f'template<class Ops> uint32_t {name}(Ops &o) {{']
    for i,w in enumerate(words):
        pc=base+4*i;op=w>>26;rs=(w>>21)&31;rt=(w>>16)&31
        lines.append(f'L{pc:x}:;')
        control=op in (2,4,5) or (op==0 and w&63==8)
        if control:
            if i+1>=len(words):raise ValueError('Missing delay slot')
            delay=instruction(words[i+1])
            if op in (4,5):
                imm=w&65535;simm=imm if imm<32768 else imm-65536
                relation='==' if op==4 else '!='
                lines.append(f'{{ const bool taken=o.u64({rs}){relation}o.u64({rt}); {delay} '
                             f'if(taken) {{ {jump(pc+4+4*simm)} }} {jump(pc+8)} }}')
            elif op==2:
                target=((pc+4)&0xF0000000)|((w&0x3ffffff)<<2)
                lines.append('{ '+delay+' '+jump(target)+' }')
            else:
                lines.append(f'{{ const uint32_t target=o.u32({rs}); {delay} return target; }}')
        else:lines.append(instruction(w))
    lines.append(f'return 0x{end:x}u;\n}}')
    return '\n'.join(lines)


def variants():
    import inactive_actor_guard as inactive
    import teammate_revive as revive
    import hud_subject as hud
    import multi_contact as contact
    import beam_clash as beam
    import dash_clash as dash
    import giant_options as giant
    import extra_throws as throws
    import lockoff_target as lockoff
    result=[]
    for capacity in (3,5):
        with policy.building_for(capacity):
            entries=[('count',combat.COUNT,combat.count_code()),
                     ('physical',combat.PHYSICAL,combat.getter_code(combat.PHYSICAL,combat.A(0x1DC178))),
                     ('logical',combat.LOGICAL,combat.getter_code(combat.LOGICAL,combat.A(0x1DC1A0),True)),
                     ('resolver',combat.RESOLVER,combat.resolver_code()),
                     ('resolver_ffa',combat.RESOLVER,combat.resolver_code(True))]
            entries.extend((('resolver_tail',combat.RESOLVER+8,combat.resolver_code()[8:]),
                            ('resolver_ffa_tail',combat.RESOLVER+8,combat.resolver_code(True)[8:]),
                            ('contact_gate',contact.GATE,contact.gate_code()),
                            ('beam_gate',beam.GATE,beam.gate_code()),
                            ('dash_gate',dash.GATE,combat.rebound(beam.gate_code,GATE=dash.GATE,CONTROL=dash.CONTROL,MAGIC=dash.MAGIC)())))
            entries.extend((('inactive',inactive.ENTRY,inactive.code()),
                            ('revive_gate',revive.GATE,revive.gate()),
                            ('revive_actor',revive.ACTOR,revive.actor()),
                            ('hud_watched',hud.CODE,hud.watched_resolver_code()),
                            ('hud_quad',hud.CODE,hud.watched_resolver_code(quad_support=True))))
            entries.extend((('giant_model',giant.MODEL,giant.model_code()),
                            ('giant_actor',giant.ACTOR,giant.actor_code()),
                            ('throw_lookup',throws.LOOKUP,throws.lookup_code()),
                            ('throw_paired',throws.PAIRED_LOOKUP,throws.paired_lookup_code()),
                            ('lock_query',lockoff.QUERY,lockoff.flag_code(lockoff.QUERY,lockoff.TAILS)),
                            ('lock_set',lockoff.SET,lockoff.flag_code(lockoff.SET,lockoff.TAILS+32))))
            for name,base,data in entries:
                result.append(dict(name=f'{name}_{capacity}',base=base,data_hex=data.hex()))
    return result

def elf_variants():
    # No calls, stack adjustments or memory writes in this first ELF slice.
    # External tail jumps return to the dispatcher, never bypass patched callees.
    from prototype import ROOT,elf_reader
    from native_map import elf_path
    native=elf_reader(elf_path(ROOT))[2]
    result=[]
    pages=(0x1D3000,0x1DA000,0x24D000,0x1CE000,0x1C3000,0x1CF000)
    for row in csv.DictReader((HERE/'repo/games/bt3/functions.csv').open()):
        b,e=int(row['Start'],16),int(row['End'],16)
        if e-b>1024 or not any(b<p+4096 and e>p for p in pages):continue
        data=native(b,e-b)
        try:
            for i,w in enumerate(struct.unpack(f'<{len(data)//4}I',data)):
                op,rs,rt,fn=w>>26,(w>>21)&31,(w>>16)&31,w&63;pc=b+4*i
                imm=w&65535;simm=imm if imm<32768 else imm-65536
                if op in (4,5):assert pc+8<=pc+4+4*simm<e # forward-only, no native spin
                elif op==2:
                    target=((pc+4)&0xf0000000)|((w&0x3ffffff)<<2)
                    assert not b<=target<e or target>=pc+8
                elif op==0 and fn==8:assert rs==31
                else:
                    assert op not in (43,31,63) # no guest writes
                    if op==9:assert rt!=29 # no stack adjustment
                    instruction(w) # unsupported operations/calls reject generation
            compile_body('audit',b,data)
        except (ValueError,AssertionError):continue
        result.append(dict(name=f'elf_{b:x}',base=b,data_hex=data.hex()))
        # Installed lock-off/extended-flag wrappers replay these two words before
        # entering the intact tail. Never bypass the wrapper at the original entry.
        if b in (0x1dac78,0x1dace8):
            result.append(dict(name=f'elf_tail_{b+8:x}',base=b+8,data_hex=data[8:].hex()))
    return result


def main():
    rows=variants()+elf_variants()
    lines=['// Generated by codex_freeze_target_pack.py. Do not edit.','#pragma once',
           '#include <cstdint>','#include <cstring>','namespace ps2x::tagteam::frozen {']
    for row in rows:
        name=row['name'];data=bytes.fromhex(row['data_hex'])
        lines.append(f'inline constexpr uint8_t bytes_{name}[]={{'+','.join(f'0x{x:02x}' for x in data)+'};')
        lines.append(compile_body(name,row['base'],data))
    lines.append('template<class Ops> bool execute(uint8_t *ram,uint32_t entry,Ops &o,uint32_t &exit) {')
    for row in rows:
        name=row['name']
        lines.append(f'if(entry==0x{row["base"]:x}u && !std::memcmp(ram+entry,bytes_{name},sizeof(bytes_{name}))) '
                     f'{{ exit={name}(o); return true; }}')
    lines.append('return false;\n}\n}')
    addresses=[row['base'] for row in rows if row['name'].startswith('elf_')]
    lines.append('namespace ps2x::tagteam::frozen { inline constexpr uint32_t elfEntries[]={'+','.join(hex(at)+'u' for at in addresses)+'};\ninline bool isElfEntry(uint32_t pc){switch(pc){'+''.join(f'case {hex(at)}u:' for at in addresses)+'return true;default:return false;}}\ninline int elfIndex(uint32_t pc){for(unsigned i=0;i<sizeof(elfEntries)/sizeof(elfEntries[0]);++i)if(elfEntries[i]==pc)return int(i);return -1;}\n}')
    target=HERE/'repo/ps2xRuntime/include/runtime/ps2_tagteam_target_pack.h'
    target.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (HERE/'codex_target_pack_oracle.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    print(f'Frozen {len(rows)} reviewed variants -> {target}')

if __name__=='__main__':main()
