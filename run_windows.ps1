[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $Arguments
)

$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path $PSScriptRoot 'migrate.py'

$python = Get-Command py -ErrorAction SilentlyContinue
if ($python) {
    & $python.Source -3 $scriptPath @Arguments
} else {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        throw 'Python 3 was not found. Install Python from https://www.python.org/downloads/windows/ and enable the PATH option.'
    }
    & $python.Source $scriptPath @Arguments
}

exit $LASTEXITCODE