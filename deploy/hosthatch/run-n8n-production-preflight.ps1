[CmdletBinding()]
param([switch]$ResumeSuccessfulBackup)

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$guidePath = Join-Path $repositoryRoot 'docs\deployment\n8n-production-preflight-execution.md'
$expectedHash = 'e51da4380f0c2549e0b57ee449139f576755844a42298e61d5846c209610275c'
$temporaryRunner = Join-Path $env:TEMP "abap-n8n-preflight-runner-$([Guid]::NewGuid().ToString('N')).ps1"
$originalLocation = Get-Location

try {
    $guide = Get-Content -LiteralPath $guidePath -Raw
    $match = [regex]::Match(
        $guide,
        '(?ms)^```powershell\r?\n(?<code>.*?)\r?\n```'
    )
    if (-not $match.Success) {
        throw 'The reviewed PowerShell procedure was not found in the production preflight guide.'
    }

    $procedure = $match.Groups['code'].Value
    $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($procedure)
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    try {
        $actualHash = ([System.BitConverter]::ToString(
            $sha256.ComputeHash($bytes)
        ) -replace '-', '').ToLowerInvariant()
    }
    finally {
        $sha256.Dispose()
    }
    if ($actualHash -ne $expectedHash) {
        throw 'The production preflight procedure has changed since safety review. Stop and review it again.'
    }

    [System.IO.File]::WriteAllText(
        $temporaryRunner,
        $procedure,
        [System.Text.UTF8Encoding]::new($false)
    )
    Set-Location -LiteralPath $repositoryRoot
    & $temporaryRunner -ResumeSuccessfulBackup:$ResumeSuccessfulBackup
}
finally {
    Set-Location -LiteralPath $originalLocation
    Remove-Item -LiteralPath $temporaryRunner -Force -ErrorAction SilentlyContinue
}
