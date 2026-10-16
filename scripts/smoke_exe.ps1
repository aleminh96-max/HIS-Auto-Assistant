param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    & $Python scripts/smoke_exe.py
    if ($LASTEXITCODE -ne 0) { throw 'Frozen EXE smoke test failed' }
} finally { Pop-Location }
