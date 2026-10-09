"""One host controller, bound to one emulator lifetime, never a replacement PID."""
import runtime_profile
import os
from pathlib import Path
import time
import psutil

from fresh_team_trainer import acquire_lock

ROOT = Path(__file__).resolve().parents[1]
EXECUTABLE = runtime_profile.EXECUTABLE
WINDOWS = os.name == 'nt'
LOCK = ROOT/'analysis/autopilot/.owner.lock'


class EmulatorClosed(RuntimeError):
    pass


def claim(path=LOCK, timeout=3):
    """Crash-released OS lock, acquired before any presentation or PINE access."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic()+timeout
    while True:
        try:
            return acquire_lock(path)
        except ValueError:
            if time.monotonic() >= deadline:
                raise ValueError('Another automatic match controller is already running. '
                                 'Close its emulator before starting another launcher.') from None
            # An immediately relaunched emulator may overlap the old watcher's
            # bounded cleanup. Wait only for its OS lease, with no PINE access.
            time.sleep(.05)


def same_file(first, second):
    try:
        return Path(first).resolve() == Path(second).resolve() or os.path.samefile(first, second)
    except (OSError, TypeError, ValueError):
        return False


def appimage_process(process, executable):
    """Linux: the launched PID runs the runtime's AppImage, then (same PID) PCSX2 from its mount.

    Before the AppImage runtime execs AppRun, /proc/<pid>/exe is the AppImage itself. Afterwards
    it is /tmp/.mount_*/usr/bin/pcsx2-qt, and the runtime's APPIMAGE variable names the file.
    """
    try:
        exe = process.exe()
        if exe and same_file(exe, executable):
            return True
        if os.path.basename(exe) != 'pcsx2-qt':
            return False
        return same_file(process.environ().get('APPIMAGE'), executable)
    except psutil.AccessDenied:  # another user's process is never ours (an exited one: EmulatorClosed)
        return False


class EmulatorLifetime:
    def __init__(self, pid, executable=EXECUTABLE):
        try:
            self.process = psutil.Process(pid)
            if WINDOWS:
                if Path(self.process.exe()).resolve() != Path(executable).resolve():
                    raise ValueError('The watcher requires its own isolated emulator process')
            elif not appimage_process(self.process, executable):
                raise ValueError('The watcher requires its own isolated emulator process')
            self.created = self.process.create_time()
        except psutil.NoSuchProcess:
            raise EmulatorClosed('The launcher emulator has closed.') from None
        # PINE's Unix-socket peer check compares the listener with this PID.
        self.pid = self.process.pid
        self.closed = False
        self.require_alive()

    def require_alive(self):
        # is_running compares process creation identity as well as PID. Once
        # lost, the lease is permanently revoked, even if Windows reuses PID.
        if not self.closed:
            try:
                self.closed = not self.process.is_running()
            except psutil.NoSuchProcess:
                self.closed = True
        if self.closed:
            raise EmulatorClosed('The launcher emulator has closed; its watcher will exit.')

    def revoke(self):
        self.closed = True
