"""Scoped Power Scale family tiers; retain reversal/cross-family admission."""
from pathlib import Path
import sys
from unittest.mock import patch

sandbox=Path(sys.argv[1]).resolve()
sys.path[:0]=[str(sandbox),str(sandbox/'power-scale-trial/controller/game/tools')]
from codex_roster_overlay import install
install()
import cpu_tactics as tactics
import game_profile

profile={'runtime_variant':'BT3 Power Scale BETA 1.5.1 (experimental)'}
with patch.object(game_profile,'installed',return_value=profile):
    tiers,families=tactics.tables()
    for forms in tactics.POWER_SCALE_TRIAL_FAMILIES:
        assert len({families[cid] for cid in forms})==1 and families[forms[0]]
        assert [tiers[cid] for cid in forms]==list(range(len(forms)))
        for source in forms:
            for dest in forms:
                allowed=families[source]==families[dest] and tiers[dest]>tiers[source]
                assert allowed==(forms.index(dest)>forms.index(source))
    assert len({families[forms[0]] for forms in tactics.POWER_SCALE_TRIAL_FAMILIES})==3
    assert families[60]!=families[119] and families[60]!=families[67]
for other in (None,{'runtime_variant':'another disc'}):
    with patch.object(game_profile,'installed',return_value=other):
        _,families=tactics.tables()
        assert all(families[cid]==0 for forms in tactics.POWER_SCALE_TRIAL_FAMILIES for cid in forms)
print('PASS: three scoped Power Scale trial families, strictly upward tiers, distinct families, absent/wrong-profile exclusion')
