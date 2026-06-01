$ErrorActionPreference = "Stop"

$AssetsPath = Join-Path $PSScriptRoot "meeting_room_system\client\assets"
$ClientAssets = "$AssetsPath;meeting_room_system\client\assets"

python -m PyInstaller --onefile --console --name meeting-server --distpath dist\server --workpath build\server --specpath build\spec src\server\server.py

python -m PyInstaller --onefile --windowed --name meeting-client --distpath dist\client --workpath build\client --specpath build\spec --add-data $ClientAssets src\client\client.py

New-Item -ItemType Directory -Force -Path dist\server\data | Out-Null
Copy-Item -Force packaging\server-config.ini dist\server\config.ini
Copy-Item -Force packaging\client-config.ini dist\client\config.ini

Write-Host "Build complete:"
Write-Host "  dist\server\meeting-server.exe"
Write-Host "  dist\client\meeting-client.exe"
