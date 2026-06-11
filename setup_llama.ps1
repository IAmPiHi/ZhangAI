# ============================================================
#  ZHANGAI - llama.cpp auto-installer (Windows)
#  Detects GPU -> downloads the right build from GitHub releases
#  into the llama\ folder. Run via setup_llama.bat
# ============================================================
$ErrorActionPreference = 'Stop'
$Dir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$Llama = Join-Path $Dir 'llama'
New-Item -ItemType Directory -Force -Path $Llama | Out-Null

# ---- detect backend flavor ----
$flavor = 'vulkan'   # works on AMD / Intel / NVIDIA
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) { $flavor = 'cuda' }
Write-Host "  GPU flavor detected: $flavor (fallback chain: $flavor -> vulkan -> cpu)"

# ---- fetch latest release info ----
Write-Host '  Fetching latest llama.cpp release info...'
$rel = Invoke-RestMethod 'https://api.github.com/repos/ggml-org/llama.cpp/releases/latest' `
        -Headers @{ 'User-Agent' = 'ZHANGAI-setup' }
Write-Host "  Latest release: $($rel.tag_name)"

function Find-Asset($keyword) {
    $rel.assets | Where-Object {
        $_.name -match 'bin-win' -and $_.name -match $keyword -and $_.name -match 'x64'
    } | Select-Object -First 1
}

$asset = Find-Asset $flavor
if (-not $asset -and $flavor -eq 'cuda')   { $asset = Find-Asset 'vulkan'; $flavor = 'vulkan' }
if (-not $asset)                            { $asset = Find-Asset 'cpu';    $flavor = 'cpu' }
if (-not $asset) {
    Write-Host '  [ERROR] No matching asset found. Download manually:'
    Write-Host '          https://github.com/ggml-org/llama.cpp/releases/latest'
    Write-Host '          and unzip into the llama\ folder.'
    exit 1
}

function Get-Zip($a) {
    $tmp = Join-Path $env:TEMP $a.name
    Write-Host "  Downloading $($a.name) ($([math]::Round($a.size/1MB,1)) MB)..."
    Invoke-WebRequest $a.browser_download_url -OutFile $tmp -UseBasicParsing
    Write-Host '  Extracting...'
    Expand-Archive -Path $tmp -DestinationPath $Llama -Force
    Remove-Item $tmp
}

Get-Zip $asset

# CUDA builds need the separate cudart runtime zip
if ($flavor -eq 'cuda') {
    $cudart = $rel.assets | Where-Object { $_.name -match 'cudart' -and $_.name -match 'win' } | Select-Object -First 1
    if ($cudart) { Get-Zip $cudart }
}

# some zips nest files in a subfolder -> flatten so llama\llama-server.exe exists
if (-not (Test-Path (Join-Path $Llama 'llama-server.exe'))) {
    $found = Get-ChildItem $Llama -Recurse -Filter 'llama-server.exe' | Select-Object -First 1
    if ($found) {
        Get-ChildItem $found.DirectoryName | Move-Item -Destination $Llama -Force
    }
}

if (Test-Path (Join-Path $Llama 'llama-server.exe')) {
    Write-Host ''
    Write-Host "  Done! ($flavor build, $($rel.tag_name)) -> llama\llama-server.exe"
    Write-Host '  You can now run start.bat'
} else {
    Write-Host '  [ERROR] llama-server.exe still missing - check the llama\ folder.'
    exit 1
}
