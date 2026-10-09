"""Launch the Power Scale/expanded-map native trial with its Python controller."""
from pathlib import Path
import argparse,os,socket,struct,subprocess,sys,time

HERE=Path(__file__).resolve().parent
TRIAL=HERE/'power-scale-trial'
TOOLS=TRIAL/'controller/game/tools'
REPO=HERE/'repo'
EXE=REPO/'build/ps2xRuntime/ps2EntryRunner.exe'
ISO=HERE.parent/'experiments/.full-install/game/maps/expanded-2x.iso'
ELF=HERE/'power-scale-input/SLUS_216.78'
PORT=28012
RUNNER_FEATURES={
    'ps2EntryRunner-four-seat-review.exe':frozenset(('rematch','roster','seat-pads')),
    'ps2EntryRunner-four-seat-fusion-review.exe':frozenset(('rematch','roster','seat-pads')),
    'ps2EntryRunner-native-rematch.exe':frozenset(('rematch',)),
    'ps2EntryRunner-native-roster.exe':frozenset(('rematch','roster')),
    'ps2EntryRunner-native-ki-default.exe':frozenset(('rematch','roster')),
    'ps2EntryRunner-native-embedded-baseline.exe':frozenset(('rematch','roster')),
}

def runner_modes(name,no_controller,environment):
    features=RUNNER_FEATURES.get(name,frozenset())
    rematch=environment.get('PS2X_NATIVE_REMATCH','1' if 'rematch' in features and not no_controller else '0')=='1'
    roster=environment.get('PS2X_POWER_SCALE_ROSTER','1' if 'roster' in features and not no_controller else '0')=='1'
    if roster and (no_controller or 'roster' not in features):
        raise ValueError('Expanded roster trial requires its matching runner and controller')
    if rematch and (no_controller or 'rematch' not in features):
        raise ValueError('Native clean rematches require their matching runner and controller')
    return rematch,roster

class TrialLog:
    def __init__(self,stream,file):self.stream,self.file=stream,file
    def write(self,text):
        if os.environ.get('PS2X_PACKAGE_DATA'):
            import re
            text=re.sub(r'[A-Za-z]:[\\/][^\r\n]*','[local path]',text)
        self.stream.write(text);self.file.write(text);self.file.flush()
        return len(text)
    def flush(self):self.stream.flush();self.file.flush()

