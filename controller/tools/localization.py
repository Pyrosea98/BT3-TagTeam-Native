"""Mod-authored text only. Stable settings keys, ISO names and code stay untouched.

Host presentation reads the saved choice at most twice a second. Builders and
tests can use ``using`` to freeze the language for a whole generated artifact.
Guest text uses the existing ASCII atlas; host-rendered menus keep accents.
"""
from contextlib import contextmanager
from contextvars import ContextVar
import json
import os
from pathlib import Path
import re
import time
import unicodedata

LANGUAGES = ('en', 'es')
WINDOWS = os.name == 'nt'
# Translate from stable English keys first, then show the actual installed
# launcher names. Windows text/pixels remain identical; formatted user paths
# are inserted afterward and must never have their extensions rewritten.
LINUX_SCRIPT_NAMES = {
    'Mod settings.cmd': 'Mod settings.sh',
    'Build expanded maps.cmd': 'Build expanded maps.sh',
    'Play (any teams).cmd': 'Play.sh',
    'Play.cmd': 'Play.sh',
    'Check installation.cmd': 'Check installation.sh',
    'Scan compatibility.cmd': 'Scan compatibility.sh',
}
NAMES = {'en': 'English', 'es': 'Español'}
SETTINGS = Path(__file__).resolve().parents[1] / 'mod-settings.json'
_override = ContextVar('mod_language', default=None)
_cached = ('en', 0.0)
_battle_language = None


def pin_battle(settings):
    """Generated match code keeps its language until the next preparation.

    Editing desktop preferences mid-match must not change the byte sequences
    that runtime ownership guards expect from already-installed guest programs.
    Host menus remain free to preview the newly selected language.
    """
    global _battle_language
    _battle_language = language(settings)


def language(settings=None):
    if settings is not None:
        value = settings.get('language', 'en') if isinstance(settings, dict) else settings
        return value if value in LANGUAGES else 'en'
    if _override.get() is not None:
        return _override.get()
    global _cached
    now = time.monotonic()
    if now >= _cached[1]:
        try:
            value = json.loads(SETTINGS.read_text(encoding='utf-8-sig')).get('language', 'en')
        except (OSError, ValueError, AttributeError):
            value = 'en'
        _cached = (value if value in LANGUAGES else 'en', now + .5)
    return _cached[0]


def invalidate():
    global _cached
    _cached = ('en', 0.0)


@contextmanager
def using(settings):
    token = _override.set(language(settings))
    try:
        yield
    finally:
        _override.reset(token)


