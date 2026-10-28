from pathlib import Path
import json,html,shutil
W=Path('F:/BT3-Builds/Tag Team Mod Installer 2');O=Path('F:/BT3-Builds/pc-release-v041');P=O/'payload';R=O/'release';R.mkdir(exist_ok=True)
profile=json.loads((P/'release-profile.json').read_text());sources=[
('Original Power Scale BETA 8','f4afdfd366e376e0e8b813729aa7a8b103fca4e7b88a338ee3ad32cca16639f1'),
('R4 + Random Select + 38 stages + Goku/Gohan, 2x','258d8b943c9e2b646ce87c77c26534bf6a22339d2727a1b8dd59c99b449a0a92'),
('R4 + Random Select + 38 stages + Goku/Gohan, normal','3039ac351ad07079d78d17dca6e6aa3a4aec40c60d3aeb47bda8cbb1520cb8f1')]
credits=json.loads((P/'assets/credits-v04/credits.json').read_text())
for lang in ['EN','ES']:
 es=lang=='ES';parts=['<!doctype html><html lang="'+lang.lower()+'"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BT3 Tag Team 0.4.1</title><style>body{font:18px/1.6 system-ui;background:#0d111a;color:#f5f0e8;max-width:1000px;margin:30px auto;padding:0 24px}h1,h2,a{color:#ffcf55}code{overflow-wrap:anywhere}li{margin:10px 0}</style><h1>BT3 Tag Team + Real Power Scale — 0.4.1</h1>']
 blocks=[('Instalación'if es else'Installation',[
 'Ejecuta el instalador de Windows de 64 bits. Elige una carpeta con espacio suficiente; no se necesita Python ni BIOS por separado.'if es else'Run the 64-bit Windows installer. Choose a folder with enough free space; no separate Python or BIOS is needed.',
 'Elige mapas normales o 2x. Ambas opciones conservan las mismas correcciones. Puedes activar los ajustes recomendados y la partida con contenido desbloqueado.'if es else'Choose normal or 2x maps. Both retain the same fixes. You can enable recommended settings and an unlocked starting save.',
 'Abre Play.exe, elige una ISO compatible de la lista inferior y espera a que termine la importación. La ISO original no se modifica. Se necesitan aproximadamente 8 GB libres para los datos, además de la aplicación.'if es else'Open Play.exe, choose a supported ISO from the list below and wait for import to finish. Your original ISO is not changed. Allow about 8 GB free for game data, in addition to the application.',
 'El juego utiliza archivos extraídos: no necesita conservar una segunda ISO de 8 GB. El tamaño elegido se aplica durante la importación.'if es else'The game uses extracted files, so it does not need to keep a second 8 GB ISO. Your map-size choice is applied during import.']),
 ('Controles y opciones'if es else'Controls and settings',[
 'F1 o Select > Ajustes abre la configuración del mod. Cuadrado guarda; los ajustes y el progreso existentes no se reemplazan al reinstalar.'if es else'F1 or Select > Settings opens mod settings. Square saves; existing settings and progress are kept on reinstall.',
 'La configuración recomendada alterna el control de una fusión entre sus jugadores cada 10 segundos. Se puede cambiar en Fusion.'if es else'Recommended fusion controls alternate the participating players every 10 seconds. Change this under Fusion settings.',
 'Incluye batallas en equipo, cooperativo, entrenamiento, espectador, torneo de equipos, fusión/desfusión, reanimación y asistencias de rayos, choques y ataques definitivos. Escenarios sigue marcado como Próximamente.'if es else'Includes Team Battle, co-op, training, spectating, team tournament, fusion/defusion, revival and beam/rush/ultimate assists. Scenarios remains marked Coming soon.',
 'Revisa los jugadores, mandos y teclado en Controles. Los créditos están en Sistema > Créditos y agradecimientos y en Acerca de.'if es else'Check player, controller and keyboard assignments under Controls. Credits are under System > Credits and thanks, and About.']),
 ('Datos y ayuda'if es else'Data and support',[
 'Los archivos importados, registros, ajustes y partidas están en data dentro de la instalación. Un archivo data-root.txt permite elegir otra ubicación. No borres saves para cambiar los mapas.'if es else'Imported data, logs, settings and saves live in the installation’s data folder. A data-root.txt file can select another location. Do not delete saves to change maps.',
 'Para preparar otra variante, usa una carpeta de instalación/datos nueva y conserva tus partidas. La reinstalación no cambia una importación ya completada.'if es else'To prepare another map variant, use a fresh installation/data folder and keep your saves. Reinstalling does not change an already completed import.',
 'Si el juego no inicia, consulta data/launcher.log y data/game.log. No uses archivos ejecutables ni controladores de la versión antigua con este port.'if es else'If launch fails, check data/launcher.log and data/game.log. Do not mix this port with executable/controller files from the older version.',
 'La versión Android se publica por separado. No se incluye un APK en este instalador.'if es else'Android is published separately. This installer does not bundle an APK.'])]
 for title,rows in blocks:parts+=['<h2>'+title+'</h2><ol>']+['<li>'+html.escape(x)+'</li>'for x in rows]+['</ol>']
 parts+=['<h2>ISO SHA256</h2><ul>']+['<li>'+html.escape(name)+'<br><code>'+h+'</code></li>'for name,h in sources]+['</ul><h2>Créditos / Credits</h2>']
 parts+=['<p>'+html.escape(c['role_es']if es and'role_es'in c else c['role'])+': <a href="'+html.escape(c['url'])+'">'+html.escape(c['name'])+'</a></p>'for c in credits['contributors']]
 parts+=['<p>'+html.escape(credits['thanks']['es'if es else'en'])+'</p></html>'];(P/'manual'/('BT3-TagTeam-Manual-'+lang+'.html')).write_text(''.join(parts),encoding='utf-8')
