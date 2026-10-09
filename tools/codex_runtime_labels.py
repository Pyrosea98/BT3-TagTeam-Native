"""Refresh engine-slot labels at select scenes using the controller's existing PINE client."""
import json
from pathlib import Path
from extract_loading_assets import english_label

HERE=Path(__file__).resolve().parent
SEEN=set()


def refresh(p, scene):
    if scene is None or scene.kind!='character_select':return
    key=(scene.manager,scene.object)
    if key in SEEN:return
    SEEN.add(key)
    cache=HERE/'roster-assets/runtime-names.json'
    previous=json.loads(cache.read_text(encoding='utf-8'))
    import game_profile
    if game_profile.installed()['iso_sha256']!=previous['iso_sha256']:return
    base=int(previous['base'],16)
    data=p.read(base,253*64)
    names=[]
    for index in range(253):
        slot=data[index*64:(index+1)*64]
        names.append(english_label(slot) if slot.startswith(b'\xff\xfe') else '')
    # A menu heap address is only a candidate. Never accept unrelated bytes.
    if names[:8]!=previous['names'][:8] or sum(bool(name) for name in names)<200:return
    path=HERE/'roster-assets/characters.json'
    manifest=json.loads(path.read_text(encoding='utf-8'))
    for row in manifest['characters']:
        cid=row['character_id']
        name=names[cid] if 0<=cid<len(names) else ''
        if name:
            row.update(name=name,base_name=name,form='')
    previous['names']=[name or old for name,old in zip(names,previous['names'])]
    from atomic_files import write_json
    write_json(cache,previous);write_json(path,manifest)
    import character_names
    character_names.character_table.cache_clear()
