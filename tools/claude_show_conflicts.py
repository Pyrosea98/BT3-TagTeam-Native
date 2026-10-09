"""Claude: print the conflict hunks of selected diff3 files (ours / base / theirs), truncated per line."""
import sys
from pathlib import Path

D = Path(r'C:\Users\JUAN\Downloads\Tag Team Mod Installer 2\repo-staging\BT3-TagTeam-Native\merge\conflicts')
W = int(sys.argv[1])
for name in sys.argv[2:]:
    t = (D / (name + '.diff3')).read_text(encoding='utf-8', errors='replace').split('\n')
    i, k = 0, 0
    while i < len(t):
        if t[i].startswith('<<<<<<<'):
            k += 1
            j = i + 1
            o = []
            while not t[j].startswith('|||||||'):
                o.append(t[j]); j += 1
            j += 1
            b = []
            while not t[j].startswith('======='):
                b.append(t[j]); j += 1
            j += 1
            n = []
            while not t[j].startswith('>>>>>>>'):
                n.append(t[j]); j += 1
            print(f'===== {name} hunk {k}')
            for tag, blk in (('OURS', o), ('BASE', b), ('THEIRS', n)):
                print(f'--- {tag} ({len(blk)})')
                for ln in blk[:14]:
                    print('   ' + ln[:W])
                if len(blk) > 14:
                    print(f'   ... {len(blk) - 14} more')
            i = j
        i += 1
