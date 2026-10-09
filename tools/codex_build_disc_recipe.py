"""Build-time only: coordinate offsets/hashes, never game bytes, for native import."""
import hashlib,json,struct,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'power-scale-trial/controller'))
from iso_compatibility.map_scaling import plan_stage
ROOT=HERE/'installer'
ROOT.mkdir(exist_ok=True)
manifest=json.loads((HERE.parent/'experiments/.full-install/game/maps/expanded-2x.json').read_text(encoding='utf-8'))
source=Path(manifest['source']['path'])
patches=[];fields=bytearray()
with source.open('rb') as f:
    for patch in manifest['patches']:
        f.seek(patch['offset']);raw=f.read(patch['length'])
        assert hashlib.sha256(raw).hexdigest()==patch['before_sha256']
        plan=plan_stage(raw,2)
        assert hashlib.sha256(plan.preview()).hexdigest()==patch['after_sha256']
        begin=len(fields);last=0
        for offset in sorted(plan.fields):
            delta=offset-last;last=offset
            while delta>=128:fields.append((delta&127)|128);delta>>=7
            fields.append(delta)
        patches.append({key:patch[key] for key in ('offset','length','before_sha256','after_sha256')} | {'field_offset':begin,'field_bytes':len(fields)-begin,'field_count':len(plan.fields)})
recipe=dict(schema=1,scale=2,source_sha256=manifest['source_sha256'],output_sha256=manifest['output_sha256'],size=manifest['source']['size'],patches=patches)
(ROOT/'map-recipe.json').write_text(json.dumps(recipe,separators=(',',':')),encoding='utf-8')
(ROOT/'map-fields.bin').write_bytes(fields)
table=dict(schema=1,discs=[dict(sha256=recipe['source_sha256'],size=recipe['size'],title='Power Scale BETA 1.5.1',region='USA',adapter_id='power-scale-1.5.1',expanded=False),dict(sha256=recipe['output_sha256'],size=recipe['size'],title='Power Scale BETA 1.5.1 · Expanded 2x',region='USA',adapter_id='power-scale-1.5.1',expanded=True)])
(ROOT/'supported-discs.json').write_text(json.dumps(table,indent=2),encoding='utf-8')
print('Native map recipe:',len(patches),'resources;',sum(p['field_count'] for p in patches),'float fields;',len(fields),'field bytes')
