"""Claude: find the battle clock word in EE RAM with three whole-RAM reads while a fight is running (read-only).
Only run this when no controller is attached (the diagnostic launcher has none)."""
import sys, time, struct, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
TRIAL = HERE / 'power-scale-trial'
sys.path.insert(0, str(TRIAL / 'controller/game/tools'))
import pine
import native_preparation as native
import numpy as np

dumps = []
stamps = []
for i in range(3):
    with pine.PineClient(port=28012, timeout=120) as p:
        t0 = time.time()
        ram = native.read_ram(p)
        stamps.append((t0, time.time()))
    dumps.append(np.frombuffer(ram, dtype='<u4').copy())
    print('dump', i, 'took', round(stamps[-1][1] - stamps[-1][0], 1), 's', flush=True)
    if i < 2:
        time.sleep(2)
a, b, c = dumps
mid = [(s[0] + s[1]) / 2 for s in stamps]
dt1, dt2 = mid[1] - mid[0], mid[2] - mid[1]
print('mid-time gaps', round(dt1, 1), round(dt2, 1), flush=True)
# candidate: strictly decreasing, small positive steps, roughly proportional to elapsed time
d1 = a.astype(np.int64) - b.astype(np.int64)
d2 = b.astype(np.int64) - c.astype(np.int64)
mask = (d1 > 0) & (d2 > 0) & (a < 100000) & (a > 0)
idx = np.nonzero(mask)[0]
cands = []
for i in idx:
    r1 = d1[i] / dt1
    r2 = d2[i] / dt2
    if r1 > 0 and abs(r1 - r2) / max(r1, r2) < 0.25:
        cands.append((int(i) * 4, int(a[i]), int(b[i]), int(c[i]), round(r1, 2), round(r2, 2)))
print('candidates', len(cands))
cands.sort(key=lambda x: abs(x[4] - 60))
for x in cands[:25]:
    print('addr 0x%X values %d %d %d  rate/s %s %s' % x)
json.dump(cands, open(TRIAL / 'clock-candidates.json', 'w'))
