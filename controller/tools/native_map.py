"""The game's native addresses and identity for the selected disc: USA (SLUS-21678) or European (SLES-54945).

The tools are written against the USA executable. Every native address in them goes through A(), every
gp-relative offset through GPO() (prototype.Assembler and ai_shadow.Assembler do that themselves for base
register 28), and every disc file ID through FILE_ID(). For the USA adapter all of them return their input
unchanged, so the USA output stays byte-identical.

For the European adapter ('bt3-pal') they look the USA value up in pal_native_map.json, which
release_tools/build_pal_map.py generates from the European executable and DBZP.BIN (plus reviewed values in
release_tools/pal_reviewed.json). An address the table does not list raises NativeMapError: the European
build never falls back to a USA address.

Adapter: the TAGTEAM_ADAPTER environment variable when set, else the installed game profile
(game-profile.json, else player-install.json), else 'bt3-usa'. It is read once, at import; tests that need
the European values run in a subprocess (or reload this module) with TAGTEAM_ADAPTER=bt3-pal.
"""
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TABLE = HERE / 'pal_native_map.json'

# Adapters whose executable keeps the USA BT3 address space (identity translation).
IDENTITY_ADAPTERS = ('bt3-usa', 'bt4-b14-rev2-eng')
USA_GP, PAL_GP = 0x304270, 0x305370
# Opcodes whose 16-bit immediate is an address offset from the base register: loads, stores (GPR, COP1, COP2,
# 64/128-bit), cache/pref, and addiu/daddiu. With base register 28 the immediate is a gp offset (GPO).
GP_RELATIVE_OPS = frozenset({0x09, 0x19, 0x1A, 0x1B, 0x1E, 0x1F, 0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27,
                             0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x31, 0x33, 0x36, 0x37, 0x39, 0x3E,
                             0x3F})


class NativeMapError(LookupError):
    """A native reference has no reviewed value for the selected disc."""


def _resolve_adapter():
    value = os.environ.get('TAGTEAM_ADAPTER', '').strip()
    source = 'TAGTEAM_ADAPTER'
    if not value:
        import game_profile
        value, source = game_profile.installed_adapter() or 'bt3-usa', 'the installed game profile'
    if value == 'bt3-pal':
        return 'bt3-pal'
    if value in IDENTITY_ADAPTERS:
        return 'bt3-usa'
    raise NativeMapError(f'Unknown game adapter {value!r} from {source}; expected bt3-usa or bt3-pal.')


ADAPTER = _resolve_adapter()
PAL = ADAPTER == 'bt3-pal'

SERIAL = 'SLES-54945' if PAL else 'SLUS-21678'
SERIAL_FILE = 'SLES_549.45' if PAL else 'SLUS_216.78'
CRC = 'A422BB13' if PAL else '428113C2'
CHEAT_PREFIX = f'{SERIAL}_{CRC}'
GP = PAL_GP if PAL else USA_GP            # the $gp register value of the native executable

HZ = 50 if PAL else 60                    # presentation fields per second
ACTOR_HZ = 25 if PAL else 30              # game-logic ticks per second
DISPLAY_H = 512 if PAL else 448           # interlaced frame height in lines
Y_ORIGIN = 1792 if PAL else 1824          # GS XYOFFSET Y in pixels (2048 - DISPLAY_H/2)
VRAM_SHIFT = 0x600 if PAL else 0          # GS blocks the larger PAL frame/Z buffers push native banks up


def elf_path(game_dir):
    """The installed copy of the executable: game_dir/analysis/<serial file>."""
    return Path(game_dir) / 'analysis' / SERIAL_FILE


def ticks(n, base=60):
    """A mod-owned duration of n ticks at `base` Hz, in presentation fields of this disc.

    Native frame counts must come from the executable, never from this helper."""
    return n if not PAL else int(round(n * HZ / base))


# ------------------------------------------------------------------------------------------ the table

_table = None


def _hex(value):
    return int(value, 16)


