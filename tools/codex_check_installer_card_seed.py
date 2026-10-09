"""Exercise complete card seeding and repair without imports, runner or installed data."""
import ast,json,os,runpy,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='bt3-complete-card-') as tmp:
    root=Path(tmp);previous=os.environ.get('BT3_TAGTEAM_DATA');os.environ['BT3_TAGTEAM_DATA']=str(root/'data')
    try:scope=runpy.run_path(str(HERE/'installer/app.pyw'),run_name='card_seed_test')
    finally:
        if previous is None:os.environ.pop('BT3_TAGTEAM_DATA',None)
        else:os.environ['BT3_TAGTEAM_DATA']=previous
    seed=scope['seed_progression'];g=seed.__globals__;app=root/'package';app.mkdir();g['APP']=app
    (app/'save-card').mkdir()
    source=HERE/'savedata/BASLUS-21678DBZT3'
    auxiliary={name:(source/name).read_bytes() for name in ('icon.sys','dbzsm.ico')}
    for name,content in auxiliary.items():(app/'save-card'/name).write_bytes(content)
    unlocked=(source/'BASLUS-21678DBZT3').read_bytes()
    fresh=(HERE/'power-scale-trial/save-backups/20261005-104334/BASLUS-21678DBZT3/BASLUS-21678DBZT3').read_bytes()
    (app/'default-save.bin').write_bytes(unlocked);(app/'fresh-save.bin').write_bytes(fresh)
    for choice in (False,True):
        data=root/str(choice);data.mkdir();g['DATA']=data
        settings={'schema':1,'all_unlocked':choice};choice_file=data/'save-start-choice.json';choice_file.write_text(json.dumps(settings))
        seed();card=data/'saves/progression/BASLUS-21678DBZT3';main=card/'BASLUS-21678DBZT3'
        assert main.read_bytes()==(unlocked if choice else fresh)
        for name,content in auxiliary.items():assert (card/name).read_bytes()==content
        assert set(p.name for p in card.iterdir())=={'BASLUS-21678DBZT3','icon.sys','dbzsm.ico'}
        # Recreate the old incomplete layout: real player progress, one custom
        # companion, and one missing companion. Only the missing one is repaired.
        main.write_bytes(b'player progress must survive upgrade')
        (card/'icon.sys').write_bytes(b'existing custom card icon metadata')
        (card/'dbzsm.ico').unlink()
        preserved={p:(p.read_bytes(),p.stat().st_mtime_ns) for p in (main,card/'icon.sys',choice_file)}
        seed()
        for p,(content,mtime) in preserved.items():assert p.read_bytes()==content and p.stat().st_mtime_ns==mtime
        assert (card/'dbzsm.ico').read_bytes()==auxiliary['dbzsm.ico']
        full={p:(p.read_bytes(),p.stat().st_mtime_ns) for p in card.iterdir()};seed()
        for p,(content,mtime) in full.items():assert p.read_bytes()==content and p.stat().st_mtime_ns==mtime
    # Validate actual staging wiring without executing its costly mutations.
    tree=ast.parse((HERE/'codex_stage_initial_installer.py').read_text())
    loops=[n for n in tree.body if isinstance(n,ast.For) and isinstance(n.iter,ast.Tuple) and [getattr(e,'value',None) for e in n.iter.elts]==['icon.sys','dbzsm.ico']]
    assert len(loops)==1
    lines=ast.unparse(loops[0]);assert "HERE / 'savedata/BASLUS-21678DBZT3' / name" in lines and "OUT / 'save-card' / name" in lines
print('PASS: both complete seeds; existing progress, companion files, mtimes and choice preserved; missing-only companion repair; actual staging wiring.')
