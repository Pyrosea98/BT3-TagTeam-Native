"""Bounded, read-only beam telemetry; no input, pause, or guest writes."""
import json
import struct
import time

import beam_struggle as struggle
import fresh_team_combat as core
from pine import PineError


def classify(value, actor):
    """Mirror gate order against a read-only sample, not an executed receipt."""
    def result(reason, side=None, **details):
        return dict(sample_gate=reason, assist_side=side, **details)
    if not actor['cpu']: return result('human')
    if not value['assist']: return result('assist-disabled')
    if not value['cpu']: return result('cpu-assist-disabled')
    if value['phase'] != 2: return result('coordinator-not-push-phase')
    physical, address = actor['physical'], actor['address']
    if address in value['participants']: return result('eligible-struggler')
    if any(slot['actor'] == address for slot in value['slots']):
        return result('eligible-pending-or-releasing')
    present, consumed = value['participation']
    if not ((present & ~consumed) >> physical) & 1:
        return result('eligible-not-participating')
    if actor['hp'] is None: return result('eligible-invalid-hp-row')
    if actor['hp'] <= 0: return result('eligible-dead')
    busy = lambda action: any(first <= action < first+length for first, length in struggle.BUSY_ACTIONS)
    if any(busy(action) for action in actor['actions'][1:]):
        return result('eligible-busy-requested-or-queued')
    enemy = lambda other: physical != other and (value['ffa'] or physical % 2 != other % 2)
    sides = [side for side, index in enumerate(value['participant_indices']) if not enemy(index)]
    if len(sides) != 1: return result('eligible-no-unique-allied-side')
    side = sides[0]
    if all(slot['actor'] for slot in value['slots'][side*4:side*4+4]):
        return result('eligible-slot-full', side)
    ally = next((item for item in value['actors'] if item['address'] == value['participants'][side]), None)
    if not actor.get('model_valid') or not ally or not ally.get('model_valid'):
        return result('eligible-invalid-model', side)
    x, y = actor.get('model_position'), ally.get('model_position')
    if x is None or y is None: return result('eligible-invalid-position', side)
    distance2 = (x[0]-y[0])**2+(x[2]-y[2])**2
    if not distance2 < value['range2']:
        return result('eligible-out-of-range', side, distance2=distance2, range2=value['range2'])
    if busy(actor['actions'][0]): return result('eligible-busy-current', side)
    if not actor['schedule_due']: return result('schedule-not-due', side)
    margin = value['side_word']
    if (side == 0 and margin > 0) or (side == 1 and margin < 0):
        return result('lead-rule', side)
    if actor['stock'] < struggle.STOCK: return result('insufficient-stock', side)
    if not 304 <= ally['actions'][0] <= 306:
        return result('register-ally-not-in-struggle-action', side)
    return result('ready-at-sample', side)


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
                  participant_indices=[bw(80), bw(84)],
                  side_word_meaning='guest tug margin: positive favours side0; negative favours side1; zero tied',
                  counters={name: word(off) for name, off in struggle.TELEMETRY.items()})
    # Read gate inputs only during an observed struggle. These are samples,
    # not a claim that ELIGIBLE accepted/rejected that actor on this frame.
    if values['active'] == 2:
        policy = struct.unpack('<4I', p.read(struggle.policy.CONTROL, 16))
        values['ffa'] = policy[0] == struggle.policy.MAGIC and policy[1] == manager and policy[3] == struggle.policy.FFA
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
                               hp=aw(0x9E4+164*row) if row < 5 else None,
                               stock=aw(0x9E4+164*row+20) if row < 5 else None,
                               schedule_due=(values['counter']-values['intro']-8-2*physical) >= 0
                               and (values['counter']-values['intro']-8-2*physical) % 32 == 0)
            model_id = aw(12)
            if model_id < 12:
                model = p.read_u32(core.MODELS+4*model_id)
                if 0x100000 <= model <= 0x8000000-0x1670:
                    header = struct.unpack('<5I', p.read(model, 20))
                    item['model_valid'] = header[1] == 1 and header[4] == model_id
                    coords = struct.unpack('<3f', p.read(model+2416, 12))
                    if all(abs(coord) < 1e8 for coord in coords):
                        item['model_position'] = coords
            actors.append(item)
        values['actors'] = actors
        values['human_struggle_sides'] = [side for side, at in enumerate(values['participants'])
                                         if any(actor['address'] == at and not actor['cpu'] for actor in actors)]
        for actor in actors:
            actor.update(classify(values, actor))
        values['sample_semantics'] = 'Read-only gate evaluation; not a guest execution receipt'
        values['counter_after_read'] = p.read_u32(manager+80)
        if p.read_u32(struggle.beam.CONTROL+24) != values['serial']:
            return None
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