readme='''BT3 Tag Team + Real Power Scale v0.4.1 — Windows native port

Run the Windows Setup, then Play.exe. Bring your own supported Power Scale BETA 8 ISO; choose normal or 2x maps during preparation. Both retain the current fixes. No separate BIOS, emulator, Python or compiler is required.

Existing saves/settings are preserved. Recommended fusion control alternates players every 10 seconds. Manuals in English/Spanish are installed under manual/. Credits and special thanks appear during import/startup and in mod settings.

This is the new Tenkaichi3Decomp-based port. Do not mix with the older BT3-Recomp/controller installer. Android is a separate release maintained by Claude.

Installer/source: https://github.com/Pyrosea98/BT3-TagTeam-Native
Native code: https://github.com/Pyrosea98/BT3-TagTeam-Runtime/tree/decomp-native
Upstream: https://github.com/z3xox/Tenkaichi3Decomp
Tag Team: https://github.com/tehmufti/Budokai-Tenkaichi-3-Tag-Team-Mod-PCSX2-
RidJuampa: https://www.youtube.com/@RidJuampa

No ISO, BIOS or full game archives are distributed. Content is reconstructed from the authenticated user ISO using verified binary deltas. Component licenses are installed under licenses/.
'''
(R/'README.txt').write_text(readme,encoding='utf-8');(P/'README-TagTeam.txt').write_text(readme,encoding='utf-8')
notes='''## Native PC release

This release moves the PC installer to our current Tenkaichi3Decomp-based Tag Team / Real Power Scale build. The previous v0.4 release remains available for the older runtime.

- Normal-size and optional 2x maps, selected before ISO import; both retain the same character, costume, fusion and menu fixes.
- Current team/co-op/training/tournament, CPU, transformation/fusion/defusion/revival and controller-selection work.
- Beam, rush and ultimate assists, configurable damage behavior, rush-team knockback and charged-smash cinematic QTE.
- Updated mod HUD/portraits/chips, shared credits and thank-you screens, corrected RidJuampa name/channel and singular thanks.
- Recommended-settings checkbox, completed-save choice, English/Spanish manuals and preservation of existing progress/settings.
- Portable embedded installer dependencies; no separate BIOS, emulator, Python or compiler required.

Use an authenticated supported Power Scale BETA 8 ISO. The installer never changes the input ISO. Import produces loose game data, not a bundled disc image. See the installed manual for supported SHA256 identities.

Android is published separately by Claude; no APK is bundled here.

### Validation
Full native Linux/Windows regression checks and source guards pass. Release validation receipts cover reconstruction hashes for both map variants and the installer checks. See the published verification summary for exact scope; automated checks do not claim new controller/device live coverage.

### Source and attribution
Native code: https://github.com/Pyrosea98/BT3-TagTeam-Runtime/tree/decomp-native. Installer: https://github.com/Pyrosea98/BT3-TagTeam-Native. Engine upstream z3xox/Tenkaichi3Decomp; original Tag Team work by The Mufti; Power Scale by LetsPlayBt3; special thanks to RidJuampa for helping me understand the code (https://www.youtube.com/@RidJuampa). Preserve included licenses/notices.
'''
(R/'RELEASE_NOTES.md').write_text(notes,encoding='utf-8')
shutil.copy2(P/'runtime/Lib/site-packages/pillow-12.3.0.dist-info/licenses/LICENSE',P/'licenses/pillow.txt')
# CPython includes its license in the standard library on this embedded build.
for candidate in [P/'runtime/LICENSE.txt',P/'runtime/Lib/LICENSE.txt',Path('C:/Python312/LICENSE.txt')]:
 if candidate.is_file():shutil.copy2(candidate,P/'licenses/python.txt');break
print('Prepared bilingual manuals, source/credit links, attribution and release notes')
