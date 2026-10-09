"""Offline check of v11 structured failures against the native cover adapter."""
from contextlib import redirect_stdout
from io import StringIO

from codex_native_ui_adapter import Presentation


def check(phase='idle', accepted=False):
    presentation = Presentation()
    surface = presentation.guest
    surface.phase = phase
    surface.accepted = accepted
    surface.available = True
    calls = []
    surface.begin = lambda: calls.append('begin')
    surface.send = lambda action: calls.append(action)
    with redirect_stdout(StringIO()) as log:
        result = presentation.show(
            'Error', 'No se pudo preparar la partida', 100,
            error=('No se pudo preparar la partida', 'Vuelve a iniciar el juego'),
        )
    assert result is True
    assert 'Vuelve a iniciar el juego' in log.getvalue()
    if accepted or phase == 'released':
        assert calls == [], calls
        assert surface.phase == phase
        assert surface.visible is False
    else:
        assert calls == ['begin', 5], calls
        assert surface.phase == 'failed'
        assert surface.visible is True


if __name__ == '__main__':
    check()
    check('ready', accepted=True)
    check('released')
    print('PASS: structured localized failures use native cover; active matches remain uncovered')
