"""Check failed/successful stage receipts without connecting to the game."""
import json
from pathlib import Path
import tempfile
from codex_preparation_timing import timed, boundary

class Session:
    def __init__(self,run):self.run=run
    @timed
    def prepare(self):
        boundary(self,'capture')
        self.install({},'resources')
        boundary(self,'activation')
    @timed
    def install(self,manifest,label):return 7
    @timed
    def wait_word(self,address,expected,label):raise RuntimeError('original failure')

with tempfile.TemporaryDirectory(dir=Path(__file__).parent/'power-scale-trial',prefix='codex-timing-check-') as temporary:
    session=Session(Path(temporary));session.prepare()
    try:session.wait_word(0,1,'actors')
    except RuntimeError as error:assert str(error)=='original failure'
    else:raise AssertionError('Failure was swallowed')
    events=[json.loads(line) for line in (session.run/'preparation-timings.jsonl').read_text().splitlines()]
    assert [e['stage'] for e in events if e['kind']=='phase']==['capture','activation']
    assert any(e['stage']=='install:resources' and e['status']=='ok' for e in events)
    assert events[-1]['stage']=='wait_word:actors' and events[-1]['status']=='failed'
    assert all(e['milliseconds']>=0 for e in events)
    assert session._timing_phase is None
print('PASS: phase/operation/total receipts and unchanged failure propagation')
