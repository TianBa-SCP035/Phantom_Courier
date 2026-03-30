[Setup]
AppName=信使鹅
AppVersion=1.0.0
AppPublisher=Phantom Courier
DefaultDirName={userdesktop}\Phantom Courier
DefaultGroupName=信使鹅
OutputDir=output
OutputBaseFilename=Phantom Courier Setup
Compression=lzma
SolidCompression=yes
SetupIconFile=..\src\Control\Courier.ico
UninstallDisplayIcon={app}\bin\Phantom Courier.exe
PrivilegesRequired=admin

[Files]
Source: "..\dist\bin\*"; DestDir: "{app}\bin"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\dist\config\*"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{app}\data"
Name: "{app}\logs"
Name: "{app}\output"

[Icons]
Name: "{commondesktop}\信使鹅"; Filename: "{app}\bin\Phantom Courier.exe"; IconFilename: "{app}\bin\Phantom Courier.exe"
Name: "{app}\信使鹅"; Filename: "{app}\bin\Phantom Courier.exe"; IconFilename: "{app}\bin\Phantom Courier.exe"
Name: "{group}\信使鹅"; Filename: "{app}\bin\Phantom Courier.exe"; IconFilename: "{app}\bin\Phantom Courier.exe"
Name: "{group}\卸载"; Filename: "{uninstallexe}"
