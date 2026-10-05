[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repository = 'https://raw.githubusercontent.com/ruci-babe/Kiamara-Migration-Assistant-/main'
$temporaryDirectory = Join-Path $env:TEMP ('Kiamara-' + [Guid]::NewGuid().ToString('N'))
$scriptPath = Join-Path $temporaryDirectory 'migrate.py'
$pythonArchive = Join-Path $temporaryDirectory 'python.zip'
$pythonDirectory = Join-Path $temporaryDirectory 'python'
$documentsDirectory = [Environment]::GetFolderPath('MyDocuments')
if ([string]::IsNullOrWhiteSpace($documentsDirectory)) {
    $documentsDirectory = Join-Path $HOME 'Documents'
}
$migrationDirectory = Join-Path $documentsDirectory 'Kiamara-Migration'
$exitCode = 0

try {
    New-Item -ItemType Directory -Path $temporaryDirectory -Force | Out-Null
    New-Item -ItemType Directory -Path $migrationDirectory -Force | Out-Null
    Invoke-WebRequest -UseBasicParsing -Uri "$repository/migrate.py" -OutFile $scriptPath
    Push-Location $migrationDirectory

    $python = Get-Command py -ErrorAction SilentlyContinue
    if ($python) {
        & $python.Source -3 $scriptPath
    } else {
        $python = Get-Command python -ErrorAction SilentlyContinue
        if ($python) {
            & $python.Source -c "import sys; sys.exit(0 if sys.version_info[0] >= 3 else 1)"
            if ($LASTEXITCODE -eq 0) {
                & $python.Source $scriptPath
            } else {
                $python = $null
            }
        }
        if (-not $python) {
            $architecture = $env:PROCESSOR_ARCHITEW6432
            if ([string]::IsNullOrWhiteSpace($architecture)) {
                $architecture = $env:PROCESSOR_ARCHITECTURE
            }
            switch ($architecture) {
                'ARM64' { $pythonPackage = 'arm64' }
                'AMD64' { $pythonPackage = 'amd64' }
                default { $pythonPackage = 'win32' }
            }
            $pythonVersion = '3.13.5'
            $pythonUrl = "https://www.python.org/ftp/python/$pythonVersion/python-$pythonVersion-embed-$pythonPackage.zip"
            Write-Host "Python was not found. Downloading temporary Python $pythonVersion runtime..."
            Invoke-WebRequest -UseBasicParsing -Uri $pythonUrl -OutFile $pythonArchive
            Expand-Archive -LiteralPath $pythonArchive -DestinationPath $pythonDirectory -Force
            & (Join-Path $pythonDirectory 'python.exe') $scriptPath
        }
    }
    $exitCode = $LASTEXITCODE
} finally {
    if ((Get-Location).Path -eq $migrationDirectory) {
        Pop-Location
    }
    if (Test-Path $temporaryDirectory) {
        Remove-Item -LiteralPath $temporaryDirectory -Recurse -Force -ErrorAction SilentlyContinue
    }
}

exit $exitCode