ES = {
    'Enable manual lock-off': 'Permitir quitar el objetivo manualmente',
    'Lock-off button': 'Botón para quitar el objetivo',
    'Target HUD while unlocked': 'Interfaz del objetivo sin fijar',
    'Lock-off hold time (seconds; 0 = tap)': 'Mantener para quitar el objetivo (segundos; 0 = pulsar)',
    'With the same button, lock-off hold time must be longer than target-switch hold time.': 'Con el mismo botón, quitar el objetivo debe requerir más tiempo que cambiarlo.',
    "Switch target on release (0 = tap). Hold to lock off; a shared button's lock-off time is extended if needed. Tap again to target the enemy nearest your camera centre; no visible enemy leaves you unlocked. Buttons retain native actions (R3 transforms, Start pauses). Rebind in Mod settings.cmd. Applies next match; Fight Again keeps the match settings.": 'Cambia de objetivo al soltar (0 = pulsar). Mantén para quitarlo; si comparten botón, este tiempo se amplía si hace falta. Pulsa de nuevo para fijar al enemigo visible más cercano al centro de tu cámara; sin enemigos visibles, sigues sin objetivo. Se conservan las acciones originales (R3 transforma, Start pausa). Reasigna en Mod settings.cmd. Se aplica al siguiente combate; las revanchas conservan los ajustes.',
    'Team Battle': 'Por equipos', 'Free-for-all': 'Todos contra todos', 'Co-op': 'Cooperativo',
    'Modded Training': 'Entrenamiento mod', '1 Player': '1 jugador', '2 Players': '2 jugadores',
    '3 Players': '3 jugadores', '4 Players': '4 jugadores', 'CPU Only': 'Solo CPU',
    'Mod Settings': 'Ajustes del mod', 'Back': 'Volver', 'Mod modes': 'Modos del mod',
    'Original game menu': 'Menú original',
    # Settings pages (mod_settings.GROUPS) and labels.
    'Menus': 'Menús', 'Character select': 'Selección de personajes', 'Controls': 'Controles',
    'Cinematics': 'Cinemáticas', 'Fusion': 'Fusión', 'Fighters': 'Luchadores', 'Giants': 'Gigantes',
    'HUD': 'Interfaz', 'Split-screen HUD': 'Interfaz dividida', 'Spectating': 'Espectador',
    'Revival': 'Reanimación', 'Training': 'Entrenamiento',
    'Launch options (restart)': 'Opciones de inicio (reiniciar)', 'Diagnostics': 'Diagnóstico',
    'Language / Idioma': 'Idioma / Language',
    'Mod mode menus': 'Menús de modos del mod',
    'Menu switch button': 'Botón para cambiar de menú',
    'Show the menu switch button hint': 'Mostrar el aviso del botón de menú',
    'Loading animation speed (%; 100 = normal)': 'Velocidad de la animación de carga (%; 100 = normal)',
    'Each player picks their own assigned fighters': 'Cada jugador elige a sus luchadores asignados',
    'Allow all controllers during character selection': 'Permitir todos los mandos al elegir personajes',
    'Show player numbers above selection slots': 'Mostrar el número de jugador en cada casilla',
    'Target / spectator switch button': 'Botón para cambiar de objetivo / luchador observado',
    'Target switch hold time (seconds; 0 = tap)': 'Tiempo de pulsación para cambiar de objetivo (s; 0 = toque)',
    'Special-move pause': 'Pausa en movimientos especiales',
    'Ultimate attacks: shared camera and pause': 'Definitivos: cámara compartida y pausa',
    'Transformations: camera and pause': 'Transformaciones: cámara y pausa',
    'Transformations in split screen': 'Transformaciones en pantalla dividida',
    'Rush attacks: shared camera and pause': 'Ataques Rush: cámara compartida y pausa',
    'Introductions for extra fighters': 'Presentación de los luchadores adicionales',
    'Two-player fusion controls': 'Controles de fusión entre dos jugadores',
    'Show "Fused - Player n has control" (swap mode)': 'Mostrar "Fusión - Jn controla" (modo alterno)',
    'Show "Pn takes control in" countdown (swap mode)': 'Mostrar la cuenta "Jn controla en" (modo alterno)',
    'Timed fusion and automatic defusion': 'Fusión temporal y separación automática',
    'Fusion time limit (seconds)': 'Límite de tiempo de fusión (segundos)',
    'Show remaining fusion time': 'Mostrar tiempo de fusión restante',
    'Play power-down animation before defusion': 'Animación de destransformación antes de separarse',
    'Ginyu: exchange bodies with the actual opponent': 'Ginyu: intercambiar cuerpos con el rival alcanzado',
    'Ginyu can use stolen-body abilities': 'Ginyu puede usar las habilidades del cuerpo robado',
    'Extra fighter voice lines': 'Voces de los luchadores adicionales',
    'Disable all CPU transformations': 'Desactivar todas las transformaciones de la CPU',
    'Disable CPU transformations into giants': 'Desactivar las transformaciones de la CPU en gigantes',
    'CPU transformation chance (%; 100 = normal)': 'Probabilidad de transformación de la CPU (%; 100 = normal)',
    'Larger canonical-style giants (expanded maps recommended)': 'Gigantes más grandes (se recomiendan mapas ampliados)',
    'Giant size multiplier': 'Multiplicador del tamaño de gigantes',
    'Giant ordinary attack speed (%)': 'Velocidad de ataques normales de gigantes (%)',
    'Giant attack damage (%)': 'Daño de los ataques de gigantes (%)',
    'Extra giant stagger resistance (0 = native)': 'Resistencia adicional de gigantes al tambaleo (0 = normal)',
    'Giant follow camera distance (%)': 'Distancia de cámara para gigantes (%)',
    'Friendly overhead health bars': 'Barras de salud sobre los aliados',
    'Enemy overhead health bars': 'Barras de salud sobre los enemigos',
    'Battle HUD (including split-screen panels)': 'Interfaz de combate (también en pantalla dividida)',
    'Kill feed': 'Registro de bajas', 'Watched fighter kill count': 'Bajas del luchador observado',
    'Split-screen HUD style': 'Estilo de la interfaz dividida',
    'Top-row HUD size (%)': 'Tamaño de la interfaz superior (%)',
    'Split-screen HUD layout': 'Distribución de la interfaz dividida',
    'HUD texture filtering': 'Filtrado de texturas de la interfaz',
    'Co-op HUD panels': 'Paneles en cooperativo',
    'Fighter portraits (native style)': 'Retratos (estilo original)',
    'Sparking lightning (native style)': 'Rayos de Sparking (estilo original)',
    'Health damage trail (seconds; 0 = off)': 'Estela de daño en salud (segundos; 0 = sin estela)',
    'Allow taking over living CPU teammates': 'Permitir controlar a aliados CPU vivos al ser derrotado',
    'Allow spectating fallen fighters': 'Permitir observar a luchadores caídos',
    'Show takeover button hint': 'Mostrar el botón para tomar el control',
    'Show takeover confirmation': 'Confirmar al tomar el control',
    'Takeover hint delay (seconds)': 'Retraso del aviso para tomar el control (segundos)',
    'Takeover confirmation time (seconds)': 'Duración de la confirmación (segundos)',
    'Enable teammate revival': 'Permitir reanimar aliados',
    'Revival cost (blast stocks)': 'Coste de reanimación (reservas de habilidad)',
    'Stand nearby for (seconds)': 'Permanecer cerca durante (segundos)',
    'Revival distance (world units)': 'Distancia de reanimación (unidades del mundo)',
    'Health bars restored': 'Barras de salud recuperadas',
    'Minimum protected get-up time (seconds)': 'Tiempo mínimo de protección al levantarse (segundos)',
    'Keep fallen fighters in bounds': 'Mantener a los luchadores caídos dentro del escenario',
    'Show revival range ring': 'Mostrar el anillo de reanimación',
    'Revival ring opacity': 'Opacidad del anillo de reanimación',
    'Revival ring wave height (0 = flat)': 'Altura de las ondas del anillo (0 = plano)',
    'Revival ring wave speed (cycles per second)': 'Velocidad de ondas del anillo (ciclos por segundo)',
    'CPU behavior': 'Comportamiento de la CPU',
    'Refill health and prevent knockouts': 'Recuperar salud y evitar derrotas',
    'Health refill delay after damage (seconds)': 'Retraso de la recuperación de salud (segundos)',
    'Refill ki': 'Recuperar ki', 'Refill blast stocks': 'Recuperar reservas de habilidad',
    'PCSX2 16:9 widescreen patch (restart; automatic for BT4)': 'Parche panorámico 16:9 de PCSX2 (reiniciar; automático en BT4)',
    'Fast disc loading (restart)': 'Carga rápida del disco (reiniciar)',
    'Emulated PS2 CPU speed (restart)': 'Velocidad de la CPU emulada (reiniciar)',
    'Experimental 2x maps (restart)': 'Mapas 2× experimentales (reiniciar)',
    'Keep preparation RAM dumps (uses a lot of disk space)': 'Conservar volcados RAM de preparación (ocupa mucho espacio)',
    'Save a large diagnostic snapshot if a match freezes': 'Guardar un volcado de diagnóstico si se bloquea el combate',
    'Write diagnostic battle history to disk': 'Guardar historial de diagnóstico de combate',
    'ON': 'SÍ', 'OFF': 'NO', 'MOD SETTINGS': 'AJUSTES DEL MOD',
    '   [L1 / R1: category]': '   [L1 / R1: categoría]',
    'Up/Down: select    Left/Right: adjust': 'Arriba/abajo: elegir   Izq./der.: ajustar',
    'Square: save    Triangle: cancel    Applies to next match': 'Cuadrado: guardar   Triángulo: cancelar   (se aplica al próximo combate)',
    '{adapter} mod settings': 'Ajustes del mod {adapter}', 'Mod settings': 'Ajustes del mod',
    'Choose a category. Saved changes apply to the next match unless its page says otherwise. This window shows a newly saved language when you reopen it.': 'Elige una categoría. Los cambios guardados se aplican al próximo combate salvo que su página indique otra cosa. Esta ventana muestra el nuevo idioma guardado al volver a abrirla.',
    'Restore defaults': 'Restaurar valores predeterminados', 'Save': 'Guardar', 'Cancel': 'Cancelar',
    'Defaults restored. Save to keep them.': 'Valores predeterminados restaurados. Guarda para conservarlos.',
    'Replace them with the default settings? A copy of the old file is kept as {name}.': '¿Sustituirlos por los ajustes predeterminados? Se guarda una copia del archivo anterior como {name}.',
    'Run Build expanded maps.cmd first.': 'Ejecuta primero Build expanded maps.cmd.',
    'Expanded maps are on, but the expanded ISO is missing or out of date. Starting the original ISO; run Build expanded maps.cmd first.': 'Los mapas ampliados están activados, pero falta la ISO ampliada o no está al día. Se inicia la ISO original; ejecuta primero Build expanded maps.cmd.',
    'Rebind…': 'Asignar…', 'Rebind: {setting}': 'Asignar: {setting}',
    'That button is needed for selecting or navigating modes. Choose Select, Start, a stick click, a shoulder button or Square.': 'Ese botón se usa para elegir o recorrer los modos. Usa Select, Start, L3, R3, L1, L2, R1, R2 o Cuadrado.',
    'Per-character transformation exceptions…': 'Excepciones de transformación por personaje…',
    'CPU transformation exceptions': 'Excepciones de transformación de la CPU',
    'Select a character/form, then choose Default, Allow or Block.\nAllow overrides both global CPU restrictions; it does not bypass native move rules.': 'Elige un personaje o forma y selecciona Predeterminado, Permitir o Bloquear.\nPermitir anula las restricciones generales de la CPU, pero respeta las reglas del juego.',
    'Current character / form': 'Personaje / forma actual', 'Transformations': 'Transformaciones',
    'Default': 'Predeterminado', 'Allow': 'Permitir', 'Block': 'Bloquear',
    'Use these exceptions': 'Usar estas excepciones',
    'Press a controller button or a key mapped in PCSX2.': 'Pulsa un botón del mando o una tecla asignada en PCSX2.',
    'Or choose a PS2 button:': 'O elige un botón de PS2:',
    'The binding uses each player’s PCSX2 mapping. Native actions on this button still happen.': 'Usa la asignación de PCSX2 de cada jugador. El botón también conserva su acción original.',
    'Controller mappings could not be read. Choose a PS2 button below.': 'No se pudo leer la asignación del mando. Elige un botón de PS2.',
    'That input has no single PS2-button mapping. Choose a button below or assign it in PCSX2 first.': 'Esa entrada no corresponde a un único botón. Elige uno o asígnalo en PCSX2.',
    'Use selected button': 'Usar botón elegido',
    'Gamepad capture is unavailable. Press a mapped keyboard key or choose a PS2 button below.': 'No se pudo detectar el mando. Pulsa una tecla asignada o elige un botón.',
    'CHOOSE YOUR TEAMS': 'ELIGE LOS EQUIPOS',
    'PLAYER SETUP': 'CONFIGURAR JUGADORES',
    'Continue': 'Continuar',
    'ASSIGN CONTROLLERS': 'ASIGNAR MANDOS',
    'Assign controllers…': 'Asignar mandos…',
    'Restore default controller order': 'Restaurar orden de mandos',
    'Choose teams and optionally assign controllers.': 'Elige equipos y, si quieres, asigna los mandos.',
    'Release all controller buttons.': 'Suelta todos los botones de los mandos.',
    'Press Cross / A on this player’s controller.': 'Pulsa Cruz / A en el mando de este jugador.',
    'One controller at a time. Release and try again.': 'Un mando cada vez. Suelta los botones e inténtalo de nuevo.',
    'That controller already belongs to another player.': 'Ese mando ya pertenece a otro jugador.',
    'A controller disconnected. Start again with Player 1.': 'Se ha desconectado un mando. Empieza con el jugador 1.',
    'Player {player} — Controller {controller}': 'Jugador {player} — Mando {controller}',
    'Controller {controller}': 'Mando {controller}',
    'Default input': 'Entrada predeterminada',
    'Triangle: cancel assignment': 'Triángulo: cancelar asignación',
    'Up/Down: select   Left/Right: team': 'Arriba/abajo: elegir   Izq./der.: equipo',
    'Cross: select / continue    Triangle: back': 'Cruz: elegir / continuar    Triángulo: volver',
    'Assigned for this session. Standard gamepad controls.': 'Asignados para esta sesión. Controles estándar de mando.',
    'Controller assignment requires Play (any teams).': 'La asignación de mandos requiere Play (any teams).',
    'Cannot read controllers. Check connections and try again.': 'No se detectan los mandos. Comprueba las conexiones.',
    'Default controller order restored.': 'Orden de mandos predeterminado restaurado.',
    'Configure Player 1-4 in Shift+Tab > Controllers.': 'Configura los jugadores 1-4 en Shift+Tab > Mandos.',
    'Configure controllers (Shift+Tab)': 'Configurar mandos (Shift+Tab)',
    'Use configured controllers': 'Usar los mandos configurados',
    'Using configured native controllers.': 'Usando los mandos nativos configurados.',
    'Controller assignment failed. Default controls restored.': 'No se pudieron asignar los mandos. Controles predeterminados restaurados.',
    'Assign all players or restore the default order.': 'Asigna todos los jugadores o restaura el orden predeterminado.',
    'Player 1 assigns teams before choosing fighters.': 'El jugador 1 asigna equipos antes de elegir luchadores.',
    'Unassigned slots are CPUs, selected by Player 1.': 'El jugador 1 elige a los luchadores CPU de las casillas libres.',
    'All players may share one team against CPUs.': 'Todos pueden formar un equipo contra la CPU.',
    'Up/Down: player   Left/Right: team': 'Arriba/abajo: jugador   Izq./der.: equipo',
    'Cross: continue       Triangle: back': 'Cruz: continuar       Triángulo: volver',
    'FREE-FOR-ALL': 'TODOS CONTRA TODOS', 'EVERY FIGHTER FOR THEMSELVES': 'CADA LUCHADOR POR SU CUENTA',
    'LAST FIGHTER STANDING WINS': 'GANA EL ÚLTIMO EN PIE',
    'ALLIES': 'ALIADOS', 'OPPONENTS': 'RIVALES', 'TEAM 1': 'EQUIPO 1', 'TEAM 2': 'EQUIPO 2',
    'TEAM BATTLE': 'COMBATE POR EQUIPOS', 'CO-OP BATTLE': 'COMBATE COOPERATIVO',
    'FIGHT TOGETHER / WIN TOGETHER': 'LUCHA Y VENCE EN EQUIPO',
    'YOUR SELECTED FIGHTERS': 'TUS LUCHADORES', 'PREPARING YOUR MATCH': 'PREPARANDO COMBATE',
    'MODDED TRAINING': 'ENTRENAMIENTO MOD', 'CO-OP TRAINING': 'ENTRENAMIENTO COOPERATIVO',
    'PRACTICE WITH YOUR SELECTED FIGHTERS': 'PRACTICA CON TUS LUCHADORES',
    'PRACTICE OPTIONS / MOD SETTINGS': 'OPCIONES EN AJUSTES DEL MOD',
    'LOADING YOUR FIGHTERS': 'CARGANDO LUCHADORES', 'PREPARING YOUR FIGHTERS': 'PREPARANDO LUCHADORES',
    'STARTING YOUR MATCH': 'INICIANDO COMBATE', 'READY': 'LISTO',
    'SETUP FAILED - CLOSE THE GAME AND REOPEN PLAY ANY TEAMS': 'ERROR - CIERRA EL JUEGO Y ABRE PLAY DE NUEVO',
    'PRESS SQUARE TO TAKE OVER': 'CUADRADO PARA CONTROLAR',
    'PRESS L2 AND SQUARE TO TAKE OVER': 'L2 Y CUADRADO PARA CONTROLAR',
    'CONTROLLING ': 'CONTROLAS A ', 'DEFUSION PENDING': 'SEPARACION PENDIENTE',
    'UNKNOWN FIGHTER': 'LUCHADOR DESCONOCIDO', 'KILLS': 'BAJAS',
    'GETTING UP': 'LEVANTANDOSE', 'REVIVING TEAMMATE': 'REANIMANDO ALIADO',
    'FIGHTER': 'LUCHADOR', '1 FIGHTER': '1 LUCHADOR',
    'TWO PLAYERS / ONE TEAM': 'DOS JUGADORES / UN EQUIPO', 'THREE PLAYERS / ONE TEAM': 'TRES JUGADORES / UN EQUIPO',
    'FOUR PLAYERS / ONE TEAM': 'CUATRO JUGADORES / UN EQUIPO',
    'TWO PLAYERS / PRACTICE TOGETHER': 'DOS JUGADORES / ENTRENAN JUNTOS',
    'THREE PLAYERS / PRACTICE TOGETHER': 'TRES JUGADORES / ENTRENAN JUNTOS',
    'FOUR PLAYERS / PRACTICE TOGETHER': 'CUATRO JUGADORES / ENTRENAN JUNTOS',
    # Fusion chord names (guest ASCII); the joiner keeps its spaces.
    ' AND ': ' Y ', 'UP': 'ARRIBA', 'RIGHT': 'DERECHA', 'DOWN': 'ABAJO', 'LEFT': 'IZQUIERDA',
    'Your settings could not be opened. The saved file was left unchanged.': 'No se pudieron abrir los ajustes. El archivo guardado no se ha modificado.',
    'Your changes could not be saved.': 'No se pudieron guardar los cambios.',
    'GETTING YOUR FIGHTERS READY': 'PREPARANDO LUCHADORES',
    'GETTING YOUR FIGHTERS READY...': 'PREPARANDO LUCHADORES...',
    'PREPARING TEAM BATTLE': 'PREPARANDO COMBATE',
    'LOADING FIGHTERS': 'CARGANDO LUCHADORES', 'PREPARING ARENA': 'PREPARANDO ESCENARIO',
    'GETTING READY': 'PREPARANDO COMBATE', 'DEFEATED': 'DERROTADO',
    'LOADING YOUR SELECTED FIGHTERS...': 'CARGANDO TUS LUCHADORES...',
    'STARTING YOUR MATCH...': 'INICIANDO COMBATE...',
    'GETTING EVERYONE READY FOR THE REMATCH...': 'PREPARANDO LA REVANCHA...',
    'RETURNING TO YOUR SELECTED MENU...': 'VOLVIENDO AL MENÚ...',
    'RETURNING TO CHARACTER SELECTION...': 'VOLVIENDO A ELEGIR PERSONAJES...',
    'RETURNING TO THE MAIN MENU...': 'VOLVIENDO AL MENÚ PRINCIPAL...',
    'FINISHING THE PREVIOUS OPERATION BEFORE RETURNING...': 'TERMINANDO LA OPERACIÓN ANTERIOR...',
    'MENU DESTINATION UNKNOWN - CLOSE AND REOPEN THE GAME': 'ERROR DE MENÚ - CIERRA Y ABRE EL JUEGO',
    'MENU RETURN BUSY - CLOSE AND REOPEN THE GAME': 'MENÚ OCUPADO - CIERRA Y ABRE EL JUEGO',
    'MENU RESTORE FAILED - CLOSE AND REOPEN THE GAME': 'ERROR DE MENÚ - CIERRA Y ABRE EL JUEGO',
    'FIGHTER UPDATE FAILED - CLOSE AND REOPEN THE GAME': 'ERROR DE LUCHADOR - CIERRA Y ABRE EL JUEGO',
    'REMATCH RESTORE FAILED - CLOSE AND REOPEN THE GAME': 'ERROR DE REVANCHA - CIERRA Y ABRE EL JUEGO',
    'PRESS SPACE IN THE GAME TO CONTINUE LOADING.': 'PULSA ESPACIO PARA SEGUIR CARGANDO.',
    'PRESS SPACE IN THE GAME TO BEGIN LOADING.': 'PULSA ESPACIO PARA EMPEZAR A CARGAR.',
}

