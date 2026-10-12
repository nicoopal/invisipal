<#
.SYNOPSIS
  Builds the Invisipal release artifacts.

.DESCRIPTION
  Output (fixed names, so /releases/latest/download/<name> links never break):
    dist\Invisipal-Setup.exe      per-user installer (Inno Setup), the recommended download
    dist\Invisipal-portable.exe   single-file exe, no install needed
    dist\invisipal-cards.skill    the Claude skill (a zip of skills\invisipal-cards)
    dist\Invisipal.zip            the Python version (recommended download), see scripts\make_python_zip.py
    dist\Invisipal\               one-folder build the installer packs (intermediate)

  The installer step needs Inno Setup 6 (ISCC.exe). If it isn't installed the
  step is skipped with a warning; install it with: winget install JRSoftware.InnoSetup

  User data lives in Documents\Invisipal (see invisipal\paths.py). Creating an
  empty file named "portable" next to the exe keeps it next to the exe instead.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\build.ps1
#>
[CmdletBinding()]
param(
    [switch]$KeepBuildDir,
    [switch]$SkipInstaller
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Invoke-Native {
    param([string]$Exe, [string[]]$Arguments)
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Exe $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
    }
}

# Version comes from invisipal/__init__.py (single source of truth).
$initText = Get-Content -Raw -Encoding UTF8 (Join-Path $root 'invisipal\__init__.py')
if ($initText -notmatch '__version__\s*=\s*"([^"]+)"') {
    throw 'Could not read __version__ from invisipal\__init__.py'
}
$version = $Matches[1]
Write-Host "Building Invisipal $version"

Invoke-Native python @('-m', 'PyInstaller', '--version')

# Fresh output; keep it inside the repo (dist/ and build/ are gitignored).
foreach ($path in @('build', 'dist')) {
    if (Test-Path $path) { Remove-Item -Recurse -Force $path }
}

$icon = Join-Path $root 'invisipal\assets\invisipal.ico'
$common = @(
    '-m', 'PyInstaller',
    '--noconfirm',
    '--clean',
    '--noconsole',
    '--specpath', 'build',
    '--icon', $icon,
    # Icons and example guides are package data; PyInstaller doesn't collect them on its own.
    '--add-data', ((Join-Path $root 'invisipal\assets') + ';invisipal\assets'),
    '--add-data', ((Join-Path $root 'invisipal\examples') + ';invisipal\examples')
)
$entry = Join-Path $root 'invisipal.pyw'

# 1) One-folder build: starts fast; the installer packs it.
Invoke-Native python ($common + @('--name', 'Invisipal', $entry))
$exe = Join-Path $root 'dist\Invisipal\Invisipal.exe'
if (-not (Test-Path $exe)) { throw "Build finished but $exe is missing" }

# 2) Single-file portable build.
Invoke-Native python ($common + @('--onefile', '--name', 'Invisipal-portable', $entry))
$portable = Join-Path $root 'dist\Invisipal-portable.exe'
if (-not (Test-Path $portable)) { throw "Build finished but $portable is missing" }

# 3) Claude skill package (.skill is a zip with the skill folder at its root).
$skillDir = Join-Path $root 'skills\invisipal-cards'
$cache = Join-Path $skillDir 'scripts\__pycache__'
if (Test-Path $cache) { Remove-Item -Recurse -Force $cache }
# Python's zipfile writes "/" separators (Compress-Archive on PowerShell 5.1 writes "\").
Invoke-Native python @('-c', "import shutil; shutil.make_archive('dist/invisipal-cards', 'zip', 'skills', 'invisipal-cards')")
Move-Item -Force (Join-Path $root 'dist\invisipal-cards.zip') (Join-Path $root 'dist\invisipal-cards.skill')

# 4) Python version: unzip and double-click "Install Invisipal.pyw".
Invoke-Native python @((Join-Path $root 'scripts\make_python_zip.py'))

# 5) Installer.
$setup = Join-Path $root 'dist\Invisipal-Setup.exe'
if (-not $SkipInstaller) {
    $iscc = (Get-Command 'ISCC.exe' -ErrorAction SilentlyContinue).Source
    if (-not $iscc) {
        foreach ($candidate in @(
                "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
                "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
                "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe")) {
            if (Test-Path $candidate) { $iscc = $candidate; break }
        }
    }
    if ($iscc) {
        Invoke-Native $iscc @("/DAppVersion=$version", "/DRoot=$root", (Join-Path $root 'installer\invisipal.iss'))
        if (-not (Test-Path $setup)) { throw "Inno Setup finished but $setup is missing" }
    }
    else {
        Write-Warning 'Inno Setup (ISCC.exe) not found: skipping the installer. winget install JRSoftware.InnoSetup'
    }
}

if (-not $KeepBuildDir -and (Test-Path 'build')) { Remove-Item -Recurse -Force 'build' }

Write-Host ''
foreach ($artifact in @((Join-Path $root 'dist\Invisipal.zip'), $setup, $portable, (Join-Path $root 'dist\invisipal-cards.skill'))) {
    if (Test-Path $artifact) {
        $size = [math]::Round((Get-Item $artifact).Length / 1MB, 1)
        Write-Host ("{0,-28} {1,6} MB" -f (Split-Path -Leaf $artifact), $size)
    }
}
