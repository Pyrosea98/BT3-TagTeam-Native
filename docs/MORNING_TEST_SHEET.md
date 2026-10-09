# Morning test sheet (written by Claude, 2026-10-09)

Goal: check the newest installer and the open bugs in about 45 minutes. Tick what works, write what does not. Anything marked REPORT should go to Claude with the screenshot or the log line.

## 0. Before you start (2 minutes)
- [ ] C: has more than 25 GB free (it had 76 GB after the cleanup). Check D: has at least 15 GB if you install there.
- [ ] No game is running. Close any old install: delete `D:\Games\BT3TagTeam` if it still exists (it is already gone).
- [ ] Installer: `native-port\installer\output\BT3-TagTeam-Preview-0.1-Setup.exe`. Expected SHA256 starts `a9f2535d`. Check with: `Get-FileHash <file>` in PowerShell. If Codex rebuilt it, the new hash will be in the board (COLLAB.md).

## 1. Installer (10 minutes)
- [ ] Run it. Windows SmartScreen warns: More info, Run anyway. (Expected, the build is unsigned.)
- [ ] Language page: pick English once, Spanish on a second run. REPORT if the terms page shows both languages together (it should show one) and if the game and menus follow your choice (needs Codex's newer build).
- [ ] Destination page: choose `D:\Games\BT3TagTeam`.
- [ ] Save choice: "Start with all content unlocked" is checked by default. Untick it once to test the fresh save.
- [ ] Shortcuts: desktop and Start menu are optional checkboxes. The icon is the two orange balls on a blue tile.
- [ ] Finish page: two checkboxes (see the manual, launch the game) if Codex has added them. REPORT if missing.
- [ ] After install: `D:\Games\BT3TagTeam\data` exists and `data-root.txt` points to it.

## 2. First run and import (10 minutes)
- [ ] Play opens with the boot credits (DBZ look, RidJuampa line).
- [ ] Import: pick the original Power Scale BETA 1.5.1 ISO. The stages say verifying, expanding maps, preparing interface art. It needs about 12 GB free. REPORT any error text.
- [ ] After import the game reaches the original main menu. Press the menu switch button to open the mod menus.

## 3. The two screens that were broken (10 minutes) (REPORT with a screenshot)
- [ ] Mod menu, Team battle, choose 2 human players: does the **team and controller setup screen** appear and can you read it?
- [ ] After the setup screen, is there a **loading cover** before character select? (Settings, Menus, "Decorative mode loading cover" may need to be on, then a restart.)
- [ ] Look at the controller log line `loading hook out of date` in `data\native-port\power-scale-trial\controller.log`. REPORT if present.

## 4. Matches (15 minutes)
- [ ] 1 human, normal characters (for example Goku Fin and Vegeta against Kid Buu), CPU tactics on Native: does the match start? REPORT "Match preparation failed" with the exact error line.
- [ ] Same match with CPU tactics on More often and Aggressive: starts? (This is the installed-build failure we saw: "Native ordinary side-eligibility call changed".)
- [ ] 2v3 with Goku Black on a team: loads?
- [ ] Free-for-all with 4 or more fighters: READY and FIGHT banners play; overhead markers show for everyone with the Everyone level.
- [ ] 5v5: runs, wins, Fight Again works. Note the speed feeling.
- [ ] Kill an enemy: only the new kill plate appears, no old pixel text at the top left.
- [ ] Revive a fallen ally (turn on Settings, Revival): the arc fills and shows the stock pips.

## 5. Fusion (10 minutes)
- [ ] Goku Black (Rose) and Zamasu, two humans: select the Pothala entry in each transformation menu and confirm. Does it start? REPORT who pressed, the screen, the log.
- [ ] Super Goku and Super Vegeta together: what does each fusion menu ask for?
- [ ] Gotenks or Gogeta fusion with fusion duration and form drain on: arc visible, drains faster in higher forms, defusion works.
- [ ] CPU Goku and Vegeta fuse on their own: note whether it is always Vegito.

## 6. Quit and cleanliness (3 minutes)
- [ ] Close the game window normally. No console window stays open and no `python`, `pythonw` or `cmd` of ours stays in Task Manager after 10 seconds.
- [ ] Reopen from the desktop shortcut: no re-import, your save and settings are still there.
- [ ] Uninstall from Windows settings: the two optional checkboxes appear; leave both unticked first, confirm the data folder is kept.

## What to send me
For each failure: the exact message, what you were doing, the screenshot, and these files if they exist: `D:\Games\BT3TagTeam\data\launcher.log`, `data\native-port\power-scale-trial\controller.log`, `runner.log`, and any folder in `data\native-port\power-scale-trial\guest-exit-captures`.
