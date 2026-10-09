"""Claude: arm the HUD capture when the battle clock reaches a target value (read-only polling, tiny reads).
Usage: claude_clock_watch.py <target_seconds> [lo]   -> triggers when lo <= clock <= target (default lo=target).
Only for the diagnostic launcher (no controller attached)."""
import sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
TRIAL = HERE / 'power-scale-trial'
sys.path.insert(0, str(TRIAL / 'controller/game/tools'))
import pine

target = int(sys.argv[1])
lo = int(sys.argv[2]) if len(sys.argv) > 2 else target
ADDRS = (0x188876C, 0x1888770, 0x188B0B4)
trigger = TRIAL / 'hud-native-capture' / 'capture.trigger'
if trigger.exists():
    trigger.unlink()   # a previous capture's trigger would block re-arming
print('watching clock for', lo, '..', target, flush=True)
last = None
while True:
    try:
        with pine.PineClient(port=28012, timeout=2) as p:
            vals = [p.read_u32(a) for a in ADDRS]
        if vals != last:
            print(time.strftime('%H:%M:%S'), 'clock words', vals, flush=True)
            last = vals
        if vals[0] == vals[1] and lo <= vals[0] <= target:
            trigger.parent.mkdir(parents=True, exist_ok=True)
            trigger.write_text('go')
            print(time.strftime('%H:%M:%S'), 'TRIGGERED at clock', vals[0], flush=True)
            break
    except (OSError, pine.PineError):
        time.sleep(0.5)
    time.sleep(0.05)
