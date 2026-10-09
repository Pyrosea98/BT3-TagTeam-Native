# First public installer: release checklist (Claude, 2026-10-08)

Goal: a build external testers and players can install without help. Everything here must be CONFIRMED before publishing; gaps are listed as blockers.

## Legal and content
- The installer ships NO game assets (no ISO, ELF, AFS, UI art, or save icons of the game): the player's own Power Scale BETA 1.5.1 disc is imported (already the design). The packed progression save contains no game assets; confirm it is fine to distribute (it is our own save data).
- Credits as decided (Power Scale: LetsPlayBt3, Tag Team mod: The Mufti, with links; special thanks: RidJuampa). A third-party licence file for every bundled component (embedded CPython and wheels, Pillow, pycdlib, psutil, numpy, capstone, pyelftools, zstandard, comtypes, pycaw, SDL2, Vulkan/paraLLEl-GS, fonts Kanit and Barlow under OFL), shown in About and in the install folder.
- A clear "unofficial fan project, not affiliated" notice and the disc requirement on the first page. The creators of Power Scale and the Tag Team mod are informed and agree to the distribution (user to confirm).

## Installer quality
- Code signing, or an explicit SmartScreen/antivirus note: embedded Python plus an unsigned exe will trigger false positives. Test on Defender, check a few AV scanners, publish the SHA256 and the exact version.
- Clean-machine tests on fresh Windows 10 and 11 profiles, a VM, and a PC with only an integrated GPU: install, import, 1v1, 5v5, FFA, co-op, save and relaunch, normal quit leaves no process or console, uninstall keeps saves, upgrade keeps settings.
- Minimum-requirements check at first run: Vulkan version and features needed by paraLLEl-GS, GPU driver age, RAM, free disk (the import needs about 2x the ISO), with plain-language messages (no stack traces) and a "copy diagnostics" button.
- Performance expectations stated honestly (5v5 runs about 20-30 updates/s today, small matches up to 60); a frame cap option; shader/pipeline cache warm-up.
- Version number in the installer, the About page and the logs. Update path: re-running a newer installer keeps data. A "known issues" file and a visible feedback route (sanitised log export: no disc path, no user name).

## Product gaps to close before public
- Restage with the latest slices (fusion/CPU work, the quiet shutdown fix). Unlock option decision (the packed save is already the progress save). CPU fusion and revive are optional extras.
- Settings that still have no native effect (legacy emulator-only `widescreen_patch`, `fast_disc_loading`, `emulated_cpu_speed`) must be hidden or labelled so testers are not misled.
- Crash handling: the unsupported-PC and guest-exit capture folders stay local only; add an "export diagnostics" bundle.
