"""Separate native-target trial; retain bulk transport and Python as oracle."""
import sys
import os
from codex_bulk_snapshot_trial import Finder

if __name__=='__main__':
    import run_power_scale_native as launch
    name='ps2EntryRunner-native-targets.exe'
    if '--target-trace' in sys.argv:
        sys.argv.remove('--target-trace')
        name='ps2EntryRunner-native-targets-trace.exe'
        os.environ['PS2X_TARGET_TRACE']='1'
    launch.RUNNER_FEATURES[name]=frozenset(('rematch','roster'))
    if '--runner' in sys.argv:raise ValueError('Native targets trial uses its dedicated runner')
    sys.argv.extend(('--runner',name))
    sys.meta_path.insert(0,Finder())
    raise SystemExit(launch.main())
