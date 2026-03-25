; SpeedOsper v2 — Inno Setup installer script
; Inclui Motor Ayvu (Rust ONNX backend)

#define MyAppName "SpeedOsper"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Felipe"
#define MyAppExeName "SpeedOsper.exe"
#define MyAppDescription "Speech-to-text, traducao e voz local com Motor Ayvu"

[Setup]
AppId={{B8F3A2E1-7C4D-4A9B-8E5F-1D2C3B4A5E6F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=installer_output
OutputBaseFilename=SpeedOsper_Setup_{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayName={#MyAppName}
SetupIconFile=
; Minimo Windows 10
MinVersion=10.0

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na &Area de Trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked
Name: "startupicon"; Description: "Iniciar com o &Windows"; GroupDescription: "Opcoes:"; Flags: unchecked

[Files]
Source: "dist\SpeedOsper\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar {#MyAppName}"; Flags: nowait postinstall skipifsilent
