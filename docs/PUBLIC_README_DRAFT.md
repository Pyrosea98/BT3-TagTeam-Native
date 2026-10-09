# BT3 Tag Team: standalone Windows build (DRAFT README, EN / ES)

Draft by Claude, 2026-10-08. Items marked TBD must be filled with measured facts before publishing (see `PUBLIC_RELEASE_CHECKLIST.md`). This is an unofficial fan project, not affiliated with or endorsed by the owners of Dragon Ball or Budokai Tenkaichi.

---

## English

### What this is
Dragon Ball Z: Budokai Tenkaichi 3 (Power Scale BETA 1.5.1) running natively on Windows with the Tag Team mod built in. No emulator, no separate Python install, no extra helper windows. Features include team battles up to 5v5, free-for-all, co-op, modded training, up to 4 local players, an overhead mini-HUD, CPU transformation options, and fusion controls for co-op.

### What you need
- A Windows 10 or 11 PC (64-bit) with a GPU and drivers that support Vulkan (minimum version and features: TBD).
- Your own copy of the **Power Scale BETA 1.5.1** disc image. The game files are NOT included; the installer imports them from your disc image.
- About 12 GB of free disk space (TBD, the import makes an expanded copy), 8 GB of RAM or more (TBD).
- A gamepad is recommended; a keyboard works.

### Install
1. Download `BT3-TagTeam-...-Setup.exe` and check its SHA256 against the one published next to the download.
2. Run it. This build is **not code-signed**, so Windows SmartScreen may say "Windows protected your PC". Click **More info**, then **Run anyway**. Some antivirus programs may also warn about the bundled runtime; the full source and hashes are published (TBD link).
3. It installs for your user only (no administrator rights needed) and adds a desktop shortcut.

### First run
1. Start **BT3 Tag Team** from the shortcut.
2. When asked, pick your Power Scale BETA 1.5.1 disc image. The game checks it (a wrong or modified disc is refused with a clear message), expands the maps to 2x size, and prepares the interface art. This takes a few minutes the first time and needs the free space above. Your disc image is never modified.
3. After the credits, choose a mode from the mod menu and play.

### Settings
Open the mod menu, then Settings. Most options apply from the next match. A few (launch options) show "Restart required" with a **Restart now** button. HUD: you can hide the original game HUD (Overhead only) and choose the overhead shape (Hexagon, Ring, Plate or Off). Fusion and CPU behaviour have their own pages.

### Controls
Player 1 and 2 use the controllers or keyboard assigned in the runtime overlay (press Shift+Tab, Controllers tab). Players 3 and 4 use their own gamepads. (Final control mapping text: TBD.)

### Uninstall
Use "Apps > Installed apps" in Windows. Your save games are kept unless you tick "also delete my saves". Your disc image is never touched.

### Troubleshooting
- "That disc isn't supported": the image is not the exact Power Scale BETA 1.5.1 build the installer expects.
- Black screen or crash: close the game, open the installed folder's `diagnostics` export (TBD) and send it with a description. No personal paths are included.
- Slow in big matches: 5v5 currently runs around 20-30 updates per second on a Ryzen 5700G; small matches run faster. Close other heavy programs.

### Credits
Power Scale: LetsPlayBt3 (https://www.youtube.com/channel/UCXiHmLmbgaSsFGrfejXESYw). Tag Team mod: The Mufti (https://www.youtube.com/channel/UCY79wsRvOdzBoe8GS77HY0A). Special thanks to RidJuampa for helping me understand the code. Third-party licences are listed in `THIRD-PARTY-LICENSES` (TBD).

---

## Espanol

### Que es
Dragon Ball Z: Budokai Tenkaichi 3 (Power Scale BETA 1.5.1) funcionando de forma nativa en Windows con el mod Tag Team integrado. Sin emulador, sin instalar Python por separado y sin ventanas auxiliares. Incluye batallas por equipos hasta 5v5, todos contra todos, cooperativo, entrenamiento modificado, hasta 4 jugadores locales, mini-HUD sobre los luchadores, opciones de transformacion de la CPU y controles de fusion en cooperativo.

### Que necesitas
- Un PC con Windows 10 u 11 (64 bits) con una GPU y controladores compatibles con Vulkan (version minima y funciones: por definir).
- Tu propia copia de la imagen de disco **Power Scale BETA 1.5.1**. Los archivos del juego NO estan incluidos; el instalador los importa desde tu imagen.
- Unos 12 GB libres en disco (por definir, la importacion crea una copia ampliada) y 8 GB de RAM o mas (por definir).
- Se recomienda un mando; el teclado tambien funciona.

### Instalacion
1. Descarga `BT3-TagTeam-...-Setup.exe` y compara su SHA256 con el publicado junto a la descarga.
2. Ejecutalo. Esta version **no esta firmada digitalmente**, asi que Windows SmartScreen puede decir "Windows protegio su PC". Pulsa **Mas informacion** y luego **Ejecutar de todas formas**. Algunos antivirus tambien pueden avisar por el entorno incluido; el codigo y los hashes estaran publicados (enlace por definir).
3. Se instala solo para tu usuario (sin permisos de administrador) y crea un acceso directo en el escritorio.

### Primer inicio
1. Abre **BT3 Tag Team** desde el acceso directo.
2. Cuando lo pida, elige tu imagen de disco Power Scale BETA 1.5.1. El juego la comprueba (un disco incorrecto o modificado se rechaza con un mensaje claro), amplia los mapas al doble y prepara el arte de la interfaz. La primera vez tarda unos minutos y necesita el espacio libre indicado. Tu imagen de disco nunca se modifica.
3. Tras los creditos, elige un modo en el menu del mod y juega.

### Ajustes
Abre el menu del mod y entra en Ajustes. La mayoria se aplica en la siguiente partida. Algunas opciones de inicio muestran "Reinicio necesario" con el boton **Reiniciar ahora**. HUD: puedes ocultar el HUD original (solo HUD superior) y elegir la forma (hexagono, anillo, placa o ninguna). La fusion y el comportamiento de la CPU tienen sus propias paginas.

### Controles
Los jugadores 1 y 2 usan los mandos o el teclado asignados en la superposicion del runtime (Shift+Tab, pestana Mandos). Los jugadores 3 y 4 usan sus propios mandos. (Texto final de controles: por definir.)

### Desinstalar
Usa "Aplicaciones > Aplicaciones instaladas" de Windows. Tus partidas guardadas se conservan salvo que marques "borrar tambien mis partidas". Tu imagen de disco nunca se toca.

### Problemas frecuentes
- "Ese disco no es compatible": la imagen no es la version exacta de Power Scale BETA 1.5.1 que espera el instalador.
- Pantalla negra o cierre inesperado: cierra el juego, abre la exportacion de `diagnostics` de la carpeta instalada (por definir) y enviala con una descripcion. No incluye rutas personales.
- Lento en partidas grandes: 5v5 funciona ahora a unas 20-30 actualizaciones por segundo en un Ryzen 5700G; las partidas pequenas son mas rapidas. Cierra otros programas pesados.

### Creditos
Power Scale: LetsPlayBt3 (https://www.youtube.com/channel/UCXiHmLmbgaSsFGrfejXESYw). Mod Tag Team: The Mufti (https://www.youtube.com/channel/UCY79wsRvOdzBoe8GS77HY0A). Agradecimiento especial a RidJuampa por ayudarme a entender el codigo. Las licencias de terceros estaran en `THIRD-PARTY-LICENSES` (por definir).
