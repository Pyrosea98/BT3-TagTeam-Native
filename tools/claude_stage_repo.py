"""Claude: stage a CLEAN, source-only copy of the project for the BT3-TagTeam-Native repo (allowlist; nothing game-derived).

Output: <workspace>/repo-staging/BT3-TagTeam-Native/ plus manifest.txt (every file, size, flags). Does not touch the originals.
"""
import fnmatch
import re
import shutil
from pathlib import Path

NP = Path(__file__).resolve().parent
WS = NP.parent
OUT = WS / 'repo-staging' / 'BT3-TagTeam-Native'
if OUT.exists():
    # keep the git history (branches, remotes); only the working tree is regenerated
    for child in OUT.iterdir():
        if child.name == '.git':
            continue
        shutil.rmtree(child) if child.is_dir() else child.unlink()
OUT.mkdir(parents=True, exist_ok=True)

SUSPECT = re.compile(rb'(JUAN|pyrosea|julianalvarez|C:\\\\Users|C:/Users)', re.I)
entries = []


def put(src: Path, dst_rel: str):
    dst = OUT / dst_rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    entries.append(dst_rel)


def put_glob(base: Path, patterns, dst_dir: str, exclude=()):
    for p in sorted(base.iterdir()):
        if not p.is_file():
            continue
        if any(fnmatch.fnmatch(p.name, e) for e in exclude):
            continue
        if any(fnmatch.fnmatch(p.name, pat) for pat in patterns):
            put(p, f'{dst_dir}/{p.name}')


# docs (not the internal COLLAB chat)
put_glob(NP, ['*.md'], 'docs', exclude=['COLLAB.md', 'ROADMAP.md.bak', 'CODEX_PROMPT.md'])
# root tooling scripts written for the project
put_glob(NP, ['*.py', '*.cmd', '*.cjs', '*.cpp'], 'tools', exclude=['tmp*'])
# controller (embedded mod logic, GPL-derived) and overlay
put_glob(NP / 'power-scale-trial/controller/game/tools', ['*.py'], 'controller/tools')
put_glob(NP / 'roster-tools', ['*.py'], 'controller/roster-tools')
for name in ('mod-settings-defaults.json', 'game-profile.json'):
    f = NP / 'power-scale-trial/controller/game' / name
    if f.exists():
        put(f, f'controller/{name}')
# installer sources only
INST = NP / 'installer'
put_glob(INST, ['*.iss', '*.pyw', 'play.cpp', 'play.rc', 'disc_import.cpp', 'package_ui.py', 'supported-discs.json', 'credits.txt', 'terms-*.txt', 'SNIPPETS*.md'], 'installer')
for f in sorted((INST / 'assets').glob('*')):
    if f.is_file():
        put(f, f'installer/assets/{f.name}')
# manual (own work) and fonts with licences
for f in sorted((NP / 'manual').glob('*')):
    if f.is_file():
        put(f, f'manual/{f.name}')
for f in sorted((NP / 'font-candidates').glob('*')):
    if f.is_file() and (f.suffix.lower() in ('.ttf', '.txt')):
        put(f, f'fonts/{f.name}')
# licence text from the runtime repo (GPL-3.0)
put(NP / 'repo' / 'LICENSE', 'LICENSE')

lines, flagged, total = [], [], 0
for rel in sorted(entries):
    f = OUT / rel
    size = f.stat().st_size
    total += size
    flag = ''
    data = f.read_bytes() if size < 3_000_000 else b''
    if SUSPECT.search(data):
        flag += ' PERSONAL-PATH'
    if size > 400_000:
        flag += ' LARGE'
    if flag:
        flagged.append((rel, size, flag))
    lines.append(f'{size:>9}  {rel}{flag}')
(OUT.parent / 'manifest.txt').write_text('\n'.join(lines), encoding='utf-8')
print('files', len(entries), 'total MB', round(total / 1e6, 2))
print('flagged', len(flagged))
for rel, size, flag in flagged[:40]:
    print(' ', rel, size, flag)
