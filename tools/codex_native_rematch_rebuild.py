"""Experimental clean native lifecycle, coordinated at the runner's boundary.

No state loads: restore owned code and match reservations after native teardown, then
let native setup and the existing fresh-preparation pipeline rebuild the actors.
"""
import json
from pathlib import Path
import struct
import time

CONTROL, MAGIC = 0x07FFF100, 0x4E524D31
PARENTS = (0x2FEB14, 0x2FEC44, 0x2FEAA8, 0x2FEB38, 0x2FF208)
LOW_RESERVATIONS = ((0xC4000, 0xC4040), (0xD1000, 0xD1100),
                    (0xD8000, 0xD8100), (0xDA000, 0xDD000), (0xE8000, 0xE8C00))
CAVE_START, CAVE_END = 0x06000000, 0x07FFF000
# fresh_team_trainer selects split-screen for TwoPlayer; four_player_mode
# also sets this word to 1. It is scene layout, not an actor/heap pointer.
SCENE_LAYOUT = 0x331DC8 + 36
# The runner clears 02000000..06000000 locally after this host handoff.
# Relocation/rematch mailboxes are at/above CAVE_END. Restore staging packets:
# their old/new
# bytes contain obsolete pointers even after a transaction was acknowledged.
# These are the only live services inside the match cave/staging region.
CAVE_LIVE = ((0x06930000, 0x06934000, 'controller assignment service'),
             (0x06A00000, 0x06B00000, 'loading cover double buffers'),
             # Quad controller code/control/pads at 06C10000..06C20000
             # belong to the match. Keeping them preserved the old owner
             # after quad view/actor caves were reset, rejecting match two.
             (0x06C30000, 0x06C40000, 'quad menu input service'),
             (0x07470000, 0x0747A000, 'loading cover code/control/emitters'),
             (0x0768F000, 0x0768F100, 'preparation service control'),
             (0x076FF000, 0x07700000, 'native mode/menu loading control'))


def cave_ranges():
    start = CAVE_START
    for lo, hi, _ in CAVE_LIVE:
        if start < lo:
            yield start, lo
        start = hi
    if start < CAVE_END:
        yield start, CAVE_END


def cave_restore_plan(p, baseline):
    current = p.read(CAVE_START, CAVE_END-CAVE_START)
    writes, changes = [], []
    for lo, hi in cave_ranges():
        for at in range(lo, hi, 0x10000):
            end = min(at+0x10000, hi)
            before = current[at-CAVE_START:end-CAVE_START]
            after = baseline[at:end]
            if before != after:
                changed = sum(a != b for a,b in zip(before, after))
                writes.append((at, after))
                changes.append({'address':at, 'length':end-at, 'changed_bytes':changed})
    return writes, {'changed_bytes':sum(row['changed_bytes'] for row in changes),
                    'written_bytes':sum(len(data) for _,data in writes),
                    'verified_bytes':sum(hi-lo for lo,hi in cave_ranges()),
                    'restored_chunks':changes,
                    'preserved':[{'start':lo,'end':hi,'service':why} for lo,hi,why in CAVE_LIVE]}


def verify_caves(p, baseline):
    current = p.read(CAVE_START, CAVE_END-CAVE_START)
    for lo, hi in cave_ranges():
        if current[lo-CAVE_START:hi-CAVE_START] != baseline[lo:hi]:
            raise RuntimeError(f'Match cave cleanup left runtime state at {lo:08X}..{hi:08X}')


def packet_arena_restore(p, baseline, prepared):
    import packet_pool_grow as packets
    u = lambda ram, at: struct.unpack_from('<I', ram, at)[0]
    native = [u(baseline, packets.BASES+i*4) for i in range(5)]
    expanded = [u(prepared, packets.BASES+i*4) for i in range(5)]
    if u(prepared, packets.CONTROL) != 5 or u(prepared, packets.CONTROL+8) != 2:
        raise ValueError('Prepared graphics arenas lack a completed growth receipt')
    if native != [u(prepared, packets.CONTROL+i) for i in (32,36,40,44,48)]:
        raise ValueError('Graphics growth receipt does not own the original arenas')
    if expanded[:2] != [u(prepared, packets.CONTROL+i) for i in (24,28)]:
        raise ValueError('Graphics growth receipt does not own the expanded arenas')
    current = list(struct.unpack('<7I', p.read(packets.BASES, 28)))
    if current[:5] not in (native, expanded) or current[5] not in (0,1):
        raise ValueError('Graphics arena descriptors changed outside preparation')
    if not current[current[5]] <= current[6] <= current[2+current[5]]:
        raise ValueError('Graphics cursor is outside its owned arena')
    for i in range(2):
        base, end = native[i], native[i+2]
        if not 0x100000 <= base < end <= 0x2000000 or end-base != native[4]:
            raise ValueError('Original graphics arena is not in the native heap')
        # Allocator alignment can leave padding between the SHBT header and
        # the returned arena. Verify the retained allocation, not just a pointer.
        retained = False
        for header in range(base-128, base-31, 4):
            data = p.read(header, 32)
            magic, used, _, _, _, payload, size, _ = struct.unpack('<8I', data)
            if (magic == 0x53484254 and used == 1 and
                    header+32 <= payload <= base and end <= payload+size):
                retained = True
                break
        if not retained:
            raise ValueError(f'Original graphics allocation is no longer retained: {base:08X}')
    index = current[5]
    # No packet construction is active at this detached main-thread boundary.
    # Start at the retained native buffer's base, rather than restoring a saved
    # cursor into a packet assembled during the original match.
    restored = native + [index, native[index]]
    return packets.BASES, struct.pack('<7I', *restored), {'before':current,'after':restored}