# Display labels only. Values in mod-settings.json never become translated text.
# Each setting's labels are unique in both languages (test_localization).
VALUES_EN = {'all':'Everyone', 'target':'Target only', 'none':'Nobody', 'shared':'One shared view',
    'single_enemy':'Only with one enemy left', 'hide':'Hide', 'show':'Always show',
    'each_half':'Each half frames it', 'swap_20s':'Swap control', 'split_controls':'P1 attacks, P2 moves',
    'player1':'Player 1 only', 'idle':'Stand still', 'fight':'Fight back', 'native':'Native',
    'compact':'Compact', 'top':'Same top row', 'top_bottom':'Player top, target bottom',
    'nearest':'Sharp (nearest)', 'linear':'Smooth (linear)', 'players':'Both players',
    'targets':'Each player and target', 'default':'PCSX2 setting', '130':'130%', '180':'180%', '300':'300%'}
VALUES = {'all':'Todos', 'target':'Solo objetivo', 'none':'Nadie', 'shared':'Vista compartida',
    'single_enemy':'Solo si queda un enemigo', 'hide':'Ocultar', 'show':'Mostrar siempre',
    'each_half':'Cada mitad', 'swap_20s':'Alternar control', 'split_controls':'J1 ataca, J2 se mueve',
    'player1':'Solo jugador 1', 'idle':'Quietos', 'fight':'Combatir', 'native':'Original',
    'compact':'Compacta', 'top':'Ambos arriba', 'top_bottom':'Jugador arriba, objetivo abajo',
    'nearest':'Sin suavizado', 'linear':'Suavizado', 'players':'Ambos jugadores',
    'targets':'Jugador y objetivo', 'default':'Ajuste de PCSX2', '130':'130%', '180':'180%', '300':'300%'}
