# OWMB local development build
# Builds into its own folder so it never touches the release files in the
# project root or in dist\:
#
#   local-build\
#     cmake\        CMake/MSBuild intermediates (incremental, kept between builds)
#     OWMB.exe      Standalone app  <-- start this one for testing
#     OWMB.vst3\    VST3 plugin bundle
#
# Usage:  .\build-local.ps1            incremental Release build
#         .\build-local.ps1 -Clean     wipe local-build\ first
#         .\build-local.ps1 -Run       build and start OWMB.exe afterwards

param(
    [switch]$Clean,
    [switch]$Run,
    [ValidateSet('Release', 'Debug')]
    [string]$Config = 'Release'
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$outDir   = Join-Path $PSScriptRoot 'local-build'
$cmakeDir = Join-Path $outDir 'cmake'

# Locate CMake (PATH, common install locations, or the copy bundled with Visual Studio)
$cmake = (Get-Command cmake -ErrorAction SilentlyContinue).Source
if (-not $cmake) {
    $candidates = @(
        "${env:ProgramFiles}\CMake\bin\cmake.exe",
        "${env:LocalAppData}\Microsoft\WinGet\Links\cmake.exe"
    )
    $vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    if (Test-Path $vswhere) {
        $vs = & $vswhere -latest -products * -property installationPath
        if ($vs) { $candidates += Join-Path $vs 'Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe' }
    }
    $cmake = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}
if (-not $cmake) { throw 'CMake not found. Install with: winget install --id Kitware.CMake -e' }

if ($Clean -and (Test-Path $outDir)) {
    Write-Host 'Cleaning local-build\ ...' -ForegroundColor Yellow
    Remove-Item $outDir -Recurse -Force
}

# Configure (only needed the first time; JUCE is downloaded here)
if (-not (Test-Path (Join-Path $cmakeDir 'CMakeCache.txt'))) {
    Write-Host 'Configuring CMake (first run downloads JUCE)...' -ForegroundColor Cyan
    & $cmake -S . -B $cmakeDir -G 'Visual Studio 17 2022' -A x64 -DOWMB_COPY_PLUGIN_AFTER_BUILD=OFF
    if ($LASTEXITCODE -ne 0) { throw 'CMake configuration failed.' }
}

Write-Host "Compiling OWMB ($Config)..." -ForegroundColor Cyan
# Single MSBuild node (/m:1, no node reuse) avoids hangs of the multi-node IPC;
# UseMultiToolTask still compiles the source files of each project in parallel.
& $cmake --build $cmakeDir --config $Config -- /v:m /m:1 /nr:false /p:UseMultiToolTask=true /p:EnforceProcessCountAcrossBuilds=true
if ($LASTEXITCODE -ne 0) { throw 'Build failed.' }

# Copy results to the top of local-build\
$artefacts = Join-Path $cmakeDir "OpenWav_artefacts\$Config"
Copy-Item (Join-Path $artefacts 'Standalone\OWMB.exe') (Join-Path $outDir 'OWMB.exe') -Force
$vst3 = Join-Path $artefacts 'VST3\OWMB.vst3'
if (Test-Path $vst3) {
    Remove-Item (Join-Path $outDir 'OWMB.vst3') -Recurse -Force -ErrorAction SilentlyContinue
    Copy-Item $vst3 (Join-Path $outDir 'OWMB.vst3') -Recurse -Force
}

Write-Host "Build succeeded: $outDir\OWMB.exe" -ForegroundColor Green

if ($Run) { Start-Process (Join-Path $outDir 'OWMB.exe') }

