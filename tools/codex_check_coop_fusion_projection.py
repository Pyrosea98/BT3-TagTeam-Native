"""Actual native projection helpers on saved fighter skeletons; no game loop."""
import os
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
runner=HERE/'repo/build/ps2xRuntime/ps2EntryRunner-coop-scene-fusion.exe'
capture=HERE/'power-scale-trial/controller/game/analysis/prepared-states/20261007-201319-d7ac1d61/16-ready-held.bin'
env=os.environ.copy();env['PS2X_COOP_FUSION_PROJECTION_CHECK']='1'
result=subprocess.run([str(runner),'--native-overhead-self-test',str(capture)],env=env,capture_output=True,text=True,timeout=45)
print(result.stdout+result.stderr,end='')
print('Native fixture exit:',result.returncode)
assert result.returncode==0
env.pop('PS2X_COOP_FUSION_PROJECTION_CHECK')
baseline=subprocess.run([str(runner),'--native-overhead-self-test',str(capture)],env=env,capture_output=True,text=True,timeout=45)
print(baseline.stdout+baseline.stderr,end='')
assert baseline.returncode==0
