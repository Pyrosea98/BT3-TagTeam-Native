[Setup]
AppId=BT3TagTeam-Update-v05
AppName=BT3 Tag Team — Update
AppVersion=0.5.alpha.3
VersionInfoVersion=0.5.0.3
DefaultDirName={localappdata}\Programs\BT3TagTeam-v041
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=payload\assets\BT3TagTeam.ico
OutputDir=release
OutputBaseFilename=BT3-TagTeam-v0.5.alpha.3-Windows-Update-Setup
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern dark
DisableProgramGroupPage=yes
DisableReadyPage=no
CreateAppDir=yes
DisableDirPage=no
UsePreviousAppDir=no
AppendDefaultDirName=no
CreateUninstallRegKey=no
Uninstallable=no
DirExistsWarning=no
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
[Files]
Source: "update\payload\*"; DestDir: "{tmp}\bt3-update\payload"; Flags: ignoreversion recursesubdirs createallsubdirs deleteafterinstall
Source: "payload\update_ui.py"; DestDir: "{tmp}\bt3-update"; Flags: deleteafterinstall
Source: "payload\update_engine.py"; DestDir: "{tmp}\bt3-update"; Flags: deleteafterinstall
Source: "payload\channel_updates.py"; DestDir: "{tmp}\bt3-update"; Flags: deleteafterinstall
[Code]
var UpdateFailed: Boolean;
function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = wpSelectDir then begin
    if not FileExists(ExpandConstant('{app}\runtime\pythonw.exe')) or not FileExists(ExpandConstant('{app}\release-profile.json')) then begin
      MsgBox('Choose your existing BT3 Tag Team installation. / Elige tu instalación existente de BT3 Tag Team.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var ResultCode: Integer; Args: String;
begin
  if CurStep = ssPostInstall then begin
    UpdateFailed := True;
    Log('Update target: '+ExpandConstant('{app}'));
    Args := '-B "'+ExpandConstant('{tmp}\bt3-update\update_engine.py')+'" "'+ExpandConstant('{app}')+'" --bundle "'+ExpandConstant('{tmp}\bt3-update\payload')+'"';
    if not Exec(ExpandConstant('{app}\runtime\python.exe'), Args, ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, ResultCode) then
      RaiseException('Could not start updater. / No se pudo iniciar la actualización.');
    if ResultCode <> 0 then
      RaiseException('Update stopped safely. Close the game and verify this is a supported installation. Saves are preserved. / Actualización detenida. Cierra el juego y verifica la instalación. Se conservan las partidas.');
    UpdateFailed := False;
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  if not FileExists(ExpandConstant('{app}\runtime\python.exe')) or not FileExists(ExpandConstant('{app}\release-profile.json')) then
    Result := 'Select an existing supported installation. / Elige una instalación existente compatible.';
end;
function GetCustomSetupExitCode: Integer;
begin
  if UpdateFailed then Result := 1 else Result := 0;
end;
