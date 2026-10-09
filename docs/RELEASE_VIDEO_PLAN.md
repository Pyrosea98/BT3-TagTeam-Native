# Release video plan (Claude, 2026-10-09)

Goal: a 5 to 7 minute video that shows what BT3 Tag Team is, how to install it, and the new features. Record the footage with the NVIDIA recorder; Claude writes the script and shot list and assembles the final MP4 with ffmpeg (already installed at `C:\ProgramData\chocolatey\bin\ffmpeg.exe`).

## What Claude can and cannot do
- CAN: script, shot list, on-screen text and captions (EN and ES, as burned-in text or `.srt` files), title cards and thumbnail (drawn with Pillow in the game's Dragon Ball style), cutting and joining your clips, speed-ups, fades, zoom crops, audio levelling, final export, chapter timestamps and the YouTube description.
- CAN see your footage: I extract frames with ffmpeg and look at them, so I can find the right moments and check the framing.
- CAN make a rough voice-over with the Windows voices installed here (Zira en-US, Hazel en-GB, Sabina es-MX), but it sounds robotic. A real voice-over by you is better; I can write it line by line with timings.
- CANNOT record gameplay, generate new footage, or produce music. Use royalty-free music (YouTube Audio Library) or none.

## Existing footage
`C:\Users\JUAN\Videos\Ps2xruntime\` has two long recordings from 2026-10-07 (about 1 GB and 1.4 GB). They predate the new HUD, CPU tactics, fusion controls, revive arc and the installer, so new clips are needed.

## Shot list (record each as its own short clip, 15 to 40 seconds, game window only, 16:9 if possible)
1. **Intro:** the boot credits screen and the mod menu (mode list, Settings page in the DBZ look).
2. **Installer (record LAST, after the final build):** download hash, SmartScreen "More info, Run anyway", language page (English), terms page, folder page, optional shortcuts and the "all content unlocked" checkbox, finish page (manual and launch checkboxes), first-run disc import progress (speed this one up).
3. **Overhead HUD:** original HUD vs "Overhead only"; hexagon and ring; the "Everyone" level in a free-for-all with 6 to 10 fighters; target switch with L3; a cinematic fade; pause hiding it.
4. **Fusion:** the transformation list with the fusion entry, the "R3 FUSE" prompt on the partner, the fusion arc and swap arc, a control swap, defusion; a Potara fusion (no timer) next to a Fusion Dance (timed); form drain (the arc draining faster after a transformation).
5. **CPU tactics:** the CPU tactics settings page; an allied CPU transforming early with Aggressive; two enemy CPUs fusing into Vegito and Gogeta.
6. **Revive:** a fallen ally, the revive arc filling, stock pips, completion.
7. **Co-op and players:** 2 humans in split screen with the overhead markers; (when ready) 3 or 4 players and the P3/P4 controller options in the Shift+Tab overlay.
8. **Modes:** a team battle 5v5 (Ready/FIGHT), free-for-all, Modded Training.
9. **Outro:** credits (Power Scale: LetsPlayBt3, Tag Team mod: The Mufti, special thanks RidJuampa), the download link and the "unofficial fan project, bring your own disc" notice.

## Script outline (about 650 words English; Spanish version written the same way)
- 0:00 Hook: "Budokai Tenkaichi 3, Power Scale and the Tag Team mod, now as one standalone Windows game."
- 0:20 What it is and what you need (your own Power Scale BETA 1.5.1 disc image; nothing from the game is included).
- 0:50 Installing: SmartScreen (the build is unsigned), folder choice, language, unlock choice, shortcuts, the import step (10 to 15 minutes, 12 GB free), the manual.
- 2:00 The new overhead HUD and how to hide the original one.
- 3:00 Fusions: prompt, control modes, swap time, fusion time and form drain.
- 4:15 CPU tactics and revive.
- 5:15 Players, modes and the settings pages.
- 6:00 Credits, links, where to report bugs (attach the log).

## Pipeline once the clips exist
1. You copy the clips into `native-port\video\raw\` and tell me which shot each one is.
2. I extract thumbnails, pick the cuts, and write a `cuts.json`.
3. ffmpeg trims and joins them, burns in the captions, adds the title cards and the outro, and exports `BT3-TagTeam-Release-EN.mp4` and a Spanish version.
4. You review; I adjust the cuts. Final files stay local until you decide to publish.

## What I need from you
- OK to read the files in `C:\Users\JUAN\Videos\Ps2xruntime\` and to create `native-port\video\`.
- Record the clips above after the next build (HUD, fusion, CPU and 4-player features are still being finished; the installer clips must come from the FINAL installer).
- Choose: English video, Spanish video, or both; and voice-over by you or the Windows voice.

## Status 2026-10-09 (captions only, no voice, English and Spanish)
- Permission given by the user to read `C:\Users\JUAN\Videos\Ps2xruntime\` and to create `native-port\video\`. Recording format of his NVIDIA recorder: **2560x1080 (21:9), 60 fps, H.264**; the video is built at 2560x1080 with the same size so nothing is scaled.
- DONE and tested: `claude_video_cards.py` (title, install, hud, fusion, cpu, revive, players and outro cards, EN and ES, in `video/cards/`), `claude_build_video.py` (cuts.json to two MP4s, one per language, with burned-in captions and `.srt` files; it skips clips that are not recorded yet), and `video/cuts.template.json` (the whole video with captions in both languages, waiting for the raw clips). A 24-second test with old footage built both languages in 38 s: `video/out/pipeline-test-EN.mp4` and `-ES.mp4`.
- NEXT: the user records the clips named in `cuts.template.json` (`raw/01-intro-menu.mp4`, `02-installer.mp4`, `02b-import.mp4`, `03-hud.mp4`, `04-fusion.mp4`, `05-cpu.mp4`, `06-revive.mp4`, `07-players-modes.mp4`) after the next build, copies them into `native-port\video\raw\`, and tells Claude; Claude then picks the best start and end times from frame sheets and builds the final videos. The old clips from 2026-10-07 and 2026-10-05 show the previous HUD and menus, so they are used for tests only.
