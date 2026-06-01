$ErrorActionPreference = "Stop"

$AppName = "Meeting Room Client"
$DefaultInstallParent = Join-Path $env:LOCALAPPDATA "Programs"
$DefaultInstallDir = Join-Path $DefaultInstallParent "MeetingRoomClient"
$StartMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Meeting Room Client"
$DesktopDir = [Environment]::GetFolderPath("Desktop")

function Show-Info($Message) {
    try {
        Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
        [System.Windows.Forms.MessageBox]::Show(
            $Message,
            "Meeting Room Client Setup",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Information
        ) | Out-Null
    } catch {
        Write-Host $Message
    }
}

function Quote-PowerShellLiteral($Value) {
    return "'" + ($Value -replace "'", "''") + "'"
}

function Select-InstallDirectory {
    New-Item -ItemType Directory -Force -Path $DefaultInstallParent | Out-Null

    try {
        Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
        $Dialog = New-Object System.Windows.Forms.FolderBrowserDialog
        $Dialog.Description = "Select the folder where Meeting Room Client will be installed."
        $Dialog.SelectedPath = $DefaultInstallDir
        $Dialog.ShowNewFolderButton = $true

        $Result = $Dialog.ShowDialog()
        if ($Result -ne [System.Windows.Forms.DialogResult]::OK -or [string]::IsNullOrWhiteSpace($Dialog.SelectedPath)) {
            throw "Installation canceled by user."
        }
        return $Dialog.SelectedPath
    } catch {
        Write-Host "Unable to open the folder selection dialog."
        Write-Host "Press Enter to use the default install directory:"
        Write-Host "  $DefaultInstallDir"
        $InputPath = Read-Host "Install directory"
        if ([string]::IsNullOrWhiteSpace($InputPath)) {
            return $DefaultInstallDir
        }
        return $InputPath
    }
}

function Ask-LaunchNow($InstallDir) {
    $ClientExe = Join-Path $InstallDir "meeting-client.exe"
    try {
        Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
        $Message = "Meeting Room Client has been installed successfully.`n`nInstall location:`n$InstallDir`n`nStart Meeting Room Client now?"
        $Result = [System.Windows.Forms.MessageBox]::Show(
            $Message,
            "Meeting Room Client Setup",
            [System.Windows.Forms.MessageBoxButtons]::YesNo,
            [System.Windows.Forms.MessageBoxIcon]::Question
        )
        if ($Result -eq [System.Windows.Forms.DialogResult]::Yes) {
            Start-Process -FilePath $ClientExe -WorkingDirectory $InstallDir
        }
    } catch {
        Write-Host "$AppName installed to $InstallDir"
        $Launch = Read-Host "Start Meeting Room Client now? (Y/N)"
        if ($Launch -match "^[Yy]") {
            Start-Process -FilePath $ClientExe -WorkingDirectory $InstallDir
        }
    }
}

$InstallDir = Select-InstallDirectory

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
New-Item -ItemType Directory -Force -Path $StartMenuDir | Out-Null

Copy-Item -Force -Path (Join-Path $PSScriptRoot "meeting-client.exe") -Destination (Join-Path $InstallDir "meeting-client.exe")

$InstalledConfig = Join-Path $InstallDir "config.ini"
if (-not (Test-Path $InstalledConfig)) {
    Copy-Item -Force -Path (Join-Path $PSScriptRoot "config.ini") -Destination $InstalledConfig
}

$InstallDirLiteral = Quote-PowerShellLiteral $InstallDir
$StartMenuDirLiteral = Quote-PowerShellLiteral $StartMenuDir
$UninstallScript = Join-Path $InstallDir "uninstall-client.ps1"
@"
`$ErrorActionPreference = "Stop"
`$InstallDir = $InstallDirLiteral
`$StartMenuDir = $StartMenuDirLiteral
`$DesktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "Meeting Room Client.lnk"
Remove-Item -Force -ErrorAction SilentlyContinue `$DesktopShortcut
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue `$StartMenuDir
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue `$InstallDir
"@ | Set-Content -Encoding UTF8 -Path $UninstallScript

$UninstallCmd = Join-Path $InstallDir "uninstall-client.cmd"
@'
@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstall-client.ps1"
'@ | Set-Content -Encoding ASCII -Path $UninstallCmd

$Shell = New-Object -ComObject WScript.Shell

$StartShortcut = $Shell.CreateShortcut((Join-Path $StartMenuDir "$AppName.lnk"))
$StartShortcut.TargetPath = Join-Path $InstallDir "meeting-client.exe"
$StartShortcut.WorkingDirectory = $InstallDir
$StartShortcut.IconLocation = Join-Path $InstallDir "meeting-client.exe"
$StartShortcut.Save()

$UninstallShortcut = $Shell.CreateShortcut((Join-Path $StartMenuDir "Uninstall Meeting Room Client.lnk"))
$UninstallShortcut.TargetPath = $UninstallCmd
$UninstallShortcut.WorkingDirectory = $InstallDir
$UninstallShortcut.Save()

$DesktopShortcut = $Shell.CreateShortcut((Join-Path $DesktopDir "$AppName.lnk"))
$DesktopShortcut.TargetPath = Join-Path $InstallDir "meeting-client.exe"
$DesktopShortcut.WorkingDirectory = $InstallDir
$DesktopShortcut.IconLocation = Join-Path $InstallDir "meeting-client.exe"
$DesktopShortcut.Save()

Ask-LaunchNow $InstallDir