def table():
    """The loaded European table (PAL only). Raises NativeMapError when it is missing or does not fit."""
    global _table
    if _table is not None:
        return _table
    if not PAL:
        raise NativeMapError('The USA adapter has no translation table.')
    try:
        doc = json.loads(TABLE.read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise NativeMapError(f'European address table unavailable ({TABLE.name}): {error}') from None
    if doc.get('schema') != 1 or doc.get('adapter') != 'bt3-pal':
        raise NativeMapError(f'{TABLE.name} is not a schema-1 bt3-pal table.')
    gp = doc.get('gp', {})
    if _hex(gp.get('usa', '0')) != USA_GP or _hex(gp.get('pal', '0')) != PAL_GP:
        raise NativeMapError(f'{TABLE.name} has unexpected gp values {gp}.')
    elf = elf_path(ROOT)
    if elf.is_file() and hashlib.sha256(elf.read_bytes()).hexdigest() != doc.get('elf_sha256'):
        raise NativeMapError(f'{elf} is not the executable {TABLE.name} was generated from; '
                             'reinstall or regenerate the table.')
    addr = {_hex(k): _hex(v) for k, v in doc.get('addr', {}).items()}
    addr.update({_hex(k): _hex(v) for k, v in doc.get('overrides', {}).items()})
    ranges = {}
    for key, (pal, length) in doc.get('ranges', {}).items():
        usa, usa_len = key.split('+')
        ranges[(_hex(usa), _hex(usa_len))] = (_hex(pal), _hex(length))
    segments = sorted((_hex(lo), _hex(hi), int(delta)) for lo, hi, delta in gp.get('segments', ()))
    _table = dict(addr=addr, ranges=ranges, segments=segments, doc=doc)
    return _table


def _pal_address(usa):
    if type(usa) is not int:
        raise TypeError(f'native address must be an int, not {type(usa).__name__}')
    value = table()['addr'].get(usa)
    if value is None:
        raise NativeMapError(f'No reviewed European address for USA {usa:#x}.')
    return value


def _pal_gp_target(usa):
    t = table()
    value = t['addr'].get(usa)
    if value is not None:
        return value
    for lo, hi, delta in t['segments']:
        if lo <= usa < hi:
            return usa + delta
    raise NativeMapError(f'No reviewed European address for the gp-relative USA target {usa:#x}.')


if PAL:
    def A(usa_addr):
        """USA native address -> European native address (NativeMapError when not reviewed)."""
        return _pal_address(usa_addr)

    def GPO(usa_gp_offset):
        """USA gp-relative offset -> the European offset reaching the same variable."""
        off = int(usa_gp_offset)
        if 0x8000 <= off <= 0xFFFF:
            off -= 0x10000
        if not -0x8000 <= off < 0x8000:
            raise NativeMapError(f'gp offset out of range: {usa_gp_offset!r}')
        new = _pal_gp_target(USA_GP + off) - PAL_GP
        if not -0x8000 <= new < 0x8000:
            raise NativeMapError(f'USA gp offset {off} does not reach its European target through $gp.')
        return new

    def RANGE(usa_addr, usa_len):
        """USA native byte range -> (European address, European length)."""
        reviewed = table()['ranges'].get((usa_addr, usa_len))
        if reviewed is not None:
            return reviewed
        start = A(usa_addr)
        if usa_len > 4:
            last = usa_addr + usa_len - 4
            if A(last) != start + usa_len - 4:
                raise NativeMapError(f'USA range {usa_addr:#x}+{usa_len:#x} changes layout in the European '
                                     'executable and has no reviewed range.')
        return start, usa_len

    _FILE_SHIFTS = ((1, 4, 1), (8, 510, 4), (511, 610, 97), (659, None, 247))

    def FILE_ID(usa_id):
        """USA disc (AFS) global file ID -> European ID (the localised volumes insert files)."""
        for lo, hi, shift in _FILE_SHIFTS:
            if usa_id >= lo and (hi is None or usa_id <= hi):
                return usa_id + shift
        raise NativeMapError(f'No reviewed European disc file for USA file ID {usa_id}.')
else:
    def A(usa_addr):
        return usa_addr

    def GPO(usa_gp_offset):
        return usa_gp_offset

    def RANGE(usa_addr, usa_len):
        return usa_addr, usa_len

    def FILE_ID(usa_id):
        return usa_id
