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
Source: "dist\TelegramDrive\.env.example"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
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
; Note: We don't delete .env as it contains user's API keys
; User should manually delete if needed

[Code]
var
  EnvPage: TInputFileWizardPage;
  ApiIdPage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  // Create a page for API credentials input (optional)
  ApiIdPage := CreateInputQueryPage(wpSelectDir,
    'Telegram API Credentials (Optional)',
    'Enter your Telegram API credentials',
    'You can get these from https://my.telegram.org/apps. You can skip this and create a .env file manually later.');
  
  ApiIdPage.Add('API ID:', False);
  ApiIdPage.Add('API HASH:', False);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  EnvFilePath: String;
  EnvContent: TArrayOfString;
begin
  if CurStep = ssPostInstall then
  begin
    // If user provided API credentials, create .env file
    if (ApiIdPage.Values[0] <> '') and (ApiIdPage.Values[1] <> '') then
    begin
      EnvFilePath := ExpandConstant('{app}\.env');
      SetArrayLength(EnvContent, 2);
      EnvContent[0] := 'API_ID=' + ApiIdPage.Values[0];
      EnvContent[1] := 'API_HASH=' + ApiIdPage.Values[1];
      SaveStringsToFile(EnvFilePath, EnvContent, False);
    end;
  end;
end;

function InitializeUninstall(): Boolean;
begin
  Result := True;
  if MsgBox('Do you also want to remove your Telegram session data and settings?', mbConfirmation, MB_YESNO) = IDYES then
  begin
    // Remove AppData session files
    DelTree(ExpandConstant('{localappdata}\TelegramDrive'), True, True, True);
  end;
end;
