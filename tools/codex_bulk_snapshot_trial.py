"""Isolated trial: override only the RAM read transport on the next launch."""
import importlib.abc
import importlib.machinery
import sys
from codex_native_bulk_snapshot import read_ram

class Loader(importlib.abc.Loader):
    def __init__(self,original):self.original=original
    def create_module(self,spec):return None
    def exec_module(self,module):
        self.original.exec_module(module)
        module.read_ram=read_ram

class Finder(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname!='native_preparation':return None
        spec=importlib.machinery.PathFinder.find_spec(fullname,path)
        if spec is None:return None
        spec.loader=Loader(spec.loader)
        return spec

if __name__=='__main__':
    import run_power_scale_native as launch
    name='ps2EntryRunner-native-bulk-snapshot.exe'
    launch.RUNNER_FEATURES[name]=frozenset(('rematch','roster'))
    if '--runner' in sys.argv:raise ValueError('Bulk snapshot trial uses its dedicated runner')
    sys.argv.extend(('--runner',name))
    sys.meta_path.insert(0,Finder())
    raise SystemExit(launch.main())
