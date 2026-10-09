"""Resolve the optional expanded-map ISO before starting PCSX2."""
from pathlib import Path
import sys
import mod_settings
from localization import tr

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from iso_compatibility.expanded_maps import installed,SOURCE,OUTPUT,MANIFEST
import game_profile
SOURCE,OUTPUT,MANIFEST=game_profile.map_paths(SOURCE,OUTPUT,MANIFEST)


MISSING='Expanded maps are on, but the expanded ISO is missing or out of date. Starting the original ISO; run Build expanded maps.cmd first.'


def expanded_ready():
    """Whether the expanded-map ISO is built and still matches its manifest."""
    return installed(SOURCE,OUTPUT,MANIFEST) is not None


def selected_iso(settings=None):
    """The ISO to boot. A missing expanded build never stops a launch: the
    original ISO starts instead, with a warning on stderr (stdout is the path)."""
    game_profile.check()
    values=mod_settings.load_settings() if settings is None else settings
    if not values.get('expanded_maps',False):return SOURCE
    if not expanded_ready():
        message=tr(MISSING,values)
        try:print(message,file=sys.stderr)
        except UnicodeEncodeError:print(message.encode('ascii','replace').decode(),file=sys.stderr)
        return SOURCE
    return OUTPUT


if __name__=='__main__':
    try:
        if '--build' in sys.argv:
            from iso_compatibility.expanded_maps import build
            build(SOURCE,OUTPUT,MANIFEST)
        else:print(selected_iso())
    except (OSError,ValueError) as error:print(str(error),file=sys.stderr);raise SystemExit(1)
