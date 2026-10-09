"""Replay real co-op preparation failures and reject altered asset aliases."""
from pathlib import Path
import json
import struct
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'power-scale-trial/controller/game/tools'))
from codex_roster_overlay import install
install()
import extra_special_pools as pools
import fresh_team_ai as ai
import fresh_team_trainer as trainer
import fusion_partner_lifecycle

fusion_partner_lifecycle.POWER_SCALE_SIDE_TARGET = 0x008CA9C0 + 0x2264
root = HERE / 'power-scale-trial/controller/game/analysis/prepared-states'
audits = json.loads((HERE / 'power-scale-trial/codex-giant-row-audit.json').read_text())
for audit in audits:
    capture = root / audit['capture']
    ram = bytearray((capture / 'current-ee.bin').read_bytes())
    addresses = {row['address'] for row in audit['unknown']}
    verified, receipts = pools.immutable_combat_literals(ram, audit['models'], addresses)
    assert verified == addresses, (audit['capture'], verified)
    assert any(r['resource_file'] == 2862 and r['bytes'] == 916096 for r in receipts)
    # The proof covers the entire file, not just the apparent pointer.
    file = next(r for r in receipts if r['resource_file'] == 2862)
    at = file['address'] + 128
    ram[at] ^= 1
    assert not pools.immutable_combat_literals(ram, audit['models'][:1], addresses)[0]
    ram[at] ^= 1
    u = lambda p: struct.unpack_from('<I', ram, p)[0]
    resource = u(audit['models'][0] + 20)
    original_id = u(resource + 24)
    struct.pack_into('<I', ram, resource + 24, original_id + 1)
    assert not pools.immutable_combat_literals(ram, audit['models'][:1], addresses)[0]
    struct.pack_into('<I', ram, resource + 24, original_id)
    original_owner = u(audit['models'][0] + 20)
    struct.pack_into('<I', ram, audit['models'][0] + 20, original_owner + 4)
    assert not pools.immutable_combat_literals(ram, audit['models'][:1], addresses)[0]
    struct.pack_into('<I', ram, audit['models'][0] + 20, original_owner)
    assert not pools.immutable_combat_literals(ram, audit['models'], {0x00100000})[0]
    print('PASS: ' + audit['capture'] + ' original animation literals proven; altered bytes/ID/owner and code rejected', flush=True)
    session = json.loads((capture / 'session.json').read_text(encoding='utf-8'))
    selection = json.loads((capture / 'selection.json').read_text(encoding='utf-8'))
    installation = json.loads((capture / 'ai-installation.json').read_text(encoding='utf-8'))
    support = json.loads((capture / 'support.json').read_text(encoding='utf-8'))
    with tempfile.TemporaryDirectory(prefix='giant-replay-', dir=HERE / 'power-scale-trial') as temp:
        path = Path(temp) / 'ai-ready.bin'
        path.write_bytes(ram)
        activation = ai.build_activation(path, installation, support)
        manifest = trainer.final_team_manifest(ram, activation, capture / '00-original-selected-match.bin',
            settings=session['settings'], battle_mode='teams', humans=2, assignment=(0, 2),
            present_mask=selection['participation_mask'], play_intro=True)
        # Asset bytes must remain untouched by the complete preparation plan.
        for block in manifest['blocks']:
            at = block['address']
            data = bytes.fromhex(block['data_hex'])
            assert not (at < file['address'] + file['bytes'] and at + len(data) > file['address'])
        print('PASS: ' + audit['capture'] + ' complete two-human preparation; blocks=' + str(len(manifest['blocks'])), flush=True)
