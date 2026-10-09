#define AppVersion "0.1"
[Setup]
AppId=BT3CodexBrandingGate-20261009
AppName=BT3 Codex Branding Gate
AppVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\BT3TagTeam
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\Play.exe
SetupIconFile=assets\BT3TagTeam.ico
OutputDir=output
OutputBaseFilename=BT3-Branding-Options-Gate
Compression=lzma2
SolidCompression=yes
WizardStyle=modern dark
DisableProgramGroupPage=yes
LicenseFile=credits.txt
CloseApplications=no
RestartApplications=no
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
[CustomMessages]
english.DesktopShortcut=Create a desktop shortcut
spanish.DesktopShortcut=Crear un acceso directo en el escritorio
english.StartMenuShortcut=Create a Start menu shortcut
spanish.StartMenuShortcut=Crear un acceso directo en el menú Inicio
english.SaveTitle=Starting progression
spanish.SaveTitle=Progreso inicial
english.SaveDescription=Choose how your first save starts.
spanish.SaveDescription=Elige cómo empieza tu primera partida guardada.
english.SaveChoice=Start with all content unlocked
spanish.SaveChoice=Empezar con todo el contenido desbloqueado
english.SaveDetail=Applies only when no save exists. Existing progress is always kept.
spanish.SaveDetail=Solo se aplica si no hay partida guardada. Siempre se conserva el progreso existente.
[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopShortcut}"
Name: "startmenuicon"; Description: "{cm:StartMenuShortcut}"
[Files]
Source: "payload\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{autodesktop}\BT3 Codex Branding Gate"; Filename: "{app}\Play.exe"; WorkingDir: "{app}"; IconFilename: "{app}\assets\BT3TagTeam.ico"; Tasks: desktopicon
Name: "{userprograms}\BT3 Codex Branding Gate\BT3 Codex Branding Gate"; Filename: "{app}\Play.exe"; WorkingDir: "{app}"; IconFilename: "{app}\assets\BT3TagTeam.ico"; Tasks: startmenuicon
[Code]
var DeleteSaves, DeleteData: Boolean; ResolvedDataRoot: String; SavePage: TWizardPage; UnlockBox: TNewCheckBox;
function PlayerDataRoot: String;
var Text: AnsiString; Legacy: String;
begin
  Result := GetEnv('BT3_TAGTEAM_DATA');
  if Result <> '' then exit;
  if LoadStringFromFile(ExpandConstant('{app}\data-root.txt'), Text) then begin
    Result := Trim(UTF8Decode(Text)); exit;
  end;
  Legacy := ExpandConstant('{localappdata}\BT3TagTeam');
  if FileExists(ExpandConstant('{app}\Play.exe')) and FileExists(Legacy+'\app-owned.json') then Result := Legacy
  else Result := ExpandConstant('{app}\data');
end;
procedure InitializeWizard;
var Detail: TNewStaticText;
begin
  SavePage := CreateCustomPage(wpSelectTasks,CustomMessage('SaveTitle'),CustomMessage('SaveDescription'));
  UnlockBox := TNewCheckBox.Create(SavePage); UnlockBox.Parent := SavePage.Surface;
  UnlockBox.SetBounds(0,ScaleY(15),SavePage.SurfaceWidth,ScaleY(35));
  UnlockBox.Caption := CustomMessage('SaveChoice'); UnlockBox.Checked := (CompareText(ExpandConstant('{param:UNLOCKED|yes}'),'no') <> 0);
  Detail := TNewStaticText.Create(SavePage); Detail.Parent := SavePage.Surface;
  Detail.SetBounds(0,ScaleY(65),SavePage.SurfaceWidth,ScaleY(60)); Detail.WordWrap := True; Detail.Caption := CustomMessage('SaveDetail');
end;
function PrepareToInstall(var NeedsRestart: Boolean): String;
var Probe: String;
begin
  Result := ''; ResolvedDataRoot := PlayerDataRoot;
  Probe := ExpandConstant('{app}\bt3-write-test.tmp');
  if not ForceDirectories(ExpandConstant('{app}')) or not SaveStringToFile(Probe,'test',False) then begin
    Result := 'This installation folder is not writable. Choose a folder owned by your account, such as Local AppData, or another drive.'; exit;
  end;
  DeleteFile(Probe);
end;
procedure CurStepChanged(CurStep: TSetupStep);
var Choice: String;
begin
  if CurStep = ssPostInstall then begin
    if not SaveStringToFile(ExpandConstant('{app}\data-root.txt'),UTF8Encode(ResolvedDataRoot),False) then
      RaiseException('Could not save the game data location.');
    if not FileExists(ResolvedDataRoot+'\save-start-choice.json') then begin
      if UnlockBox.Checked then Choice := '{"schema":1,"all_unlocked":true}'
      else Choice := '{"schema":1,"all_unlocked":false}';
      if not ForceDirectories(ResolvedDataRoot) or not SaveStringToFile(ResolvedDataRoot+'\save-start-choice.json',UTF8Encode(Choice),False) then
        RaiseException('Could not save the starting progression choice.');
    end;
  end;
