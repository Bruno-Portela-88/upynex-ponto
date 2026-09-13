[Setup]
AppName=UPYNEX Sentinel
AppVersion=1.0
AppPublisher=UPYNEX
DefaultDirName={localappdata}\UPYNEX
DefaultGroupName=UPYNEX
OutputDir=assets
OutputBaseFilename=UPYNEX_Setup
SetupIconFile=app_icon.ico
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
DisableDirPage=yes
DisableProgramGroupPage=yes

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos:"
Name: "startupicon"; Description: "Iniciar automaticamente com o Windows"; GroupDescription: "Inicialização:"

[Files]
; Executável gerado pelo PyInstaller
Source: "dist\UPYNEX_Agent.exe"; DestDir: "{app}"; Flags: ignoreversion

; Copia a pasta data e todos os arquivos CSV para o diretório de instalação
Source: "data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\UPYNEX Sentinel"; Filename: "{app}\UPYNEX_Agent.exe"; IconFilename: "{app}\UPYNEX_Agent.exe"
Name: "{autodesktop}\UPYNEX Sentinel"; Filename: "{app}\UPYNEX_Agent.exe"; Tasks: desktopicon; IconFilename: "{app}\UPYNEX_Agent.exe"
; Inicialização automática com o Windows
Name: "{userstartup}\UPYNEX Sentinel"; Filename: "{app}\UPYNEX_Agent.exe"; Tasks: startupicon; IconFilename: "{app}\UPYNEX_Agent.exe"

[Run]
; Inicia o Sentinela imediatamente ao concluir a instalação
Filename: "{app}\UPYNEX_Agent.exe"; Description: "Iniciar UPYNEX Sentinel agora"; Flags: nowait postinstall skipifsilent