"""Separate projectile-routing trial; uses the existing controller connection."""
import os
import sys
from codex_bulk_snapshot_trial import Finder
if __name__=='__main__':
    import run_power_scale_native as launch
    name='ps2EntryRunner-native-ki-routing.exe'
    launch.RUNNER_FEATURES[name]=frozenset(('rematch','roster'))
    if '--runner' in sys.argv:raise ValueError('Ki routing trial uses its dedicated runner')
    os.environ['PS2X_KI_ROUTE']='1'
    os.environ['PS2X_KI_TRACE']='1'
    sys.argv.extend(('--runner',name))
    sys.meta_path.insert(0,Finder())
    raise SystemExit(launch.main())