# PS2 button values (input_binding.BUTTONS -> input_binding.LABELS). Only settings
# screens translate them; guest text keeps input_binding.LABELS unchanged.
BUTTON_LABELS = {'select':'Select', 'l3':'L3', 'r3':'R3', 'start':'Start', 'up':'Up', 'right':'Right',
    'down':'Down', 'left':'Left', 'l2':'L2', 'r2':'R2', 'l1':'L1', 'r1':'R1', 'triangle':'Triangle',
    'circle':'Circle', 'cross':'Cross', 'square':'Square'}
ES.update({'Up':'Arriba', 'Right':'Derecha', 'Down':'Abajo', 'Left':'Izquierda', 'Triangle':'Triángulo',
    'Circle':'Círculo', 'Cross':'Cruz', 'Square':'Cuadrado'})

ES.update({
    'Fight with every selected teammate\non the battlefield at the same time.': 'Lucha con todos tus aliados\nen el campo de batalla a la vez.',
    'Every fighter is an opponent.\nChoose one to four players, or CPUs.': 'Todos los luchadores son rivales.\nDe uno a cuatro jugadores, o solo CPU.',
    'Two to four players share Team 1.\nSelect an ally for every human player.': 'De dos a cuatro jugadores en el equipo 1.\nElige un aliado para cada jugador.',
    'Practice with selected team rosters.\nSet CPU behavior and refill in Mod settings.\nOriginal Training stays in the original menu.': 'Practica con tus equipos. Configura la CPU\ny la recuperación en Ajustes del mod.\nEl entrenamiento original sigue disponible.',
    'Adjust the mod with your controller.\nSave changes for your next match.': 'Ajusta el mod con tu mando.\nGuarda para el próximo combate.',
    'Control Team 1 against CPU opponents.\nChoose the fighters for each team.': 'Controla el equipo 1 contra la CPU.\nElige los luchadores de cada equipo.',
    'Player 1 faces Player 2.\nAdd CPU teammates on either side.': 'Jugador 1 contra jugador 2.\nAñade aliados CPU a ambos equipos.',
    'Watch two teams of CPU fighters.\nChoose the fighters for each team.': 'Observa un combate entre equipos CPU.\nElige los luchadores de cada equipo.',
    'Return to the mod mode groups.': 'Vuelve al menú de modos del mod.',
    'One player against every other fighter.\nAll remaining fighters are CPUs.': 'Un jugador contra todos los demás.\nLos otros luchadores son CPU.',
    'Two players fight each other and CPUs.\nEvery fighter is an opponent.': 'Dos jugadores luchan entre sí y contra la CPU.\nTodos los luchadores son rivales.',
    'Watch a free-for-all between CPUs.\nEvery fighter is an opponent.': 'Observa un todos contra todos entre CPU.\nTodos los luchadores son rivales.',
    'Two players share Team 1.\nChoose at least two Team 1 fighters\nand one or more CPU opponents.': 'Dos jugadores comparten el equipo 1.\nElige al menos dos aliados\ny al menos un rival CPU.',
    'Two to four allies practice together.\nSelect an ally for every human player\nand one or more CPU opponents.': 'De dos a cuatro aliados practican juntos.\nElige un aliado por jugador\ny uno o más rivales CPU.',
    'Practice with one human and CPU fighters.\nChoose CPU behavior and refill in Mod settings.': 'Practica con un jugador y luchadores CPU.\nConfigura la CPU y la recuperación en Ajustes.',
    'Practice with a human on each side.\nAdd CPU fighters to either team.': 'Practica con un jugador en cada equipo.\nAñade luchadores CPU a cualquier equipo.',
    'Four players and any selected CPUs.\nSelect at least four fighters total.': 'Cuatro jugadores y las CPU elegidas.\nSelecciona al menos cuatro luchadores.',
    'Four players share Team 1.\nSelect at least four Team 1 fighters.': 'Cuatro jugadores comparten el equipo 1.\nSelecciona al menos cuatro aliados.',
    'Four allies practice against CPUs.\nSelect at least four Team 1 fighters.': 'Cuatro aliados practican contra la CPU.\nSelecciona al menos cuatro aliados.',
    'Two allies practice against CPUs.\nSelect at least two Team 1 fighters.': 'Dos aliados practican contra la CPU.\nSelecciona al menos dos aliados.',
    'Return to Modded Training.': 'Vuelve al entrenamiento mod.',
    'Three players and any selected CPUs.\nSelect at least three fighters total.': 'Tres jugadores y las CPU elegidas.\nSelecciona al menos tres luchadores.',
    'Three allies share Team 1.\nSelect at least three Team 1 fighters.': 'Tres aliados comparten el equipo 1.\nSelecciona al menos tres aliados.',
    'Three allies practice against CPUs.\nSelect at least three Team 1 fighters.': 'Tres aliados practican contra la CPU.\nSelecciona al menos tres aliados.',
    'Choose each player team before character select.\nShare a team for cooperative play.\nAdd CPU fighters to either team.': 'Asigna equipos antes de elegir luchadores.\nComparte equipo para jugar en cooperativo.\nPuedes añadir CPU a ambos equipos.',
})