def ownership_plan(source, *, strict=True, unclassified=None):
    from elftools.elf.elffile import ELFFile
    from native_map import elf_path
    from prototype import ROOT
    source = Path(source)
    baseline_path = next(source.parent.glob('*original-selected-match.bin'))
    baseline, prepared = baseline_path.read_bytes(), source.read_bytes()
    if len(baseline) != 0x8000000 or len(prepared) != len(baseline):
        raise ValueError('Cleanup requires this match\'s complete original and prepared RAM')
    if any(memoryview(baseline)[0x02000000:0x06000000]):
        raise ValueError('Original match baseline does not have an unused expanded heap')
    with Path(elf_path(ROOT)).open('rb') as stream:
        segments = [(int(s['p_vaddr']), int(s['p_vaddr'])+int(s['p_memsz']))
                    for s in ELFFile(stream).iter_segments() if int(s['p_flags']) & 1]
    spans = []
    for path in source.parent.glob('*.json'):
        for block in json.loads(path.read_text()).get('blocks', []):
            at, data = block.get('address'), block.get('data_hex')
            if not isinstance(at, int) or not isinstance(data, str):
                continue
            end = at + len(bytes.fromhex(data))
            code = 0x100000 <= at < end <= 0x2C0000 and any(a <= at < end <= b for a,b in segments)
            owned = any(a <= at < end <= b for a,b in LOW_RESERVATIONS) or CAVE_START <= at < end <= CAVE_END
            layout = (at == SCENE_LAYOUT and end == at+4 and
                      struct.unpack_from('<I', baseline, at)[0] in (0, 1) and
                      struct.unpack_from('<I', prepared, at)[0] in (0, 1) and
                      struct.unpack('<I', bytes.fromhex(data))[0] in (0, 1))
            if code or owned or layout:
                spans.append((at, end, code))
            elif at < 0x400000:
                if strict:
                    raise ValueError(f'Unclassified low-memory preparation write {at:08X}..{end:08X}')
                if unclassified is not None:
                    unclassified.append({'address':at,'end':end,'manifest':path.name,
                                         'baseline_hex':baseline[at:min(end,at+32)].hex(),
                                         'prepared_hex':prepared[at:min(end,at+32)].hex()})
    merged = []
    for at, end, code in sorted(set(spans)):
        if merged and at <= merged[-1][1] and code == merged[-1][2]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]), code)
        else:
            merged.append((at, end, code))
    if not merged:
        raise ValueError('No registered preparation ownership ranges')
    return baseline, prepared, merged


def record_unclassified(p, source, rows, obs):
    """Retain evidence without loading a checkpoint or writing guest memory."""
    for row in rows:
        row['observed_hex'] = p.read(row['address'], min(32,row['end']-row['address'])).hex()
    receipt = {'status':'match continues; clean rematch not armed',
               'checkpoint':Path(source).name, 'unclassified':rows,
               'manager':obs.manager, 'loop':obs.loop, 'team_mode':obs.team_mode}
    (Path(source).parent/'native-rematch-unclassified.json').write_text(
        json.dumps(receipt,indent=2)+'\n',encoding='utf-8')


