param([string]$GameDirectory, [switch]$Restore)
$ErrorActionPreference = 'Stop'
if (!$GameDirectory) {
    $parentDirectory = Split-Path -Parent $PSScriptRoot
    foreach ($candidate in @($PSScriptRoot, $parentDirectory, (Split-Path -Parent $parentDirectory))) {
        if ((Test-Path -LiteralPath (Join-Path $candidate 'Aikagi_en.exe') -PathType Leaf) -and
            (Test-Path -LiteralPath (Join-Path $candidate 'Aikagi_en.pfs') -PathType Leaf)) {
            $GameDirectory = $candidate
            break
        }
    }
}
if (!$GameDirectory -or !(Test-Path -LiteralPath (Join-Path $GameDirectory 'Aikagi_en.pfs') -PathType Leaf)) {
    throw 'Folder game tidak ditemukan. Letakkan installer bersama Aikagi_en.exe dan Aikagi_en.pfs, atau di subfolder game. Bisa juga gunakan -GameDirectory "D:\lokasi\Aikagi".'
}
$GameDirectory = (Resolve-Path -LiteralPath $GameDirectory).ProviderPath
Write-Host "Folder game: $GameDirectory"
if (!(Test-Path -LiteralPath (Join-Path $PSScriptRoot 'build-report.json') -PathType Leaf)) {
    $sourceRoot = Split-Path -Parent $PSScriptRoot
    $buildDirectory = Join-Path $sourceRoot '.build/furigana'
    $builtInstaller = Join-Path $buildDirectory 'Install-Furigana.ps1'
    if (!(Test-Path -LiteralPath (Join-Path $buildDirectory 'build-report.json') -PathType Leaf)) {
        if ($Restore) { throw 'Build lokal belum ditemukan. Jalankan Install-Furigana.cmd terlebih dahulu.' }
        $venv = Join-Path $sourceRoot '.venv'
        $python = Join-Path $venv 'Scripts/python.exe'
        if ($env:OS -ne 'Windows_NT') { $python = Join-Path $venv 'bin/python' }
        if (!(Test-Path -LiteralPath $python -PathType Leaf)) {
            $launcher = Get-Command py -ErrorAction SilentlyContinue
            if ($launcher) {
                & $launcher.Source -3 -m venv $venv
            } else {
                $launcher = Get-Command python -ErrorAction SilentlyContinue
                if (!$launcher) { $launcher = Get-Command python3 -ErrorAction SilentlyContinue }
                if (!$launcher) { throw 'Pasang Python 3.12 dari python.org, lalu jalankan installer lagi.' }
                & $launcher.Source -m venv $venv
            }
            if ($LASTEXITCODE -ne 0) { throw 'Gagal menyiapkan Python. Gunakan Python 3.12.' }
        }
        & $python -m pip install -r (Join-Path $sourceRoot 'tools/requirements.txt')
        if ($LASTEXITCODE -ne 0) { throw 'Gagal memasang dependensi Python. Periksa koneksi internet.' }
        & $python (Join-Path $sourceRoot 'tools/build_furigana.py') --game $GameDirectory --output $buildDirectory
        if ($LASTEXITCODE -ne 0) { throw 'Build patch gagal. Arsip game belum diganti.' }
    }
    & $builtInstaller -GameDirectory $GameDirectory -Restore:$Restore
    exit
}
$report = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'build-report.json') -Raw | ConvertFrom-Json
$archive = Join-Path $GameDirectory 'Aikagi_en.pfs'
$backup = "$archive.before-furigana"
function Get-Digest([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}
if ($Restore) {
    if (!(Test-Path -LiteralPath $backup) -or (Get-Digest $backup) -ne $report.source_sha256) {
        throw 'Verified original backup not found.'
    }
    $current = Get-Digest $archive
    if ($current -ne $report.patch_sha256 -and $current -ne $report.source_sha256) {
        throw 'Archive changed since installation. Refusing to overwrite it.'
    }
    Copy-Item -LiteralPath $backup -Destination $archive -Force
    Write-Host 'Original archive restored. Save data was preserved.'
    exit
}
$patchArchive = Join-Path (Join-Path $PSScriptRoot 'payload') 'Aikagi_en.pfs'
if (!(Test-Path -LiteralPath $patchArchive -PathType Leaf)) {
    $patchArchive = Join-Path $PSScriptRoot 'Aikagi_en.pfs'
}
if ((Get-Digest $patchArchive) -ne $report.patch_sha256) {
    throw 'Patch checksum mismatch.'
}
$current = Get-Digest $archive
$alreadyInstalled = $current -eq $report.patch_sha256
if (!$alreadyInstalled -and $current -ne $report.source_sha256) { throw 'Unsupported game archive version.' }
if ((Test-Path -LiteralPath $backup) -and (Get-Digest $backup) -ne $report.source_sha256) {
    throw 'A different backup already exists.'
}
$assets = Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'pc') -Recurse -Filter '*.png'
foreach ($source in $assets) {
    $relative = $source.FullName.Substring($PSScriptRoot.Length + 1)
    $target = Join-Path $GameDirectory $relative
    if ((Test-Path -LiteralPath $target) -and (Get-Digest $target) -ne (Get-Digest $source.FullName)) {
        throw "Asset already exists with different contents: $target"
    }
}
if (!$alreadyInstalled -and !(Test-Path -LiteralPath $backup)) {
    Copy-Item -LiteralPath $archive -Destination $backup
}
foreach ($source in $assets) {
    $target = Join-Path $GameDirectory ($source.FullName.Substring($PSScriptRoot.Length + 1))
    if ($source.FullName -eq $target) { continue }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
    Copy-Item -LiteralPath $source.FullName -Destination $target -Force
}
if ($alreadyInstalled) {
    Write-Host 'Patch already installed. Button assets checked.'
    if (!(Test-Path -LiteralPath $backup)) {
        Write-Warning 'Arsip sudah berisi patch, tetapi backup asli tidak ditemukan. Installer tidak akan membuat backup dari arsip yang sudah dipatch.'
    }
    exit
}
Copy-Item -LiteralPath $patchArchive -Destination "$archive.furigana-installing" -Force
Move-Item -LiteralPath "$archive.furigana-installing" -Destination $archive -Force
Write-Host "Furigana patch installed. Original: $backup"