def value_label(value, settings=None):
    if type(value) is bool:
        return tr('ON' if value else 'OFF', settings)
    if isinstance(value, str) and value in NAMES:
        return NAMES[value]
    if isinstance(value, str) and value in BUTTON_LABELS:
        return tr(BUTTON_LABELS[value], settings)
    if isinstance(value, str) and value in VALUES_EN:
        return VALUES[value] if language(settings) == 'es' else VALUES_EN[value]
    return str(value).replace('_', ' ')


def tr(text, settings=None, **values):
    if language(settings) == 'es':
        translated = ES.get(text)
        if translated is None:
            for pattern, replacement in PATTERNS:
                if re.fullmatch(pattern, text):
                    translated = re.sub(pattern, replacement, text)
                    break
        text = translated if translated is not None else text
    if not WINDOWS and '.cmd' in text:
        for source, target in LINUX_SCRIPT_NAMES.items():
            text = text.replace(source, target)
    return text.format(**values) if values else text


PATTERNS = (
    (r'NEED 1 BLAST STOCKS', r'NECESITAS 1 RESERVA'),
    (r'NEED (\d+) BLAST STOCKS', r'NECESITAS \1 RESERVAS'),
    (r'PLAYER (\d+)', r'JUGADOR \1'), (r'SLOT (\d+)', r'CASILLA \1'),
    (r'<  TEAM (\d+)  >', r'<  EQUIPO \1  >'),
    (r'(\d+) unsaved changes', r'\1 cambios sin guardar'),
    (r'(\d+) FIGHTERS? / ALL CPU', r'\1 LUCHADORES / SOLO CPU'),
    (r'(\d+) FIGHTERS? / 1 PLAYER', r'\1 LUCHADORES / 1 JUGADOR'),
    (r'(\d+) FIGHTERS? / (\d+) PLAYERS?', r'\1 LUCHADORES / \2 JUGADORES'),
    (r'(\d+) FIGHTERS?', r'\1 LUCHADORES'),
    (r'(TWO|THREE|FOUR) PLAYERS / ONE TEAM', r'JUGADORES EN UN EQUIPO'),
    (r'(TWO|THREE|FOUR) PLAYERS / PRACTICE TOGETHER', r'PRACTICA EN EQUIPO'),
    (r'FUSION - P(\d) TAP R3 TO ACCEPT', r'FUSION - J\1 ACEPTA CON R3'),
    (r'FUSED - PLAYER (\d) HAS CONTROL', r'FUSION - J\1 CONTROLA'),
    (r'P(\d) TAKES CONTROL IN (\d+)', r'J\1 CONTROLA EN \2'),
)


def guest(text, settings=None):
    """ASCII glyphs for guest HUD strings, without lossy UTF-8 atlas indexing."""
    if settings is None and _override.get() is None and _battle_language is not None:
        settings = _battle_language
    translated = unicodedata.normalize('NFKD', tr(text, settings))
    return translated.encode('ascii', 'ignore')


def slot(text, size, settings=None):
    data = guest(text, settings)
    if len(data) >= size:
        raise ValueError('Localized guest text exceeds reserved slot: ' + text)
    return data.ljust(size, b'\0')

