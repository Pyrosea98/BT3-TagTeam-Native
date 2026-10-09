"""Apply the reviewed Power Scale engine-slot portrait map to local assets.

Portrait files retain their ISO UI indices. Only manifest references change.
This map is specific to the captured disc; other discs need their own mapping.
"""
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAPTURED_ISO = 'f3e495b8eb2269c2808f00352058d0be6facf3db4bf1c013f2d78ea2a531c6d3'
CAPTURED_UI = '6d1cc40d2fb63c6a14ad261510a29067fb6618032defc227b8679695e9d9de24'


def apply(assets=HERE/'roster-assets', mapping=HERE/'power-scale-trial/portrait-slot-map.json'):
    manifest_path = assets/'characters.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    portrait_map = json.loads(mapping.read_text(encoding='utf-8'))
    ui = json.loads((assets/'ui-characters.json').read_text(encoding='utf-8'))
    if manifest.get('iso_sha256') != CAPTURED_ISO:
        raise ValueError('Portrait map belongs to the captured Power Scale disc only')
    if ui.get('source_sha256') != CAPTURED_UI:
        raise ValueError('Extracted UI assets do not match the captured portrait source')
    rows = manifest['characters']
    entries = portrait_map['map']
    expected = set(range(253))
    if (portrait_map.get('complete') is not True or
        set(entries) != {str(i) for i in expected} or
        len(rows) != 253 or {r['character_id'] for r in rows} != expected):
        raise ValueError('Requires complete engine slots and portrait mapping')
    indices = [entries[str(i)]['iso_index'] for i in range(253)]
    if any(type(i) is not int for i in indices) or set(indices) != expected:
        raise ValueError('Portrait map must be a permutation of all 253 ISO indices')
    ui_rows = {r['ui_index']: r for r in ui['ui_entries']}
    if len(ui_rows) != 253 or set(ui_rows) != expected:
        raise ValueError('Requires all 253 extracted ISO UI entries')
    # Validate every path before publishing any manifest changes.
    from PIL import Image
    for row in rows:
        item = entries[str(row['character_id'])]
        source = ui_rows[item['iso_index']]
        for field in ('portrait', 'bitmap'):
            relative = Path(source[field])
            target = (assets/relative).resolve()
            if relative.is_absolute() or assets.resolve() not in target.parents:
                raise ValueError('Portrait asset path escapes asset directory')
            with Image.open(target) as image:
                image.verify()
        row.update(portrait=source['portrait'], bitmap=source['bitmap'],
                   portrait_iso_index=item['iso_index'], portrait_source=item['source'])
    manifest['source'] = 'Captured runtime menu names by engine slot; reviewed runtime-slot portrait mapping'
    manifest['portrait_mapping'] = dict(iso_sha256=CAPTURED_ISO,
        method='Runtime portrait block order with documented name/elimination inference',
        iso_ui_sha256=ui['source_sha256'], engine_slots=253)
    temporary = manifest_path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    os.replace(temporary, manifest_path)
    return sum(i != indices[i] for i in range(253))


if __name__ == '__main__':
    print(f'Applied 253 engine-slot portraits; {apply()} non-identity mappings')
