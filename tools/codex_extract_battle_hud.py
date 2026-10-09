"""Offline importer prototype: extract verified AFS1 entry-5 HUD streams.

Reads the player's ISO; writes derived files only. Requires the small native
codex_decode_disc_indices helper, pycdlib and Pillow on the development host.
This is not yet integrated into the standalone native importer.
"""
import argparse
import hashlib
import json
import struct
import subprocess
from pathlib import Path

import pycdlib
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
TRIAL = HERE / 'power-scale-trial'
ENTRY_SHA256 = '019665de20c36caeff3d25d2b1f40e76cf549f1df122955cf3274c3cf9a822c3'
# Explicit transfer geometry, not assumptions about entry-5 header offsets.
ASSETS = [
    ('timer-grey', 2528, 20, 128, 128, 2, 64, 32, 10848, 16, 10752, 11392),
    ('timer-yellow', 2528, 20, 128, 128, 2, 64, 32, 11040, 16, 10752, 11396),
    ('timer-red', 2528, 20, 128, 128, 2, 64, 32, 11232, 16, 10752, 11400),
    ('plate', 20000, 19, 256, 64, 4, 128, 32, 36512, 256, 10752, 11392),
    ('bars-grey', 55328, 19, 256, 64, 4, 128, 32, 71840, 256, 10880, 11400),
    ('bars-green', 55328, 19, 256, 64, 4, 128, 32, 72992, 256, 10880, 11404),
    ('bars-red', 55328, 19, 256, 64, 4, 128, 32, 74144, 256, 10880, 11408),
    ('bars-blue', 55328, 19, 256, 64, 4, 128, 32, 77600, 256, 10880, 11420),
]