end;
function InitializeUninstall: Boolean;
var Form: TSetupForm; DataBox, SavesBox: TNewCheckBox; Button: TNewButton;
begin
  ResolvedDataRoot := PlayerDataRoot;
  Result := True; DeleteSaves := False; DeleteData := False;
  DeleteFile(ExpandConstant('{app}\uninstall-choice.txt'));
  if UninstallSilent then begin
    DeleteData := (Pos('/DELETEGAMEDATA',Uppercase(GetCmdTail)) > 0);
    DeleteSaves := DeleteData and (Pos('/DELETESAVES',Uppercase(GetCmdTail)) > 0); exit;
  end;
  Form := CreateCustomForm(ScaleX(480),ScaleY(210),False,True);
  try
    Form.Caption := 'BT3 Tag Team'; Form.ClientWidth := ScaleX(480); Form.ClientHeight := ScaleY(210);
    DataBox := TNewCheckBox.Create(Form); DataBox.Parent := Form; DataBox.SetBounds(ScaleX(20),ScaleY(25),ScaleX(440),ScaleY(45)); DataBox.Checked := False;
    SavesBox := TNewCheckBox.Create(Form); SavesBox.Parent := Form; SavesBox.SetBounds(ScaleX(20),ScaleY(80),ScaleX(440),ScaleY(45)); SavesBox.Checked := False;
    if ActiveLanguage = 'spanish' then begin
      DataBox.Caption := 'Eliminar tambien mis datos de juego (conservar partidas)'; SavesBox.Caption := 'Eliminar tambien mis partidas (requiere eliminar datos)';
    end else begin
      DataBox.Caption := 'Also delete my game data (keep saves)'; SavesBox.Caption := 'Also delete my saves (requires deleting game data)';
    end;
    Button := TNewButton.Create(Form); Button.Parent := Form; Button.SetBounds(ScaleX(270),ScaleY(160),ScaleX(90),ScaleY(25)); Button.Caption := 'OK'; Button.ModalResult := mrOk; Button.Default := True;
    Button := TNewButton.Create(Form); Button.Parent := Form; Button.SetBounds(ScaleX(370),ScaleY(160),ScaleX(90),ScaleY(25)); Button.Caption := SetupMessage(msgButtonCancel); Button.ModalResult := mrCancel; Button.Cancel := True;
    Result := Form.ShowModal = mrOk;
    if Result then begin
      DeleteData := DataBox.Checked; DeleteSaves := DeleteData and SavesBox.Checked;
      if DeleteSaves then SaveStringToFile(ExpandConstant('{app}\uninstall-choice.txt'),'all',False)
      else if DeleteData then SaveStringToFile(ExpandConstant('{app}\uninstall-choice.txt'),'data',False);
    end;
  finally Form.Free; end;
end;
function DataOwned: Boolean;
var Text: AnsiString;
begin
  Result := (Length(ResolvedDataRoot) > 3) and
    (CompareText(RemoveBackslashUnlessRoot(ResolvedDataRoot),RemoveBackslashUnlessRoot(ExpandConstant('{app}'))) <> 0) and
    LoadStringFromFile(ResolvedDataRoot+'\app-owned.json',Text) and (Pos('BT3TagTeam-initial-0.1',String(Text)) > 0);
end;
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var Root: String; Names: TArrayOfString; I: Integer; Find: TFindRec; Choice: AnsiString;
begin
  if CurUninstallStep = usUninstall then begin
    { InitializeUninstall runs in phase one; capture again in the deleting process. }
    ResolvedDataRoot := PlayerDataRoot;
    DeleteData := False; DeleteSaves := False;
    if UninstallSilent then begin
      DeleteData := (Pos('/DELETEGAMEDATA',Uppercase(GetCmdTail)) > 0);
      DeleteSaves := DeleteData and (Pos('/DELETESAVES',Uppercase(GetCmdTail)) > 0);
    end else if LoadStringFromFile(ExpandConstant('{app}\uninstall-choice.txt'),Choice) then begin
      DeleteData := (Choice = 'data') or (Choice = 'all'); DeleteSaves := Choice = 'all';
    end;
    DeleteFile(ExpandConstant('{app}\uninstall-choice.txt'));
    Log('Game data root: '+ResolvedDataRoot);
    if DeleteData then Log('Explicit game data removal selected');
    if DeleteSaves then Log('Explicit save removal selected');
  end;
  if (CurUninstallStep = usPostUninstall) and DeleteData and DataOwned then begin
    Root := ResolvedDataRoot;
    { Remove only named app-owned content. Keep saves unless separately selected. }
    Names := ['native-port','import','restart-request.json','sources-ready.json','launcher.log','runtime-check.json','package-check.json','save-start-choice.json'];
    for I := 0 to GetArrayLength(Names)-1 do begin
      if DirExists(Root+'\'+Names[I]) then DelTree(Root+'\'+Names[I],True,True,True)
      else DeleteFile(Root+'\'+Names[I]);
    end;
    if FindFirst(Root+'\import-*',Find) then begin
      try repeat
        if (Find.Attributes and FILE_ATTRIBUTE_DIRECTORY <> 0) and (Find.Attributes and FILE_ATTRIBUTE_REPARSE_POINT = 0) then
          DelTree(Root+'\'+Find.Name,True,True,True);
      until not FindNext(Find); finally FindClose(Find); end;
    end;
    if DeleteSaves then DelTree(Root+'\saves',True,True,True);
    if DeleteSaves then DeleteFile(Root+'\app-owned.json');
    RemoveDir(Root);
  end;
end;

