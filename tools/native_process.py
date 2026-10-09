"""One hidden runner child, reaped on every controller exit path."""
import os
import subprocess

def closed_runner_connection(process,error):
    """A lost socket is shutdown only after this exact runner has exited."""
    seen=set();current=error;disconnect=False
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current,ConnectionError) or (isinstance(current,OSError) and
                (getattr(current,'winerror',None) in (10053,10054,10061) or
                 current.errno in (53,54,61,10053,10054,10061,104,111))):disconnect=True
        current=current.__cause__ or current.__context__
    if not disconnect:return False
    code=process.poll()
    if code is None:
        # The window can close its socket just before the process exits.
        try:code=process.wait(timeout=.5)
        except subprocess.TimeoutExpired:return False
    return code in (0,1,-9,-15,0xC000013A,-1073741510)

def runner_exit_status(causes):
    """Only setup errors merit a brief developer-shell diagnostic delay."""
    if any('[tagteam] preparation service failed' in line for line in causes):return 1
    return 2 if causes else 0

def spawn_runner(command, **options):
    if os.name == 'nt':
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 1  # Show the game window; no console is allocated.
        options.update(startupinfo=startup, creationflags=subprocess.CREATE_NO_WINDOW)
    return subprocess.Popen(command, **options)

def finish_runner(process, pump=None):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    else:
        process.wait()
    if pump:
        pump.join(timeout=5)
    if process.stdout:
        process.stdout.close()
    return process.returncode
