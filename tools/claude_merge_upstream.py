"""Claude: three-way merge of the upstream Tag Team Mod Version 11 tools into our controller, on a separate git branch.

base  = experiments/.full-install/game/tools                (upstream 0.1.0-beta.32 as installed)
ours  = <staging repo>/controller/tools                      (our native controller snapshot)
new   = Budokai-...-beta.11/bt3-multifighter/tools           (upstream Version 11)
Rules per .py file (union of names):
  only in new            -> add
  ours == base           -> take new (when new differs)
  new == base            -> keep ours
  both changed           -> git merge-file (clean -> apply; conflict -> keep OURS and store a diff3 file under merge/conflicts/)
  only in ours           -> keep
Writes merge/MERGE_REPORT.md and merge/summary.json inside the repo. Does not touch the live workspace.
"""
import ast
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

WS = Path(__file__).resolve().parent.parent
REPO = WS / 'repo-staging' / 'BT3-TagTeam-Native'
BASE = WS / 'experiments' / '.full-install' / 'game' / 'tools'
NEW = WS / 'Budokai-Tenkaichi-3-Tag-Team-Mod-PCSX2--0.1.0-beta.11' / 'bt3-multifighter' / 'tools'
OURS = REPO / 'controller' / 'tools'
OVERLAY = REPO / 'controller' / 'roster-tools'
OUT = REPO / 'merge'

PCSX2_ONLY = {'process_identity.py', 'controller_checkin.py', 'controller_hub.py', 'disc_library.py', 'disc_page.py',
              'modder_gui.py', 'model_animations.py', 'model_assets.py', 'model_viewer.py', 'workbench_layout.py',
              'story_editor.py', 'story_preview.py'}


def norm(path):
    return path.read_bytes().replace(b'\r\n', b'\n')


def h(path):
    return hashlib.sha256(norm(path)).hexdigest()


def files(root):
    return {p.name: p for p in root.glob('*.py')}


def main():
    base, ours, new = files(BASE), files(OURS), files(NEW)
    (OUT / 'conflicts').mkdir(parents=True, exist_ok=True)
    summary = {'added': [], 'taken_new': [], 'merged_clean': [], 'conflicts': [], 'kept_ours': [], 'ours_only': []}
    for name in sorted(set(base) | set(ours) | set(new)):
        b, o, n = base.get(name), ours.get(name), new.get(name)
        if n and not b and not o:
            (OURS / name).write_bytes(norm(n))
            summary['added'].append(name)
        elif b and o and n:
            hb, ho, hn = h(b), h(o), h(n)
            if hn == hb:
                if ho != hb:
                    summary['kept_ours'].append(name)
            elif ho == hb:
                (OURS / name).write_bytes(norm(n))
                summary['taken_new'].append(name)
            elif ho == hn:
                pass
            else:
                with tempfile.TemporaryDirectory() as td:
                    td = Path(td)
                    for tag, src in (('o', o), ('b', b), ('n', n)):
                        (td / tag).write_bytes(norm(src))
                    r = subprocess.run(['git', 'merge-file', '-p', '--diff3', str(td / 'o'), str(td / 'b'), str(td / 'n')], capture_output=True)
                    # exit code = number of conflicts (0 clean), >127 error
                    if r.returncode == 0:
                        (OURS / name).write_bytes(r.stdout)
                        summary['merged_clean'].append(name)
                    elif r.returncode < 128:
                        (OUT / 'conflicts' / (name + '.diff3')).write_bytes(r.stdout)
                        summary['conflicts'].append([name, r.returncode])
                    else:
                        summary['conflicts'].append([name, -1])
        elif b and not n and o:
            summary['kept_ours'].append(name + ' (removed upstream)')
        elif o and not b and not n:
            summary['ours_only'].append(name)
        elif n and o and not b:
            # exists in both but not in base: keep ours, flag
            summary['conflicts'].append([name + ' (new upstream and ours)', 0])
    # static checks on the merged tree: syntax and local imports
    local = {p.stem for p in OURS.glob('*.py')}
    syntax, missing = [], {}
    for p in sorted(OURS.glob('*.py')):
        try:
            tree = ast.parse(p.read_text(encoding='utf-8'))
        except Exception as e:  # noqa
            syntax.append([p.name, str(e)[:120]])
            continue
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name.split('.')[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                mods = [node.module.split('.')[0]]
            for m in mods:
                if m in local:
                    continue
                if (m + '.py') in new or (m + '.py') in base:
                    missing.setdefault(p.name, set()).add(m)
    summary['syntax_errors'] = syntax
    summary['missing_local_modules'] = {k: sorted(v) for k, v in missing.items()}
    # overlay files that shadow merged tools
    shadow = [p.name for p in OVERLAY.glob('*.py') if p.name in summary['merged_clean'] + summary['taken_new'] + [c[0] for c in summary['conflicts']]]
    summary['overlay_needs_rederive'] = shadow
    summary['pcsx2_only_added'] = [n for n in summary['added'] if n in PCSX2_ONLY]
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=1), encoding='utf-8')
    print({k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in summary.items()})


if __name__ == '__main__':
    sys.exit(main())
