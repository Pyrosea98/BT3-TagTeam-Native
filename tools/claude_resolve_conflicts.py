"""Claude: apply reviewed resolutions to the diff3 conflicts produced by claude_merge_upstream.py (bytes preserved via latin-1).

Each file maps to a list of resolutions, one per conflict hunk, in order. A resolution is a function (ours, base, theirs) -> list of lines
(LF, no trailing newline per element). Files not listed stay on OUR version and are reported.
"""
import json
from pathlib import Path

REPO = Path(r'C:\Users\JUAN\Downloads\Tag Team Mod Installer 2\repo-staging\BT3-TagTeam-Native')
D = REPO / 'merge' / 'conflicts'
OURS_DIR = REPO / 'controller' / 'tools'


def ours(o, b, t): return list(o)
def theirs(o, b, t): return list(t)
def both(o, b, t): return list(o) + list(t)  # ours first, then upstream additions


def swap(lines, old, new):
    return [ln.replace(old, new) if old in ln else ln for ln in lines]


R = {
    'autopilot.py': [
        lambda o, b, t: list(t[:5]) + list(o[1:5]),
        lambda o, b, t: list(o[:6]) + [o[6].replace("self.connection_error = f'Cannot observe the game through PINE: {error}'", 'self.connection_error = say(SAY_NO_CONNECTION, error=error)')],
    ],
    'controller_assignment.py': [
        ours,
        lambda o, b, t: [t[0]] + list(o[1:5]) + [t[1]],
    ],
    'display_settings.py': [both],
    'extra_reload_forms.py': [ours],
    'extra_reload_preload.py': [ours],
    'extra_reload_worker.py': [ours],
    'extra_special_pools.py': [ours],
    'feature_preferences.py': [both],
    'fresh_team_trainer.py': [both, both, lambda o, b, t: list(o[:2]) + [t[1]]],
    'fusion_partner_lifecycle.py': [ours, ours],
    'game_profile.py': [lambda o, b, t: list(t) + list(o[1:])],
    'guest_loading_screen.py': [ours, ours],
    'localization.py': [both, both],
    'mod_settings.py': [
        lambda o, b, t: [o[0], o[1], o[2],
                         "       ('Controls', (LOCKON_KEY, LOCKON_HOLD_KEY, 'lockoff_enabled', 'lockoff_button', 'lockoff_hold_seconds',",
                         t[3].replace("'lockon_right_stick', ", "                     'lockon_right_stick', ", 1) if False else t[3],
                         t[4], t[5], t[6]],
        lambda o, b, t: [t[0], t[1], o[1].replace("('Fusion', (COOP_FUSION_KEY,", "('Fusion', ('fusion_enabled', COOP_FUSION_KEY,"), o[2]],
        lambda o, b, t: [o[0], o[1].replace("'lockoff_target_hud')),", "'lockoff_target_hud', 'lockon_target_marker', 'lockon_target_style', 'lockon_threat_marks')),")],
        lambda o, b, t: [o[0], t[1], t[2], t[3], t[4],
                         o[3].replace("'Fusion': '", "'Fusion': 'Allow fusions controls new fusions for humans and CPUs; preselected fused characters are unaffected. ", 1)],
        both,
    ],
    'native_mode_menu.py': [ours, both],
    'quad_controller.py': [ours],
    'quad_menu_input.py': [ours],
    'team_assignment.py': [ours, ours, ours],
}


def parse(text):
    lines = text.split('\n')
    segs, i = [], 0
    cur = []
    while i < len(lines):
        if lines[i].startswith('<<<<<<<'):
            segs.append(('text', cur)); cur = []
            j = i + 1
            o = []
            while not lines[j].startswith('|||||||'):
                o.append(lines[j]); j += 1
            j += 1
            b = []
            while not lines[j].startswith('======='):
                b.append(lines[j]); j += 1
            j += 1
            t = []
            while not lines[j].startswith('>>>>>>>'):
                t.append(lines[j]); j += 1
            segs.append(('hunk', (o, b, t)))
            i = j + 1
        else:
            cur.append(lines[i]); i += 1
    segs.append(('text', cur))
    return segs


report = {'resolved': [], 'left_ours': []}
for diff in sorted(D.glob('*.diff3')):
    name = diff.name[:-6]
    spec = R.get(name)
    if not spec:
        report['left_ours'].append(name)
        continue
    text = diff.read_bytes().decode('latin-1')
    segs = parse(text)
    hunks = [s for s in segs if s[0] == 'hunk']
    if len(hunks) != len(spec):
        report['left_ours'].append(f'{name} (hunk count {len(hunks)} != {len(spec)})')
        continue
    out, k = [], 0
    for kind, data in segs:
        if kind == 'text':
            out.extend(data)
        else:
            out.extend(spec[k](*data)); k += 1
    (OURS_DIR / name).write_bytes('\n'.join(out).encode('latin-1'))
    report['resolved'].append(name)
(REPO / 'merge' / 'resolution_report.json').write_text(json.dumps(report, indent=1), encoding='utf-8')
print(report)
