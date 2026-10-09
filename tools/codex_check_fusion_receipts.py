"""Offline transform/defusion/transform ownership handoff regression."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sys
here=Path(__file__).resolve().parent
sys.path.insert(0,str(here/'power-scale-trial/controller/game/tools'))
from codex_roster_overlay import install
install()
import fusion_duration_worker as fusion
import extra_reload_worker as reload

old2={'resource':200};old3={'resource':300};unaffected={'resource':400,'handle':4}
stage={'stage':'must remain owned'}
extra=SimpleNamespace(form_job=None,resources={2:old2,3:old3,4:unaffected},
    retained={2:[{'resource':190}],4:[{'resource':410,'handle':5}]},owned=stage,retirement_notes=[])
worker=fusion.Worker.__new__(fusion.Worker)
worker._coordinated_generation=None
worker.completed=dict(generation=7,physical_ids=[2,3],old_resources={2:900,3:901},
    new_resources={},descriptor_mapping={410:420},mapped_handles={420:6})
worker.progress=lambda *_:None
worker.coordinate_reload_worker(extra)
assert 2 not in extra.resources and 3 not in extra.resources and 2 not in extra.retained
assert extra.resources[4] is unaffected and extra.retained[4][0]==dict(resource=420,handle=6)
assert len(extra.fusion_receipt_quarantine)==3 and extra.owned is stage
worker.coordinate_reload_worker(extra)
assert len(extra.fusion_receipt_quarantine)==3
# A fresh completed transformation can register its own exact receipt without
# attempting to destroy the previous fusion/initial bundle.
new={'resource':1000};ram=b'unchanged'
with patch.object(reload.retire,'receipt',return_value=new),patch.object(reload.retire,'build_memory',side_effect=AssertionError('Unexpected destructor audit')):
    assert reload.Worker._complete_resources(extra,None,ram,{'physical':2,'old_resource':902}) is ram
assert extra.resources[2] is new
# Unexplained stale ownership outside a verified defusion is still a failure.
with patch.object(reload.retire,'receipt',return_value={'resource':1001}):
    try:reload.Worker._complete_resources(extra,None,ram,{'physical':2,'old_resource':999})
    except RuntimeError as error:assert 'Owned resource identity changed' in str(error)
    else:raise AssertionError('Unexplained ownership mismatch accepted')
extra.form_job={'pending':True};worker.completed=dict(worker.completed,generation=8)
before=dict(extra.resources)
try:worker.coordinate_reload_worker(extra)
except RuntimeError:pass
else:raise AssertionError('In-flight owner invalidated')
assert extra.resources==before
# Actual producer shape: fusion_duration_commit.build_memory emits
# configurations=[cfg] for the leader, and a separate partner_plan. This is
# source-derived, not a recorded live event (the failed run did not log IDs).
for health in (1,5,100):
    for old_ids in ({0:900},{0:900,4:940}):
        extra=SimpleNamespace(form_job=None,resources={0:{'resource':100},2:{'resource':200},4:{'resource':400}},
            retained={2:[{'resource':190}]},owned=stage,retirement_notes=[])
        worker=fusion.Worker.__new__(fusion.Worker);worker._coordinated_generation=None
        worker.completed=dict(generation=10,physical_ids=[0,2],old_resources=old_ids,
            new_resources={},descriptor_mapping={},mapped_handles={},
            bodies=[dict(physical=0,health=health),dict(physical=2,health=health)])
        messages=[];worker.progress=messages.append
        worker.coordinate_reload_worker(extra)
        assert 0 not in extra.resources and 2 not in extra.resources and 2 not in extra.retained
        assert (4 not in extra.resources)==(4 in old_ids)
        assert len(extra.fusion_receipt_quarantine)==3+int(4 in old_ids)
        assert 'physical_ids=[0, 2]' in messages[0] and 'old_resources=' in messages[0]
        worker.coordinate_reload_worker(extra)
        assert len(messages)==2  # diagnostic + reconciliation, once per generation
        # No previous transformation: there are no receipts to quarantine.
        extra.resources={};extra.retained={};worker._coordinated_generation=None
        worker.coordinate_reload_worker(extra)
        assert not extra.resources and not extra.retained
# Malformed ownership remains diagnosed BEFORE any authority is discarded.
from codex_fusion_receipts import invalidate_restored_partners
for changes,condition in ((dict(physical_ids=[0,10]),'physical IDs'),
                          (dict(physical_ids=[0,0]),'Duplicate'),
                          (dict(new_resources={0:{'resource':123}}),'new resource ownership')):
    event=dict(worker.completed,**changes)
    extra.resources={0:{'resource':100}};before=dict(extra.resources)
    try:invalidate_restored_partners(extra,event)
    except ValueError as error:
        assert condition in str(error) and 'old_resources=' in str(error) and 'physical_ids=' in str(error)
    else:raise AssertionError('Malformed ownership accepted')
    assert extra.resources==before
print('PASS: defusion receipt invalidation, unaffected ownership/migration, next transformation and strict mismatch guards')
