# DBZ settings and mode menus

Trial executable: `repo/build/ps2xRuntime/ps2EntryRunner-dbz-menus-polish.exe`

SHA256: `485421E356BB80883F3296B6BE2EBDE9CF97CD1E968D32502F9AB723EC703DAB`

Both UI trial launchers select this build. No live game was launched for this change.

## Presentation

Settings and About now share the boot credits' opaque dark-blue gradient,
subtle stars, gold rules, seven Dragon Balls and flat blue panels. Existing
fonts, row positions, text/value columns, EN/ES labels and About links remain.
Selection has a gold left edge and underline. Battle portrait frames and
stretched banner art are absent from these pages.

`codex_native_mode_style.py` presents the existing guest mode menu through the
same native renderer. Guest code still owns input, sounds, choices and the
return route. It publishes only an authenticated custom menu with matching
owner, page, row IDs and live lease. Original menus are excluded. It closes its
surface before settings/About/team setup takes ownership; a newly opened
settings surface is never closed by the previous menu. No additional mode
presentation RAM reads occur before its first native surface exists.

The mode footer retains up to two wrapped description lines plus navigation.
Settings keep their original two-line footer. Existing long settings labels
still use the renderer's ellipsis policy. Controller-assignment/team-setup
dialogs retain their separate existing guest presentation.

## Review and evidence

`power-scale-trial/dbz-menu-polish-review/contact-sheet.png`: all 162 captures, EN/ES
pairs. `index.html` is the same contact sheet with clickable full-size images.
Coverage per language: three index pages, 18 settings segments, 14 group help
pages, five option-help pages, 32 character-exception pages, three confirmation
pages, About, and six mode-menu pages (including legacy submenu definitions).
The fixture generator calls the real settings publisher and mode page model.
`manifest.json` records every title, row, value and footer.

Run `codex_dbz_menu_review.py` to reproduce the fixture packets, native Vulkan
readbacks and contact sheet without a game, ISO or PINE connection.
`vulkan-check.log` records 162 PASS results and CPU compose samples.
`codex_ui_adapter_check.py` passed real settings transport/navigation,
localization persistence, links, acknowledgement and concurrency checks.
`codex_native_mode_style_check.py` passed ownership, unsigned cursor wrap,
changing lease and cross-surface handoff checks.

Visual samples reviewed: root mode menu, Spanish training footer, Spanish
fighter settings, last exception page, About and full contact sheet.
Build completed successfully; stable three runner hashes remain unchanged.

Live native mode-overlay navigation and transition timing remain unverified.
Claude approved the original contact sheet. URLs and the About build label/value
now use a separate upright Body atlas made from the existing bundled OFL
Liberation Sans Regular font at 12px. Display text retains its accepted font.
EN/ES thanks use a balanced two-line word split. Updated full-size About captures
were visually reviewed and all162 new captures passed. Existing disc caches add
the upright font without re-extracting game art. The previous build is preserved.

Test mode selection, settings/About entry
and return, Original-menu toggle and starting a prepared match. Previously
accepted gameplay changes are included; no new gameplay/performance fix is
claimed by this styling slice.

## Installer correction

The later user correction restores only the mode list to its original guest
presentation: native mode-style registration is disabled. DBZ Settings and its
child screens stay, and the DBZ About screen stays from both entry points.
Earlier mode-overlay captures document the superseded design. They are not
evidence for the restored mode list. One live mode/settings capture is pending;
installer work takes priority over another contact sheet.
