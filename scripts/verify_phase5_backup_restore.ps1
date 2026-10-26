[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-f]{12}$')]
    [string]$Suffix,
    [string]$PythonExecutable = (Join-Path (Split-Path -Parent $PSScriptRoot) '.venv\Scripts\python.exe'),
    [string]$PythonPath,
    [string]$Container = 'django_app_db'
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$helperPath = Join-Path $PSScriptRoot 'verify_phase5_backup_restore.py'
$sourceName = "sgtp_p5_restore_source_$Suffix"
$targetName = "sgtp_p5_restore_target_$Suffix"
$containerDump = "/tmp/sgtp-p5-restore-$Suffix.dump"
$runRoot = Join-Path $repositoryRoot ".test-private-assets\sgtp-phase5-restore-$Suffix"
$sourceMedia = Join-Path $runRoot 'source-private-media'
$backupMedia = Join-Path $runRoot 'backup-private-media'
$restoredMedia = Join-Path $runRoot 'restored-private-media'
$dumpFile = Join-Path $runRoot 'database.dump'
$createdSource = $false
$createdTarget = $false
$createdContainerDump = $false
$originalDbName = $env:DB_NAME
$originalPythonPath = $env:PYTHONPATH

function Invoke-CheckedPython {
    param([string[]]$Arguments)

    $output = & $PythonExecutable $helperPath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Phase 5 verification helper failed at stage '$($Arguments[1])' (exit $LASTEXITCODE)."
    }
    $text = ($output | Out-String).Trim()
    try {
        return $text | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        throw "Phase 5 helper did not return its expected JSON result. Output: $text"
    }
}

function Invoke-ContainerCommand {
    param(
        [string]$DatabaseName,
        [string]$Script,
        [string[]]$ExtraEnvironment = @()
    )

    $arguments = @('exec', '--env', "SGTP_DB_NAME=$DatabaseName")
    foreach ($entry in $ExtraEnvironment) {
        $arguments += @('--env', $entry)
    }
    $arguments += @($Container, 'sh', '-c', $Script)
    & docker.exe @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Disposable PostgreSQL container command failed (exit $LASTEXITCODE)."
    }
}

