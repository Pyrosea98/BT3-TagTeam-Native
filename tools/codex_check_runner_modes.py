"""Launcher compatibility checks; no sockets, logs or game process."""
from run_power_scale_native import runner_modes

baseline='ps2EntryRunner-native-embedded-baseline.exe'
roster='ps2EntryRunner-native-roster.exe'
rematch='ps2EntryRunner-native-rematch.exe'
enabled={'PS2X_NATIVE_REMATCH':'1','PS2X_POWER_SCALE_ROSTER':'1'}
for name in (baseline,roster):
    assert runner_modes(name,False,{})==(True,True)
    assert runner_modes(name,False,enabled)==(True,True)
    assert runner_modes(name,False,{'PS2X_NATIVE_REMATCH':'0','PS2X_POWER_SCALE_ROSTER':'0'})==(False,False)
    assert runner_modes(name,True,{})==(False,False)
assert runner_modes(rematch,False,{})==(True,False)
assert runner_modes('ps2EntryRunner-interp-hooks.exe',True,{})==(False,False)
for name,no_controller,environment in (
    (baseline,True,enabled),
    (rematch,False,enabled),
    ('ps2EntryRunner.exe',False,{'PS2X_NATIVE_REMATCH':'1'}),
    ('unknown.exe',False,enabled),
):
    try:runner_modes(name,no_controller,environment)
    except ValueError:pass
    else:raise AssertionError('Incompatible runner/controller accepted')
print('PASS: baseline accepted; defaults/overrides and incompatible combinations checked')
