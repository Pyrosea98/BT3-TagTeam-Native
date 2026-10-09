"""Summarize the latest cumulative main-thread fight profile in a runner log."""
from pathlib import Path
import json
import re
import sys

HERE=Path(__file__).resolve().parent
GROUPS={0x071A0000:'multi_contact',0x07180000:'dash_clash',0x07183000:'dash_clash',
        0x07243000:'beam_clash',0x07245000:'beam_clash',0x07368000:'combat getters/resolver',
        0x07260000:'HUD subject',0x072D0000:'viewport/debris',0x070F0000:'giant model/actor',
        0x070F6000:'giant hurt box',0x07784000:'throw resolver chain',0x07788000:'paired throw lookup',
        0x07781000:'throw lookup',0x06944000:'lock-off QUERY/SET/native tails',
        0x073C6000:'cinematic contact reverse/throw wrappers',0x073C4000:'cinematic contact gates',
        0x07400000:'effect texture guard',
        0x077C4000:'inactive actor',0x077D0000:'participation/fusion'}

def parse(text):
    reports=[];current=None
    for line in text.splitlines():
        if '[interp-profile]' in line:
            fields=dict(re.findall(r'(\w+)=([\w.]+)',line))
            if 'total' in fields:
                current={'total':int(fields['total']),'main':int(fields.get('main',0)),'pages':[]}
                reports.append(current)
        elif '[interp-profile-page]' in line and current is not None:
            match=re.search(r'base=(0x[0-9a-fA-F]+) instructions=(\d+) percent=([\d.]+)',line)
            if match:
                address=int(match[1],16)
                label=GROUPS.get(address,'unmapped cave')
                if 0x070B0000<=address<0x070C0000:label='teammate revival'
                elif address<0x04000000:label='patched ELF/overlay'
                current['pages'].append({'address':f'0x{address:08X}','instructions':int(match[2]),
                                         'percent':float(match[3]),'module':label})
    candidates=[r for r in reports if r['pages'] and r['main']>0]
    if not candidates:candidates=[r for r in reports if r['pages']]
    if not candidates:raise ValueError('No interpreter profile found; use Profile Power Scale 5v5.cmd and play a prepared fight for at least30 seconds')
    return max(candidates,key=lambda r:r['main'] or r['total'])

def main():
    path=Path(sys.argv[1]) if len(sys.argv)>1 else HERE/'power-scale-trial/runner.log'
    result=parse(path.read_text(encoding='utf-8',errors='replace'))
    output=path.with_name(path.stem+'-fight-profile.json')
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(f'Main instructions: {result["main"]:,}; report: {output}')
    print('Instruction counts rank work volume, not measured CPU time per instruction.')
    for row in result['pages'][:20]:print(f'{row["percent"]:6.2f}% {row["address"]} {row["module"]}')
if __name__=='__main__':main()
