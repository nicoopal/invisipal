; Inno Setup script for Invisipal. Built by scripts\build.ps1:
;   ISCC.exe /DAppVersion=1.0.0 /DRoot=C:\path\to\repo installer\invisipal.iss
;
; Per-user install (no admin rights, no UAC prompt) into
; %LOCALAPPDATA%\Programs\Invisipal. User data stays in Documents\Invisipal and
; is never touched by install, upgrade or uninstall.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef Root
  #define Root ".."
#endif

[Setup]
AppId={{8C3F2A51-6E4B-4C2D-9A7E-1B5D0F3C9E21}
AppName=Invisipal
AppVersion={#AppVersion}
AppVerName=Invisipal {#AppVersion}
AppPublisher=Nico Palermo
AppPublisherURL=https://github.com/nicoopal/invisipal
AppSupportURL=https://github.com/nicoopal/invisipal/issues
AppUpdatesURL=https://github.com/nicoopal/invisipal/releases
DefaultDirName={autopf}\Invisipal
DefaultGroupName=Invisipal
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir={#Root}\dist
OutputBaseFilename=Invisipal-Setup
SetupIconFile={#Root}\invisipal\assets\invisipal.ico
UninstallDisplayIcon={app}\Invisipal.exe
UninstallDisplayName=Invisipal
LicenseFile={#Root}\LICENSE
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.19041
; Refuse to install/uninstall while Invisipal is running (see win32.APP_MUTEX_NAME).
AppMutex=Invisipal.AppMutex
CloseApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[CustomMessages]
english.StartWithWindows=Start Invisipal when I sign in to Windows
spanish.StartWithWindows=Iniciar Invisipal al iniciar sesión en Windows
english.LaunchNow=Start Invisipal now
spanish.LaunchNow=Abrir Invisipal ahora

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startup"; Description: "{cm:StartWithWindows}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#Root}\dist\Invisipal\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#Root}\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#Root}\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[InstallDelete]
; Upgrades: drop the previous build's bundled Python files before copying the new ones.
Type: filesandordirs; Name: "{app}\_internal"

[Icons]
Name: "{autoprograms}\Invisipal"; Filename: "{app}\Invisipal.exe"
Name: "{autodesktop}\Invisipal"; Filename: "{app}\Invisipal.exe"; Tasks: desktopicon
Name: "{userstartup}\Invisipal"; Filename: "{app}\Invisipal.exe"; Tasks: startup

[Run]
Filename: "{app}\Invisipal.exe"; Description: "{cm:LaunchNow}"; Flags: nowait postinstall skipifsilent
