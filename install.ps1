# forge installer for Windows (PowerShell)
# Run from an elevated PowerShell or Windows Terminal:
#
#   .\install.ps1                            (from inside the cloned repo)
#   irm https://raw.githubusercontent.com/atharva336/forge/main/install.ps1 | iex
#
# Requirements: Python 3.10+, Git (both available at python.org and git-scm.com)

$ErrorActionPreference = "Stop"

$REPO_URL   = "https://github.com/atharva336/forge"
$INSTALL_DIR = "$env:USERPROFILE\.local\bin"
$MIN_MINOR   = 10

function Write-Ok   { param($m) Write-Host "  [OK] $m" -ForegroundColor Green }
function Write-Info { param($m) Write-Host "  --> $m" -ForegroundColor Cyan }
function Write-Warn { param($m) Write-Host "  [!] $m"  -ForegroundColor Yellow }
function Write-Fail { param($m) Write-Host "  [X] $m"  -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "  forge installer" -ForegroundColor White
Write-Host ""

# ── find Python ──────────────────────────────────────────────────────────────
$PythonExe = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($ver -match "^3\.(\d+)$") {
            $minor = [int]$Matches[1]
            if ($minor -ge $MIN_MINOR) {
                $PythonExe = $cmd
                Write-Ok "Python $ver found"
                break
            }
        }
    } catch {}
}

if (-not $PythonExe) {
    Write-Fail "Python 3.$MIN_MINOR+ not found.`n  Download from: https://python.org/downloads`n  Make sure 'Add to PATH' is checked during install."
}

# ── locate repo ──────────────────────────────────────────────────────────────
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# If run via irm|iex, $ScriptDir may be empty or temp — check for pyproject.toml
if (-not $ScriptDir -or -not (Test-Path "$ScriptDir\pyproject.toml")) {
    Write-Info "Cloning forge from GitHub..."
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Fail "Git not found.`n  Download from: https://git-scm.com/download/win"
    }
    $TmpDir = Join-Path $env:TEMP "forge-install"
    if (Test-Path $TmpDir) { Remove-Item $TmpDir -Recurse -Force }
    git clone --depth 1 $REPO_URL $TmpDir
    if ($LASTEXITCODE -ne 0) { Write-Fail "Could not clone $REPO_URL" }
    $ScriptDir = $TmpDir
    Write-Ok "Cloned to $TmpDir"
}

# ── create venv ──────────────────────────────────────────────────────────────
$VenvDir = Join-Path $ScriptDir ".venv"
Write-Info "Creating virtual environment..."
& $PythonExe -m venv $VenvDir
if ($LASTEXITCODE -ne 0) { Write-Fail "Failed to create virtual environment." }
Write-Ok "Virtual environment created"

$PipExe   = Join-Path $VenvDir "Scripts\pip.exe"
$ForgeExe = Join-Path $VenvDir "Scripts\forge.exe"

# ── install ──────────────────────────────────────────────────────────────────
Write-Info "Installing forge..."
& $PipExe install --quiet --upgrade pip
& $PipExe install --quiet -e $ScriptDir
if ($LASTEXITCODE -ne 0) { Write-Fail "pip install failed." }
Write-Ok "forge installed"

# ── create wrapper in INSTALL_DIR ────────────────────────────────────────────
New-Item -ItemType Directory -Force -Path $INSTALL_DIR | Out-Null

$WrapperPath = Join-Path $INSTALL_DIR "forge.cmd"
$WrapperContent = "@echo off`r`n`"$ForgeExe`" %*"
Set-Content -Path $WrapperPath -Value $WrapperContent -Encoding ASCII
Write-Ok "Wrapper created at $WrapperPath"

# ── PATH ─────────────────────────────────────────────────────────────────────
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$INSTALL_DIR*") {
    $NewPath = "$UserPath;$INSTALL_DIR"
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    Write-Ok "Added $INSTALL_DIR to user PATH"
    Write-Warn "Restart your terminal for PATH changes to take effect."
} else {
    Write-Ok "PATH already includes $INSTALL_DIR"
}

Write-Host ""
Write-Host "  Done! Open a new terminal and run: forge --help" -ForegroundColor White
Write-Host ""
Write-Host "  Quick start:"
Write-Host "    cd your-project"
Write-Host "    forge init --scaffold"
Write-Host "    forge docs edit tasks"
Write-Host "    forge chat"
Write-Host ""
