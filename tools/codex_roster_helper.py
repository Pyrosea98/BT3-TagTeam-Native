"""Run the loading cover with the same staged roster modules as its controller."""
import sys
from codex_roster_overlay import HERE, STAGED, TOOLS, install

if __name__ == '__main__':
    sys.path.insert(0, str(HERE/'power-scale-trial/controller'))
    sys.path.insert(0, str(TOOLS))
    install()
    sys.argv[0] = str(TOOLS/'loading_presentation.py')
    source = STAGED/'loading_presentation.py'
    exec(compile(source.read_text(encoding='utf-8'), str(source), 'exec'),
         dict(__name__='__main__', __file__=sys.argv[0]))