# Settings page help (mod_settings.notes), shown on the desktop and in game.
ES.update({
    'Press the menu switch button on the original main menu to open or close the mod menus; its hint can be hidden. With mod mode menus off, only Mod settings.cmd can turn them back on. Menu settings saved in game apply when you leave Mod Settings; saved in Mod settings.cmd, after restarting Play. Language also changes match text from the next match. Loading speed applies from the next loading screen.':
        'El botón de cambio de menú abre o cierra los menús del mod desde el menú principal original; su aviso se puede ocultar. Si los desactivas, solo Mod settings.cmd puede reactivarlos. Guardados en el juego, los ajustes de menú se aplican al salir de Ajustes del mod; desde Mod settings.cmd, al reiniciar Play. El idioma cambia también el texto del combate desde el próximo. La velocidad de carga, desde la próxima carga.',
    'With own fighters on, each human picks the slots assigned to them with their own controller; otherwise Player 1 picks. Allowing all controllers lets any controller move the cursor. Player numbers mark whose slot is whose. Saved in game, these apply when you leave Mod Settings; saved in Mod settings.cmd, after restarting Play.':
        'Con luchadores propios, cada jugador elige con su mando las casillas que tiene asignadas; si no, elige el jugador 1. Con todos los mandos, cualquiera puede mover el cursor. Los números indican de quién es cada casilla. Guardados en el juego se aplican al salir de Ajustes del mod; desde Mod settings.cmd, al reiniciar Play.',
    'Any PS2 button can switch target or watched fighter; its native action still happens, so Start also pauses and R3 also transforms. Hold for the set time, then release (0 = tap). Mod settings.cmd can also capture a pressed button. Applies from the next match; a Fight Again rematch keeps the settings of its match.':
        'Cualquier botón de PS2 puede cambiar de objetivo o de luchador observado; conserva su acción original, así que Start también pausa y R3 también transforma. Mantén el tiempo elegido y suelta (0 = toque). Mod settings.cmd también puede detectar el botón pulsado. Se aplica desde el próximo combate; la revancha (Fight Again) conserva los ajustes de su combate.',
    'Special-move pause chooses who stops during a special. Shared cameras pause everyone for one view; off keeps separate views and lets others move (paired attacks still hold their fighters). Split-screen transformations use one shared view or frame each half. Extra fighter intros follow the two leads and can be skipped. Applies from the next match; a Fight Again rematch keeps the settings of its match.':
        'La pausa en especiales elige quién se detiene. Las cámaras compartidas pausan a todos; desactivadas, cada uno conserva su vista y los demás se mueven (los ataques en pareja siguen deteniendo a los suyos). En pantalla dividida, la transformación usa una vista o cada mitad. Las presentaciones extra siguen a los líderes y se pueden omitir. Se aplica desde el próximo combate; la revancha conserva sus ajustes.',
    'When two humans share a fusion, swap passes control every 20 s, split gives P1 attacks and P2 movement, or Player 1 controls it. The control message and countdown show in swap mode only. The time limit covers Fusion Dance fusions made in the match, not Potara or preselected ones; its timer and power-down animation are optional. Applies from the next match; a Fight Again rematch keeps the settings of its match.':
        'Si dos jugadores comparten una fusión, el modo alterno pasa el control cada 20 s, el reparto da ataque al J1 y movimiento al J2, o controla el J1. El aviso y la cuenta atrás solo salen en modo alterno. El límite afecta a la Danza de la Fusión del combate, no a Potara ni a fusiones elegidas; el temporizador y la animación son opcionales. Se aplica desde el próximo combate; la revancha conserva sus ajustes.',
    'Ginyu can exchange bodies with the opponent he actually hits; stolen-body abilities are optional. Extra voices borrow idle native voice streams. The CPU switches and chance limit native CPU transformations; per-character exceptions override them. Humans, fusion and Body Change are unaffected. Applies from the next match; a Fight Again rematch keeps the settings of its match.':
        'Ginyu puede intercambiar cuerpos con el rival que alcanza; las habilidades robadas son opcionales. Las voces adicionales usan canales de voz libres. Los ajustes de la CPU y la probabilidad limitan sus transformaciones; las excepciones por personaje los anulan. No afectan a jugadores, fusiones ni al Cambio de Cuerpo. Se aplica desde el próximo combate; la revancha (Fight Again) conserva sus ajustes.',
    'Larger giants scale native giant forms; expanded maps give them room. Size, attack speed, damage, stagger resistance and camera distance apply only while larger giants are on. Applies from the next match; a Fight Again rematch keeps the settings of its match.':
        'Los gigantes grandes amplían las formas gigantes del juego; los mapas ampliados les dan espacio. Tamaño, velocidad, daño, resistencia y distancia de cámara solo se aplican con gigantes grandes activados. Se aplica desde el próximo combate; la revancha (Fight Again) conserva los ajustes de su combate.',
    'Overhead health bars, the battle HUD, the kill feed and the watched fighter kill count are separate switches. Turning the battle HUD off also hides the split-screen panels. Applies from the next match; a Fight Again rematch keeps the settings of its match.':
        'Las barras de salud, la interfaz de combate, el registro de bajas y las bajas del luchador observado se activan por separado. Sin interfaz de combate tampoco hay paneles en pantalla dividida. Se aplica desde el próximo combate; la revancha (Fight Again) conserva los ajustes de su combate.',
    'Native style uses the game frames and meters; portraits and lightning need it. "Same top row" holds both panels (size in %); "Player top, target bottom" puts your target opposite you. Co-op panels show both players or each player and target. Smooth filtering softens textures. The damage trail briefly shows lost health (0 = off). Applies from the next match; a Fight Again rematch keeps the settings of its match.':
        'El estilo original usa marcos y medidores del juego; retratos y rayos lo requieren. "Ambos arriba" pone los dos paneles arriba (tamaño en %); "Jugador arriba, objetivo abajo" coloca a tu objetivo frente a ti. En cooperativo se ven los jugadores o cada uno con su objetivo. El suavizado alisa las texturas. La estela muestra la salud perdida (0 = no). Se aplica desde el próximo combate; la revancha conserva sus ajustes.',
    'A defeated human can watch fighters and take over a living CPU teammate, never an enemy, and not in free-for-all or CPU-only matches. Fallen fighters can be watched for their score. The hint shows the takeover button after its delay; the confirmation names your new fighter. Applies from the next match; a Fight Again rematch keeps the settings of its match.':
        'Un jugador derrotado puede observar y tomar el control de un aliado CPU vivo, nunca de un enemigo, y no en Todos contra todos ni solo CPU. También puede observar a caídos para ver sus bajas. El aviso muestra el botón tras su retraso; la confirmación indica tu nuevo luchador. Se aplica desde el próximo combate; la revancha (Fight Again) conserva sus ajustes.',
    'Stay inside the circle of a fallen teammate for the set time. Moving and taunting keep progress; damage or leaving interrupts. Revival costs blast stocks, not ki, and restores the set health. Get-up protection, corpse safety and ring appearance are adjustable. No revival in free-for-all. Applies from the next match; a Fight Again rematch keeps its settings.':
        'Permanece en el círculo de un aliado caído el tiempo elegido. Moverte y provocar conservan el progreso; recibir daño o salir lo interrumpe. Cuesta reservas, no ki, y restaura la salud elegida. Puedes ajustar la protección al levantarse, el límite para caídos y el aspecto del anillo. No funciona en Todos contra todos. Se aplica al próximo combate; la revancha conserva sus ajustes.',
    'Modded Training takes one to four players; share a team to practice together. The CPU stands still or fights back. Health refills after the delay, and ki and blast stocks refill. With health refill off, defeats can end the session. Native Training stays in the original menu. Applies from the next session; a Fight Again rematch keeps the settings of its session.':
        'El entrenamiento mod admite de uno a cuatro jugadores; compartir equipo permite practicar juntos. La CPU se queda quieta o combate. La salud se recupera tras el retraso; el ki y las reservas también. Sin recuperación de salud, las derrotas pueden terminar la sesión. El entrenamiento original sigue en su menú. Se aplica desde la próxima sesión; la revancha conserva sus ajustes.',
    'Applied when Play starts, so restart Play after saving. Widescreen enables the PCSX2 16:9 patch. Fast disc loading shortens loading screens. A faster emulated CPU smooths split screen; PCSX2 setting leaves the rate alone. 2x maps need Build expanded maps.cmd first (seven animated stages stay native); without that build, Play starts the original ISO.':
        'Se aplican al iniciar Play: reinícialo después de guardar. El parche panorámico activa el 16:9 de PCSX2. La carga rápida acorta las pantallas de carga. Una CPU emulada más rápida suaviza la pantalla dividida; Ajuste de PCSX2 no la cambia. Los mapas 2× requieren Build expanded maps.cmd (siete escenarios animados no cambian); sin esa copia, Play inicia la ISO original.',
    'For troubleshooting; these files can be large. Preparation dumps keep intermediate RAM images, freeze snapshots save memory when a match stops responding, and battle history records match events. Applies from the next match; a Fight Again rematch keeps the settings of its match.':
        'Para diagnosticar problemas; estos archivos pueden ocupar mucho. Los volcados de preparación guardan imágenes intermedias de la RAM, las capturas de bloqueo guardan la memoria si un combate se congela y el historial registra los sucesos del combate. Se aplica desde el próximo combate; la revancha (Fight Again) conserva sus ajustes.',
})

