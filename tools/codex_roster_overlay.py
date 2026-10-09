"""Load the roster trial's staged modules, preserving their original data paths."""
import importlib.abc
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
STAGED = HERE/'roster-tools'
TOOLS = HERE/'power-scale-trial/controller/game/tools'


class RosterLoader(importlib.abc.Loader):
    def __init__(self, name): self.name = name
    def create_module(self, spec): return None
    def exec_module(self, module):
        original, staged = TOOLS/(self.name+'.py'), STAGED/(self.name+'.py')
        module.__file__ = str(original)
        exec(compile(staged.read_text(encoding='utf-8'), str(staged), 'exec'), module.__dict__)


class RosterFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if '.' not in fullname and (STAGED/(fullname+'.py')).is_file():
            return importlib.util.spec_from_loader(fullname, RosterLoader(fullname))


def install():
    names = {path.stem for path in STAGED.glob('*.py')}
    if not names or names.intersection(sys.modules):
        raise RuntimeError('Roster overlay must be installed before controller modules load')
    sys.meta_path.insert(0, RosterFinder())

