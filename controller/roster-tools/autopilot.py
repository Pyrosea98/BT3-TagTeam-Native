"""Zero-configuration simultaneous teams: watch the emulator and prepare matches.

Run alongside PCSX2 (see launch-autopilot.ps1). The launcher prepares matches
only after a mode is selected in Modded Modes. Original-menu selections stay
native, including Team Battle. Character selection still uses the game's own
roster screens. Headless diagnostic callers without a menu retain auto-detection.

States: MENU (battle loop off), BATTLE (native 1v1 or a battle that was already
handled), PREPARING (trainer running), ACTIVE (prepared match), RECOVER.
After a prepared match, Fight Again reloads the playable checkpoint (the
native rematch cannot rebuild the extra fighters), and leaving to the menu
reloads the clean menu checkpoint captured at boot.
"""
from native_map import A, CRC, PAL, SERIAL, elf_path
import argparse
import json
import os
import shutil
import runtime_profile
import game_profile
import guest_loading_screen
guest_loading_screen.CHEAT = runtime_profile.CHEATS/game_profile.cheat_name(SERIAL)
import struct
import subprocess
import sys
import threading
import time
import traceback
from functools import lru_cache
from pathlib import Path
from atomic_files import write_json as atomic_json

from pine import PineClient, PineError
from fresh_team_trainer import Session, StreamingSession, PreparationBusyError, STATES, PREFIX, ROOT, ACK_ADDRESS
import native_preparation
import menu_return
import battle_mode_policy
from battle_mode_policy import ACTOR_COUNTS
from battle_mode_policy import TEAM_CAPACITY

SCENE, BATTLE_OBJECT, MANAGER, REPLAY = A(0x331DC8), A(0x2FEB38), A(0x2FEB14), A(0x31BE04)
LOOP_FLAG = SCENE+6648
MODE, HEAP1_START, HEAP1_END = 0xD8080, A(0x2FF084), A(0x2FF08C)
ACTOR_HOOK, NATIVE_PROLOGUE = A(0x1C2A28), bytes.fromhex('f0ffbd270000b0ff')
MENU_SLOT, RELOAD_SLOT = 219, 218
INPUT_HOLD = 0x07361850  # fresh_memory preparation hold word; 1 while the leaders are held idle
SUPPORTED_SIDES = tuple(range(1, TEAM_CAPACITY + 1))
# Freeze watchdog: the render observer counts every submitted graphics packet
# (capacity_stage CONTROL+16), including in-game pause menus and cutscenes. If
# it stops for this long while the emulator runs, the game's main loop is hung.
import capacity_stage
FRAME_HEARTBEAT = capacity_stage.CONTROL+16
FREEZE_SECONDS = 5.0
WINDOWS = os.name == 'nt'  # PowerShell key injection and the pycaw loading-audio helper


def supported_teams(rows, include_single=False):
    return len(rows) == 2 and all(n in SUPPORTED_SIDES for n in rows) and (include_single or max(rows) > 1)


def log(message):
    print(time.strftime('%H:%M:%S'), message, flush=True)


@lru_cache(maxsize=1)
def native_guards():
    from prototype import elf_reader
    from selected_team_capture import NATIVE_RANGES
    _, _, readelf = elf_reader(elf_path(ROOT))
    return [(address, readelf(address, size)) for address, size in
            (*NATIVE_RANGES, (ACTOR_HOOK, 8), (A(0x12BC8C), 8))]


def send_space():
    if not WINDOWS:
        # No portable key injection (Wayland has none) and PINE has no pause opcode: the
        # player presses PCSX2's pause key. The Linux launcher also runs with --manual-pause.
        log('Press the PCSX2 pause key (Space by default) in the game window to continue.')
        return False
    script = ("Add-Type -AssemblyName Microsoft.VisualBasic; Add-Type -AssemblyName System.Windows.Forms; "
              "$p = Get-Process -Name 'pcsx2-qt' -ErrorAction SilentlyContinue | Select-Object -First 1; "
              "if ($p) { [Microsoft.VisualBasic.Interaction]::AppActivate($p.Id); Start-Sleep -Milliseconds 300; "
              "[System.Windows.Forms.SendKeys]::SendWait(' ') }")
    subprocess.run(['powershell', '-NoProfile', '-Command', script], capture_output=True, text=True, timeout=20)


class Observation:
    def __init__(self, p, status=None):
        # Fetch independent fields together. PINE executes each request on the
        # emulator thread; dozens of tiny round trips add avoidable polling work.
        captured = {}
        def capture(ranges):
            if hasattr(p, 'read_ranges'):
                captured.update(zip(ranges, p.read_ranges(ranges)))
        def read(address, size):
            key = (address, size)
            return captured[key] if key in captured else p.read(address, size)
        u = lambda address: struct.unpack('<I', read(address, 4))[0]
        self.status = p.status() if status is None else status
        guards = native_guards()
        capture([(address,4) for address in (LOOP_FLAG,BATTLE_OBJECT,SCENE+8,
            SCENE+192,SCENE+816,MANAGER,REPLAY,MODE,HEAP1_START,HEAP1_END,
            INPUT_HOLD,native_preparation.HOOK,native_preparation.CONTROL+20,
            native_preparation.CONTROL+56,menu_return.RESULT_FLAGS,menu_return.REASON_FLAGS)]
            + [(ACTOR_HOOK,8),(ACK_ADDRESS,16)] + [(a,len(b)) for a,b in guards])
        self.loop = u(LOOP_FLAG)
        obj = u(BATTLE_OBJECT)
        self.battle_object = obj
        manager = u(MANAGER)
        scene_counts = [u(SCENE+192+624*i) for i in range(2)]
        capture(([(obj,4)] if 0x100000 <= obj < 0x8000000 else []) +
                ([(manager,4),(manager+4,4),(manager+16,4)] if 0x100000 <= manager < 0x8000000 else []) +
                [(SCENE+196+624*i+100*j,4) for i,n in enumerate(scene_counts)
                 for j in range(n if 1 <= n <= 5 else 0)])
        self.battle_state = u(obj) if 0x100000 <= obj < 0x8000000 else -1
        self.mode = u(SCENE+8)
        self.scene_rows = scene_counts
        self.scene_characters = [tuple(u(SCENE+196+624*i+100*j) for j in range(n))
                                 if 1 <= n <= 5 else () for i,n in enumerate(self.scene_rows)]
        self.manager = u(MANAGER)
        self.count = u(self.manager) if 0x100000 <= self.manager < 0x8000000 else -1
        self.initialised = bool(u(self.manager+16) & 1) if self.count >= 0 else False
        self.rows, self.slots, self.hp, self.actions, self.characters = [], [], [], [], []
        self.array = 0
        if self.count == 2:
            self.array = u(self.manager+4)
            if 0x100000 <= self.array <= 0x8000000-0x2C00 and self.array % 16 == 0:
                capture([(self.array+i*0x1600+offset,4) for i in range(2) for offset in (0x994,0x998,0x948)])
                counts = [u(self.array+i*0x1600+0x998) for i in range(2)]
                capture([(self.array+i*0x1600+0x9E4+min(u(self.array+i*0x1600+0x994),4)*0xA4,4) for i in range(2)] +
                        [(self.array+i*0x1600+0x9A4+j*0xA4,4) for i,n in enumerate(counts)
                         for j in range(n if 1 <= n <= 5 else 0)])
                for i in range(2):
                    actor = self.array+i*0x1600
                    slot = u(actor+0x994); rows = u(actor+0x998)
                    self.rows.append(rows); self.slots.append(slot)
                    self.hp.append(struct.unpack('<i', read(actor+0x9E4+min(slot, 4)*0xA4, 4))[0])
                    self.actions.append(u(actor+0x948))
                    self.characters.append(tuple(u(actor+0x9A4+j*0xA4) for j in range(rows)) if 1 <= rows <= 5 else ())
        self.replay = u(REPLAY)
        self.team_mode = u(MODE)
        self.heap1 = u(HEAP1_START) | u(HEAP1_END)
        self.native_hook = read(ACTOR_HOOK, 8) == NATIVE_PROLOGUE
        self.changed_native = [hex(address) for address, expected in guards
                               if read(address, len(expected)) != expected]
        self.ack = read(ACK_ADDRESS, 16)
        self.hold = u(INPUT_HOLD)
        self.streaming = (read(native_preparation.HOOK,4)==native_preparation.HOOK_WORD)
        self.native_held = self.streaming and u(native_preparation.CONTROL+20)==1
        self.native_intro = self.streaming and u(native_preparation.CONTROL+56)==1
        self.result_flags = u(menu_return.RESULT_FLAGS)
        self.return_flags = u(menu_return.REASON_FLAGS)
        self.menu_scene = menu_return.read_scene(p) if self.loop == 0 else None
        from codex_runtime_labels import refresh
        refresh(p,self.menu_scene)

    @property
    def clean(self):
        # A load acknowledgement can legitimately survive restoring a clean
        # original state. Actual hooks/heap ownership determine cleanliness.
        return self.heap1 == 0 and self.team_mode == 0 and self.native_hook and not self.changed_native

    @property
    def pending_reason(self):
        if self.loop != 1: return 'Waiting in the game menus for a Duel/Versus battle.'
        if self.mode != 0: return f'Game mode {self.mode} is not ordinary Duel/Versus.'
        if self.replay != 0: return 'Replay playback is not a fresh selected match.'
        if self.battle_state not in (2, 3): return f'Waiting for battle initialization (state {self.battle_state}).'
        if self.count != 2 or not self.initialised or len(self.rows) != 2:
            return 'Waiting for both native leaders and their selected rosters to initialize.'
        if not all(1 <= r <= 5 for r in self.rows): return f'Waiting for valid selected rosters ({self.rows}).'
        if not all(s == 0 for s in self.slots): return 'A leader already tagged or was replaced; start a fresh match.'
        if not all(h > 0 for h in self.hp): return 'A leader is already defeated; start a fresh match.'
        return None

    @property
    def fresh_battle(self):
        return self.pending_reason is None

    @property
    def early_teams(self):
        return self.selected_early_teams()

    def selected_early_teams(self, include_single=False):
        if (self.loop != 1 or self.mode != 0 or self.replay != 0 or not self.clean or
                not supported_teams(self.scene_rows, include_single=include_single)):
            return None
        if not all(len(team) == count and all(0 <= c <= 252 for c in team)
                   for team, count in zip(self.scene_characters, self.scene_rows)): return None
        return self.scene_characters

    @property
    def key(self):
        return (self.manager, self.array, tuple(self.rows), tuple(self.characters))

    def summary(self):
        return {key: getattr(self, key) for key in ('status', 'loop', 'battle_state', 'mode',
            'manager', 'array', 'count', 'initialised', 'rows', 'slots', 'hp', 'actions',
            'characters', 'replay', 'team_mode', 'heap1', 'native_hook', 'changed_native', 'hold')}


