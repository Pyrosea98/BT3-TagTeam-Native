"""Check emitted prompt programs, fallback ABI and presentation allocations."""
import struct
import sys

sys.path.insert(0, sys.argv[1])
import beam_struggle as beam
import lockon_select as select
import lockon_threat as threat
import battle_mode_policy as policy

stub = struct.pack('<4I', 0x24020000, 0x03E00008, 0, 0)
for capacity in (3, 5):
    with policy.building_for(capacity):
        parts = (
            beam.programs(beam.disc_constants(beam.native()), beam.beam.contact_code()[:8]),
            select.code_parts(), threat.code_parts(),
        )
        for module, programs in zip((beam, select, threat), parts):
            assert dict(programs)[module.NATIVE_PROBE] == stub
            spans = sorted((start, start+len(data)) for start, data in programs)
            assert all(end<=start for (_, end), (start, _) in zip(spans, spans[1:])), module.__name__
        draws = (beam.draw_code(), threat.draw_code(), select.marker_code())
        for module, code in zip((beam, threat, select), draws):
            assert struct.pack('<I', (3<<26)|(module.NATIVE_PROBE>>2)) in code
assert beam.NATIVE_ROWS+32*10 <= beam.CONTROL+beam.CONTROL_SIZE
assert select.NATIVE_ROWS+16*policy.ENGINE_ACTORS <= select.END
print('PASS: both capacities assemble, allocations do not overlap, fallback probes and guards agree')