# In-game Mod Settings screens (ingame_settings.TEXTS).
ES.update({
    'Choose a category': 'Elige una categoría',
    'Per-character exceptions ({n} set)…': 'Excepciones por personaje ({n} definidas)…',
    'Restore defaults…': 'Restaurar valores predeterminados…',
    'Up/Down: select    Cross: open    Circle: help': 'Arriba/abajo: elegir    Cruz: abrir    Círculo: ayuda',
    'Square: save and exit    Triangle: close': 'Cuadrado: guardar y salir    Triángulo: cerrar',
    'Up/Down: select    Left/Right: change    L2/R2: ×10': 'Arriba/abajo: elegir    Izq./der.: cambiar    L2/R2: ×10',
    'Up/Down: select    Left/Right: change    L2/R2: first/last': 'Arriba/abajo: elegir    Izq./der.: cambiar    L2/R2: primero/último',
    'Up/Down: select    Left/Right: change    L2/R2: off/on': 'Arriba/abajo: elegir    Izq./der.: cambiar    L2/R2: NO/SÍ',
    'L1/R1: category    Circle: help    Square: save    Triangle: back': 'L1/R1: categoría   Círculo: ayuda   Cuadrado: guardar   Triángulo: volver',
    'Help: {group}': 'Ayuda: {group}', 'Circle or Triangle: back': 'Círculo o Triángulo: volver',
    'Default follows the CPU switches; Allow and Block override them.': 'Predeterminado sigue los ajustes de la CPU; Permitir y Bloquear los anulan.',
    'Only characters with an exception ({n})': 'Solo personajes con excepción ({n})',
    'No exceptions set.': 'No hay excepciones.',
    'Up/Down: select    Left/Right: change    L1/R1: page    L2/R2: 5 pages': 'Arriba/abajo: elegir   Izq./der.: cambiar   L1/R1: página   L2/R2: 5 páginas',
    'Select: exceptions only    Square: save    Triangle: back': 'Select: solo excepciones    Cuadrado: guardar    Triángulo: volver',
    'Select: every character    Square: save    Triangle: back': 'Select: todos    Cuadrado: guardar    Triángulo: volver',
    'Discard unsaved changes?': '¿Descartar los cambios sin guardar?',
    'Your unsaved changes will be lost.': 'Se perderán los cambios sin guardar.',
    'Triangle: discard and close    Cross: go back': 'Triángulo: descartar y cerrar    Cruz: volver',
    'Square: save and exit': 'Cuadrado: guardar y salir',
    'Restore defaults?': '¿Restaurar los valores predeterminados?',
    'Every setting except the language returns to its default and the per-character exceptions are cleared. Nothing is saved until you press Square.':
        'Todos los ajustes salvo el idioma vuelven a su valor predeterminado y se borran las excepciones por personaje. No se guarda nada hasta que pulses Cuadrado.',
    'Cross: restore    Triangle: back': 'Cruz: restaurar    Triángulo: volver',
    'Turn off the mod mode menus?': '¿Desactivar los menús de modos del mod?',
    'This screen opens from those menus, so after saving only the desktop Mod settings (Mod settings.cmd) can turn them back on.':
        'Esta pantalla se abre desde esos menús: después de guardar, solo los ajustes de escritorio (Mod settings.cmd) pueden reactivarlos.',
    'Cross: turn off    Triangle: keep on': 'Cruz: desactivar    Triángulo: mantener',
    'Repair replaces the file with the default settings and keeps a copy as {name}.': 'Reparar sustituye el archivo por los ajustes predeterminados y guarda una copia como {name}.',
    'Cross: repair settings    Triangle: close': 'Cruz: reparar ajustes    Triángulo: cerrar',
    'This screen could not be drawn.': 'No se pudo dibujar esta pantalla.',
    'Cross: back to the categories    Triangle: close': 'Cruz: volver a las categorías    Triángulo: cerrar',
    'Triangle: close': 'Triángulo: cerrar',
    'Your settings could not be repaired.': 'No se pudieron reparar los ajustes.',
    'Settings repaired. The old file was kept as {name}.': 'Ajustes reparados. El archivo anterior se guardó como {name}.',
    'Saved.': 'Guardado.',
    'Saved. Launch options apply after restarting Play.': 'Guardado. Las opciones de inicio se aplican al reiniciar Play.',
    '{n} unsaved changes': '{n} cambios sin guardar', '1 unsaved change': '1 cambio sin guardar',
    'Character {cid}': 'Personaje {cid}',
    'An exception applies to a CPU fighter in that character or form. Default follows the CPU switches; Allow ignores them (the chance setting still applies); Block stops it from transforming. Humans are unaffected. Select lists only the exceptions. Applies from the next match; a Fight Again rematch keeps the settings of its match.':
        'Una excepción se aplica a un luchador CPU con ese personaje o forma. Predeterminado sigue los ajustes de la CPU; Permitir los ignora (la probabilidad se sigue aplicando); Bloquear impide que se transforme. No afecta a los jugadores. Select muestra solo las excepciones. Se aplica desde el próximo combate; la revancha (Fight Again) conserva sus ajustes.',
    'Restore defaults stages the default of every setting except the language and clears the per-character exceptions. It never turns the mod mode menus off. Nothing is saved until you press Square.':
        'Restaurar prepara el valor predeterminado de cada ajuste salvo el idioma y borra las excepciones por personaje. Nunca desactiva los menús de modos del mod. No se guarda nada hasta que pulses Cuadrado.',
})