# The cover messages of a fresh preparation, in the order they appear: the fresh-detection
# cover, Session.progress stage labels (fresh_team_trainer), then the Ready frame.
PREPARATION_MESSAGES = ('Loading your selected fighters...', 'Getting your fighters ready...', 'Preparing team battle', 'Loading fighters',
                        'Preparing arena', 'Getting ready', 'Starting your match...')


class Autopilot:
    def __init__(self, mode='Original', poll=0.2, menu_checkpoint=True, status_file=None, manual_pause=False,
                 presentation=None, lifetime=None, in_game_menu=False, launcher_token=None):
        self.launcher_token = launcher_token
        self.mode, self.poll, self.menu_checkpoint = mode, poll, menu_checkpoint
        self.handled = set()
        self.noted = set()
        self.playable = None
        self.ack_token = None
        self.state = 'MENU'
        self.menu_saved = False
        self.worker = None
        self.reload_worker = None
        self.body_worker = None
        self.fusion_worker = None
        self.reload_capture = None
        self.reload_epoch = None
        self.result = {}
        self.resume_needed = False
        self.resume_attempted = False
        self.status_file = Path(status_file) if status_file else None
        self.last_report = None
        self.last_status_time = 0
        self.report_lock = threading.RLock()
        self.status_error = False
        self.connection_error = 'Waiting for the emulator to start the game.'
        self.last_loop = 0
        self.manual_pause = manual_pause
        self.presentation = presentation
        self.cover_started = False
        self.progress = 0
        self.play_intro_after_loading = False
        self.deferred_intro_object = None
        self.lifetime = lifetime
        from controller_mailbox import Owner
        # Off Windows a failed 3-4 player input check reaches the status the launcher shows,
        # and so does its recovery after a provisional "could not be confirmed yet".
        unavailable = lambda message: self.report(message, None, 'warning')
        recovered = lambda message: self.report(message, None, 'info')
        self.controller_input = Owner(lifetime.process.pid, report=unavailable, notice=recovered) if lifetime is not None else None
        from quad_menu_input import Owner as MenuInputOwner
        self.menu_input = MenuInputOwner(lifetime.process.pid, report=unavailable, notice=recovered) if lifetime is not None else None
        self.menu_input_failed = None  # {capture, retry time or None} of a failed three/four-player attach
        self.battle_input_failed = self.battle_input_reported = None  # match capture whose 3-4 player input failed / was reported
        self.input_checked = WINDOWS   # the startup 3-4 player input check runs once, off Windows
        from controller_assignment import Owner as AssignmentOwner
        self.assigned_input = AssignmentOwner(lifetime.process.pid) if lifetime is not None else None
        self.battle_mode, self.humans = 'teams', 1
        self.assignment=None
        self.menu_checkpoints = None
        self.menu_return_started = None
        self.mode_menu = None
        from battle_diagnostics import Recorder
        self.battle_diagnostics = Recorder()
        self.heartbeat = None      # (packet count, time it last changed)
        self.freeze_dumped = False
        self.hold_overruns = None
        import mod_settings
        self.diagnostic_settings=mod_settings.load_settings() if in_game_menu else dict(mod_settings.DEFAULTS)
        if in_game_menu:
            import native_mode_menu
            import mod_settings
            self.mode_menu = native_mode_menu.Controller(settings=mod_settings.load_settings())
            self.mode_menu.team_menu.inputs=self.assigned_input

    def checkpoints(self):
        if self.menu_checkpoints is None:
            self.menu_checkpoints = menu_return.MenuCheckpoints()
        return self.menu_checkpoints

    @property
    def preparation_enabled(self):
        # The launcher always installs a menu controller. Merely opening its
        # page is not an opt-in: only a committed custom mode grants ownership.
        return self.mode_menu is None or bool(getattr(self.mode_menu,'custom_match',False))

    def sync_preparation(self, obs):
        if not (obs.streaming and obs.clean):return
        with PineClient(timeout=5) as p:
            if self.preparation_enabled:
                native_preparation.arm(p, include_single_ffa=battle_mode_policy.prepare_singleton(self.battle_mode,self.humans))
            else:
                native_preparation.disarm(p)

    MENU_INPUT_RETRY = (2.0, 30.0)  # first and longest wait before a failed attach is tried again

    def check_controller_input(self):
        """Off Windows, once the game runs: can 3-4 player input work here (SDL2, PCSX2's memory)?
        The owner caches the verdict for this emulator and reports a failure once."""
        if self.controller_input is None:self.input_checked=True;return
        try:
            with PineClient(timeout=5) as p:self.controller_input.available(p)
        except (OSError,PineError) as error:
            log(f'Three/four-player input check delayed: {error}');return   # PINE busy: next poll
        self.input_checked=True

    def attach_menu_input(self, menu_input, capture, obs=None):
        """Controllers 3/4 in character select. If they cannot work here (no SDL2, no access to
        PCSX2's memory), say so once per selection screen and keep watching: players 1 and 2 play on.
        Other failures are tried again after a growing pause."""
        failed=getattr(self,'menu_input_failed',None)
        if failed is not None and failed['capture']==capture and (failed['retry'] is None or time.monotonic()<failed['retry']):
            return
        try:
            with PineClient(timeout=5) as p:menu_input.attach(p,capture)
        except Exception as error:
            from runtime_owner import EmulatorClosed
            if isinstance(error,EmulatorClosed):raise
            from controller_mailbox import MailboxUnavailable, plain_reason
            from input_binding import SDLUnavailable
            again=failed is not None and failed['capture']==capture
            first,longest=self.MENU_INPUT_RETRY
            delay=None if isinstance(error,(SDLUnavailable,MailboxUnavailable)) else min(longest,failed['delay']*2) if again else first
            self.menu_input_failed=dict(capture=capture,delay=delay,retry=None if delay is None else time.monotonic()+delay)
            try:menu_input.close()
            except Exception as close_error:log(f'Could not release three/four-player input: {close_error}')
            detail=plain_reason(error)
            if again:
                log(f'Three/four-player input still unavailable: {detail}.'+('' if delay is None else f' Trying again in {delay:.0f} s.'))
                return
            then=('on this selection screen' if delay is None else 'yet (trying again)')
            self.report(f'Three/four-player input unavailable: {detail}. Players 3 and 4 (and the all-controllers '
                        f'option) cannot use their controllers {then}; players 1 and 2 are not affected.',obs,'warning')
        else:self.menu_input_failed=None

    def attach_assigned_input(self, assigned, p, capture, obs=None):
        """Player Setup's controller assignment for `capture`. If its input cannot start (no SDL2,
        no access to PCSX2's memory, OpenProcess refused...), say so once, restore the default
        controls as Player Setup does, and keep watching. A closed emulator and PINE failures
        (PineError, the socket's connection and timeout errors) still propagate."""
        try:
            assigned.attach(p,capture)
        except Exception as error:
            from runtime_owner import EmulatorClosed
            if isinstance(error,(EmulatorClosed,PineError,ConnectionError,TimeoutError)):raise
            import controller_assignment
            from controller_mailbox import plain_reason
            # Close the input thread once. One that does not stop is dropped, never closed again.
            try:assigned.close()
            except Exception as close_error:log(f'Could not release the assigned controllers: {close_error}')
            assigned.service=assigned.capture=assigned.order=None
            for owner in (getattr(self,'menu_input',None),getattr(self,'controller_input',None)):
                if owner is not None:owner.devices=(2,3)   # players 3 and 4 back on controllers 3 and 4
            p.write_u32(controller_assignment.CONTROL+12,0)   # disarm the hook; PINE errors propagate
            self.report(f'Controller assignment stopped: {plain_reason(error)}. Default controls are restored (players 1 and 2 use '
                        'their PCSX2 controllers); assign controllers again in Player Setup.',obs,'warning')

    def attach_battle_input(self, p, capture, rewound=False, obs=None):
        """Players 3 and 4 in a prepared match. If their input cannot start or stops (no SDL2, no
        access to PCSX2's memory, OpenProcess refused, a failed input thread...), release it, say so
        once for this match and keep the match: players 1 and 2 and the fighter updates go on. It is
        tried again after a rewind or once the watcher starts the match over (the next match); a
        repeated failure in the same match is only logged. A closed emulator and PINE failures
        (PineError, the socket's connection and timeout errors) still propagate."""
        owner=self.controller_input
        if getattr(self,'battle_input_failed',None)==capture and not rewound:return
        try:
            owner.attach(p,capture,rewound=rewound)
        except (OSError,ValueError,RuntimeError) as error:
            from runtime_owner import EmulatorClosed
            if isinstance(error,(EmulatorClosed,PineError,ConnectionError,TimeoutError)):raise
            from controller_mailbox import plain_reason
            # Close the input thread once. One that does not stop is dropped, never closed again.
            try:owner.close()
            except Exception as close_error:log(f'Could not release three/four-player input: {close_error}')
            owner.service=owner.capture=None
            self.battle_input_failed=capture
            detail=plain_reason(error)
            if getattr(self,'battle_input_reported',None)==capture:
                log(f'3-4 player input still unavailable: {detail}.');return
            self.battle_input_reported=capture
            self.report(f'3-4 player input stopped: {detail}. Players 3 and 4 cannot use their controllers in this match; '
                        'the match goes on and players 1 and 2 are not affected.',obs,'warning')

    def service_menu(self, obs):
        """Make menu navigation ready before checkpoint IO; avoid nested PINE."""
        native_menu=bool(getattr(self.mode_menu,'native',False))
        scene=obs.menu_scene
        assigned=getattr(self,'assigned_input',None)
        if assigned is not None:
            import controller_assignment
            import native_mode_menu as native_menu_module
            devices=controller_assignment.private_devices(assigned.order) if assigned.order else (2,3)
            self.menu_input.devices=devices;self.controller_input.devices=devices
            with PineClient(timeout=5) as p:
                custom=bool(self.preparation_enabled or (native_menu and p.read_u32(native_menu_module.CONTROL+4)==2))
                if assigned.order and custom:self.attach_assigned_input(assigned,p,('menu',),obs)
                else:assigned.disable(p)
        menu_input=getattr(self,'menu_input',None)
        if menu_input is not None:
            shared_selection=getattr(self.mode_menu,'settings',{}).get('all_controllers_character_select',False)
            if self.preparation_enabled and scene is not None and scene.kind=='character_select' and (self.humans>=3 or shared_selection):
                self.attach_menu_input(menu_input,(scene.manager,scene.object),obs)
            else:menu_input.close();self.menu_input_failed=None
        stock_main=bool(scene is not None and getattr(scene,'kind',None)=='main' and getattr(scene,'ready',False))
        def capture(capture_scene=None):
            if not(self.menu_checkpoint and obs.clean and obs.status=='running'):return
            try:
                record=self.checkpoints().consider_scene(scene if capture_scene is None else capture_scene,clean=True)
                if record:
                    self.menu_saved=True
                    log(f"Saved clean {record['kind'].replace('_',' ')} checkpoint.")
            except (OSError,ValueError,RuntimeError,TimeoutError) as error:
                self.report(f'Clean menu capture delayed: {error}',obs,'waiting')
        # Navigation is independent of checkpoint IO; launch remains gated by
        # a current archive. Options/save visits still refresh that archive.
        returning_to_mod=False
        if native_menu and stock_main and callable(getattr(self.mode_menu,'return_pending',None)):
            with PineClient(timeout=5) as p:returning_to_mod=self.mode_menu.return_pending(p)
        checkpoint=self.checkpoints() if native_menu and self.menu_checkpoint else None
        reuse_main=bool(returning_to_mod and checkpoint and 'main' in checkpoint.records and
                        checkpoint.card_reader()==checkpoint.card_revision)
        # A custom selector cancellation has a current clean main checkpoint.
        # Do not recapture/save it merely to reopen the same mod page. If game
        # saves changed, keep the loading cue while the new clean capture runs.
        # Publish the interactive pager first. The recovery snapshot may finish
        # while the user browses; only committing a mode needs its receipt.
        checkpoint_current=bool(checkpoint and checkpoint.handled_scene and scene and
            (checkpoint.handled_scene.kind,checkpoint.handled_scene.manager,checkpoint.handled_scene.object)==
            (scene.kind,scene.manager,scene.object) and checkpoint.card_reader()==checkpoint.card_revision)

        if self.mode_menu is not None:
            with PineClient(timeout=5) as p:
                if native_menu:
                    checkpoint=self.checkpoints() if self.menu_checkpoint else None
                    capture_ready=(not self.menu_checkpoint or reuse_main or
                                   (checkpoint_current and 'main' in checkpoint.records))
                    selected=self.mode_menu.tick(p,allow_activate=stock_main,
                                                 checkpoint_ready=capture_ready)
                else:selected=self.mode_menu.tick(p)
            if selected is not None:
                self.battle_mode,self.humans=selected['mode'],selected['humans']
                self.assignment=selected.get('assignment')
                self.report(f"Selected {self.battle_mode}: {self.humans} human player(s).",obs)
        if native_menu and scene is not None and getattr(scene,'kind',None)=='main':
            if not reuse_main:
                with PineClient(timeout=5) as p:
                    checkpoint_scene=menu_return.read_scene(p,allow_owned_main=True)
                capture(checkpoint_scene)
            return
        capture()

    def return_to_menu(self, obs):
        self.reset_reload_worker()
        if not self.menu_checkpoint:
            self.state = 'MENU'
            return
        checkpoints = self.checkpoints()
        # Native flags normally arrive during results. The observed native
        # destination also covers a fast menu choice between watcher polls.
        destination = checkpoints.destination
        if destination is None and obs.menu_scene is not None:
            destination = obs.menu_scene.kind
        if destination is None:
            if self.menu_return_started is None:
                self.menu_return_started = time.monotonic()
            self.cover('Returning to your selected menu...', 50)
            if time.monotonic()-self.menu_return_started > 15:
                self.state = 'FAILED'
                self.cover('MENU DESTINATION UNKNOWN - CLOSE AND REOPEN THE GAME', 100)
                self.report('The game did not identify its return destination. No different menu was substituted.', level='error')
            return
        self.cover('Returning to character selection...' if destination == 'character_select'
                   else 'Returning to the main menu...', 50)
        try:
            checkpoints.restore(destination)
            if self.mode_menu is not None:
                # The archived guest cover/lease belongs to an earlier visit.
                # Reopen only when returning to the actual main menu.
                import mode_menu
                with PineClient(timeout=5) as p:
                    if getattr(self.mode_menu,'native',False):
                        if destination=='main' and getattr(self.mode_menu,'custom_match',False):
                            page={'teams':1,'ffa':2,'coop':1,'training':4,'training_coop':4}[self.battle_mode]
                            self.mode_menu.reset(p,return_page=page)
                        else:self.mode_menu.reset(p)
                    else:
                        self.mode_menu.screen.hide(client=p)
                        p.write_u32(mode_menu.CONTROL+4, 0)
                        p.write_u32(mode_menu.CONTROL+12, 0)
                        p.write_u32(mode_menu.CONTROL+20, 0)
                self.mode_menu.active = False
                self.mode_menu.dismissed = False
                self.mode_menu.last_choice = None
            self.state = 'MENU'
            self.menu_return_started = None
            self.uncover()
            self.report(f"Returned to {destination.replace('_', ' ')}.")
        except PreparationBusyError:
            # A short overlap with another owned operation is not a corrupt
            # archive. Keep the requested destination and cover until its lease
            # is released; never load underneath the existing owner.
            if self.menu_return_started is None:self.menu_return_started=time.monotonic()
            if time.monotonic()-self.menu_return_started<30:
                self.cover('Finishing the previous operation before returning...',50)
                self.report('Menu return is waiting for the preparation lock.',level='waiting')
            else:
                self.state='FAILED'
                self.cover('MENU RETURN BUSY - CLOSE AND REOPEN THE GAME',100)
                self.report('Menu return could not acquire the preparation lock within 30 seconds. '
                            'No checkpoint was loaded over another operation.',level='error')
        except (OSError, ValueError, RuntimeError, TimeoutError) as error:
            self.state = 'FAILED'
            self.cover('MENU RESTORE FAILED - CLOSE AND REOPEN THE GAME', 100)
            self.report(f'Clean {destination.replace("_", " ")} restore failed: {error}. '
                        'No different menu was substituted. Close and reopen Play (any teams).', level='error')

    def set_loading_teams(self, characters):
        if self.presentation is None or not hasattr(self.presentation, 'set_teams'): return
        outside=[(side,slot,character) for side,team in enumerate(characters)
                 for slot,character in enumerate(team) if type(character) is not int or not 0<=character<=252]
        if outside:
            self.report(f'Selected character IDs outside the audited Tag Team roster: {outside}. '
                        'Preparation will check the native rows and report the exact unsupported slot.',
                        level='warning')
            return
        self.presentation.set_teams([dict(side=i, fighters=[dict(character_id=c,player=(self.assignment.index(2*slot+i)+1 if 2*slot+i in self.assignment else 0)) if self.assignment is not None else dict(character_id=c) for slot,c in enumerate(team)])
                                     for i,team in enumerate(characters)])

    def early_loading(self, obs):
        """Cover native arena/intro loading, then defer dialogue to prepared start."""
        if not self.preparation_enabled:return
        teams = obs.selected_early_teams(include_single=battle_mode_policy.prepare_singleton(self.battle_mode,self.humans))
        if teams is None or obs.battle_state not in (-1, 0, 1): return
        self.set_loading_teams(teams)
        if self.presentation is not None and hasattr(self.presentation, 'set_mode'):
            self.presentation.set_mode(self.battle_mode, self.humans)
        # 12BD10 starts native disc loading before BATTLE_OBJECT exists. Paint
        # ahead while its minigame is visible, but publish only when phase 0
        # initializes the arena (or phase 1 if the polling interval missed 0).
        self.prerender_cover()
        if obs.battle_state == -1: return
        self.play_intro_after_loading = True
        self.cover('Loading your selected fighters...', 0)
        if obs.battle_state != 1 or self.deferred_intro_object == obs.battle_object: return
        # Phase1's documented substate4 returns phase2 through the normal exit.
        # Actor initialization therefore still runs on its original path. Voice
        # and camera setup are repeated natively only after preparation ends.
        with PineClient(timeout=5) as p:
            obj = p.read_u32(BATTLE_OBJECT)
            if (obj != obs.battle_object or p.read_u32(obj) != 1 or
                    p.read_u32(obj+260) != A(0x2C6070) or p.read_u32(obj+8) not in range(4)):
                return
            p.write_u32(obj+8, 4)
        self.deferred_intro_object = obj

    def prerender_cover(self):
        # Native loading leaves the host idle for ~20 s; paint the preparation's pictures
        # then instead of between its holds. A miss still renders when shown.
        prerender = getattr(self.presentation, 'prerender', None)
        if prerender is None: return
        try: prerender(PREPARATION_MESSAGES)
        except (OSError, RuntimeError) as error:
            log(f'Loading pictures will render when shown: {error}')

    def cover(self, message='Getting your fighters ready...', progress=None, mute_audio=True):
        if self.presentation is None: return
        try:
            if progress is not None: self.progress = progress
            if hasattr(self.presentation, 'set_mode'):
                self.presentation.set_mode(self.battle_mode, self.humans)
            title = {'teams': 'Preparing team battle', 'ffa': 'Preparing free-for-all',
                     'coop': 'Preparing co-op battle','training':'Preparing modded training',
                     'training_coop':'Preparing co-op training'}[self.battle_mode]
            self.presentation.show(title, message, self.progress, mute_audio=mute_audio)
            if not self.cover_started:
                self.cover_started = True
                if not self.presentation.wait_visible():
                    log('Loading screen is waiting for the game window; preparation status is also in this window.')
        except (OSError, RuntimeError) as error:
            log(f'Loading screen unavailable: {error}. Preparation status remains in this window.')

    def uncover(self, refresh_surface=False):
        if self.presentation is not None:
            try:
                self.presentation.hide(refresh_surface=refresh_surface)
                if not self.presentation.wait_hidden(timeout=2):
                    # An unresponsive cover must not keep hiding a match after
                    # Session releases its final hold in the Ready callback.
                    self.presentation.close()
            except OSError as error:
                log(f'Could not update loading screen: {error}')
                self.presentation.close()
        self.cover_started = False

    def on_progress(self, stage, completed, total):
        if stage == 'Ready':
            # Session releases the final all-fighter hold only after returning
            # from this callback. The frame revealed here already has its bars.
            self.cover('Starting your match...',100)
            guest=getattr(self.presentation,'guest',None)
            if guest:guest.wait_drawn(timeout=2)
            self.uncover()
            return
        progress = round(100*completed/total) if total else 0
        self.cover(str(stage), progress)

    def report(self, message, obs=None, level='info'):
        with self.report_lock:
            self._report(message, obs, level)

    def _report(self, message, obs=None, level='info'):
        marker = (self.state, level, message)
        changed = marker != self.last_report
        if changed: log(f'{level.upper()}: {message}')
        now = time.monotonic()
        if self.status_file and (changed or now-self.last_status_time >= 5):
            value = dict(updated=time.strftime('%Y-%m-%d %H:%M:%S'), pid=os.getpid(),
                         state=self.state, level=level, message=message,
                         battle_mode=self.battle_mode, humans=self.humans,
                         observation=obs.summary() if obs else None)
            value['launcher_token'] = self.launcher_token
            if self.lifetime is not None:
                value['emulator_pid'] = self.lifetime.process.pid
                value['emulator_created'] = self.lifetime.created
            try:
                atomic_json(self.status_file, value)
                self.last_status_time = now
                self.status_error = False
            except OSError as error:
                if not self.status_error: log(f'Status file update delayed: {error}')
                self.status_error = True
        self.last_report = marker

    def track_match_boundary(self, obs):
        # The native allocator can reuse exactly the same manager/array and
        # roster for another match. A prior failure must not suppress it forever.
        if self.last_loop == 1 and obs.loop == 0:
            self.handled.clear(); self.noted.clear()
            self.heartbeat = None; self.freeze_dumped = False; self.hold_overruns = None
        self.last_loop = obs.loop

    def observe(self):
        try:
            with PineClient(timeout=5) as p:
                info = p.info()
                if info['status'] == 'shutdown':
                    self.connection_error = 'Waiting for the emulator to boot the game.'; return None
                if info.get('serial', '').upper() != SERIAL or info.get('crc', '').upper() != game_profile.pcsx2_crc():
                    self.connection_error = f'Waiting for {"European" if PAL else "USA"} BT3 (current game: {info.get("serial", "unknown")}, CRC {info.get("crc", "unknown")}).'
                    return None
                runtime_profile.require_version(info['version'])
                observed=Observation(p, status=info['status'])
                import fusion_input_trace
                fusion_input_trace.poll(p,self)
                return observed
        except (OSError, PineError, ValueError) as error:
            if isinstance(error,FileNotFoundError) and error.filename:
                location=Path(error.filename).resolve()
                roots=[('game',ROOT.resolve())]
                if os.environ.get('PS2X_PACKAGE_DATA'):roots.insert(0,('data',Path(os.environ['PS2X_PACKAGE_DATA']).resolve()))
                relative=next((label+'/'+location.relative_to(root).as_posix() for label,root in roots if location.is_relative_to(root)),location.name)
                self.connection_error=f'Cannot observe the game through PINE: missing file {relative}'
            else:self.connection_error = f'Cannot observe the game through PINE: {error}'
            return None

    def save_slot(self, slot):
        path = STATES/f'{PREFIX}{slot:02}.p2s'
        before = path.stat().st_mtime_ns if path.exists() else None
        with PineClient(timeout=5) as p: p.save_state(slot)
        deadline = time.monotonic()+40
        while time.monotonic() < deadline:
            time.sleep(0.3)
            if path.exists() and path.stat().st_mtime_ns != before and path.stat().st_size > 0x100000:
                time.sleep(0.5); return path
        return None

    def load_file(self, source, expect_ack=None):
        import prepared_rematch
        import saved_game_state
        # Later rematches reuse this watcher's decoded playable and, for identical
        # blocks, its verified staged archive (prepared_rematch.ArchiveCache).
        cache=getattr(self,'rematch_cache',None)
        if cache is None:cache=self.rematch_cache=prepared_rematch.ArchiveCache()
        source_ram=cache.read(source)
        source_ack=bytes(source_ram[ACK_ADDRESS:ACK_ADDRESS+16])
        if len(source_ack)!=16 or (expect_ack is not None and source_ack!=expect_ack):
            raise ValueError('Prepared checkpoint acknowledgement changed')
        # A headless/no-loading-screen watcher has no presentation owner to
        # dismiss an archived cover after the restore.
        capture=prepared_rematch.plan(source_ram,show_loading=self.presentation is not None)
        self.reset_reload_worker()
        lease=None
        try:
            # Borrow the trainer's verified slot lease, as menu restoration
            # does. Fixed218/219 may contain foreign saves and are never used.
            lease=Session()
            staged=lease.run/'rematch-staged.p2s'
            with PineClient(timeout=5) as p:
                prior_ack=p.read(ACK_ADDRESS,16)
                # A rematch rewinds the match, not saved options/progress.
                # Read before staging, and include the data in the immutable
                # archive rather than overwriting a live save writer.
                payload=saved_game_state.preserve(p,source_ram)
                blocks=(capture['blocks'] if capture is not None else [])+payload['blocks']
                if blocks:
                    if cache.stage(source,dict(serial=SERIAL,crc=CRC,blocks=blocks),staged):
                        log('Reused the verified rematch archive.')
                else:shutil.copyfile(source,staged)
                slot,target=lease.check_slot(1)
                shutil.copyfile(staged,target)
                lease.record_slot(1,staged)
                if p.read(ACK_ADDRESS,16)!=prior_ack:
                    raise RuntimeError('The current checkpoint changed before reload')
                sentinel=os.urandom(16)
                while sentinel==source_ack:sentinel=os.urandom(16)
                # The immutable source token may already be in live RAM during a
                # rematch. Only restoration from this load can replace our sentinel.
                p.write(ACK_ADDRESS,sentinel)
                if p.read(ACK_ADDRESS,16)!=sentinel:
                    raise RuntimeError('Checkpoint reload sentinel was not accepted')
                p.load_state(slot)
                # The loaded state brings its own loading buffers: nothing this
                # process wrote there can be trusted for a header-only republish.
                import guest_loading_screen;guest_loading_screen.invalidate_buffers()
            deadline = time.monotonic()+40
            while time.monotonic() < deadline:
                time.sleep(0.3)
                try:
                    with PineClient(timeout=5) as p:
                        ack = p.read(ACK_ADDRESS, 16)
                        if ack == source_ack:
                            if capture is None:return True
                            try:return prepared_rematch.complete(p,capture)
                            except (OSError,PineError,ValueError,RuntimeError,TimeoutError) as error:
                                log(f'Prepared rematch remains covered: {error}')
                                return False
                except (OSError, PineError):
                    pass
            return False
        finally:
            # Retain the immutable staged archive so a later Session can prove
            # this slot is ours before reusing it. Close releases the lock and
            # removes empty claims, including failures before the first copy.
            if lease is not None:lease.close()

    def reset_reload_worker(self, *, keep_menu_input=False, keep_battle_input=False):
        if getattr(self,'reload_worker',None) is not None:
            from codex_reload_hook_receipt import capture
            self.native_reload_hook_receipt=capture(self.reload_worker,getattr(self,'playable',None))
        menu_input=getattr(self,'menu_input',None)
        if menu_input is not None and not keep_menu_input:menu_input.close();self.menu_input_failed=None
        if not keep_battle_input:
            if self.controller_input is not None:self.controller_input.close()
            self.battle_input_failed=None   # the next match tries players 3 and 4 again
        assigned=getattr(self,'assigned_input',None)
        if assigned is not None and not (keep_menu_input or keep_battle_input):assigned.close()
        self.reload_worker = self.reload_capture = self.reload_epoch = None
        self.body_worker = None
        self.fusion_worker = None

    def service_extra_reloads(self, obs):
        """The watcher owns one serial reload worker for this prepared match."""
        if obs.status!='running':
            return
        if obs.battle_state!=3:
            # Results still consume controller input (including Fight Again).
            # Closing an assigned mailbox leaves its armed guest hook emitting
            # neutral input once the lease expires, so nobody can confirm a
            # result-menu choice. Fighter reloads stop here; input lives until
            # the actual teardown/restore, which resets both owners normally.
            self.reset_reload_worker(keep_battle_input=(obs.loop==1 and obs.team_mode==1
                                     and obs.battle_state in (1,2,4,5,6)))
            return
        import extra_reload_worker
        import extra_reload_requests
        import fighter_updates
        import trainer_bridge
        import team_start_gate
        from preset_runtime import epoch
        operation_started = False
        capture = None
        try:
            with PineClient(timeout=10) as p:
                if p.status()!='running': return
                battle = p.read_u32(BATTLE_OBJECT)
                phase=p.read_u32(battle) if 0x100000<=battle<0x8000000-0x200 else -1
                if phase!=3:
                    # The phase can advance between Observation and this read.
                    self.reset_reload_worker(keep_battle_input=(phase in (1,2,4,5,6)
                                             and p.read_u32(MODE)==1))
                    return
                manager = p.read_u32(MANAGER)
                mode,count,captured,configured = struct.unpack('<4I',p.read(MODE,16))
                enabled,owner,request_count = struct.unpack('<3I',p.read(extra_reload_requests.CONTROL,12))
                started = struct.unpack('<6I',p.read(team_start_gate.CONTROL,24))
                if (mode!=1 or count not in ACTOR_COUNTS or enabled!=1 or
                        (captured,configured,owner,request_count)!=(manager,count,manager,count) or
                        started[0]!=0 or started[2:4]!=(manager,count) or started[5]!=1):
                    self.reset_reload_worker()
                    return  # Legacy, preparing, or withdrawn checkpoint.
                capture = (manager,count,p.read(ACK_ADDRESS,16))
                counters = epoch(p)
                rewound = self.reload_epoch is not None and any(
                    new<old for new,old in zip(counters,self.reload_epoch))
                operation_started = True
                assigned=getattr(self,'assigned_input',None)
                if assigned is not None:
                    if assigned.order:
                        if rewound:assigned.close()
                        self.attach_assigned_input(assigned,p,('battle',capture),obs)
                    else:assigned.disable(p)
                if self.controller_input is not None:
                    self.attach_battle_input(p,capture,rewound,obs)
                if self.reload_worker is None or capture!=self.reload_capture or rewound:
                    import mod_settings
                    worker=extra_reload_worker.Worker(progress=log,cell_auxiliary=True)
                    worker.attach(p)
                    self.reload_worker=worker
                    self.body_worker=fighter_updates.attach_body(p,progress=log)
                    self.fusion_worker=fighter_updates.attach_fusion(p,progress=log)
                    self.reload_capture=capture
                fighter_updates.poll(p,self.reload_worker,self.body_worker,self.fusion_worker)
                trainer_bridge.service(p,extra=self.reload_worker,body=self.body_worker,fusion=self.fusion_worker)
                if self.reload_worker.failure:
                    raise RuntimeError(self.reload_worker.failure)
                if not self.reload_worker.active:
                    self.reset_reload_worker()
                else:
                    # poll can complete several transactions. Retain the final
                    # counters, so a manual load cannot reuse their ownership.
                    self.reload_epoch=epoch(p)
        except (OSError,PineError) as error:
            if operation_started: self.fail_extra_reload(error,capture)
            # Retry read-only connection/preflight failures before any guest
            # operation; an uncertain transaction remains terminal.
        except Exception as error:
            self.fail_extra_reload(error,capture)

    def freeze_folder(self):
        return self.status_file.parent if self.status_file else ROOT/'analysis'/'autopilot'

    def capture_freeze(self, p):
        """Savestate first (it holds the CPU registers and kernel memory the
        diagnosis needs); a compressed EE image if no savestate completes.

        The slot comes from the trainer's verified lease, as menu restoration
        and rematches use: only an empty slot or one proven to be ours.
        """
        stamp = time.strftime('%Y%m%d-%H%M%S'); folder = self.freeze_folder()
        if StreamingSession.native_runtime:
            if os.environ.get('BT3_PREVIEW_DIAGNOSTICS') != '1':
                raise PineError('Native freeze capture is disabled outside preview diagnostics.')
            # Native runners have no emulator savestate format. Capture RAM
            # directly instead of waiting up to 60 seconds for an absent slot.
            import zstandard
            target = folder/f'freeze-{stamp}.bin.zst'
            target.write_bytes(zstandard.ZstdCompressor(level=3).compress(native_preparation.read_ram(p)))
            return target
        lease = None
        try:
            lease = Session()
            slot, path = lease.check_slot(0)
            before = path.stat().st_mtime_ns if path.exists() else None
            p.save_state(slot)
            deadline = time.monotonic()+60
            while time.monotonic() < deadline:
                time.sleep(0.5)
                if path.exists() and path.stat().st_mtime_ns != before and path.stat().st_size > 0x100000:
                    time.sleep(1.0)
                    target = folder/f'freeze-{stamp}.p2s'
                    shutil.copyfile(path, target)
                    lease.record_slot(0, target)
                    return target
            log('Freeze savestate did not complete in time.')
        except (OSError, PineError, ValueError) as error:
            log(f'Freeze savestate failed: {error}')
        finally:
            if lease is not None: lease.close()
        import zstandard
        target = folder/f'freeze-{stamp}.bin.zst'
        target.write_bytes(zstandard.ZstdCompressor(level=3).compress(native_preparation.read_ram(p)))
        return target

    def watch_holds(self, client):
        """Report a shared cinematic pause that outlived its bound and was released.

        The render watchdog below cannot see this: a presentation that holds every
        fighter keeps drawing frames at full rate, so the heartbeat never stops. The
        guest releases the hold itself; this only tells the player why the match stood
        still, and leaves the counters for a later diagnosis.
        """
        import cinematic_policy
        if client.read_u32(cinematic_policy.CONTROL) != cinematic_policy.MAGIC:
            self.hold_overruns = None
            return
        overruns = client.read_u32(cinematic_policy.CONTROL+cinematic_policy.HOLD_OVERRUNS)
        if self.hold_overruns is None:
            self.hold_overruns = overruns
            return
        if overruns <= self.hold_overruns:
            return
        self.hold_overruns = overruns
        longest = client.read_u32(cinematic_policy.CONTROL+cinematic_policy.HOLD_LONGEST)
        self.report('A cinematic pause did not end on its own and was released after '
                    f'{longest} updates; the fighters are moving again. Please report what move caused it.',
                    level='warning')

    def watch_freeze(self, obs, clock=time.monotonic):
        """Capture the game once if a prepared match stops rendering.

        Read-only toward the guest: the game is already hung. The capture is
        what a later diagnosis needs (registers, saved thread contexts, the
        model table and every guard's telemetry), since the emulator log only
        shows the symptom.
        """
        if obs.status != 'running' or obs.battle_state != 3:
            self.heartbeat = None
            return
        try:
            with PineClient(timeout=10) as p:
                # Only a match whose render observer is installed and counting.
                if (p.read_u32(capacity_stage.CONTROL) != capacity_stage.MAGIC or
                        p.read_u32(capacity_stage.CONTROL+48) != 1):
                    self.heartbeat = None
                    return
                self.watch_holds(p)
                count = p.read_u32(FRAME_HEARTBEAT)
                if self.diagnostic_settings['record_battle_diagnostics']:
                    self.battle_diagnostics.tick(p,self.freeze_folder()/'battle-diagnostics.json',clock)
                now = clock()
                if self.heartbeat is None or self.heartbeat[0] != count:
                    self.heartbeat = (count, now)
                    return
                if self.freeze_dumped or now - self.heartbeat[1] < FREEZE_SECONDS or p.status() != 'running':
                    return
                self.freeze_dumped = True
                if not self.diagnostic_settings['capture_freeze_dumps']:
                    self.report('The game stopped responding. Diagnostic dumps are disabled; close and reopen the game.',level='error')
                    return
                self.report('The game stopped responding. Saving a diagnostic snapshot; this takes a moment.', level='warning')
                target = self.capture_freeze(p)
                atomic_json(target.with_name(target.name.split('.')[0]+'.json'),
                            dict(capture=str(target), packets=count, frozen_seconds=round(now-self.heartbeat[1], 1),
                                 playable=str(self.playable), battle_mode=self.battle_mode, humans=self.humans,assignment=self.assignment))
        except (OSError, PineError) as error:
            log(f'Freeze watchdog could not capture the game: {error}')
            return
        self.report(f'The game stopped responding. Diagnostic snapshot saved to {target}. Close the game and report this file.', level='error')

    def hold_failed_reload(self,capture):
        """Hold only the exact failed world through its verified native service."""
        if capture is None:return False
        manager,count,marker=capture
        try:
            with PineClient(timeout=5) as p:
                if (p.status()!='running' or not native_preparation.installed(p) or
                        p.read_u32(native_preparation.CONTROL)!=native_preparation.MAGIC or
                        p.read_u32(MANAGER)!=manager or p.read(ACK_ADDRESS,16)!=marker or
                        struct.unpack('<4I',p.read(MODE,16))!=(1,count,manager,count)):
                    return False
                if (p.read_u32(native_preparation.CONTROL+16) and
                        p.read_u32(native_preparation.CONTROL+24)!=manager):return False
                native_preparation.quiet(p,timeout=2)
                return (p.read_u32(native_preparation.CONTROL+20)==1 and
                        p.read_u32(native_preparation.CONTROL+24)==manager)
        except Exception as hold_error:
            log(f'Could not confirm failed-match combat hold: {hold_error}')
            return False

    def fail_extra_reload(self,error,capture=None):
        held=self.hold_failed_reload(capture)
        self.state='FAILED'
        self.cover('FIGHTER UPDATE FAILED - CLOSE AND REOPEN THE GAME',100)
        hold_status='Combat is held.' if held else 'Combat hold could not be confirmed.'
        self.report(f'Fighter update stopped: {error}. {hold_status} Close and reopen the game.',level='error')
        if self.status_file:
            try:
                atomic_json(self.status_file.with_name('reload-failure.json'),
                            dict(error=str(error),playable=str(self.playable),hold_confirmed=held))
            except OSError as receipt_error:
                log(f'Could not save fighter-update failure details: {receipt_error}')

    def prepare(self):
        import mod_settings
        self.diagnostic_settings=mod_settings.load_settings()
        self.result = {}
        try:
            session_type=StreamingSession if self.streaming else Session
            session = session_type(self.mode, progress=self.on_progress,
                              play_intro=self.play_intro_after_loading,
                              battle_mode=self.battle_mode, humans=self.humans,assignment=self.assignment)
            try:
                try:session.prepare()
                finally:
                    # The trainer loads its prepared checkpoint through the same PINE slot lease.
                    import guest_loading_screen;guest_loading_screen.invalidate_buffers()
                self.result = dict(ok=True, playable=session.source)
            except (OSError, ValueError, AssertionError, RuntimeError, TimeoutError) as error:
                from fresh_team_trainer import write_json
                write_json(session.run/'failure.json',dict(error=str(error),source=str(session.source),
                    transport='native-frame' if self.streaming else 'state-load',status='failed'))
                originals = list(session.run.glob('*original-selected-match.p2s'))
                self.result = dict(ok=False, error=str(error), original=originals[0] if originals else None)
            finally:
                session.close()
        except Exception as error:  # noqa: BLE001 - report anything to the console
            traceback.print_exc()
            self.result = dict(ok=False, error=str(error), original=None)

    def handle_preparation_resume(self, obs):
        if obs is None:
            return
        if obs.status == 'running':
            self.resume_needed = False
            self.report('Game running; simultaneous-team preparation is continuing.', obs)
        elif obs.status == 'paused' and obs.hold == 1:
            if not self.resume_attempted and not self.manual_pause:
                send_space()
                self.resume_attempted = True
                self.report('Input hold active. Resume requested; waiting for the game to run.', obs, 'waiting')
            else:
                self.resume_attempted = True
                self.cover('Press Space in the game to continue loading.')
                self.report('Input hold active. Resume the game with Space to continue preparation.', obs, 'waiting')

    def run(self):
        self.report(f'Autopilot watching PINE (mode {self.mode}). Choose a mode in Modded Modes to enable the trainer. Original-menu matches stay native.')
        # Clear an inherited Windows mute when this launch creates its audio session.
        startup_audio = None
        audio_ready = not (WINDOWS and self.lifetime is not None)
        audio_deadline = time.monotonic() + 90
        next_audio_check = 0
        while True:
            import fighter_updates
            time.sleep(fighter_updates.poll_delay(self.reload_worker,self.body_worker,self.fusion_worker,self.poll))
            if self.lifetime is not None:
                self.lifetime.require_alive()
            if not audio_ready and time.monotonic() >= next_audio_check:
                next_audio_check = time.monotonic() + 1
                try:
                    if startup_audio is None:
                        from loading_audio import AudioMute
                        startup_audio = AudioMute(self.lifetime.process.exe())
                    audio_ready = startup_audio.unmute(self.lifetime.pid)
                except Exception as error:
                    if time.monotonic() >= audio_deadline:
                        self.report(f'Could not restore startup audio session: {error}', level='error')
                        audio_ready = True
                if time.monotonic() >= audio_deadline:
                    audio_ready = True
            if self.presentation is not None: self.presentation.tick()
            if self.worker is not None:
                if self.worker.is_alive():
                    if self.resume_needed:
                        # The leaders are held idle once the memory stage is loaded; resume then.
                        self.handle_preparation_resume(self.observe())
                    continue
                self.worker = None
                if self.result.get('ok'):
                    self.playable = self.result['playable']
                    with PineClient(timeout=5) as p: self.ack_token = p.read(ACK_ADDRESS, 16)
                    self.state = 'ACTIVE'
                    self.uncover()
                    self.report(f'Simultaneous match ready. Rematch checkpoint: {self.playable}')
                else:
                    error = self.result.get('error')
                    self.report(f'PREPARATION FAILED: {error}. The game is not a prepared simultaneous match.', level='error')
                    # A boot/menu archive is not a recovery transaction. In
                    # particular, another controller's lock failure must never
                    # load a state underneath the actual preparation owner.
                    self.state='FAILED'
                    self.cover('SETUP FAILED - CLOSE THE GAME AND REOPEN PLAY ANY TEAMS',self.progress,
                               mute_audio=False)
                    self.report(f'Team setup stopped: {error}. No checkpoint was loaded. Close the emulator and reopen Play (any teams).',level='error')
                    self.handled.add(self.current_key)
                continue
            obs = self.observe()
            if obs is None:
                # The launcher owns our lifetime. BIOS/loading delays must not
                # quietly terminate the watcher before the user chooses teams.
                self.report(self.connection_error, level='waiting')
                continue
            if self.state=='FAILED':
                # A failed transaction/restore is not permission to expose the
                # partial world when the native loop next visits its menu.
                continue
            if not getattr(self,'input_checked',True) and obs.status=='running':
                # Tell Linux players at startup, not first in character select, when P3/P4 cannot work.
                self.check_controller_input()
            if self.state == 'ACTIVE' and self.menu_checkpoint:
                self.checkpoints().observe_result(obs.result_flags, obs.return_flags)
            self.track_match_boundary(obs)
            if obs.status == 'paused' and obs.loop == 0 and self.state == 'MENU' and not self.menu_saved:
                if self.manual_pause:
                    self.report('The game is paused in its menus. Resume with Space.', obs, 'waiting')
                else:
                    log('Resuming the paused emulator.'); send_space(); time.sleep(1.0)
                continue
            if obs.loop == 0:
                # The selector owns its service across menu polls. Closing it
                # here would repeatedly recreate SDL devices while P3/P4 pick.
                # service_menu closes it when leaving character selection.
                self.reset_reload_worker(keep_menu_input=True)
                self.play_intro_after_loading = False
                self.deferred_intro_object = None
                if self.state == 'ACTIVE':
                    self.return_to_menu(obs)
                    continue
                if self.state != 'MENU': self.state = 'MENU'
                if self.cover_started: self.uncover()
                self.report(obs.pending_reason, obs, 'waiting')
                self.service_menu(obs)
                # Consume Original/Modded selection before changing the guest
                # gate, including cancellation or return from a custom match.
                self.sync_preparation(obs)
                continue
            # Native shutdown clears the team marker before LOOP_FLAG. A
            # pause-menu exit can therefore resemble a rematch for one poll.
            # Honor the latched destination and wait for native teardown first.
            if self.state == 'ACTIVE' and (
                    menu_return.return_destination(obs.result_flags, obs.return_flags) is not None or
                    (self.menu_checkpoint and self.checkpoints().destination is not None)):
                continue
            # battle loop active
            if self.state == 'ACTIVE':
                if obs.team_mode == 0:
                    log('Native rematch detected; reloading the prepared match instead.')
                    self.cover('Getting everyone ready for the rematch...', 90)
                    restore_error=None
                    try:restored=bool(self.playable and self.load_file(self.playable,self.ack_token))
                    except (OSError,PineError,ValueError,RuntimeError,TimeoutError) as error:
                        restored=False;restore_error=str(error)
                    if restored:
                        self.heartbeat=None
                        log('Prepared match reloaded.');self.uncover()
                    else:
                        self.state='FAILED'
                        self.cover('REMATCH RESTORE FAILED - CLOSE AND REOPEN THE GAME',100)
                        detail=f' {restore_error}.' if restore_error else ''
                        self.report('Prepared rematch restore was not acknowledged.'+detail+' No native tag match was substituted.',level='error')
                else:
                    self.service_extra_reloads(obs)
                    self.watch_freeze(obs)
                continue
            if self.state in ('MENU', 'BATTLE', 'PAUSE_REQUIRED'):
                self.sync_preparation(obs)
                if not self.preparation_enabled:
                    self.state='BATTLE'
                    self.report('Original-menu match: playing normally; trainer inactive.',obs)
                    continue
                self.early_loading(obs)
                if not obs.fresh_battle:
                    self.report(obs.pending_reason, obs, 'waiting'); continue
                if not obs.clean:
                    # A prepared checkpoint loaded by hand, or leftovers after a native
                    # rematch: transient, so do not remember it as handled.
                    if obs.key not in self.noted:
                        self.noted.add(obs.key)
                        self.report('This process already carries preparation changes; restart Play (any teams).cmd for a new roster.', obs, 'warning')
                    self.state = 'BATTLE'; continue
                if obs.key in self.handled: continue
                if max(obs.rows) <= 1 and not battle_mode_policy.prepare_singleton(self.battle_mode,self.humans):
                    if self.cover_started: self.uncover()
                    self.handled.add(obs.key); self.state = 'BATTLE'
                    self.report('1v1 battle: playing the normal native match.', obs); continue
                if not supported_teams(obs.rows, include_single=battle_mode_policy.prepare_singleton(self.battle_mode,self.humans)):
                    if self.cover_started: self.uncover()
                    self.handled.add(obs.key)
                    self.state = 'BATTLE'
                    self.report(f'Teams {obs.rows[0]}v{obs.rows[1]} exceed {TEAM_CAPACITY} fighters per side; playing a normal tag match.', obs, 'warning'); continue
                self.set_loading_teams(obs.characters)
                self.streaming=obs.streaming
                self.play_intro_after_loading=self.play_intro_after_loading or obs.streaming or obs.native_intro
                if obs.streaming and not obs.native_held:
                    self.report('Waiting for the native team preparation hold.',obs,'waiting');continue
                if obs.status == 'running' and not obs.streaming:
                    if self.manual_pause or self.state == 'PAUSE_REQUIRED':
                        self.state = 'PAUSE_REQUIRED'
                        self.report(f'Fresh {obs.rows[0]}v{obs.rows[1]} Duel detected. Pause with Space to capture the selected match.', obs, 'waiting')
                        continue
                    # Freeze the moment of capture so no hit lands before the input hold exists.
                    self.cover(progress=0)
                    send_space()
                    paused = False
                    for _ in range(15):
                        time.sleep(0.2); check = self.observe()
                        if check is not None and check.status == 'paused': paused = True; break
                    if not paused:
                        self.state = 'PAUSE_REQUIRED'
                        self.cover('Press Space in the game to begin loading.')
                        self.report('Automatic pause was not confirmed. Pause with Space to begin simultaneous-team preparation.', obs, 'warning')
                        continue
                self.state = 'PREPARING'
                self.menu_return_started = None
                if self.menu_checkpoint:
                    self.checkpoints().begin_battle()
                self.cover(progress=0)
                self.report(f'Fresh {obs.rows[0]}v{obs.rows[1]} Duel detected; preparing simultaneous teams. Fighters will stay idle during setup.', obs)
                self.resume_needed = not obs.streaming
                self.resume_attempted = False
                self.current_key = obs.key; self.state = 'PREPARING'
                self.worker = threading.Thread(target=self.prepare, daemon=True); self.worker.start()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('Original', 'Player', 'Cpu', 'TwoPlayer'), default='Original')
    parser.add_argument('--no-menu-checkpoint', action='store_true', help='Do not capture the clean menu checkpoint at boot')
    parser.add_argument('--manual-pause', action='store_true', help='Never send UI input; wait for manual pause/resume')
    parser.add_argument('--no-loading-screen', action='store_true', help='Diagnostic console-only preparation')
    parser.add_argument('--status-file', type=Path, default=ROOT/'analysis/autopilot/status.json')
    parser.add_argument('--check', action='store_true', help='Check Python/dependencies without accessing the emulator')
    parser.add_argument('--emulator-pid', type=int, help='Exact emulator process started by this launcher')
    parser.add_argument('--launcher-token', help='Private launch receipt; supports Windows virtual-environment redirectors')
    parser.add_argument('--inspect-state', type=Path, help='Explain detection using an offline RAM/save-state file only')
    args = parser.parse_args()
    if args.check:
        if sys.version_info < (3, 11): raise RuntimeError('Python3.11+ is required by the trainer')
        import elftools, zstandard, capstone, numpy  # noqa:F401 - fail before opening a game
        from PIL import Image  # noqa:F401 - native loading portraits
        import importlib.util
        if WINDOWS:
            from loading_audio import WHEEL
            if not WHEEL.is_file() or any(importlib.util.find_spec(x) is None for x in ('comtypes', 'psutil')):
                raise RuntimeError('The loading audio helper requires local pycaw, comtypes and psutil')
        else:
            # The loading-audio helper (pycaw/comtypes) is Windows-only; the emulator lifetime needs psutil.
            if importlib.util.find_spec('psutil') is None:
                raise RuntimeError('The watcher requires psutil')
            from input_binding import sdl_status
            print(f'Three/four-player input: {sdl_status()}', flush=True)
        native_guards()
        import mod_settings
        mod_settings.load_settings()
        print(f'Autopilot dependencies ready: {sys.executable}', flush=True)
        return 0
    if args.inspect_state:
        from camera_snapshot import read_ram
        ram = read_ram(args.inspect_state)
        class OfflineReader:
            def status(self): return 'paused'
            def read(self, address, size): return ram[address:address+size]
            def read_u32(self, address): return struct.unpack_from('<I', ram, address)[0]
        obs = Observation(OfflineReader())
        print(json.dumps(dict(observation=obs.summary(), fresh_battle=obs.fresh_battle,
            clean=obs.clean, reason=obs.pending_reason,
            supported=obs.fresh_battle and supported_teams(obs.rows)), indent=2))
        return 0
    from loading_presentation import LoadingPresentation
    from runtime_owner import claim, EmulatorLifetime, EmulatorClosed
    from pine import set_runtime_guard
    ownership = presentation = watcher = lifetime = None
    try:
        if args.emulator_pid is None:
            raise ValueError('Start Play (any teams).cmd so the watcher has an owned emulator PID.')
        ownership = claim()
        lifetime = EmulatorLifetime(args.emulator_pid)
        set_runtime_guard(lifetime.require_alive, lifetime.pid)
        presentation = None if args.no_loading_screen else LoadingPresentation(
            args.status_file.with_name('presentation.json'), native=True)
        # Only Windows can send PCSX2 its pause key; elsewhere the player presses it when asked.
        watcher = Autopilot(args.mode, menu_checkpoint=not args.no_menu_checkpoint,
                            status_file=args.status_file, manual_pause=args.manual_pause or not WINDOWS,
                            presentation=presentation, lifetime=lifetime, in_game_menu=True, launcher_token=args.launcher_token)
        watcher.run()
    except EmulatorClosed as error:
        if watcher is not None:
            watcher.state = 'CLOSED'
            watcher.report(str(error))
        else:
            log(str(error))
        return 0
    except KeyboardInterrupt:
        log('Automatic preparation was stopped.')
        return 0
    except Exception as error:
        if watcher is not None:
            watcher.state = 'FAILED'
            watcher.report(f'AUTOMATIC PREPARATION STOPPED: {error}. See the error log; the game may still be native.', level='error')
        else:
            log(f'AUTOMATIC PREPARATION STOPPED: {error}')
        traceback.print_exc()
        return 1
    finally:
        try:
            # Revoke before cleanup: a surviving daemon/cover must not connect
            # to a newly opened emulator after this controller is stopped.
            if lifetime is not None: lifetime.revoke()
            if watcher is not None:watcher.reset_reload_worker()
            if watcher is not None and watcher.mode_menu is not None:
                watcher.mode_menu.close()
            if watcher is not None and watcher.worker is not None:
                watcher.worker.join(timeout=2)
            if presentation is not None:
                try: presentation.close()
                except EmulatorClosed: pass
        finally:
            if ownership is not None: ownership.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
