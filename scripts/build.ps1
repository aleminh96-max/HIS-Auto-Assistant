param([string]$Python = "python")
$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    & $Python -m PyInstaller --noconfirm --clean --windowed --onedir --name HIS-Auto-Assistant --paths src scripts/assistant_entry.py
    if ($LASTEXITCODE -ne 0) { throw 'Assistant build failed' }
    & $Python -m PyInstaller --noconfirm --clean --windowed --onedir --name HIS-Simulator --paths src scripts/simulator_entry.py
    if ($LASTEXITCODE -ne 0) { throw 'Simulator build failed' }
    Copy-Item README.md,docs/USER_GUIDE.vi.md -Destination dist/HIS-Auto-Assistant
    Compress-Archive -Path dist/HIS-Auto-Assistant,dist/HIS-Simulator -DestinationPath dist/HIS-Auto-Assistant-trial-win64.zip -Force
} finally { Pop-Location }
