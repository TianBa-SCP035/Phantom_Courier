[Setup]
AppName=Phantom Courier2
AppVersion=1.0.0
AppPublisher=Phantom Courier2
DefaultDirName={userdesktop}\Phantom Courier2
DefaultGroupName=Phantom Courier2
OutputDir=output
OutputBaseFilename=Phantom Courier2 Setup
Compression=lzma
SolidCompression=yes
SetupIconFile=..\src\Control\Courier.ico
UninstallDisplayIcon={app}\bin\Phantom Courier2.exe
PrivilegesRequired=admin

[Files]
Source: "..\dist\bin\*"; DestDir: "{app}\bin"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\dist\config\*"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{app}\data"
Name: "{app}\logs"
Name: "{app}\output"

[Icons]
Name: "{commondesktop}\Phantom Courier2"; Filename: "{app}\bin\Phantom Courier2.exe"; IconFilename: "{app}\bin\Phantom Courier2.exe"
Name: "{app}\Phantom Courier2"; Filename: "{app}\bin\Phantom Courier2.exe"; IconFilename: "{app}\bin\Phantom Courier2.exe"
Name: "{group}\Phantom Courier2"; Filename: "{app}\bin\Phantom Courier2.exe"; IconFilename: "{app}\bin\Phantom Courier2.exe"
Name: "{group}\Uninstall"; Filename: "{uninstallexe}"
