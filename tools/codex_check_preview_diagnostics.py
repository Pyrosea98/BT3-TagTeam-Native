"""Check the actual preview switch and native freeze method in isolation."""
import ast,os,runpy,tempfile,time,types
from pathlib import Path
import zstandard
HERE=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='bt3-preview-flags-') as temp:
    root=Path(temp);old=os.environ.get('BT3_TAGTEAM_DATA');os.environ['BT3_TAGTEAM_DATA']=str(root/'data')
    try:app=runpy.run_path(str(HERE/'installer/app.pyw'),run_name='preview_flags_test')
    finally:
        if old is None:os.environ.pop('BT3_TAGTEAM_DATA',None)
        else:os.environ['BT3_TAGTEAM_DATA']=old
    configure=app['configure_preview_diagnostics'];settings=app['preview_diagnostic_settings']
    for channel,override,expected in [('preview',None,True),('public',None,False),('preview','0',False),('public','1',True)]:
        (root/'release-channel.txt').write_text(channel)
        env={'PS2X_MCLOG':'0','PS2X_STALL_INTERP':'0','PS2X_EXIT_CAPTURE_DIR':'old'}
        if override is not None:env['BT3_PREVIEW_DIAGNOSTICS']=override
        assert configure(root,env)==expected
        assert env['BT3_PREVIEW_DIAGNOSTICS']==str(int(expected))
        if expected:assert env['PS2X_MCLOG']=='1' and env['PS2X_MCLOGMAX']=='1000' and env['PS2X_STALL_HISTORY']=='1' and env['PS2X_STALL_INTERP']=='1' and env['PS2X_EXIT_CAPTURE_DIR'].endswith('guest-exit-captures')
        else:assert all(k not in env for k in ['PS2X_MCLOG','PS2X_MCLOGMAX','PS2X_STALL_HISTORY','PS2X_STALL_INTERP','PS2X_EXIT_CAPTURE_DIR'])
        original={'capture_freeze_dumps':False,'language':'es'};copy=settings(original,expected)
        assert original=={'capture_freeze_dumps':False,'language':'es'}
        assert copy['language']=='es' and all(copy[k]==expected for k in ['capture_freeze_dumps','record_battle_diagnostics','keep_preparation_diagnostics'])
    (root/'release-channel.txt').unlink();assert configure(root,{}) is False
    class PineError(Exception):pass
    class FakeWatcher:
        def freeze_folder(self):return root
    payload=b'actual native RAM fixture'*40
    def forbidden(*args,**kwargs):raise AssertionError('emulator savestate/session path must not run')
    old=os.environ.get('BT3_PREVIEW_DIAGNOSTICS')
    try:
        for relative in ['power-scale-trial/controller/game/tools/autopilot.py','roster-tools/autopilot.py']:
            tree=ast.parse((HERE/relative).read_text());method=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='capture_freeze')
            module=ast.Module(body=[method],type_ignores=[]);ast.fix_missing_locations(module)
            scope={'time':time,'os':os,'StreamingSession':types.SimpleNamespace(native_runtime=True),'PineError':PineError,'Session':forbidden,'native_preparation':types.SimpleNamespace(read_ram=lambda p:payload)}
            exec(compile(module,str(HERE/relative),'exec'),scope)
            os.environ['BT3_PREVIEW_DIAGNOSTICS']='1'
            result=scope['capture_freeze'](FakeWatcher(),types.SimpleNamespace(save_state=forbidden))
            assert zstandard.ZstdDecompressor().decompress(result.read_bytes())==payload
            result.unlink();os.environ['BT3_PREVIEW_DIAGNOSTICS']='0'
            try:scope['capture_freeze'](FakeWatcher(),object())
            except PineError:pass
            else:raise AssertionError('public native capture was not blocked')
    finally:
        if old is None:os.environ.pop('BT3_PREVIEW_DIAGNOSTICS',None)
        else:os.environ['BT3_PREVIEW_DIAGNOSTICS']=old
print('PASS: preview/public defaults, explicit switch, bounded supported flags, process-local settings; base+roster native capture skips emulator and public capture disabled.')