def restore_detached(p, source, plan, hook_receipt=None):
    import native_preparation as native
    baseline, prepared, spans = plan
    if p.read_u32(CONTROL) != MAGIC or p.read_u32(CONTROL+4) != 2:
        raise ValueError('Runner has not acknowledged native teardown')
    if any(p.read_u32(at) for at in PARENTS):
        raise ValueError('Native battle owners remain attached')
    # Validate every code range before the first write. Never restore old actor
    # pointers or records into freed native heap allocations.
    for at, end, code in spans:
        if code:
            from codex_reload_hook_receipt import accepted_span
            if not accepted_span(p,source,baseline,prepared,at,end,p.read(at,end-at),hook_receipt):
                raise ValueError(f'Owned hook changed outside this preparation: {at:08X}')
    arena_at, arena_data, arena_receipt = packet_arena_restore(p, baseline, prepared)
    cave_writes, cave_receipt = cave_restore_plan(p, baseline)
    receipt = {'status': 'native owners detached', 'ranges': len(spans),
               'restored_bytes': sum(end-at for at,end,_ in spans), 'source': str(source),
               'graphics_arenas': arena_receipt, 'match_caves':cave_receipt}
    p.write(arena_at, arena_data)
    if p.read(arena_at, len(arena_data)) != arena_data:
        raise RuntimeError('Native graphics arena restore readback failed')
    for at, end, _ in spans:
        if CAVE_START <= at < end <= CAVE_END:
            continue  # full reservation restoration also includes runtime counters
        p.write(at, baseline[at:end])
        if p.read(at, end-at) != baseline[at:end]:
            raise RuntimeError(f'Cleanup readback failed at {at:08X}')
    for at, data in cave_writes:
        p.write(at, data)
    verify_caves(p, baseline)
    receipt['match_caves']['verified_against_baseline'] = True
    # Remove only the extra-slot registrations; native teardown already freed
    # their pool storage. No stale model record is freed a second time.
    p.write(0x31C640+8, bytes(10*4))
    include_single = p.read_u32(native.CONTROL+60)
    control = [native.MAGIC] + [0]*15
    control[12], control[15] = 1, include_single
    p.write(native.CONTROL, struct.pack('<16I', *control))
    destination = Path(source).parent/'native-rematch-rebuild.json'
    destination.write_text(json.dumps(receipt, indent=2)+'\n')
    p.write_u32(CONTROL+4, 3)


