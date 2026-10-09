# Installer snippets for Codex: single-language terms, language to mod, manual and finish page (drafted by Claude, 2026-10-09)

Nothing in `*.iss` or `app.pyw` was edited by me. Files I created (new): `installer/terms-en.txt`, `installer/terms-es.txt` (UTF-8 with BOM, CRLF), `manual/BT3-TagTeam-Manual-EN.html|pdf`, `manual/BT3-TagTeam-Manual-ES.html|pdf`.

## 1. One language per terms page
Today `LicenseFile=credits.txt` shows English and Spanish together. Replace it with one file per language inside `[Languages]`:

```
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"; LicenseFile: "terms-en.txt"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"; LicenseFile: "terms-es.txt"
```
and remove the global `LicenseFile=credits.txt` from `[Setup]`. Inno Setup 6 shows the file of the selected installer language; `terms-*.txt` are UTF-8 with BOM so accents render. Keep `credits.txt` only if something else reads it.

## 2. The installer language also sets the mod language
`app.pyw` already has a language choice (variable `LANG`, written to `mod-settings.json` as `language`, lines about 92 and 144-148) but it does not know which language the installer used. Make the installer record it, and let `app.pyw` use it as the first-run default:

```
[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var Lang: String;
begin
  if CurStep = ssPostInstall then
  begin
    if ActiveLanguage = 'spanish' then Lang := 'es' else Lang := 'en';
    SaveStringToFile(ExpandConstant('{app}\install-language.txt'), Lang, False);
  end;
end;
```
(merge into your existing `CurStepChanged`). In `app.pyw`: when there is no saved `language` yet (first run), initialise `LANG` from `install-language.txt` (`es` or `en`, fallback `en`), write it into `mod-settings.json` when the game data is created, and make the first-run window, the importer messages, the mod menus (`language` setting, EN/ES catalogue) and `PUBLIC` strings follow it. A later change in the app or in Mod settings still wins. An upgrade must not overwrite an existing `language` value. Add `install-language.txt` as an uninstall-owned file.

## 3. Manual shipped with the game
Copy the manual into the package: `Source: "manual\*"; DestDir: "{app}\manual"; Flags: ignoreversion recursesubdirs`. Files: `BT3-TagTeam-Manual-EN.pdf/.html`, `BT3-TagTeam-Manual-ES.pdf/.html` (the PDF is the main one; the HTML is a fallback). Also add a Start menu entry "BT3 Tag Team manual" (language-specific) next to the shortcuts.

## 4. Finish page with two checkboxes: see the manual, launch the game
Inno shows `[Run]` entries flagged `postinstall` as checkboxes on the last page:

```
[CustomMessages]
english.SeeManual=See the manual
spanish.SeeManual=Ver el manual
english.LaunchGame=Launch the game
spanish.LaunchGame=Iniciar el juego

[Run]
Filename: "{app}\manual\BT3-TagTeam-Manual-EN.pdf"; Description: "{cm:SeeManual}"; Flags: postinstall shellexec skipifsilent; Check: not IsSpanish
Filename: "{app}\manual\BT3-TagTeam-Manual-ES.pdf"; Description: "{cm:SeeManual}"; Flags: postinstall shellexec skipifsilent; Check: IsSpanish
Filename: "{app}\Play.exe"; Description: "{cm:LaunchGame}"; WorkingDir: "{app}"; Flags: postinstall nowait skipifsilent

[Code]
function IsSpanish: Boolean;
begin
  Result := ActiveLanguage = 'spanish';
end;
```
Default state: both checked. Both are skipped in silent mode so the gates are unaffected. The manual opens with the user's default PDF handler (a browser or reader); keep the `.html` as a fallback if no PDF handler exists (a `Check:` that tests the registry association, optional).

## 5. Gate additions
English install: terms page shows only English, `install-language.txt = en`, `language = en`. Spanish install: terms only Spanish, `es`, mod menus in Spanish at first launch. Upgrade keeps an existing language. The manual files exist and are language-matched; the finish page has exactly the two checkboxes (verify the compiled `[Run]` entries and flags); silent install launches nothing.