def main():
    args=argparse.ArgumentParser()
    args.add_argument('--seconds',type=float,help='Bounded diagnostic run')
    args.add_argument('--no-controller',action='store_true')
    args.add_argument('--renderer',choices=('opengl','vulkan','native-vulkan'),default='opengl')
    args.add_argument('--runner',help='Runner .exe filename inside repo/build/ps2xRuntime')
    args.add_argument('--controller-poll',type=float,default=.2,
                      help='Diagnostic ordinary controller polling seconds (default 0.2; 2.0 for 10x slower comparison). Pending workers retain their required polling.')
    options=args.parse_args()
    if not 0.02<=options.controller_poll<=5:
        args.error('--controller-poll must be between 0.02 and 5 seconds')
    global EXE
    EXE=REPO/'build/ps2xRuntime'/('ps2EntryRunner-interp-hooks.exe' if options.no_controller else 'ps2EntryRunner-native-ki-default.exe')
    if options.runner:
        if Path(options.runner).name!=options.runner or not options.runner.lower().endswith('.exe'):
            raise ValueError('--runner must be an .exe filename without a directory')
        EXE=REPO/'build/ps2xRuntime'/options.runner
    native_rematch,roster_trial=runner_modes(EXE.name,options.no_controller,os.environ)
    os.environ.setdefault('PS2X_NATIVE_SEAT_PADS','1' if 'seat-pads' in RUNNER_FEATURES.get(EXE.name,()) and not options.no_controller else '0')
    os.environ.setdefault('PS2X_NATIVE_REMATCH','1' if native_rematch else '0')
    try:
        existing=socket.create_connection(('127.0.0.1',PORT),timeout=.5)
    except OSError:pass
    else:
        existing.close()
        raise RuntimeError('A native trial is already running. Close its game window before opening another trial.')
    for path in (EXE,ISO,ELF,ELF.parent/'BIN/MOD.BIN',ELF.parent/'DATA/MOD.AFS',ELF.parent/'DATA/DLC.AFS',TRIAL/'tagteam-bootstrap.pnach'):
        if not path.is_file():raise FileNotFoundError(path)
    from codex_dependency_check import check_dependencies
    if not options.no_controller:
        check_dependencies(roster=roster_trial)
    if native_rematch:
        import shutil
        archive=TRIAL/'log-archive'/f'native-rematch-before-{time.strftime("%Y%m%d-%H%M%S")}'
        archive.mkdir(parents=True,exist_ok=False)
        for name in ('runner.log','controller.log','controller-status.json','loading-state.json'):
            previous=TRIAL/name
            if previous.is_file():shutil.copy2(previous,archive/name)
    # Argument errors and rejected duplicate launches must preserve the live log.
    controller_log=(TRIAL/'controller.log').open('w',encoding='utf-8')
    sys.stdout=TrialLog(sys.stdout,controller_log)
    sys.stderr=TrialLog(sys.stderr,controller_log)
    sys.path.insert(0,str(TOOLS))
    if roster_trial:
        from codex_roster_overlay import install as install_roster
        install_roster()
        print('Expanded Power Scale roster trial enabled: IDs0..252',flush=True)
    import fresh_team_combat
    fresh_team_combat.program()  # Check patch inputs before opening the game.
    # Generate the cold-boot hooks with the SAME modules/environment the
    # controller will validate. A frozen pnach can lag behind Python UI edits.
    import mod_settings
    os.environ['PS2X_NATIVE_MODE_COVER']='1' if mod_settings.load_settings().get('native_mode_cover',False) else '0'
    import guest_loading_screen
    from atomic_files import write_bytes
    bootstrap=TRIAL/'tagteam-bootstrap.pnach'
    current_boot=guest_loading_screen.pnach()
    if bootstrap.read_bytes()!=current_boot:
        write_bytes(bootstrap,current_boot)
    import hashlib
    print(f'Current controller bootstrap: {len(current_boot)} bytes SHA256 {hashlib.sha256(current_boot).hexdigest()}',flush=True)
    source_game=HERE.parent/'experiments/.full-install/game'
    for directory in (('analysis','assets') if source_game.is_dir() else ()):
        for asset in (source_game/directory).iterdir():
            if asset.is_file() and asset.suffix in ('.json','.bin'):
                if not (TOOLS.parent/directory/asset.name).is_file():
                    raise FileNotFoundError(TOOLS.parent/directory/asset.name)
    env=os.environ.copy();env.update(PS2X_CD_IMAGE=str(ISO),PS2X_TAGTEAM_PORT=str(PORT),PS2X_TAGTEAM_BOOT=str(TRIAL/'tagteam-bootstrap.pnach'),PS2X_MODS='0',PS2X_PGS='0',PS2X_SEAMVK='0')
    if env.get('BT3_PREVIEW_DIAGNOSTICS','1')=='1':
        env.setdefault('PS2X_EXIT_CAPTURE_DIR',str(TRIAL/'guest-exit-captures'))
    else:
        env.pop('PS2X_EXIT_CAPTURE_DIR',None)
    if options.renderer!='opengl':
        env.update(PS2X_VK_NATIVE='1',PS2X_PGS='1',PS2X_PGS_EXCLUSIVE='1',PS2X_SEAMVK='1' if options.renderer=='native-vulkan' else '0')
    if options.no_controller:env['PS2X_TAGTEAM_BOOT_SNAPSHOT']=str(TRIAL/'boot-ram.bin')
    log=TRIAL/'runner.log'
    with log.open('wb') as output:
        from native_process import spawn_runner, finish_runner, runner_exit_status, closed_runner_connection
        packaged=bool(os.environ.get('PS2X_PACKAGE_DATA'))
        process=spawn_runner([str(EXE),str(ELF)],cwd=EXE.parent,env=env,stdout=subprocess.PIPE if packaged else output,stderr=subprocess.STDOUT)
        pump=None
        if packaged:
            import re,threading
            def sanitize_output():
                for line in process.stdout:
                    line=re.sub(rb'[A-Za-z]:[\\/][^\r\n]*',b'[local path]',line)
                    output.write(line);output.flush()
            pump=threading.Thread(target=sanitize_output,daemon=True);pump.start()
        print(f'Native Power Scale PID {process.pid}; log {log}',flush=True)
        deadline=None if options.seconds is None else time.monotonic()+options.seconds
        try:
            sys.path.insert(0,str(TOOLS))
            import pine,runtime_profile
            original_init=pine.PineClient.__init__
            def native_init(self,port=PORT,timeout=5.0,batch_commands=32768):
                original_init(self,port,timeout,batch_commands)
            pine.PineClient.__init__=native_init
            original_close=pine.PineClient.close
            def native_close(self):
                if os.name=='nt' and self.sock is not None:
                    # Every PINE exchange has consumed its response. Release the
                    # short-lived client port immediately instead of accumulating
                    # TIME_WAIT sockets during preparation polling.
                    try:self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_LINGER,struct.pack('<HH',1,0))
                    except OSError:pass
                original_close(self)
            pine.PineClient.close=native_close
            def require_native(version):
                if version!='BT3-Recomp TagTeam bridge v1':raise ValueError(f'Unexpected native bridge {version}')
            runtime_profile.require_version=require_native
            from runtime_owner import EmulatorLifetime
            lifetime=EmulatorLifetime(process.pid,EXE)
            pine.set_runtime_guard(lifetime.require_alive,process.pid)
            from relocate_power_scale import install
            connection=pine.PineClient()
            for attempt in range(100):
                try:connection.connect();break
                except OSError as error:
                    last_bridge_error=error
                    lifetime.require_alive();time.sleep(.1)
            else:raise RuntimeError(f'Native bridge did not start: {last_bridge_error}')
            try:module_base=install(connection,(ELF.parent/'BIN/MOD.BIN').read_bytes(),process)
            finally:connection.close()
            import select_duplicates
            with pine.PineClient() as p:
                address,patch=select_duplicates.code_pieces()[0]
                current=p.read(address,8)
                expected=struct.pack('<2I',(2<<26)|((module_base+0x1644)>>2),0)
                if current not in (patch,expected):
                    raise ValueError('Unexpected Power Scale duplicate-selection hook')
                p.write(address,patch)
                if p.read(address,8)!=patch:raise ValueError('Duplicate-selection hook readback failed')
                print('Tag Team duplicate-selection/loading hook restored',flush=True)
            import fusion_partner_lifecycle
            fusion_partner_lifecycle.POWER_SCALE_SIDE_TARGET=module_base+0x2264
            if options.no_controller:
                while process.poll() is None and (deadline is None or time.monotonic()<deadline):time.sleep(.2)
            else:
                import autopilot,loading_audio
                import fresh_team_trainer
                fresh_team_trainer.StreamingSession.native_runtime=True
                from codex_training_cleanup import install as install_fresh_cleanup
                install_fresh_cleanup(fresh_team_trainer.StreamingSession)
                import native_rematch
                native_rematch.install_stable(autopilot,pine)
                import native_rematch_trace
                native_rematch_trace.attach(autopilot,pine,TRIAL/'rematch-traces'/f'{time.strftime("%Y%m%d-%H%M%S")}-{process.pid}.jsonl')
                if os.environ.get('PS2X_NATIVE_UI_SLICE')=='1':
                    from codex_native_ui_adapter import install as install_native_ui
                    install_native_ui()
                import native_contact_probe
                native_contact_probe.start(pine,process,TRIAL/'ki-contact-status.json')
                # Native playback does not need the PCSX2 audio-session helper.
                class NativeAudio:
                    def __init__(self,*args,**kwargs):pass
                    def unmute(self,*args):return True
                    def close(self):pass
                loading_audio.AudioMute=NativeAudio
                from loading_presentation import LoadingPresentation
                presentation=LoadingPresentation(TRIAL/'loading-state.json',emulator=EXE,native=True,helper=False)
                # Reuse the mod's real guest menu and streaming preparation;
                # checkpoints and PCSX2 process-memory controllers stay off.
                watcher=autopilot.Autopilot('Original',poll=options.controller_poll,menu_checkpoint=False,manual_pause=True,presentation=presentation,lifetime=None,in_game_menu=True,status_file=TRIAL/'controller-status.json')
                watcher.lifetime=lifetime
                original_alive=lifetime.require_alive
                def bounded_alive():
                    original_alive()
                    if os.environ.get('PS2X_PACKAGE_DATA'):
                        import json
                        request=Path(os.environ['PS2X_PACKAGE_DATA'])/'restart-request.json'
                        if request.is_file():
                            value=json.loads(request.read_text(encoding='utf-8'))
                            if value.get('owner_pid')==os.getpid():raise KeyboardInterrupt
                    if deadline is not None and time.monotonic()>=deadline:raise KeyboardInterrupt
                pine.set_runtime_guard(bounded_alive,process.pid)
                watcher.run()
        except KeyboardInterrupt:pass
        except Exception as error:
            from runtime_owner import EmulatorClosed
            if not isinstance(error,EmulatorClosed) and not closed_runner_connection(process,error):raise
            print('Native game closed; controller connection ended.',flush=True)
        finally:
            finish_runner(process,pump)
            print(f'Native trial stopped: {process.returncode}; {log}',flush=True)
    # The runtime can stop cleanly after an interpreter failure (exit code 0).
    # Preserve the actual cause in the visible launcher instead of closing it.
    with log.open('rb') as stream:
        stream.seek(max(0,log.stat().st_size-65536))
        tail=stream.read().decode('utf-8',errors='replace')
    causes=[line for line in tail.splitlines() if '[interp] UNKNOWN' in line or '[tagteam] unsupported patched code' in line or '[tagteam] preparation service failed' in line]
    if causes:
        for cause in causes:print('NATIVE GAME ERROR:',cause,flush=True)
        print(f'Full details: {log}',flush=True)
        return runner_exit_status(causes)
    # External close/terminate is a user exit, not a startup error that should
    # keep the developer shell waiting. Specific runtime causes remain above.
    return 0

if __name__=='__main__':raise SystemExit(main())
