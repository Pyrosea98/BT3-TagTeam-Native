"""Claude: look for GS TEX0 values (PSMT4 128x128 = the match-clock digits; PSMT8 256x64 = HUD plates/bars) anywhere in the
game archives, at any offset, in decoded packages up to depth 5. Read-only; writes power-scale-trial/hud-provenance-scan.json."""
import sys
import struct
import json
import time
from pathlib import Path
HERE = Path(__file__).resolve().parent
TRIAL = HERE / 'power-scale-trial'
sys.path.insert(0, str(TRIAL / 'controller/game/tools'))
import extract_loading_assets as ex
import pycdlib

ISO = HERE.parent / 'experiments/.full-install/game/maps/expanded-2x.iso'
# (psm, tw, th) wanted: numerals PSMT4 128x128; plate/bars PSMT8 256x64 (tw 8, th 6); blast numerals PSMT8 128x64
WANT = {(20, 7, 7): 'timer_digits_P4_128x128', (19, 8, 6): 'hud_plate_or_bars_P8_256x64', (19, 7, 6): 'blast_numerals_P8_128x64'}
hits = []
t0 = time.time()
iso = pycdlib.PyCdlib()
iso.open(str(ISO))


def scan_blob(blob, path):
    # TEX0 candidates at 8-byte alignment
    n = len(blob) // 8
    if n:
        words = struct.unpack_from('<%dQ' % n, blob, 0)
        for i, v in enumerate(words):
            psm = (v >> 20) & 63
            tw = (v >> 26) & 15
            th = (v >> 30) & 15
            key = (psm, tw, th)
            if key in WANT and i + 1 < n and words[i + 1] in (6, 7):   # GIF A+D qword: TEX0_1/TEX0_2 register address
                tbp = v & 0x3FFF
                tbw = (v >> 14) & 63
                cpsm = (v >> 51) & 15
                if tbw in (1, 2, 3, 4) and cpsm in (0, 2, 10) and tbp < 0x4000:
                    hits.append(dict(path=path, off=i * 8, what=WANT[key], tbp=tbp, tbw=tbw, tex0=hex(v)))


def descend(blob, path, depth):
    scan_blob(blob, path)
    if depth >= 5:
        return
    try:
        sub = ex.package(blob)
    except Exception:
        try:
            sub = ex.package(ex.unpack_bpe(blob))
        except Exception:
            return
    for i, b in enumerate(sub):
        if len(b) > 64:
            descend(b, path + [i], depth + 1)


for name, limit in (('PZS3US1', 6 * 1024 * 1024), ('PZS3US0', 6 * 1024 * 1024), ('PZS3US2', 2 * 1024 * 1024)):
    with iso.open_file_from_iso(iso_path='/DATA/%s.AFS;1' % name) as s:
        magic, cnt = struct.unpack('<4sI', s.read(8))
        tab = s.read(cnt * 8)
        for i in range(cnt):
            off, size = struct.unpack_from('<II', tab, i * 8)
            if size > limit or size < 128:
                continue
            s.seek(off)
            descend(s.read(size), [name, i], 0)
        print(name, 'done', round(time.time() - t0), 's, hits so far', len(hits), flush=True)
json.dump(hits, open(TRIAL / 'hud-provenance-scan.json', 'w'), indent=1)
by = {}
for h in hits:
    by.setdefault(h['what'], []).append(h)
for k, v in by.items():
    print(k, len(v), [(x['path'], x['off'], x['tbp']) for x in v[:6]])
