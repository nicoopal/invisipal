<#
.SYNOPSIS
  Builds Invisipal.exe (PyInstaller, one-folder, windowed) and zips it for release.

.DESCRIPTION
  Output:
    dist\Invisipal\Invisipal.exe
    dist\Invisipal\guides\*          (example guides, editable next to the exe)
    dist\Invisipal-<version>-win64.zip

  When frozen, the app keeps config.json and guides\ next to the exe (see app_dir()
  in invisipal\__main__.py), so the zip is fully portable.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\build.ps1
#>
[CmdletBinding()]
param(
    [switch]$KeepBuildDir
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
foreach ($dir in @('build', 'dist\Invisipal')) {
    if (Test-Path $dir) { Remove-Item -Recurse -Force $dir }
}

$pyiArgs = @(
    '-m', 'PyInstaller',
    '--noconfirm',
    '--clean',
    '--noconsole',
    '--name', 'Invisipal',
    '--specpath', 'build'
)
$icon = Join-Path $root 'assets\invisipal.ico'
if (Test-Path $icon) {
    $pyiArgs += @('--icon', $icon)
}
else {
    Write-Host 'assets\invisipal.ico not found - building without a custom icon'
}
$pyiArgs += (Join-Path $root 'invisipal.pyw')

Invoke-Native python $pyiArgs

$exe = Join-Path $root 'dist\Invisipal\Invisipal.exe'
if (-not (Test-Path $exe)) { throw "Build finished but $exe is missing" }

# Example guides live next to the exe so users can edit them.
$guidesOut = Join-Path $root 'dist\Invisipal\guides'
New-Item -ItemType Directory -Force -Path $guidesOut | Out-Null
$guidesSrc = Join-Path $root 'guides'
if (Test-Path $guidesSrc) {
    Get-ChildItem -Path $guidesSrc -File | Copy-Item -Destination $guidesOut -Force
}

foreach ($extra in @('README.md', 'LICENSE')) {
    $src = Join-Path $root $extra
    if (Test-Path $src) { Copy-Item $src (Join-Path $root 'dist\Invisipal') -Force }
}

$zip = Join-Path $root "dist\Invisipal-$version-win64.zip"
if (Test-Path $zip) { Remove-Item -Force $zip }
Compress-Archive -Path (Join-Path $root 'dist\Invisipal') -DestinationPath $zip -CompressionLevel Optimal

if (-not $KeepBuildDir -and (Test-Path 'build')) { Remove-Item -Recurse -Force 'build' }

$size = [math]::Round((Get-Item $zip).Length / 1MB, 1)
Write-Host "Done: $exe"
Write-Host "Zip : $zip ($size MB)"
