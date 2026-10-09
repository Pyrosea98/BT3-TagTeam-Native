"""Read-only inventory of the known English UI package in the user's ISO."""
from pathlib import Path
import json
import struct
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE/'power-scale-trial/controller/game/tools'))
from extract_loading_assets import package, unpack_bpe
import pycdlib


def main():
    iso_path = HERE.parent/'experiments/.full-install/game/maps/expanded-2x.iso'
    iso = pycdlib.PyCdlib()
    iso.open(str(iso_path))
    try:
        with iso.open_file_from_iso(iso_path='/DATA/PZS3US1.AFS;1') as stream:
            magic, count = struct.unpack('<4sI', stream.read(8))
            if magic != b'AFS\0' or not 450 < count <= 100000:
                raise ValueError('Unexpected USA UI archive')
            table = stream.read(count*8)
            offset, size = struct.unpack_from('<II', table, 450*8)
            stream.seek(offset)
            outer = package(stream.read(size))
    finally:
        iso.close()
    ui = package(unpack_bpe(outer[1]))
    entries = []
    for index, data in enumerate(ui):
        entry = {'index': index, 'bytes': len(data)}
        try:
            children = package(data)
        except ValueError:
            children = []
        entry['children'] = len(children)
        candidates = []
        for child_index, blob in enumerate(children):
            if len(blob) < 0x58:
                continue
            tex0 = struct.unpack_from('<Q', blob, 0x50)[0]
            psm, tw, th = (tex0 >> 20) & 63, (tex0 >> 26) & 15, (tex0 >> 30) & 15
            if psm in (0, 1, 2, 19, 20) and 3 <= tw <= 10 and 3 <= th <= 10:
                candidates.append({'child': child_index, 'psm': psm,
                                   'width': 1 << tw, 'height': 1 << th,
                                   'bytes': len(blob)})
        entry['texture_header_candidates_unverified'] = candidates
        entries.append(entry)
    report = {'source': str(iso_path), 'archive_entries': count, 'afs_index': 450, 'outer_packages': len(outer),
              'ui_entries': entries,
              'confirmed': {'names_entry': 29, 'forms_entry': 30, 'portraits_entry': 31},
              'unknown': ['Shenron', 'Dragon Balls', 'Z sword', 'native VS/frame art'],
              'note': 'Header candidates require decoding and visual inspection; they are not identified art.'}
    output = HERE/'loading-mockups/codex_asset_survey.json'
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(f'UI entries={len(ui)}; inventory={output}')
    print('Candidate texture packages:', [(e['index'], len(e['texture_header_candidates_unverified']))
          for e in entries if e['texture_header_candidates_unverified']])


if __name__ == '__main__':
    main()
