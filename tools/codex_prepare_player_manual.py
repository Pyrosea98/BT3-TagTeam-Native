"""Prepare current player-facing copies without editing Claude's draft manuals."""
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
OUT = HERE / 'installer/payload/manual'
OUT.mkdir(parents=True, exist_ok=True)
changes = {
    'EN': [
        ('press the menu switch button on the original main menu', 'press Select (the default menu switch button) on the original main menu'),
        ('Fusion between Goku Black (Rose) and Zamasu may not start yet, and Super Goku and Super Vegeta may not pair with each other yet.', 'Base Super Goku/Vegeta and Black Ros&eacute;/Zamasu fusions have succeeded in live tests. The Black/Zamasu cinematic may show only the initiating fighter. Other transformed-form pairings remain unverified.'),
        ('CPU fusion always picks the same result for a pair (for example Vegito); a choice between results is planned.', 'CPU fusion now rotates eligible native choices (for example Dance and Potara) when the original AI starts a fusion. It does not force a CPU to fuse; live acceptance remains pending.'),
        ('The loading cover between the mod menu and character select and the 2-player setup screen are being fixed.', 'The decorative mode loading cover is unavailable and its setting is hidden. If a multiplayer setup screen is invisible, stop and report it rather than confirming selections blindly.</li><li>Three- and four-human play is experimental: real P3/P4 controller input has not been tested.</li><li>A second-match crash at 0x216661A8 remains unresolved. Restart the game if it occurs.</li><li>Failed match preparation now requests a clean game/controller restart. The installed FFA 3v4 start failure remains undiagnosed; automatic recovery has been checked offline, not in a live installed match.'),
        ('loading animation speed, the decorative loading cover.', 'loading animation speed.'),
        ('Some options inherited from the emulator version (widescreen patch, fast disc loading, emulated CPU speed) do not apply to this build.', 'Emulator-only controls (widescreen patch, fast disc loading and emulated CPU speed) are hidden. Use the native display settings for resolution and aspect ratio.'),
        ('Everything the game creates (imported data, saves, settings, logs) is inside', 'For new installations, everything the game creates (imported data, saves, settings, logs) is inside'),
        ('the logs do not contain personal paths.', 'review logs for personal paths before sharing them.'),
        ('5v5 currently runs around 20 to 30 updates per second on a Ryzen 5700G; small matches reach 60.', 'Performance depends on the machine, arena and fighter count; large simultaneous matches are more demanding.'),
    ],
    'ES': [
        ('pulsa el bot&oacute;n de cambio de men&uacute; del men&uacute; principal original', 'pulsa Select (el bot&oacute;n predeterminado para cambiar de men&uacute;) en el men&uacute; principal original'),
        ('El 5v5 funciona ahora a unas 20 a 30 actualizaciones por segundo en un Ryzen 5700G; las partidas peque&ntilde;as llegan a 60.', 'El rendimiento depende del equipo, el escenario y el n&uacute;mero de luchadores; las partidas simult&aacute;neas grandes exigen m&aacute;s recursos.'),
        ('La fusi&oacute;n entre Goku Black (Rose) y Zamasu puede no iniciarse a&uacute;n, y Super Goku y Super Vegeta pueden no emparejarse entre s&iacute; todav&iacute;a.', 'Las fusiones de Goku/Vegeta de Super en forma base y Black Ros&eacute;/Zamasu funcionaron en pruebas en juego. La cinem&aacute;tica de Black/Zamasu puede mostrar solo al luchador que inicia la fusi&oacute;n. Otras parejas de formas transformadas siguen sin verificar.'),
        ('La fusi&oacute;n de la CPU elige siempre el mismo resultado para una pareja (por ejemplo Vegetto); est&aacute; prevista una elecci&oacute;n entre resultados.', 'La CPU alterna entre las opciones nativas disponibles cuando la IA original inicia una fusi&oacute;n. No obliga a la CPU a fusionarse; la prueba en juego sigue pendiente.'),
        ('La cubierta de carga entre el men&uacute; del mod y la selecci&oacute;n de personajes y la pantalla de preparaci&oacute;n de 2 jugadores se est&aacute;n corrigiendo.', 'La cubierta decorativa de carga no est&aacute; disponible y su ajuste est&aacute; oculto. Si la preparaci&oacute;n multijugador no es visible, detente y rep&oacute;rtalo en vez de confirmar a ciegas.</li><li>El juego con tres o cuatro personas es experimental: no se ha probado la entrada de mandos reales P3/P4.</li><li>Sigue pendiente un cierre de la segunda partida en 0x216661A8. Reinicia el juego si ocurre.</li><li>Si falla la preparaci&oacute;n, se solicita un reinicio limpio del juego y del controlador. La causa del fallo de inicio FFA 3v4 instalado sigue sin diagnosticar; la recuperaci&oacute;n se comprob&oacute; fuera del juego, no en una partida instalada.'),
        ('velocidad de la animaci&oacute;n de carga, la cubierta decorativa de carga.', 'velocidad de la animaci&oacute;n de carga.'),
        ('Algunas opciones heredadas de la versi&oacute;n de emulador (parche panor&aacute;mico, carga r&aacute;pida del disco, velocidad de CPU emulada) no se aplican a esta versi&oacute;n.', 'Los ajustes exclusivos del emulador (parche panor&aacute;mico, carga r&aacute;pida del disco y velocidad de CPU emulada) est&aacute;n ocultos. Usa los ajustes nativos de pantalla para la resoluci&oacute;n y la relaci&oacute;n de aspecto.'),
        ('los registros no contienen rutas personales.', 'revisa si los registros contienen rutas personales antes de compartirlos.'),
    ],
}
for lang in ('EN', 'ES'):
    text = (HERE / f'manual/BT3-TagTeam-Manual-{lang}.html').read_text(encoding='utf-8')
    for old, new in changes[lang]:
        assert old in text, f'Manual draft changed: {lang}: {old}'
        text = text.replace(old, new)
    # Avoid a section heading stranded at the bottom of a page.
    text = text.replace('break-after: avoid;', 'break-after: avoid; page-break-after: avoid;')
    (OUT / f'BT3-TagTeam-Manual-{lang}.html').write_text(text, encoding='utf-8')
node = Path.home() / '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
subprocess.run([str(node), str(HERE / 'codex_render_player_manual.cjs')], check=True)
print('Prepared localized HTML/PDF player guides with current preview status')
