"""Resolve the native controller's lazy dependency graph without running tools."""
import ast
import importlib
import importlib.util
import os
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
CONTROLLER=HERE/'power-scale-trial/controller'
TOOLS=CONTROLLER/'game/tools'


def check_dependencies(roster=True):
    sys.path.insert(0,str(CONTROLLER))
    sys.path.insert(0,str(TOOLS))
    wheels=list((CONTROLLER/'vendor-wheels').glob('*.whl'))+list((TOOLS/'vendor-wheels').glob('*.whl'))
    for wheel in wheels:
        sys.path.insert(0,str(wheel))
    # Independently spawned loading/audio helpers need these same local imports.
    paths=[str(CONTROLLER),*(str(wheel) for wheel in wheels)]
    existing=os.environ.get('PYTHONPATH','')
    os.environ['PYTHONPATH']=os.pathsep.join(paths+([existing] if existing else []))
    pending=['autopilot','fusion_audio_restore','map_scale_launch','regional','game_profile']
    visited=set();missing=[]
    while pending:
        name=pending.pop()
        if name in visited:continue
        visited.add(name)
        source=TOOLS/(name+'.py')
        if roster and (HERE/'roster-tools'/source.name).is_file():
            source=HERE/'roster-tools'/source.name
        if not source.is_file():continue
        tree=ast.parse(source.read_text(encoding='utf-8-sig'),str(source))
        # Offline preview functions may depend on developer-only test helpers.
        # Production lazy methods and their imports are still traversed.
        def runtime_nodes(node):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name=='preview':return
            yield node
            for child in ast.iter_child_nodes(node):yield from runtime_nodes(child)
        for node in runtime_nodes(tree):
            if isinstance(node,ast.Import):names=[item.name for item in node.names]
            elif isinstance(node,ast.ImportFrom) and node.module and not node.level:names=[node.module]
            else:continue
            for dependency in names:
                top=dependency.split('.')[0]
                if (top=='fcntl' and os.name=='nt') or (top=='msvcrt' and os.name!='nt'):
                    continue
                if (TOOLS/(top+'.py')).is_file():
                    pending.append(top)
                    continue
                try:spec=importlib.util.find_spec(dependency)
                except (ImportError,ValueError):spec=None
                if spec is None:missing.append((name,dependency,node.lineno))
    # Import the staged package's actual lazy entry points and relative imports.
    for name in ('iso_compatibility.disc','iso_compatibility.scanner','iso_compatibility.expanded_maps'):
        module=importlib.import_module(name)
        if not Path(module.__file__).resolve().is_relative_to(CONTROLLER.resolve()):
            raise RuntimeError('Disc compatibility package resolved outside the native trial')
    if missing:
        raise RuntimeError('Missing controller dependencies: '+', '.join(f'{owner}:{line} {name}' for owner,name,line in sorted(set(missing))))
    return dict(controller_modules=len(visited),controller_module_names=sorted(visited),package='Native trial local iso_compatibility',missing=[])


if __name__=='__main__':print(check_dependencies())
