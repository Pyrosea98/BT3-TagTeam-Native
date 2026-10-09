"""Recover an installed failed preparation through a clean owned-process restart."""
import os
from pathlib import Path
from atomic_files import write_json

class RestartPreparation(KeyboardInterrupt):
    pass

def recover(watcher):
    package=os.environ.get('PS2X_PACKAGE_DATA')
    if not package or watcher.state!='FAILED':return False
    worker=getattr(watcher,'worker',None)
    if worker is not None and worker.is_alive():return False
    write_json(Path(package)/'restart-request.json',
               dict(schema=1,owner_pid=os.getpid(),reason='failed-preparation'))
    print('Native preparation failed; restarting the owned game and controller cleanly.',flush=True)
    raise RestartPreparation
