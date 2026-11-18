# Windows setup for the NaviGator WordPress Agent.
# Right-click this folder > Open in Terminal, then run:
#   powershell -ExecutionPolicy Bypass -File setup.ps1

Set-Location -Path $PSScriptRoot
Write-Host "== NaviGator WordPress Agent setup (Windows) =="

# 1. Find Python 3.10 or newer. Prefer the "py" launcher; "python" can be a
#    Microsoft Store shortcut that isn't really installed.
$exe = $null; $pre = @()
foreach ($cand in @("py -3", "python")) {
    $parts = $cand -split ' '
    try {
        $tryPre = @($parts | Select-Object -Skip 1)
        & $parts[0] @tryPre -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) { $exe = $parts[0]; $pre = $tryPre; break }
    } catch { }
}
if (-not $exe) {
    Write-Host ""
    Write-Host "You need Python 3.10 or newer."
    Write-Host "Download it from https://www.python.org/downloads/ and, in the installer,"
    Write-Host "TICK 'Add python.exe to PATH'. Then open a new terminal and run setup.ps1 again."
    exit 1
}
Write-Host ("Using " + (& $exe @pre --version))

# 2. Create a private Python environment for this project.
if (-not (Test-Path ".venv")) {
    Write-Host "Creating .venv (about 30 seconds)..."
    & $exe @pre -m venv .venv
    if ($LASTEXITCODE -ne 0) { Write-Host "Couldn't create .venv"; exit 1 }
}

# 3. Install the four packages listed in requirements.txt.
Write-Host "Installing packages..."
& .\.venv\Scripts\python.exe -m pip install --quiet --upgrade pip
& .\.venv\Scripts\python.exe -m pip install --quiet -r requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Host "Package install failed"; exit 1 }

# 4. Create your private settings file and open it.
if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
    Write-Host "Created .env. It's opening in Notepad: fill it in and save."
    Start-Process notepad .env
} else {
    Write-Host ".env already exists (left unchanged)."
}

Write-Host ""
Write-Host "Setup done. Next, in this window:"
Write-Host "  .\.venv\Scripts\Activate.ps1   (if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned)"
Write-Host "  python navipress.py login      # one-time WordPress sign-in"
Write-Host "  python navipress.py check      # confirm everything works"
