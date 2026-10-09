"""Reversible mute of only the isolated PCSX2 audio sessions during loading.

No endpoint/master volume API is used. Original per-session mute values are
recorded before changes; an independent helper-death watchdog restores them.
Windows/COM access is lazy so all ownership tests run without touching audio.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path
from atomic_files import read_json, write_json, unlink

ROOT = Path(__file__).resolve().parents[1]
WHEEL = ROOT/'tools/vendor-wheels/pycaw-20251023-py3-none-any.whl'
WINDOWS = os.name == 'nt'
RECEIPT = ROOT/'analysis/loading-audio-restore.json'


class WindowsAudio:
    def __init__(self):
        sys.path.insert(0, str(WHEEL))
        import comtypes
        import psutil
        from pycaw.utils import AudioUtilities, AudioSession
        from pycaw.api.audiopolicy import IAudioSessionControl2, IAudioSessionManager2
        self.comtypes, self.psutil = comtypes, psutil
        self.utilities, self.session = AudioUtilities, AudioSession
        self.control, self.manager = IAudioSessionControl2, IAudioSessionManager2

    def sessions(self, executable):
        wanted = os.path.normcase(str(Path(executable).resolve()))
        result = []
        enum = self.utilities.GetDeviceEnumerator()
        devices = enum.EnumAudioEndpoints(0, 1)  # active render endpoints only
        for i in range(devices.GetCount()):
            device = devices.Item(i)
            interface = device.Activate(self.manager._iid_, self.comtypes.CLSCTX_ALL, None)
            sessions = interface.QueryInterface(self.manager).GetSessionEnumerator()
            for j in range(sessions.GetCount()):
                session = self.session(sessions.GetSession(j).QueryInterface(self.control))
                pid = session.ProcessId
                if not pid: continue
                try:
                    process = self.psutil.Process(pid)
                    if os.path.normcase(process.exe()) != wanted: continue
                    result.append(dict(pid=pid, created=process.create_time(),
                        instance=session.InstanceIdentifier, identifier=session.Identifier,
                        volume=session.SimpleAudioVolume))
                except (self.psutil.NoSuchProcess, self.psutil.AccessDenied):
                    continue
        return result


class AudioMute:
    def __init__(self, executable, receipt=RECEIPT, backend=None):
        self.executable, self.receipt = Path(executable).resolve(), Path(receipt)
        self.backend = backend; self.records = {}
        if self.receipt.exists():
            saved = read_json(self.receipt)
            if Path(saved['executable']).resolve() != self.executable:
                raise ValueError('Audio recovery receipt belongs to another executable')
            self.records = saved['sessions']

    def _sessions(self):
        if self.backend is None:
            if not WINDOWS:
                # PipeWire/PulseAudio muting (pactl) is deferred: a crash could leave PCSX2 muted.
                raise RuntimeError('Loading audio muting uses Windows audio sessions; it is off on this system')
            self.backend = WindowsAudio()
        return self.backend.sessions(self.executable)

    def _save(self):
        self.receipt.parent.mkdir(parents=True, exist_ok=True)
        if not self.records:
            unlink(self.receipt); return
        write_json(self.receipt, dict(executable=str(self.executable), sessions=self.records))

    def mute(self, pid):
        for session in self._sessions():
            if session['pid'] != pid: continue
            key = session['instance']
            record = self.records.get(key)
            if record is None:
                record = {k: session[k] for k in ('pid', 'created', 'instance', 'identifier')}
                record['muted'] = bool(session['volume'].GetMute())
                record['applied'] = False
                self.records[key] = record
                self._save()  # Preserve original state before the first mutation.
            elif record['pid'] != session['pid'] or record['created'] != session['created']:
                continue
            if record.get('applied', False): continue
            session['volume'].SetMute(1, None)
            record['applied'] = True
            self._save()

    def restore(self):
        if not self.records: return True
        for session in self._sessions():
            record = self.records.get(session['instance'])
            if record is None: continue
            if record['pid'] != session['pid'] or record['created'] != session['created']:
                continue  # PID/session reuse is never permission to alter it.
            session['volume'].SetMute(int(record['muted']), None)
            del self.records[session['instance']]
            self._save()
        return not self.records

    def unmute(self, pid):
        """Keep this launch's PCSX2 audio session audible, even if Windows inherited a mute."""
        found = False
        for session in self._sessions():
            if session['pid'] != pid: continue
            found = True
            if session['volume'].GetMute(): session['volume'].SetMute(0, None)
        return found


def recover(executable, receipt=RECEIPT, timeout=5):
    controller = AudioMute(executable, receipt)
    deadline = time.monotonic()+timeout
    while True:
        try:
            if controller.restore(): return True
        except Exception as error:
            print(f'Audio restore is pending: {error}', flush=True)
        if time.monotonic() >= deadline: return False
        time.sleep(.2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--watch', type=int, required=True)
    parser.add_argument('--emulator', required=True, type=Path)
    parser.add_argument('--receipt', type=Path, default=RECEIPT)
    args = parser.parse_args()
    from presentation_settings import wait_process
    wait_process(args.watch)
    recover(args.emulator, args.receipt)
