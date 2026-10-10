# BT3 Tag Team + Real Power Scale — OpenGL compatibility preview

Separate Windows x64 edition based on v0.2-preview. The Vulkan edition remains available.

## English

- Uses the existing OpenGL game renderer plus a new OpenGL compositor for the native mod menus, credits, loading screens, HUD, revival and fusion prompts. Both backends share the same UI assets and layouts.
- Installs into `BT3TagTeam-OpenGL` with separate shortcuts and data. It does not upgrade the Vulkan installation. Import your own supported Power Scale BETA 1.5.1 ISO into this edition. Python and controller dependencies are included.
- Requires Windows 10/11 x64, a CPU with SSE4.1 and a working OpenGL 3.3 driver. Older GPU compatibility and minimum RAM are not certified. Import needs at least 12 GB free in the data drive.
- OpenGL may help with renderer compatibility. It is not a guarantee of better speed or identical graphics. Start with native rendering scale and smaller teams on slower PCs.
- Preserves v0.2's transformation safety restrictions, including destination 72 for extra fighters. No arena or Story Mode changes are included.
- Startup exceptions now retain their actual error in `data/startup.log` and show where to find the logs. Also send `data/launcher.log`, `data/native-port/power-scale-trial/runner.log` and `data/native-port/power-scale-trial/native-stderr.log`. A generic startup error is not evidence that reinstalling will help.
- A reported v0.2 startup failure on a Ryzen 7 5700G integrated Radeon machine was an access violation (`0xC0000005`) inside `amdvlk64.dll`, the AMD Vulkan driver. OpenGL avoids that Vulkan rendering path. This identifies the crash location, not whether its root cause is driver code or our Vulkan usage; acceptance on that particular PC is still needed.
- Offline rendering probes and packaged startup are checked separately from interactive combat. See the release verification manifest for actual results; full gameplay acceptance on low-end PCs remains pending.

## Español

- Usa el renderizador OpenGL del juego y un nuevo compositor OpenGL para los menús, créditos, pantallas de carga, HUD y avisos de resurrección y fusión del mod. Comparte el arte y los diseños con Vulkan.
- Se instala en `BT3TagTeam-OpenGL`, con accesos directos y datos separados. Importa tu propia ISO compatible de Power Scale BETA 1.5.1. Python y las dependencias del controlador están incluidos.
- Requiere Windows 10/11 de 64 bits, CPU con SSE4.1 y controlador OpenGL 3.3 funcional. No se han certificado la compatibilidad con GPU antiguas ni la RAM mínima. La importación necesita al menos 12 GB libres.
- OpenGL puede ayudar con la compatibilidad, pero no garantiza mayor velocidad ni gráficos idénticos. En equipos lentos, empieza con escala de renderizado nativa y equipos pequeños.
- Conserva las restricciones de seguridad de v0.2 para transformaciones. No incluye cambios de arenas ni del modo Historia.
- Si falla el inicio, envía `data/startup.log`, `data/launcher.log`, `data/native-port/power-scale-trial/runner.log` y `data/native-port/power-scale-trial/native-stderr.log`. El nuevo aviso muestra el error real y las rutas de los registros.
- El fallo de inicio reportado en un Ryzen 7 5700G ocurre dentro de `amdvlk64.dll` (controlador Vulkan de AMD), con código `0xC0000005`. OpenGL evita esa ruta de renderizado. Aún falta probar esta edición en ese equipo concreto.
- Las pruebas de renderizado e inicio se distinguen de la aceptación de combates interactivos. Consulta el manifiesto de verificación de la versión.
