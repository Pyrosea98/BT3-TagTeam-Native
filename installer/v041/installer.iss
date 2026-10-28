#define AppVersion "0.4.1"
[Setup]
AppId=BT3TagTeam-Native-v041
AppName=BT3 Tag Team + Real Power Scale
AppVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\BT3TagTeam-v041
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=payload\assets\BT3TagTeam.ico
UninstallDisplayIcon={app}\Play.exe
OutputDir=release
OutputBaseFilename=BT3-TagTeam-v0.4.1-Windows-Setup
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern dark
DisableProgramGroupPage=yes
CloseApplications=yes
CloseApplicationsFilter=Play.exe,Tenkaichi3Decomp.exe
RestartApplications=no
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
[CustomMessages]
english.DesktopShortcut=Create a desktop shortcut
spanish.DesktopShortcut=Crear un acceso directo en el escritorio
english.StartMenuShortcut=Create a Start menu shortcut
spanish.StartMenuShortcut=Crear un acceso directo en el menú Inicio
english.OptionsTitle=Game preparation
spanish.OptionsTitle=Preparación del juego
english.OptionsDescription=Choose the map size and first-install settings. Existing progress and settings are kept.
spanish.OptionsDescription=Elige el tamaño de los mapas y los ajustes iniciales. Se conservan el progreso y los ajustes existentes.
english.MapChoice=Use 2x maps (unchecked: normal size)
spanish.MapChoice=Usar mapas 2x (sin marcar: tamaño normal)
english.RecommendedChoice=Use recommended settings for a new installation
spanish.RecommendedChoice=Usar ajustes recomendados para una instalación nueva
english.SaveChoice=Start with all content unlocked when no save exists
spanish.SaveChoice=Empezar con todo desbloqueado si no hay partida guardada
english.Manual=Open the manual
spanish.Manual=Abrir el manual
english.Launch=Prepare or play the game
spanish.Launch=Preparar o iniciar el juego
[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopShortcut}"
Name: "startmenuicon"; Description: "{cm:StartMenuShortcut}"
[Files]
Source: "payload\*"; DestDir: "{app}"; Excludes: "data\*,__pycache__\*,*.pyc,*.pyo"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{autodesktop}\BT3 Tag Team v0.4.1"; Filename: "{app}\Play.exe"; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{userprograms}\BT3 Tag Team v0.4.1\Play"; Filename: "{app}\Play.exe"; WorkingDir: "{app}"; Tasks: startmenuicon
Name: "{userprograms}\BT3 Tag Team v0.4.1\{cm:Manual}"; Filename: "{code:ManualPath}"; Tasks: startmenuicon
[Run]
Filename: "{code:ManualPath}"; Description: "{cm:Manual}"; Flags: postinstall shellexec skipifsilent unchecked
Filename: "{app}\Play.exe"; Description: "{cm:Launch}"; WorkingDir: "{app}"; Flags: postinstall nowait skipifsilent unchecked
[Code]
var OptionsPage: TWizardPage; MapBox, RecommendedBox, SaveBox: TNewCheckBox;
function ManualPath(Param: String): String;
var Locale: String;
begin
  if ActiveLanguage = 'spanish' then Locale := 'ES' else Locale := 'EN';
  Result := ExpandConstant('{app}\manual\BT3-TagTeam-Manual-')+Locale+'.html';
end;
function JsonBool(Value: Boolean): String;
begin
  if Value then Result := 'true' else Result := 'false';
end;
procedure InitializeWizard;
begin
  OptionsPage := CreateCustomPage(wpSelectTasks,CustomMessage('OptionsTitle'),CustomMessage('OptionsDescription'));
  MapBox := TNewCheckBox.Create(OptionsPage); MapBox.Parent := OptionsPage.Surface;
  MapBox.Caption := CustomMessage('MapChoice'); MapBox.Checked := True;
  if ExpandConstant('{param:MAPSIZE|2x}') = 'normal' then MapBox.Checked := False;
  MapBox.SetBounds(0,ScaleY(12),OptionsPage.SurfaceWidth,ScaleY(40));
  RecommendedBox := TNewCheckBox.Create(OptionsPage); RecommendedBox.Parent := OptionsPage.Surface;
  RecommendedBox.Caption := CustomMessage('RecommendedChoice'); RecommendedBox.Checked := True;
  if ExpandConstant('{param:RECOMMENDED|yes}') = 'no' then RecommendedBox.Checked := False;
  RecommendedBox.SetBounds(0,ScaleY(64),OptionsPage.SurfaceWidth,ScaleY(40));
  SaveBox := TNewCheckBox.Create(OptionsPage); SaveBox.Parent := OptionsPage.Surface;
  SaveBox.Caption := CustomMessage('SaveChoice'); SaveBox.Checked := True;
  if ExpandConstant('{param:COMPLETEDSAVE|yes}') = 'no' then SaveBox.Checked := False;
  SaveBox.SetBounds(0,ScaleY(116),OptionsPage.SurfaceWidth,ScaleY(40));
end;
procedure CurStepChanged(CurStep: TSetupStep);
var Language, Choices: String;
begin
  if CurStep = ssPostInstall then begin
    if ActiveLanguage = 'spanish' then Language := 'es' else Language := 'en';
    Choices := '{"language":"'+Language+'","expanded_maps":'+JsonBool(MapBox.Checked)+',"recommended":'+JsonBool(RecommendedBox.Checked)+',"completed_save":'+JsonBool(SaveBox.Checked)+'}';
    if not SaveStringToFile(ExpandConstant('{app}\install-choices.json'),Choices,False) then
      RaiseException('Could not save installation choices.');
  end;
end;
