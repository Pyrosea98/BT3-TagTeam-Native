"""Exercise real app initialization: install language, upgrade preservation."""
import json,os,runpy,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='bt3-lang-',dir=HERE/'installer') as temporary:
    folder=Path(temporary)
    for selected in ('en','es','invalid'):
        app=folder/selected;app.mkdir();data=app/'data'
        (app/'app.pyw').write_bytes((HERE/'installer/app.pyw').read_bytes())
        (app/'install-language.txt').write_text(selected)
        resource=app/'resources/native-port';game=resource/'power-scale-trial/controller/game';game.mkdir(parents=True)
        (resource/'source-build.json').write_text(json.dumps({'revision':'first'}))
        (game/'mod-settings.json').write_text(json.dumps({'language':'en','custom_marker':'default'}))
        previous=os.environ.get('BT3_TAGTEAM_DATA');os.environ['BT3_TAGTEAM_DATA']=str(data)
        try:scope=runpy.run_path(str(app/'app.pyw'),run_name='language_test')
        finally:
            if previous is None:os.environ.pop('BT3_TAGTEAM_DATA',None)
            else:os.environ['BT3_TAGTEAM_DATA']=previous
        expected=selected if selected in ('en','es') else 'en'
        assert scope['LANG']==expected
        scope['initialize']()
        actual=data/'native-port/power-scale-trial/controller/game/mod-settings.json'
        values=json.loads(actual.read_text());assert values['language']==expected
        # Selecting another installer language must not override the player.
        kept='es' if expected=='en' else 'en'
        values.update(language=kept,custom_marker='player');actual.write_text(json.dumps(values))
        (app/'install-language.txt').write_text(expected)
        (resource/'source-build.json').write_text(json.dumps({'revision':'upgrade'}))
        scope['initialize']();assert json.loads(actual.read_text())==values
        assert scope['saved_language'](data,expected)==kept
for name in ('initial.iss','preview-current.iss'):
    source=(HERE/'installer'/name).read_text(encoding='utf-8')
    assert 'LicenseFile=credits.txt' not in source
    assert 'LicenseFile: "terms-en.txt"' in source and 'LicenseFile: "terms-es.txt"' in source
    entries=source.split('[Run]\n',1)[1].split('\n[',1)[0].strip().splitlines()
    assert len(entries)==2
    assert all('postinstall' in entry and 'skipifsilent' in entry and 'unchecked' in entry for entry in entries)
    assert 'shellexec' in entries[0] and 'nowait' in entries[1]
    assert "Locale := 'ES' else Locale := 'EN'" in source
    assert 'Name: "{app}\\install-language.txt"' in source
    assert '{cm:ManualShortcut}' in source
print('PASS: EN/ES fresh data, invalid language fallback, real initialize upgrade preserves settings; localized terms, manual path, two unchecked silent-safe finish choices.')
