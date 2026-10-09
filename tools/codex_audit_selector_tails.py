"""Read-only inventory of direct generated tails into patched target selectors."""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE / 'power-scale-trial/controller/game/tools'
patches = json.loads((TOOLS.parent / 'analysis/research_opponent_patches.json').read_text())['patches']
selectors = [int(row['address'], 16) for row in patches]
selectors += [0x1DB268, 0x1DB2C0, 0x1DB844, 0x1DB8DC, 0x1DBA48, 0x1DBCF4]
assert len(set(selectors)) == 27
files = list((HERE / 'repo/ps2xRuntime/src/runner').glob('*.cpp'))
bodies = {path: path.read_text(errors='replace') for path in files}
owners = {}
site_pattern = re.compile(r'//\s*0x([0-9a-fA-F]+):')
selector_set = set(selectors)
for path, body in bodies.items():
    sites = {int(match.group(1), 16) for match in site_pattern.finditer(body)} & selector_set
    if sites:
        name = re.search(r'void\s+(\w+)\(', body)
        if name:
            owners.setdefault(name.group(1), set()).update(sites)
tails = []
pattern = re.compile(r'(\w+)\(rdram,\s*ctx,\s*runtime\);\s*return;')
for path, body in bodies.items():
    for match in pattern.finditer(body):
        if match.group(1) in owners:
            tails.append({'caller_file': path.name, 'line': body.count('\n', 0, match.start()) + 1,
                          'callee': match.group(1),
                          'patched_sites': [f'{a:08X}' for a in sorted(owners[match.group(1)])]})
report = {'scope': '27 team_targets selector sites; direct call followed by return only',
          'limitations': 'Does not prove embedded copies, arbitrary indirect chains or every attack family safe.',
          'selector_count': len(selectors), 'identified_callee_count': len(owners),
          'unlocated_sites': [f'{a:08X}' for a in sorted(selector_set - set().union(*owners.values()))],
          'tails': tails}
output = HERE / 'power-scale-trial/native-selector-tail-audit.json'
output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
