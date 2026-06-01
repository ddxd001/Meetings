$ErrorActionPreference = "Stop"

$Root = $PSScriptRoot
$ClientDist = Join-Path $Root "dist\client"
$InstallerSource = Join-Path $Root "packaging\client-installer"
$WorkDir = Join-Path $Root "build\client-installer"
$OutputDir = Join-Path $Root "installer"
$OutputExe = Join-Path $OutputDir "meeting-client-setup.exe"
$IExpress = Join-Path $env:WINDIR "System32\iexpress.exe"

if (-not (Test-Path $IExpress)) {
    throw "IExpress was not found at $IExpress"
}

foreach ($Required in @(
    (Join-Path $ClientDist "meeting-client.exe"),
    (Join-Path $ClientDist "config.ini"),
    (Join-Path $InstallerSource "install-client.cmd"),
    (Join-Path $InstallerSource "install-client.ps1")
)) {
    if (-not (Test-Path $Required)) {
        throw "Required file not found: $Required"
    }
}

New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

Copy-Item -Force (Join-Path $ClientDist "meeting-client.exe") (Join-Path $WorkDir "meeting-client.exe")
Copy-Item -Force (Join-Path $ClientDist "config.ini") (Join-Path $WorkDir "config.ini")
Copy-Item -Force (Join-Path $InstallerSource "install-client.cmd") (Join-Path $WorkDir "install-client.cmd")
Copy-Item -Force (Join-Path $InstallerSource "install-client.ps1") (Join-Path $WorkDir "install-client.ps1")

$SourceDir = $WorkDir.TrimEnd("\") + "\"
$SedPath = Join-Path $WorkDir "meeting-client-setup.sed"
$Sed = @"
[Version]
Class=IEXPRESS
SEDVersion=3

[Options]
PackagePurpose=InstallApp
ShowInstallProgramWindow=1
HideExtractAnimation=1
UseLongFileName=1
InsideCompressed=0
CAB_FixedSize=0
CAB_ResvCodeSigning=0
RebootMode=N
InstallPrompt=
DisplayLicense=
FinishMessage=
TargetName=$OutputExe
FriendlyName=Meeting Room Client Setup
AppLaunched=install-client.cmd
PostInstallCmd=<None>
AdminQuietInstCmd=install-client.cmd
UserQuietInstCmd=install-client.cmd
SourceFiles=SourceFiles

[Strings]
FILE0="meeting-client.exe"
FILE1="config.ini"
FILE2="install-client.cmd"
FILE3="install-client.ps1"

[SourceFiles]
SourceFiles0=$SourceDir

[SourceFiles0]
%FILE0%=
%FILE1%=
%FILE2%=
%FILE3%=
"@

$Sed | Set-Content -Encoding ASCII -Path $SedPath

$PSNativeCommandUseErrorActionPreference = $false
& $IExpress /N /Q $SedPath
$IExpressExitCode = $LASTEXITCODE

if (-not (Test-Path $OutputExe)) {
    throw "Installer was not created: $OutputExe"
}

if ($IExpressExitCode -ne 0) {
    Write-Warning "IExpress returned exit code $IExpressExitCode, but the installer file was created."
}

Write-Host "Client installer created:"
Write-Host "  $OutputExe"
