"""Check configured ranges reach the guest in map-scaled world units."""
from pathlib import Path
import struct
import sys

sandbox=Path(sys.argv[1]).resolve()
sys.path[:0]=[str(sandbox),str(sandbox/'power-scale-trial/controller/game/tools')]
from codex_roster_overlay import install
install()
import mod_settings as settings
import world_ranges
import beam_struggle as beam

assert settings.DEFAULTS['beam_assist_range']==300
consts=beam.disc_constants(beam.native())
for expanded,scale in ((False,1),(True,2)):
    for distance in (30,300,1500):
        values=settings.validate_settings(dict(expanded_maps=expanded,beam_assist_range=distance))
        config=beam.config_bytes(values,consts,beam.groups(values))
        assert struct.unpack_from('<f',config,0x30)[0]==(distance*scale)**2
    values=settings.validate_settings(dict(expanded_maps=expanded,revive_radius=200))
    assert world_ranges.effective(values,'revive_radius')==200*scale
    for lang in ('en','es'):
        values['language']=lang
        for group,reach in (('Beam struggles',300*scale),('Revival',200*scale)):
            note=settings.help_note(group,values)
            assert str(reach) in note[:100],(group,lang,note)
# Recorded closest-to-enemy failures at 244..265 now fit even the old chosen
# base range 150 on a 2x map; the new default also admits ordinary 448-distance
# samples. Very distant 1385 remains outside 600, but is configurable to 3000.
assert 265 < world_ranges.effective(dict(expanded_maps=True,beam_assist_range=150),'beam_assist_range')
assert 448 < world_ranges.effective(dict(expanded_maps=True,beam_assist_range=300),'beam_assist_range')
assert 1468 < world_ranges.effective(dict(expanded_maps=True,beam_assist_range=1500),'beam_assist_range')
print('PASS: guest range squared at 1x/2x, default/cap, revival limits and visible EN/ES effective-range help')
