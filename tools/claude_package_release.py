"""Claude: build the GitHub release ZIP for an installer (no publishing).

Usage: python claude_package_release.py <Setup.exe> <version> [--out installer/release]
Creates <out>/BT3-TagTeam-<version>-Windows.zip containing: the Setup.exe, SHA256SUMS.txt, README.txt (EN/ES), LICENSE, NOTICE,
THIRD_PARTY_NOTICES.md, SOURCE.txt (repo links + exact commits = GPLv3 source offer), plus <out>/RELEASE_NOTES.md (EN/ES)
and <out>/SHA256SUMS.txt. It refuses to run when the two repositories are not clean and pushed (the commits named in
SOURCE.txt must exist on GitHub), unless --allow-dirty is passed (dry run).
"""
import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
WS = HERE.parent
RUNTIME = HERE / 'repo'
NATIVE = WS / 'repo-staging' / 'BT3-TagTeam-Native'
URLS = {
    'native': 'https://github.com/Pyrosea98/BT3-TagTeam-Native',
    'runtime': 'https://github.com/Pyrosea98/BT3-TagTeam-Runtime',
    'upstream_mod': 'https://github.com/tehmufti/Budokai-Tenkaichi-3-Tag-Team-Mod-PCSX2-',
    'upstream_runtime': 'https://github.com/z3xox/BT3-Recomp',
}


