"""Check restart ownership and worker safety without launching a game."""
import json
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE/'power-scale-trial/controller/game/tools'))
from native_failed_preparation import recover, RestartPreparation

previous = os.environ.pop('PS2X_PACKAGE_DATA', None)
try:
    assert recover(SimpleNamespace(state='FAILED', worker=None)) is False
    with tempfile.TemporaryDirectory(prefix='bt3-prep-recovery-', dir=HERE) as folder:
        os.environ['PS2X_PACKAGE_DATA'] = folder
        request = Path(folder)/'restart-request.json'
        for state in ('WAITING', 'PREPARING', 'RUNNING'):
            assert recover(SimpleNamespace(state=state, worker=None)) is False
        assert recover(SimpleNamespace(state='FAILED', worker=SimpleNamespace(is_alive=lambda: True))) is False
        assert not request.exists()
        try:
            recover(SimpleNamespace(state='FAILED', worker=SimpleNamespace(is_alive=lambda: False)))
        except RestartPreparation:
            pass
        else:
            raise AssertionError('Failed installed preparation did not end the controller loop')
        value = json.loads(request.read_text())
        assert value == dict(schema=1, owner_pid=os.getpid(), reason='failed-preparation')
finally:
    if previous is None:
        os.environ.pop('PS2X_PACKAGE_DATA', None)
    else:
        os.environ['PS2X_PACKAGE_DATA'] = previous
print('PASS: installed recovery requests its own restart; active workers and developer runs stay untouched')
