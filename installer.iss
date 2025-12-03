; Inno Setup Script for Telegram Drive
; Installer for Windows Desktop Application

#define MyAppName "Telegram Drive"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Your Name/Company"
#define MyAppURL "https://github.com/gnadiah/tg-drive"
#define MyAppExeName "TelegramDrive.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
AppId={{8A9B2C3D-4E5F-6A7B-8C9D-0E1F2A3B4C5D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=
InfoBeforeFile=
InfoAfterFile=
; Uncomment the following line to run in non administrative install mode (install for current user only.)
;PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=installer_output
OutputBaseFilename=TelegramDrive-Setup-{#MyAppVersion}
SetupIconFile=
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
; Remove the following line to disable "Select Setup Language" dialog at the start
ShowLanguageDialog=no
DisableProgramGroupPage=yes
DisableWelcomePage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main application files
Source: "dist\TelegramDrive\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\TelegramDrive\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

; Optional files - won't fail if missing

Source: "dist\TelegramDrive\README.txt"; DestDir: "{app}"; Flags: ignoreversion isreadme skipifsourcedoesntexist

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Optionally launch the application after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up session files and temp folders on uninstall
Type: filesandordirs; Name: "{app}\temp_uploads"
Type: filesandordirs; Name: "{app}\temp_download_*"

[Code]
function InitializeUninstall(): Boolean;
begin
  Result := True;
  if MsgBox('Do you also want to remove your Telegram session data and settings?', mbConfirmation, MB_YESNO) = IDYES then
  begin
    // Remove AppData session files
    DelTree(ExpandConstant('{localappdata}\TelegramDrive'), True, True, True);
  end;
end;
