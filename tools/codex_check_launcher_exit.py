"""Actual hidden runner/controller/cmd lifecycle; never boot a game."""
from pathlib import Path
import json,os,signal,socket,subprocess,sys,tempfile,time
HERE=Path(__file__).resolve().parent
PY=HERE.parent/'experiments/.full-install/.venv/Scripts/python.exe'
from native_process import spawn_runner,runner_exit_status,closed_runner_connection,finish_runner
assert runner_exit_status([])==0
assert runner_exit_status(['[interp] UNKNOWN'])==2
assert runner_exit_status(['[tagteam] preparation service failed'])==1
server="""import socket,struct,sys,time
s=socket.socket();s.bind(('127.0.0.1',0));s.listen(1)
print(s.getsockname()[1],flush=True)
c,_=s.accept();c.recv(1);c.setsockopt(socket.SOL_SOCKET,socket.SO_LINGER,struct.pack('hh',1,0));c.close();s.close()
if sys.argv[1]=='alive':time.sleep(60)
raise SystemExit(13 if sys.argv[1]=='error' else 0)
"""
for mode in ('normal','alive','error'):
    p=spawn_runner([str(PY),'-c',server,mode],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    try:
        port=int(p.stdout.readline());client=socket.create_connection(('127.0.0.1',port),timeout=3)
        try:
            client.sendall(b'x')
            try:
                client.recv(1)
            except OSError as cause:
                wrapped=RuntimeError('Native clean rematch cannot continue');wrapped.__cause__=cause
                assert closed_runner_connection(p,wrapped)==(mode=='normal'),mode
            else:raise AssertionError('Expected reset during observation')
        finally:client.close()
    finally:finish_runner(p)
print('PASS actual reset mid-observe: exited normal runner is shutdown; live runner and native-error exit remain errors')
with tempfile.TemporaryDirectory(dir=HERE/'installer') as folder:
    root=Path(folder);pidfile=root/'pid.json';controller=root/'controller.py'
    controller.write_text('''import json,subprocess,sys
from pathlib import Path
sys.path.insert(0,sys.argv[2])
from native_process import spawn_runner,finish_runner,runner_exit_status
p=spawn_runner([sys.executable,'-c','import time;time.sleep(60)'])
Path(sys.argv[1]).write_text(json.dumps({'child':p.pid}))
p.wait()
finish_runner(p)
raise SystemExit(runner_exit_status([]))
''',encoding='utf-8')
    # Keep the real developer CMD exit handling; substitute only the game launch.
    source=(HERE.parent/'Play Power Scale native UI Slice.cmd').read_text()
    lines=source.splitlines();lines[2]=f'"{PY}" "{controller}" "{pidfile}" "{HERE}"'
    cmd=root/'trial.cmd';cmd.write_text('\n'.join(lines)+'\n')
    owner=spawn_runner(['cmd.exe','/c',str(cmd)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    deadline=time.monotonic()+10
    while not pidfile.exists() and time.monotonic()<deadline:time.sleep(.05)
    assert pidfile.exists(),'Controller did not start'
    child=json.loads(pidfile.read_text())['child']
    # TerminateProcess, the same forced-exit mechanism used by taskkill /F.
    os.kill(child,signal.SIGTERM)
    owner.communicate(timeout=5)
    assert owner.returncode==0
    # tasklist excludes dead child and owner; controller is synchronously reaped
    # by the actual cmd invocation before its successful exit.
    import ctypes
    kernel=ctypes.windll.kernel32
    for pid in (child,owner.pid):
        handle=kernel.OpenProcess(0x100000,False,pid)
        if handle:
            assert kernel.WaitForSingleObject(handle,0)==0
            kernel.CloseHandle(handle)
print('PASS actual forced child exit: controller/cmd exit <5s, no child/owner remaining; runtime error has no delay; setup timeout is bounded')
