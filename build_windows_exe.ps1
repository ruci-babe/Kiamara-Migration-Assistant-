[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$dist = Join-Path $root 'dist\windows'
$build = Join-Path $root 'build'

$python = Get-Command py -ErrorAction SilentlyContinue
if ($python) {
    $pythonArguments = @('-3')
} else {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        throw 'Python 3 was not found. Install Python and enable the PATH option.'
    }
    $pythonArguments = @()
}

& $python.Source @pythonArguments -m pip install -r (Join-Path $root 'requirements-dev.txt')
if ($LASTEXITCODE -ne 0) {
    Write-Error 'Installing build dependencies failed.'
    exit $LASTEXITCODE
}

& $python.Source @pythonArguments -m PyInstaller --onefile --name Kiamara --distpath $dist --workpath $build --specpath $build (Join-Path $root 'migrate.py')
if ($LASTEXITCODE -ne 0) {
    Write-Error 'PyInstaller failed.'
    exit $LASTEXITCODE
}

Write-Host "Build complete: $dist\Kiamara.exe"