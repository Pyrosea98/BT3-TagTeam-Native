"""Engine-slot runtime labels and independently verified portrait assets."""
import json
from functools import lru_cache
from pathlib import Path

ASSETS=Path(__file__).resolve().parents[4]/'roster-assets'


@lru_cache(maxsize=1)
def character_table():
    try: rows=json.loads((ASSETS/'characters.json').read_text(encoding='utf-8'))['characters']
    except (OSError,ValueError,KeyError):return {}
    return {row['character_id']:row for row in rows if isinstance(row,dict) and isinstance(row.get('character_id'),int)}


def character_info(character_id):
    row=character_table().get(character_id,{})
    return dict(character_id=character_id,name=row.get('name',f'Fighter {character_id}'),
        base_name=row.get('base_name',f'Fighter {character_id}'),form=row.get('form',''),
        portrait_path=str(ASSETS/row['portrait']) if row.get('portrait') else None,
        bitmap_path=str(ASSETS/row['bitmap']) if row.get('bitmap') else None)


def character_name(character_id):return character_info(character_id)['name']
