"""Read-only, reproducible audit of the reported M5.2 captures."""
from pathlib import Path
import json,struct,hashlib
HERE=Path(__file__).resolve().parent
TRIAL=HERE/'power-scale-trial'
def main():
    path=TRIAL/'controller/game/analysis/prepared-states/20261007-130820-72065da3/00-original-selected-match.bin'
    ram=path.read_bytes();u=lambda at:struct.unpack_from('<I',ram,at)[0]
    pages=[{'address':hex(at),'nonzero':sum(v!=0 for v in ram[at:at+4096])}
        for at in range(0x02000000,0x06000000,4096) if any(ram[at:at+4096])]
    report={'training_after_5v5':{'capture':str(path),'heap_bounds':[hex(u(0x2FF084)),hex(u(0x2FF08C))],
        'nonzero_pages':pages,'copy_destination':'0x02E03B50..0x02E04080','copy_source':'0x0056D350..0x0056D880',
        'exact_copy':ram[0x02E03B50:0x02E04080]==ram[0x0056D350:0x0056D880],
        'sha256':hashlib.sha256(ram[0x02E03B50:0x02E04080]).hexdigest(),
        'status':'Confirmed: bounds cleared; residual span matches a low-RAM stat block. Writer/ownership unknown; no cleanup writes performed.'},
        'freezes':[]}
    for folder in ('20261007-131800-m52-costume-stall','20261007-132800-vanilla-form-chain-freeze'):
        path=TRIAL/'freeze-captures'/folder/'ram.bin';ram=path.read_bytes()
        report['freezes'].append({'capture':str(path),
            'packet_lookup_words':[{ 'pc':hex(at),'word':hex(u(at))} for at in range(0x250570,0x2505A8,4)],
            'packet_lookup':'Object+0x44 -> packet; match halfword+10 against requested type; if flags halfword+6 == 0, advance by packet word+0. A zero next offset with a nonmatching type loops forever. Packet register/address at freeze is unavailable; NULL vs malformed packet remains unknown.',
            'main_lookup_words':[{ 'pc':hex(at),'word':hex(u(at))} for at in range(0x10A3B0,0x10A47C,4)]})
    # Counter hook is often the revival wrapper, not the original feed jump.
    path=TRIAL/'controller/game/analysis/prepared-states/20261007-133116-b583765b/16-ready-held.bin'
    ram=path.read_bytes()
    report['training_damage_chain']={'entry_jump':hex(u(0x1CE630)),
        'target':hex((u(0x1CE630)&0x3FFFFFF)<<2),'revival_magic':hex(u(0x070BF000)),
        'revival_previous_damage':hex(u(0x070BF028))}
    out=TRIAL/'codex-m52-live-failure-audit.json';out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('PASS read-only archived heap/packet/counter audit:',out)
if __name__=='__main__':main()
