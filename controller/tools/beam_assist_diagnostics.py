"""Bounded, read-only beam telemetry; no input, pause, or guest writes."""
import json
import struct
import time

import beam_struggle as struggle
import fresh_team_combat as core
from pine import PineError


def snapshot(p):
    data = p.read(struggle.CONTROL, struggle.SLOTS+8*struggle.SLOT_STRIDE)
    word = lambda off: struct.unpack_from('<I', data, off)[0]
    if word(0) != struggle.MAGIC or word(0x10) != struggle.VERSION:
        return None
    manager, count = word(4), word(8)
    if not 0x100000 <= manager <= 0x8000000-632 or not 2 <= count <= 10:
        return None
    if p.read_u32(core.ACTORS) != manager:
        return None
    beam = p.read(struggle.beam.CONTROL, 96)
    bw = lambda off: struct.unpack_from('<I', beam, off)[0]
    if (bw(0), bw(4), bw(8)) != (struggle.beam.MAGIC, manager, count):
        return None
    values = dict(manager=manager, count=count, serial=bw(24), age=bw(20), active=bw(16),
                  assist=word(struggle.C['assist']), cpu=word(struggle.C['assist_cpu']),
                  range2=struct.unpack_from('<f', data, struggle.C['range2'])[0],
                  counter=p.read_u32(manager+80), intro=word(struggle.C['intro']),
                  phase=p.read_u32(manager+64),
                  side_word=struct.unpack('<i', p.read(manager+88, 4))[0],
                  participants=[bw(64), bw(68)],
                  counters={name: word(off) for name, off in struggle.TELEMETRY.items()})
    # Read gate inputs only during an observed struggle. These are samples,
    # not a claim that ELIGIBLE accepted/rejected that actor on this frame.
    if values['active'] == 2:
        values['participation'] = [p.read_u32(struggle.participation.CONTROL+12),
                                   p.read_u32(struggle.participation.CONTROL+16)]
        values['slots'] = [{name: word(struggle.SLOTS+i*struggle.SLOT_STRIDE+off)
                            for name, off in struggle.S.items() if name in ('actor','state','fail','phys')}
                           for i in range(8)]
        actors = []
        pointers = struct.unpack('<'+'I'*count, p.read(core.POINTERS, count*4))
        for physical, at in enumerate(pointers):
            if not 0x100000 <= at <= 0x8000000-0x1600:
                continue
            actor = p.read(at, 0x1600)
            aw = lambda off: struct.unpack_from('<I', actor, off)[0]
            row = aw(0x994)
            item = dict(physical=physical, address=at, cpu=aw(0x1278),
                               actions=[aw(off) for off in struggle.throws.ACTION_FIELDS],
                               stock=aw(0x9E4+164*row+20) if row < 5 else None,
                               schedule_due=(values['counter']-values['intro']-8-2*physical) >= 0
                               and (values['counter']-values['intro']-8-2*physical) % 32 == 0)
            model_id = aw(12)
            if model_id < 12:
                model = p.read_u32(core.MODELS+4*model_id)
                if 0x100000 <= model <= 0x8000000-0x1670:
                    coords = struct.unpack('<3f', p.read(model+2416, 12))
                    if all(abs(coord) < 1e8 for coord in coords):
                        item['model_position'] = coords
            actors.append(item)
        values['actors'] = actors
    if p.read_u32(core.ACTORS) != manager:
        return None
    return values


class Recorder:
    def __init__(self):
        self.next_sample = 0.
        self.last = None
        self.active = False
        self.failed = False

    def emit(self, log, event, value):
        log('Beam assist '+event+': '+json.dumps(value, separators=(',', ':'), allow_nan=False))

    def finish(self, log):
        if self.last is not None:
            self.emit(log, 'match ended (last observed counters)', self.last)
        self.last = None
        self.active = False
        self.failed = False
        self.next_sample = 0.

    def tick(self, p, log, clock=time.monotonic):
        now = clock()
        if now < self.next_sample:
            return
        self.next_sample = now+.5
        try:
            value = snapshot(p)
            if value is None:
                if self.last is not None:
                    self.finish(log)
                return
            previous = self.last
            running = value['active'] == 2
            if previous is not None and (previous['manager'], previous['count']) != (value['manager'], value['count']):
                self.finish(log)
                previous = None
            if self.active and (not running or previous['serial'] != value['serial']):
                self.emit(log, 'struggle ended', previous if running else value)
            if running and (not self.active or previous['serial'] != value['serial']):
                self.emit(log, 'struggle started', value)
            elif running:
                # At most two lines/s, enough to see stock/actions/schedule
                # even when all guest request counters stay at zero.
                self.emit(log, 'sample', value)
            elif previous and not self.active and value['counters'] != previous['counters']:
                self.emit(log, 'counters changed between samples', value)
            self.active, self.last = running, value
        except (OSError, PineError, ValueError, struct.error) as error:
            if not self.failed:
                log(f'Beam assist diagnostic unavailable: {error}')
                self.failed = True