def install(autopilot, pine):
    import native_preparation as native
    encode = native.encode
    def reserved_encode(manifest):
        packet, count = encode(manifest)
        # Relocation and rematch mailboxes occupy the staging area's tail.
        if len(packet) > 0x07FFF000 - native.PACKET:
            raise ValueError('Preparation packet overlaps the native lifecycle mailboxes')
        return packet, count
    native.encode = reserved_encode
    def no_state_restore(self, *args, **kwargs):
        raise RuntimeError('Native rematch boundary was missed; checkpoint restoration is disabled')
    autopilot.Autopilot.load_file = no_state_restore
    report = autopilot.Autopilot.report
    def native_report(self, message, *args, **kwargs):
        if message.startswith('Simultaneous match ready. Rematch checkpoint:'):
            message = 'Simultaneous match ready. Native clean rematch trial enabled.'
        return report(self, message, *args, **kwargs)
    autopilot.Autopilot.report = native_report
    original = autopilot.Autopilot.observe
    def observe(self):
        read_only = True
        try:
            with pine.PineClient(timeout=15) as p:
                if p.read_u32(CONTROL) == MAGIC:
                    state = p.read_u32(CONTROL+4)
                    if state == 6:
                        for name in ('reload_worker', 'body_worker', 'fusion_worker'):
                            worker = getattr(self, name, None)
                            if worker is not None and (getattr(worker, 'busy', False) or
                                    getattr(worker, 'form_job', None) is not None):
                                raise ValueError(f'{name} still owns an actor at rematch boundary')
                        # Input services may own their own PINE connection.
                        # Release this one before joining/closing those services.
                        p.close()
                        read_only = False
                        self.reset_reload_worker()
                        self.state = 'NATIVE_REBUILD'
                        self.connection_error = 'Native rematch: rebuilding the selected teams.'
                        with pine.PineClient(timeout=15) as acknowledge:
                            if acknowledge.read_u32(CONTROL+4) != 6:
                                raise ValueError('Native lifecycle lease handoff changed')
                            acknowledge.write_u32(CONTROL+4, 7)
                        autopilot.log('Native rematch: worker leases retired; beginning full teardown')
                        return None
                    elif state == 2:
                        read_only = False
                        restore_detached(p, self.playable, self.native_cleanup_plan,
                                         getattr(self,'native_reload_hook_receipt',None))
                        autopilot.log('Native rematch: owned hooks/reservations restored; loading fresh match')
                        return None
                    elif state == 4:
                        if p.read_u32(CONTROL+8) == 1:
                            flags = struct.unpack('<2I', p.read(0x333700, 8))
                            if flags != (0, 0):
                                raise ValueError(f'Native setup retained post-match destination flags: {flags}')
                            baseline = self.native_cleanup_plan[0]
                            for side in range(2):
                                row = 0x331DC8+624*side
                                count = struct.unpack_from('<I', baseline, row+192)[0]
                                if not 1 <= count <= 5 or p.read_u32(row+192) != count:
                                    raise ValueError('Native reload changed the selected team sizes')
                                for slot in range(count):
                                    at = row+196+100*slot
                                    if p.read(at, 4) != baseline[at:at+4]:
                                        raise ValueError('Native reload changed the selected roster')
                            autopilot.log('Native rematch: selected roster retained; result/return flags cleared')
                        read_only = False
                        self.state = 'MENU'
                        self.handled.clear(); self.noted.clear()
                        self.current_key = None; self.heartbeat = None
                        self.freeze_dumped = False; self.hold_overruns = None
                        self.playable = None
                        self.native_reload_hook_receipt = None
                        p.write_u32(CONTROL+4, 0)
                        autopilot.log('Native rematch: native reload complete; preparing selected simultaneous teams again')
                    elif state == 5:
                        raise RuntimeError(f'Native rebuild stopped: boundary error {p.read_u32(CONTROL+20)}')
                    elif state in (7, 3, 8, 9):
                        return None
            obs = original(self)
            if (obs is not None and self.state == 'ACTIVE' and obs.loop == 1 and obs.team_mode == 0
                    and autopilot.menu_return.return_destination(obs.result_flags, obs.return_flags) is None):
                raise RuntimeError('Native lifecycle interception was missed; refusing an ordinary tag rematch')
            with pine.PineClient(timeout=15) as p:
                if obs is not None and self.state == 'ACTIVE' and self.playable and obs.team_mode == 1:
                    if (getattr(self, 'native_armed_source', None) != self.playable and
                            getattr(self, 'native_unclassified_source', None) != self.playable):
                        unclassified = []
                        plan = ownership_plan(self.playable, strict=False, unclassified=unclassified)
                        if unclassified:
                            # A diagnostic gap must not kill a successfully prepared
                            # match. Do not arm a partial cleanup plan or restore any
                            # unknown state. Offline audits retain the strict gate.
                            self.native_unclassified_source = self.playable
                            summary = ', '.join(f"{row['address']:08X}..{row['end']:08X}" for row in unclassified)
                            autopilot.log('WARNING: Unclassified preparation writes '+summary+
                                          '; current match continues, clean rematch not armed.')
                            try:
                                record_unclassified(p,self.playable,unclassified,obs)
                            except Exception as capture_error:
                                autopilot.log('WARNING: Rematch classification capture unavailable: '+
                                              type(capture_error).__name__)
                            return obs
                        if p.read(CONTROL, 32) not in (bytes(32), struct.pack('<8I', MAGIC,0,0,0,0,0,0,0)):
                            # Previous receipts may retain manager/reason fields;
                            # they are ours only when magic and inert state match.
                            if p.read_u32(CONTROL) != MAGIC or p.read_u32(CONTROL+4) != 0:
                                raise ValueError('Rematch control reservation is not free')
                        read_only = False
                        self.native_cleanup_plan = plan
                        self.native_armed_source = self.playable
                        p.write(CONTROL, struct.pack('<8I', MAGIC,0,0,obs.manager,0,0,0,0))
                        p.write_u32(CONTROL+4, 1)  # publish last
                        autopilot.log('Native clean rematch armed for this prepared roster')
                return obs
        except Exception as error:
            # A process exit between require_alive and a PINE read is normal
            # shutdown. Preserve that lifetime exception instead of wrapping it
            # as a failed rematch or attempting another write to a dead runner.
            from runtime_owner import EmulatorClosed
            if isinstance(error,EmulatorClosed):raise
            pine.require_runtime()
            if isinstance(error, TimeoutError) and read_only:
                # A queued read-only poll can time out behind a diagnostic client.
                # Its socket has closed; retry with a fresh observation next tick.
                # Never retry an uncertain write/cleanup or retire a live lease.
                pine.require_runtime()
                now = time.monotonic()
                count = getattr(self, 'native_bridge_timeouts', 0) + 1
                self.native_bridge_timeouts = count
                if count == 1 or now-getattr(self, 'native_bridge_timeout_log', 0) >= 15:
                    autopilot.log(f'Native bridge busy: read-only poll timed out; retrying (timeouts={count})')
                    self.native_bridge_timeout_log = now
                self.connection_error = 'Native bridge busy; waiting to observe the game again.'
                return None
            try:
                with pine.PineClient(timeout=5) as p:
                    if p.read_u32(CONTROL) == MAGIC:
                        p.write_u32(CONTROL+4, 5)
            except Exception:
                pass
            raise RuntimeError(f'Native clean rematch cannot continue: {error}') from error
    autopilot.Autopilot.observe = observe