def git(repo, *args):
    r = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True)
    return r.stdout.strip()


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def repo_state(repo, branch, remote):
    commit = git(repo, 'rev-parse', 'HEAD')
    dirty = bool(git(repo, 'status', '--porcelain', '--untracked-files=no'))
    pushed = git(repo, 'branch', '-r', '--contains', commit).find(remote + '/') >= 0
    return commit, dirty, pushed


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) < 2:
        print(__doc__)
        return 2
    exe, version = Path(args[0]), args[1]
    out = HERE / 'installer' / 'release'
    if '--out' in sys.argv:
        out = Path(sys.argv[sys.argv.index('--out') + 1])
    allow_dirty = '--allow-dirty' in sys.argv
    if not exe.exists():
        print('installer not found:', exe)
        return 2
    n_commit, n_dirty, n_pushed = repo_state(NATIVE, 'main', 'origin')
    r_commit, r_dirty, r_pushed = repo_state(RUNTIME, 'tagteam-native', 'tagteam')
    problems = []
    if n_dirty or not n_pushed:
        problems.append(f'BT3-TagTeam-Native not clean/pushed (commit {n_commit[:10]}, dirty={n_dirty}, pushed={n_pushed})')
    if r_dirty or not r_pushed:
        problems.append(f'BT3-TagTeam-Runtime not clean/pushed (commit {r_commit[:10]}, dirty={r_dirty}, pushed={r_pushed})')
    if problems and not allow_dirty:
        print('REFUSING: the commits named in SOURCE.txt must be pushed.\n  ' + '\n  '.join(problems))
        return 3
    out.mkdir(parents=True, exist_ok=True)
    exe_hash = sha256(exe)
    zip_name = f'BT3-TagTeam-{version}-Windows.zip'
    notice_files = {
        'LICENSE': NATIVE / 'LICENSE',
        'NOTICE': NATIVE / 'NOTICE',
        'THIRD_PARTY_NOTICES.md': NATIVE / 'THIRD_PARTY_NOTICES.md',
    }
    readme = f"""BT3 Tag Team Native {version} (Windows, 64-bit)
=====================================================
Unofficial fan project. Not affiliated with the owners of Dragon Ball or Budokai Tenkaichi.
Built on The Mufti's Tag Team Mod ({URLS['upstream_mod']}). Power Scale: LetsPlayBt3.

ENGLISH
1. Check the SHA256 of {exe.name} against SHA256SUMS.txt:  Get-FileHash {exe.name}
2. Run {exe.name}. This build is NOT code-signed, so Windows SmartScreen may warn: choose "More info", then "Run anyway".
3. Pick the install folder (the game data goes in a "data" folder inside it). You need about 12 GB of free space on that drive.
4. On first run pick YOUR OWN Power Scale BETA 1.5.1 disc image. No game files are included; your disc image is never modified.
5. The manual (English and Spanish PDF) is installed with the game and opens from the finish page or the Start menu.

ESPANOL
1. Comprueba el SHA256 de {exe.name} con SHA256SUMS.txt:  Get-FileHash {exe.name}
2. Ejecuta {exe.name}. Esta version NO esta firmada digitalmente, asi que SmartScreen puede avisar: pulsa "Mas informacion" y luego "Ejecutar de todas formas".
3. Elige la carpeta de instalacion (los datos del juego van en una carpeta "data" dentro). Necesitas unos 12 GB libres en esa unidad.
4. En el primer inicio elige TU PROPIA imagen del disco Power Scale BETA 1.5.1. No se incluyen archivos del juego; tu imagen nunca se modifica.
5. El manual (PDF en ingles y espanol) se instala con el juego y se abre desde la pagina final o el menu Inicio.

Source code (GPL-3.0): see SOURCE.txt.
"""
    source = f"""SOURCE OFFER (GPL-3.0)
======================
This build is distributed under the GNU General Public License v3. The complete corresponding source code is public:

Project (controller, installer sources, manual, tools): {URLS['native']}
  commit {n_commit}
Native runtime (branch tagteam-native): {URLS['runtime']}
  commit {r_commit}
Derived from: The Mufti's Tag Team Mod {URLS['upstream_mod']} (GPL-3.0) and z3xox's BT3-Recomp {URLS['upstream_runtime']} (GPL-3.0).

Installer: {exe.name}  SHA256 {exe_hash}
No game files are included. Third-party licences: THIRD_PARTY_NOTICES.md and the notices folder installed with the game.
"""
    sums = f'{exe_hash}  {exe.name}\n'
    zpath = out / zip_name
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.write(exe, exe.name)
        z.writestr('README.txt', readme)
        z.writestr('SOURCE.txt', source)
        z.writestr('SHA256SUMS.txt', sums)
        for name, path in notice_files.items():
            z.write(path, name)
    zip_hash = sha256(zpath)
    (out / 'SHA256SUMS.txt').write_text(f'{exe_hash}  {exe.name}\n{zip_hash}  {zip_name}\n', encoding='utf-8')
    notes = f"""# BT3 Tag Team Native {version}

## English
A standalone Windows build of Dragon Ball Z: Budokai Tenkaichi 3 (Power Scale BETA 1.5.1) with The Mufti's Tag Team Mod built in, running natively without an emulator.
**You must bring your own Power Scale BETA 1.5.1 disc image.** No game files are included.

- Download `{zip_name}`, extract it and run the installer. The build is **unsigned**: SmartScreen may warn (More info, Run anyway). Check the SHA256 in `SHA256SUMS.txt`.
- Installs per user, no administrator rights. About 12 GB free space needed. English and Spanish.
- Includes the overhead HUD, fusion control modes with timers and form drain, CPU tactics, revive arc, up to five fighters per side, free-for-all, co-op and Modded Training, and the player manual (EN/ES).
- Known limits: see the manual, section "Known limits of this preview".

SHA256 of the zip: `{zip_hash}`

## Espanol
Version independiente para Windows de Dragon Ball Z: Budokai Tenkaichi 3 (Power Scale BETA 1.5.1) con el Tag Team Mod de The Mufti integrado, sin emulador.
**Debes traer tu propia imagen de disco Power Scale BETA 1.5.1.** No se incluyen archivos del juego.

- Descarga `{zip_name}`, extraelo y ejecuta el instalador. La version **no esta firmada**: SmartScreen puede avisar (Mas informacion, Ejecutar de todas formas). Comprueba el SHA256 en `SHA256SUMS.txt`.
- Se instala por usuario, sin permisos de administrador. Unos 12 GB libres. Ingles y espanol.
- Incluye el HUD sobre los luchadores, modos de control de fusion con temporizadores y desgaste por forma, tacticas de la CPU, arco de revivir, hasta cinco luchadores por lado, todos contra todos, cooperativo y entrenamiento modificado, y el manual (EN/ES).
- Limites conocidos: consulta la seccion correspondiente del manual.

## Source / Codigo fuente (GPL-3.0)
- Project: {URLS['native']} (commit `{n_commit[:12]}`)
- Runtime: {URLS['runtime']} (commit `{r_commit[:12]}`)
- Built on: {URLS['upstream_mod']}

Unofficial fan project, not affiliated with the owners of Dragon Ball. / Proyecto de fans no oficial, sin relacion con los duenos de Dragon Ball.
"""
    (out / 'RELEASE_NOTES.md').write_text(notes, encoding='utf-8')
    print('zip      ', zpath, f'({zpath.stat().st_size / 1e6:.1f} MB)')
    print('zip sha  ', zip_hash)
    print('exe sha  ', exe_hash)
    print('native   ', n_commit[:12], 'dirty' if n_dirty else 'clean', 'pushed' if n_pushed else 'NOT pushed')
    print('runtime  ', r_commit[:12], 'dirty' if r_dirty else 'clean', 'pushed' if r_pushed else 'NOT pushed')
    if problems:
        print('WARNING (dry run, not publishable):', *problems, sep='\n  ')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