try {
    if (-not (Test-Path -LiteralPath $PythonExecutable -PathType Leaf)) {
        throw "Python executable not found: $PythonExecutable"
    }
    if (Test-Path -LiteralPath $runRoot) {
        throw "Exact temporary path already exists; refusing to overwrite it: $runRoot"
    }
    if ($PythonPath) {
        $env:PYTHONPATH = if ($originalPythonPath) {
            "$PythonPath;$originalPythonPath"
        }
        else {
            $PythonPath
        }
    }

    $running = & docker.exe inspect --format '{{.State.Running}}' $Container
    if ($LASTEXITCODE -ne 0 -or $running.Trim().ToLowerInvariant() -ne 'true') {
        throw "Expected local PostgreSQL container is not running: $Container"
    }

    $preflight = Invoke-CheckedPython -Arguments @('--stage', 'preflight', '--suffix', $Suffix)
    $containerUser = & docker.exe exec $Container sh -c 'printf "%s" "$POSTGRES_USER"'
    if ($LASTEXITCODE -ne 0 -or $containerUser -ne $preflight.user) {
        throw 'Configured application DB user and local PostgreSQL container user do not match; stopping.'
    }
    $containerServerStart = & docker.exe exec $Container sh -c 'export PGPASSWORD="$POSTGRES_PASSWORD"; psql -h 127.0.0.1 -U "$POSTGRES_USER" -d postgres -XAt -c "SELECT (extract(epoch FROM pg_postmaster_start_time()) * 1000000)::bigint"'
    if ($LASTEXITCODE -ne 0 -or $containerServerStart.Trim() -ne $preflight.server_started_at_us) {
        throw 'Configured local PostgreSQL endpoint is not the same server as the requested Docker container; stopping.'
    }

    Write-Host "Configured application database (not used for writes): $($preflight.configured_application_database_not_used)"
    Write-Host "Disposable database targets: $sourceName and $targetName (both confirmed absent)."

    if (Test-Path -LiteralPath $runRoot) {
        throw "Refusing to reuse an existing verification media directory: $runRoot"
    }
    New-Item -ItemType Directory -Path $runRoot | Out-Null

    $createDatabase = 'set -eu; export PGPASSWORD="$POSTGRES_PASSWORD"; createdb -h 127.0.0.1 -U "$POSTGRES_USER" --template=template0 --encoding=UTF8 "$SGTP_DB_NAME"'
    Invoke-ContainerCommand -DatabaseName $sourceName -Script $createDatabase
    $createdSource = $true
    Invoke-ContainerCommand -DatabaseName $targetName -Script $createDatabase
    $createdTarget = $true

    $env:DB_NAME = $sourceName
    $seed = Invoke-CheckedPython -Arguments @(
        '--stage', 'seed', '--suffix', $Suffix, '--media-root', $sourceMedia
    )
    New-Item -ItemType Directory -Path $backupMedia | Out-Null
    Get-ChildItem -LiteralPath $sourceMedia -Force | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $backupMedia -Recurse
    }

    $dumpScript = 'set -eu; export PGPASSWORD="$POSTGRES_PASSWORD"; pg_dump -h 127.0.0.1 -U "$POSTGRES_USER" -Fc --no-owner --no-privileges -f "$SGTP_DUMP_PATH" --dbname="$SGTP_DB_NAME"'
    Invoke-ContainerCommand -DatabaseName $sourceName -Script $dumpScript -ExtraEnvironment @("SGTP_DUMP_PATH=$containerDump")
    $createdContainerDump = $true
    & docker.exe cp "${Container}:$containerDump" $dumpFile
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $dumpFile -PathType Leaf)) {
        throw 'PostgreSQL dump could not be copied to the isolated temporary backup folder.'
    }
    if ((Get-Item -LiteralPath $dumpFile).Length -le 0) {
        throw 'PostgreSQL dump archive is empty.'
    }

    $restoreScript = 'set -eu; export PGPASSWORD="$POSTGRES_PASSWORD"; pg_restore -h 127.0.0.1 -U "$POSTGRES_USER" --exit-on-error --no-owner --no-privileges --dbname="$SGTP_DB_NAME" "$SGTP_DUMP_PATH"'
    Invoke-ContainerCommand -DatabaseName $targetName -Script $restoreScript -ExtraEnvironment @("SGTP_DUMP_PATH=$containerDump")

    New-Item -ItemType Directory -Path $restoredMedia | Out-Null
    Get-ChildItem -LiteralPath $backupMedia -Force | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $restoredMedia -Recurse
    }
    $env:DB_NAME = $targetName
    $null = Invoke-CheckedPython -Arguments @(
        '--stage', 'verify',
        '--suffix', $Suffix,
        '--media-root', $restoredMedia,
        '--shop-id', $seed.shop_id,
        '--document-id', $seed.document_id
    )

    Write-Host 'PASS: fresh migrations, PostgreSQL dump/restore, invoice/payment/credit/refund totals and Shop ownership, plus private A5 PDF v2 media checksum.'
}
finally {
    if ($originalDbName) { $env:DB_NAME = $originalDbName } else { Remove-Item Env:DB_NAME -ErrorAction SilentlyContinue }
    if ($originalPythonPath) { $env:PYTHONPATH = $originalPythonPath } else { Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue }

    $dropDatabase = 'set -eu; export PGPASSWORD="$POSTGRES_PASSWORD"; dropdb -h 127.0.0.1 -U "$POSTGRES_USER" --if-exists --force "$SGTP_DB_NAME"'
    if ($createdTarget) {
        Invoke-ContainerCommand -DatabaseName $targetName -Script $dropDatabase
    }
    if ($createdSource) {
        Invoke-ContainerCommand -DatabaseName $sourceName -Script $dropDatabase
    }
    if ($createdContainerDump) {
        $removeDump = 'set -eu; rm -f -- "$SGTP_DUMP_PATH"'
        Invoke-ContainerCommand -DatabaseName $sourceName -Script $removeDump -ExtraEnvironment @("SGTP_DUMP_PATH=$containerDump")
    }

    $fullRunPath = [System.IO.Path]::GetFullPath($runRoot)
    $expectedRunPath = [System.IO.Path]::GetFullPath(
        (Join-Path $repositoryRoot ".test-private-assets\sgtp-phase5-restore-$Suffix")
    )
    if ($fullRunPath -eq $expectedRunPath -and
        (Split-Path -Leaf $fullRunPath) -eq "sgtp-phase5-restore-$Suffix" -and
        (Test-Path -LiteralPath $fullRunPath -PathType Container)) {
        Remove-Item -LiteralPath $fullRunPath -Recurse -Force
    }
}