# Native overhead HUD preferences (stable saved keys remain language neutral).
ES.update({'HUD style':'Estilo del HUD','Overhead names':'Nombres sobre los luchadores',
 'Detailed overhead HUD':'HUD detallado sobre los luchadores','Overhead portraits':'Retratos sobre los luchadores',
 'Contestant list':'Lista de participantes','Overhead HUD size (%)':'Tamaño del HUD superior (%)',
 'Overhead HUD opacity (%)':'Opacidad del HUD superior (%)','game_overhead':'HUD del juego y superior',
 'overhead_only':'Solo HUD superior','focused':'Jugador y objetivo','owner':'Solo jugador','allies':'Jugador, objetivo y aliados',
 'off':'Desactivado','all':'Todos'})

VALUES_EN.update({'game_overhead':'Game HUD + overhead','overhead_only':'Overhead only',
 'focused':'Player and target','owner':'Player only','allies':'Player, target and allies','off':'Off'})
VALUES.update({'game_overhead':'HUD del juego y superior','overhead_only':'Solo HUD superior',
 'focused':'Jugador y objetivo','owner':'Solo jugador','allies':'Jugador, objetivo y aliados','off':'Desactivado'})
ES.update({'Overhead shape':'Forma del HUD superior','Overhead ki stocks':'Reservas de ki en el HUD superior'})
VALUES_EN.update({'hexagon':'Hexagon','ring':'Ring','plate':'Plate','tiny':'Tiny','normal':'Normal'})
VALUES.update({'hexagon':'Hexagono','ring':'Anillo','plate':'Panel','tiny':'Pequeños','normal':'Normal'})

VALUES_EN['everyone']='Everyone'
VALUES['everyone']='Todos'

VALUES_EN.update({'split_controls_reverse':'P2 attacks, P1 moves','swap_roles':'Swap roles','player1':'P1 does everything','player2':'P2 does everything'})
VALUES.update({'split_controls_reverse':'J2 ataca, J1 se mueve','swap_roles':'Alternar funciones','player1':'J1 controla todo','player2':'J2 controla todo'})
ES.update({'Fusion control swap interval (seconds)':'Intervalo de control de fusión (segundos)','Show R3 fusion prompt':'Mostrar aviso de fusión R3'})

ES['P1 and P2 mean the first and second fuser, for any seat pair. Swap control or movement/attack roles at the chosen interval; the first swap starts one full interval after fusion. Timers pause with battle pauses and cinematics. Applies next match; Fight Again keeps the match settings.']='J1 y J2 son el primer y segundo participante, para cualquier pareja. Alterna el control o las funciones con el intervalo elegido; el primer cambio espera un intervalo completo desde la fusión. El reloj se pausa con el combate y las cinemáticas. Se aplica al próximo combate; Revancha conserva sus ajustes.'

ES.update({'Fusion controls (first/second fuser)':'Control de fusi\u00f3n (primer/segundo participante)','Show fusion control owner and roles':'Mostrar jugador y funciones en la fusi\u00f3n','Show time until control or role swap':'Mostrar tiempo hasta alternar control o funciones'})

ES.update({'Fusion time drains faster in stronger forms':'El tiempo de fusi\u00f3n se agota m\u00e1s r\u00e1pido en formas fuertes','Fusion form drain strength':'Intensidad del consumo de fusi\u00f3n'})
VALUES_EN.update({'mild':'Mild','heavy':'Heavy'})
VALUES.update({'mild':'Suave','heavy':'Fuerte'})

ES['P1 and P2 mean the first and second fuser, for any seat pair. Swap control or movement/attack roles at the chosen interval; the first swap starts one full interval after fusion. Timers pause with battle pauses and cinematics. Applies next match; Fight Again keeps the match settings. Form drain affects timed Dance fusions only: Normal reduces full-form duration by 10/20/30/40/50%, Mild by 5/10/15/20/25%, Heavy by 20/35/50/60/70%. Changing forms changes future drain without resetting spent time; a completed transformation grants at least one combat second. Enable fusion duration as well. Unknown forms use base drain.']='J1 y J2 son el primer y segundo participante, para cualquier pareja. Alterna el control o las funciones con el intervalo elegido. Los relojes se pausan con el combate y las cinemáticas. Se aplica al próximo combate; Revancha conserva sus ajustes. El consumo por forma afecta solo a fusiones temporales de Danza: Normal reduce la duración por 10/20/30/40/50%, Suave por 5/10/15/20/25%, Fuerte por 20/35/50/60/70%. Cambiar de forma modifica el consumo futuro sin reiniciar el tiempo gastado; una transformación completada concede al menos un segundo de combate. Activa también la duración de fusión. Las formas desconocidas usan el consumo base.'

# Autonomous ordinary transformations (next-match preferences).
ES.update({'CPU tactics':'Tácticas de CPU', 'Allied CPU transformations':'Transformaciones de CPU aliadas',
           'Enemy CPU transformations':'Transformaciones de CPU enemigas', 'CPU tactics difficulty':'Dificultad de tácticas de CPU'})
VALUES_EN.update({'more_often':'More often', 'outmatched':'When outmatched', 'aggressive':'Aggressive', 'relentless':'Relentless'})
VALUES.update({'more_often':'Más a menudo', 'outmatched':'Al estar en desventaja', 'aggressive':'Agresiva', 'relentless':'Implacable'})
ES['CPU transformations use native stock costs, character exceptions, giant restrictions and chance limits. Allies means the first player team; free-for-all CPUs are enemies. Native leaves the existing AI unchanged. When outmatched considers health, ki, recent damage and reviewed form tiers; unknown tiers add no score. Presets tune thresholds and cooldowns. Applies next match; Training keeps its own CPU behavior. CPU revival and autonomous fusion are not included yet.']='Las transformaciones de CPU respetan el coste nativo, las excepciones por personaje, los límites de gigantes y la probabilidad. Aliados significa el equipo del primer jugador; en todos contra todos las CPU son enemigas. Nativo conserva la IA existente. Al estar en desventaja considera vida, ki, daño reciente y niveles de formas verificados; las formas desconocidas no añaden puntos. La dificultad ajusta los umbrales y las pausas entre intentos. Se aplica en el siguiente combate; Entrenamiento conserva su propio comportamiento de CPU. La reanimación de CPU y la fusión autónoma aún no están incluidas.'