def entry5(path):
    iso = pycdlib.PyCdlib()
    iso.open(str(path))
    try:
        with iso.open_file_from_iso(iso_path='/DATA/PZS3US1.AFS;1') as stream:
            magic, count = struct.unpack('<4sI', stream.read(8))
            if magic != b'AFS\x00' or count <= 5:
                raise ValueError('Invalid AFS1 directory')
            stream.seek(8 + 5 * 8)
            offset, size = struct.unpack('<II', stream.read(8))
            if size != 701856:
                raise ValueError('Unsupported entry-5 size; offsets require this disc layout')
            stream.seek(offset)
            blob = stream.read(size)
            if len(blob) != size:
                raise ValueError('Truncated AFS entry')
            return blob
    finally:
        iso.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iso', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expected-entry-sha256', default=ENTRY_SHA256,
                        help='Require known entry hash for this layout (default: verified entry)')
    parser.add_argument('--verify-captures', action='store_true', help='Developer capture regression')
    args = parser.parse_args()
    blob = entry5(args.iso)
    digest = hashlib.sha256(blob).hexdigest()
    if args.expected_entry_sha256 and digest.lower() != args.expected_entry_sha256.lower():
        raise ValueError('Entry hash mismatch: unsupported asset layout')
    args.output.mkdir(parents=True, exist_ok=True)
    report = {'schema_version': 1, 'source': str(args.iso.resolve()), 'afs': 'PZS3US1.AFS',
              'entry': 5, 'entry_bytes': len(blob), 'entry_sha256': digest,
              'layout_support': 'Power Scale observed layout; other discs unverified', 'assets': []}
    # Preserve all observed slices, including overlays whose sampled geometry
    # has not been correlated yet. Do not assign speculative texture names.
    for dbp, off, size, uw, uh, verified in json.loads((TRIAL / 'hud-entry5-map.json').read_text()):
        if not verified or off < 0 or off + size > len(blob) or size != uw * uh * 4:
            raise ValueError('Invalid provenance slice')
        (args.output / f'entry5-{off:06x}-dbp{dbp}.ct32').write_bytes(blob[off:off + size])
    captures = []
    if args.verify_captures:
        upload_dir = TRIAL / 'log-archive/hud-upload-capture-vanilla-1v1'
        verified_uploads = 0
        for row in map(json.loads, (upload_dir / 'uploads.jsonl').read_text().splitlines()):
            source = row['ee_source']
            if source is None or not 0x17bce00 <= source < 0x17bce00 + len(blob):
                continue
            off = source - 0x17bce00
            saved = (upload_dir / row['file']).read_bytes()
            if saved != blob[off:off + len(saved)]:
                raise ValueError('Upload/disc provenance regression')
            verified_uploads += 1
        if verified_uploads != 29:
            raise ValueError('Expected 29 verified upload slices')
        report['verified_upload_slices'] = verified_uploads
        folders = [TRIAL / 'log-archive/hud-native-capture-1v1-vanilla']
        folders += list((TRIAL / 'log-archive/hud-native-capture-clock8-clock2-success').glob('capture-*'))
        for folder in folders:
            for row in map(json.loads, (folder / 'textures.jsonl').read_text().splitlines()):
                captures.append((folder, row))
    sheet = Image.new('RGB', (600, 4 * 180), '#252536')
    draw = ImageDraw.Draw(sheet)
    for n, (name, off, psm, w, h, bw, uw, uh, paloff, count, tbp, clut) in enumerate(ASSETS):
        raw = blob[off:off + uw * uh * 4]
        binary = args.output / (name + '.ct32')
        binary.write_bytes(raw)
        indices_path = args.output / (name + '.indices')
        subprocess.run([str(TRIAL / 'codex_decode_disc_indices.exe'), str(binary), str(indices_path),
                        *map(str, (psm, w, h, bw, uw, uh))], check=True)
        indices = indices_path.read_bytes()
        if len(indices) != w * h:
            raise ValueError('Unexpected decoder length')
        palette = blob[paloff:paloff + count * 4]
        (args.output / (name + '.palette')).write_bytes(palette)
        colours = []
        for i in indices:
            # P4 CSA=0 uses first 16 entries: an 8x2 palette remains direct;
            # a full 16x16 CLUT uses the CSM1 bit-3/4 swap, including P4.
            e = i if count == 16 else (i & 0xe7) | ((i & 8) << 1) | ((i & 16) >> 1)
            r, g, b, a = palette[4 * e:4 * e + 4]
            colours.append((r, g, b, min(255, a * 255 // 128)))
        image = Image.new('RGBA', (w, h))
        image.putdata(colours)
        image.save(args.output / (name + '.png'))
        results = []
        for folder, row in captures:
            if (row['tbp'], row['psm'], row['width'], row['height'], row['clut'], row['csa']) != (tbp, psm, w, h, clut, 0):
                continue
            with Image.open(folder / row['file']) as captured:
                reference = captured.convert('RGBA').tobytes()
            actual = image.tobytes()
            results.append({'capture': str(folder / row['file']), 'exact_rgba': reference == actual,
                            'different_bytes': sum(a != b for a, b in zip(actual, reference))})
        report['assets'].append({'name': name, 'psm': psm, 'width': w, 'height': h, 'tbw': bw,
                                'pixels_offset': off, 'palette_offset': paloff, 'palette_entries': count,
                                'transfer_width': uw, 'transfer_height': uh,
                                'pixels_sha256': hashlib.sha256(raw).hexdigest(),
                                'capture_comparisons': results})
        x, y = (n % 2) * 300 + 12, (n // 2) * 180 + 24
        draw.text((x, y - 17), name, fill='white')
        sheet.paste(image, (x, y), image)
        print(name, 'capture exact:', [r['exact_rgba'] for r in results])
    sheet.save(args.output / 'contact-sheet.png')
    (args.output / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print('entry sha256:', digest)
    if args.verify_captures and any(not a['capture_comparisons'] or
                                  not all(r['exact_rgba'] for r in a['capture_comparisons'])
                                  for a in report['assets']):
        raise ValueError('Missing or mismatching capture regression; inspect manifest')


if __name__ == '__main__':
    main()
