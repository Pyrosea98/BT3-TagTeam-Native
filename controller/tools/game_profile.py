"""Paths for an installer-owned ISO; developer folders retain their defaults."""
import json
import re
from functools import lru_cache
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ADAPTERS=('bt3-usa','bt3-pal','bt4-b14-rev2-eng')
POWER_SCALE_VARIANT='BT3 Power Scale BETA 1.5.1 (experimental)'
POWER_SCALE_DISCS=frozenset(('f3e495b8eb2269c2808f00352058d0be6facf3db4bf1c013f2d78ea2a531c6d3',
                           'e26dbbe6cfb75d7e407f7d197330b270de47b50ac83920ba435f946868a0390e'))


def installed():
    path=ROOT/'game-profile.json'
    if not path.exists():return None
    value=json.loads(path.read_text(encoding='utf-8'))
    if value.get('schema')!=1 or value.get('adapter') not in ADAPTERS:
        raise ValueError('Invalid installed game profile; run the installer in a new folder.')
    # The first native importer omitted this field. Recover only these exact
    # supported disc identities; opcode and relocated-module guards remain.
    if 'runtime_variant' not in value and value.get('adapter')=='bt3-usa' and value.get('iso_sha256') in POWER_SCALE_DISCS:
        value['runtime_variant']=POWER_SCALE_VARIANT
    return value


def installed_adapter():
    """The installed adapter (game-profile.json, else player-install.json); None in a developer tree."""
    profile=installed()
    marker=ROOT/'player-install.json'
    value=json.loads(marker.read_text(encoding='utf-8')).get('adapter') if marker.is_file() else None
    if profile:
        if value is not None and value!=profile['adapter']:
            raise ValueError('player-install.json and game-profile.json name different games; reinstall in a new folder.')
        return profile['adapter']
    if value is not None and value not in ADAPTERS:
        raise ValueError('Invalid player-install.json adapter; run the installer in a new folder.')
    return value


def source_iso(default):
    profile=installed()
    return Path(profile['iso']).resolve() if profile else Path(default).resolve()


@lru_cache(maxsize=1)
def pcsx2_crc():
    """Selected disc identity for PINE, cheats and savestate filenames.

    Patch manifests retain the adapter's internal ID; that is independent of
    this emulator identifier. Repackaging an otherwise identical ELF can
    change its CRC. The installer records it only after runtime validation.
    """
    from native_map import CRC
    profile=installed()
    value=profile.get('pcsx2_crc',CRC) if profile else CRC
    if not isinstance(value,str) or not re.fullmatch('[0-9A-Fa-f]{8}',value):
        raise ValueError('Invalid PCSX2 game identifier in installed profile')
    return value.upper()


def cheat_name(serial):
    return f'{serial}_{pcsx2_crc()}_BT3Loading.pnach'


def map_paths(default_source,default_output,default_manifest):
    profile=installed()
    if profile:
        return source_iso(default_source),ROOT/'maps/expanded-2x.iso',ROOT/'maps/expanded-2x.json'
    return Path(default_source),Path(default_output),Path(default_manifest)


def check(refresh=False):
    record=installed()
    if record is None:return None
    import sys
    sys.path.insert(0,str(ROOT.parent))
    from iso_compatibility.scanner import scan,report
    value=scan(record['iso'],refresh=refresh,progress=lambda line:print(line,file=sys.stderr))
    if not value['capabilities']['runtime_hooks'] or value['identity']['adapter']!=record['adapter']:
        raise ValueError('Selected ISO no longer matches its installed runtime adapter. Install it in a new folder.')
    if value['identity']['iso_sha256']!=record['iso_sha256']:
        raise ValueError('Selected ISO changed since installation. Reinstall to refresh portraits, resources and native references.')
    if value['identity']['pcsx2_crc']!=pcsx2_crc():
        raise ValueError('Installed PCSX2 identifier differs from the scanned ISO. Reinstall to refresh the game profile.')
    (ROOT/'COMPATIBILITY.md').write_text(report(value),encoding='utf-8')
    return value


if __name__=='__main__':check(refresh=True)
