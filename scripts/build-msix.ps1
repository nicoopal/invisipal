<#
.SYNOPSIS
  Packages the one-folder build (dist\Invisipal) as an MSIX for the Microsoft Store.

.DESCRIPTION
  Needs the Windows 10/11 SDK (makeappx.exe, makepri.exe) and a prior run of
  scripts\build.ps1. The Store identity comes from installer\msix\store-identity.json
  (Partner Center > Invisipal > Product management > Product identity).

  The package is left unsigned: the Store signs it with Microsoft's certificate
  when it publishes the app.

  Output: dist\Invisipal-<version>.msix

.PARAMETER AllowPlaceholderIdentity
  Build even if store-identity.json still has placeholders, using a dummy
  identity. Only useful to test the packaging (CI does this).
#>
[CmdletBinding()]
param(
    [switch]$AllowPlaceholderIdentity
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

function Find-SdkTool([string]$Name) {
    $kits = Join-Path ${env:ProgramFiles(x86)} 'Windows Kits\10\bin'
    $tool = Get-ChildItem -Path $kits -Filter $Name -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -match '\\x64\\' } |
        Sort-Object FullName -Descending | Select-Object -First 1
    if (-not $tool) { throw "$Name not found. Install the Windows SDK: winget install Microsoft.WindowsSDK.10.0.26100" }
    return $tool.FullName
}

# Version: Store packages need four parts and the last one must be 0.
$initText = Get-Content -Raw -Encoding UTF8 (Join-Path $root 'invisipal\__init__.py')
if ($initText -notmatch '__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)"') {
    throw 'Could not read a x.y.z __version__ from invisipal\__init__.py'
}
$version = "$($Matches[1]).$($Matches[2]).$($Matches[3]).0"

$identity = Get-Content -Raw -Encoding UTF8 (Join-Path $root 'installer\msix\store-identity.json') | ConvertFrom-Json
if ($identity.identity_name -eq '__SET_ME__' -or $identity.publisher -eq '__SET_ME__') {
    if (-not $AllowPlaceholderIdentity) {
        throw 'installer\msix\store-identity.json still has placeholders. Fill it in from Partner Center.'
    }
    Write-Warning 'Using a placeholder identity: this package can be tested but not uploaded to the Store.'
    $identity.identity_name = 'Invisipal.PackagingTest'
    $identity.publisher = 'CN=Invisipal Packaging Test'
}

$app = Join-Path $root 'dist\Invisipal'
if (-not (Test-Path (Join-Path $app 'Invisipal.exe'))) { throw 'dist\Invisipal\Invisipal.exe is missing: run scripts\build.ps1 first.' }

$makeappx = Find-SdkTool 'makeappx.exe'
$makepri = Find-SdkTool 'makepri.exe'
Write-Host "Packaging Invisipal $version as $($identity.identity_name)"

# Layout: AppxManifest.xml, Assets\, resources.pri and the app in Invisipal\.
$stage = Join-Path $root 'build\msix'
$priRoot = Join-Path $root 'build\msix-pri'
foreach ($dir in @($stage, $priRoot)) {
    if (Test-Path $dir) { Remove-Item -Recurse -Force $dir }
    New-Item -ItemType Directory -Path $dir | Out-Null
}

$manifest = Get-Content -Raw -Encoding UTF8 (Join-Path $root 'installer\msix\AppxManifest.xml')
$manifest = $manifest.Replace('__IDENTITY_NAME__', $identity.identity_name)
$manifest = $manifest.Replace('__PUBLISHER__', [Security.SecurityElement]::Escape($identity.publisher))
$manifest = $manifest.Replace('__PUBLISHER_DISPLAY_NAME__', [Security.SecurityElement]::Escape($identity.publisher_display_name))
$manifest = $manifest.Replace('__VERSION__', $version)
$utf8 = New-Object System.Text.UTF8Encoding($false)
foreach ($dir in @($stage, $priRoot)) {
    [IO.File]::WriteAllText((Join-Path $dir 'AppxManifest.xml'), $manifest, $utf8)
    Copy-Item -Recurse (Join-Path $root 'installer\msix\Assets') (Join-Path $dir 'Assets')
}
Copy-Item -Recurse $app (Join-Path $stage 'Invisipal')

# resources.pri lets Windows pick the right icon size (scale-200, targetsize-*).
# It is indexed from a folder with only the assets, not the ~1000 app files.
$priConfig = Join-Path $root 'build\priconfig.xml'
Invoke-Native $makepri @('createconfig', '/cf', $priConfig, '/dq', 'en-US', '/pv', '10.0.0', '/o')
Invoke-Native $makepri @('new', '/pr', $priRoot, '/cf', $priConfig, '/mn', (Join-Path $priRoot 'AppxManifest.xml'),
    '/of', (Join-Path $stage 'resources.pri'), '/o')

$msix = Join-Path $root "dist\Invisipal-$($version.Substring(0, $version.Length - 2)).msix"
Invoke-Native $makeappx @('pack', '/d', $stage, '/p', $msix, '/o')

$size = [math]::Round((Get-Item $msix).Length / 1MB, 1)
Write-Host "Done: $msix ($size MB, unsigned; the Store signs it)"
