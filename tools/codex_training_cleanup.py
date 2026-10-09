"""Request verified cleanup on the guest thread before taking a fresh image."""
import os
import time

CONTROL = 0x07FFF100
MAGIC = 0x4E524D31

def recover(p, timeout=10):
    if os.environ.get('PS2X_NATIVE_FRESH_CLEANUP') != '1':
        return False
    if p.read_u32(CONTROL) != MAGIC:
        return False
    if p.read_u32(CONTROL+4) != 0:
        raise RuntimeError('Fresh cleanup requires a completed native teardown')
    if p.read_u32(CONTROL+8) not in (1, 2):
        return False # First match: no teardown receipt to consume.
    p.write_u32(CONTROL+28, 0)
    p.write_u32(CONTROL+4, 8)
    deadline = time.monotonic()+timeout
    while time.monotonic() < deadline:
        if p.read_u32(CONTROL) != MAGIC:
            raise RuntimeError('Fresh cleanup mailbox ownership changed')
        state = p.read_u32(CONTROL+4)
        if state == 9:
            error = p.read_u32(CONTROL+28)
            p.write_u32(CONTROL+4, 0)
            if error:
                raise RuntimeError(f'Native fresh cleanup refused unknown or live heap ownership: {error}')
            return True
        if state != 8:
            raise RuntimeError(f'Fresh cleanup state changed: {state}')
        time.sleep(.02)
    raise TimeoutError('Native fresh cleanup was not acknowledged; match was not prepared')

def install(session):
    original = session.snapshot
    def snapshot(self, label, *args, **kwargs):
        if label == 'original-selected-match' and getattr(self, 'native_runtime', False):
            with self.client() as p:
                recover(p)
        return original(self, label, *args, **kwargs)
    session.snapshot = snapshot
