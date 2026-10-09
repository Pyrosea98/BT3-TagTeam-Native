"""Native UI trial with interpreter blocks and verified fresh-match cleanup."""
import os,sys,json,time,uuid
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main(runner_name=None):
    if (HERE/'GAME_LOCK').exists():raise RuntimeError('GAME_LOCK is owned by another session')
    # Developer trials retain the evidence needed for unfinished fusion bugs.
    # Installed packages set their own preview/public choice before this call.
    os.environ.setdefault('BT3_PREVIEW_DIAGNOSTICS','1')
    if os.environ['BT3_PREVIEW_DIAGNOSTICS']=='1':
        os.environ.setdefault('PS2X_STALL_INTERP','1')
        os.environ.setdefault('PS2X_STALL_HISTORY','1')
    import run_power_scale_native as launch
    from codex_import_native_ui import DEFAULT
    manifest=DEFAULT/'manifest.json'
    try:cache=json.loads(manifest.read_text(encoding='utf-8'))
    except (OSError,ValueError):cache={}
    iso=launch.ISO.stat()
    first_import=not manifest.exists()
    if cache.get('version')!=7 or not (DEFAULT/'brand-logo.rgba').is_file() or (not os.environ.get('PS2X_PACKAGE_DATA') and (cache.get('source_size')!=iso.st_size or cache.get('source_mtime_ns')!=iso.st_mtime_ns)):
        from codex_import_native_ui import main as import_assets
        import_assets()
    # Add the upright Body atlas to an existing player-disc cache without
    # re-extracting game art or changing the user's settings.
    if not (DEFAULT/'body-upright-12.gatl').exists():
        import shutil
        for asset in (HERE/'ui-assets/glyph-atlas-v2').glob('body-upright-12.*'):
            if asset.suffix=='.gatl':shutil.copy2(asset,DEFAULT/asset.name)
        for asset in (HERE/'ui-assets/glyph-atlas-v2').glob('body-upright-12-*'):
            if asset.suffix in ('.indices','.rgba'):shutil.copy2(asset,DEFAULT/asset.name)
    os.environ.update(PS2X_NATIVE_UI_TEST='1',PS2X_NATIVE_UI_SLICE='1',PS2X_NATIVE_UI_ASSETS=str(DEFAULT))
    try:settings=json.loads((HERE/'power-scale-trial/controller/game/mod-settings.json').read_text(encoding='utf-8'))
    except (OSError,ValueError):settings={}
    os.environ['PS2X_NATIVE_UI_BOOT_CREDITS']='1' if first_import or settings.get('show_credits_at_startup',True) else '0'
    os.environ['PS2X_NATIVE_UI_LANGUAGE']=settings.get('language','en')
    os.environ['PS2X_NATIVE_UI_MENU_CREDITS']='1'
    name=runner_name or 'ps2EntryRunner-four-seat-fusion-review.exe'
    if Path(name).name!=name or not name.startswith('ps2EntryRunner-') or not name.endswith('.exe'):
        raise ValueError('Invalid native diagnostic runner')
    if '--trace-scene-writes' in sys.argv:
        sys.argv.remove('--trace-scene-writes')
        # Preserve repeated set/clear pairs: the default write-watch dedup
        # would hide a second transformation using the same native writer.
        os.environ.update(PS2X_AWATCH='0x3337B8:0x3337C0',
                          PS2X_GWATCH_NODEDUP='1',PS2X_AWATCH_FROM='0')
    if '--no-overhead-hud' in sys.argv:
        sys.argv.remove('--no-overhead-hud')
        os.environ['PS2X_NATIVE_OVERHEAD_HUD']='0'
    os.environ['PS2X_NATIVE_FRESH_CLEANUP']='1'
    if '--baseline-interpreter' in sys.argv:
        sys.argv.remove('--baseline-interpreter')
        os.environ['PS2X_INTERP_BLOCKS']='0'
    else:
        os.environ.setdefault('PS2X_INTERP_BLOCKS','1')
    if '--profile-interpreter' in sys.argv:
        sys.argv.remove('--profile-interpreter')
        os.environ.update(PS2X_INTERP_PROFILE='1',PS2X_INTERP_PROFILE_FIGHT_ONLY='1')
    if '--baseline-native-leaves' in sys.argv:
        sys.argv.remove('--baseline-native-leaves')
        os.environ['PS2X_NATIVE_LEAVES']='0'
    launch.RUNNER_FEATURES[name]=frozenset(('rematch','roster')) | (frozenset(('seat-pads',)) if name in ('ps2EntryRunner-four-seat-review.exe','ps2EntryRunner-four-seat-fusion-review.exe','ps2EntryRunner-standalone.exe') else frozenset())
    if '--runner' in sys.argv or '--no-controller' in sys.argv:raise ValueError('This slice requires its runner and controller')
    sys.argv.extend(('--runner',name))
    lock=HERE/'GAME_LOCK'
    owner=f'user-ui-slice {time.strftime("%Y-%m-%dT%H:%M:%S")} M5.2-live-test pid={os.getpid()} token={uuid.uuid4().hex}\n'
    with lock.open('x',encoding='utf-8') as file:file.write(owner)
    try:return launch.main()
    finally:
        if lock.exists() and lock.read_text(encoding='utf-8')==owner:lock.unlink()
if __name__=='__main__':raise SystemExit(main())
