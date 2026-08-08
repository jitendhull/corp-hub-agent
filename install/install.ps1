# Powershell installer script for Windows Corp-Hub Agent
# Run in Admin PowerShell:
# iex (iwr -UseBasicParsing https://raw.githubusercontent.com/jitendhull/corp-hub-agent/main/install/install.ps1).Content -BackendUrl "http://hermes:8000"

[CmdletBinding()]
param (
    [Parameter(Mandatory=$true)]
    [string]$BackendUrl,

    [string]$Org = "jitendhull",
    [string]$Repo = "corp-hub-agent",
    [string]$Version = "latest"
)

$ErrorActionPreference = "Stop"

# Ensure Admin
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "ERROR: Must run PowerShell as Administrator"
    exit 1
}

Write-Host "==> Corp-Hub Windows Agent Installer (org=$Org, backend=$BackendUrl)"

$InstallDir = "$env:ProgramFiles\CorpHubAgent"
$DataDir = "$env:ProgramData\CorpHubAgent"
$BinPath = "$InstallDir\corp-hub-agent.exe"
$ConfPath = "$DataDir\agent.conf"

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
New-Item -ItemType Directory -Force -Path $DataDir | Out-Null

# 1. Download Binary from Release
if ($Version -eq "latest") {
    $AssetUrl = "https://github.com/$Org/$Repo/releases/latest/download/corp-hub-agent-windows-x86_64.exe"
} else {
    $AssetUrl = "https://github.com/$Org/$Repo/releases/download/$Version/corp-hub-agent-windows-x86_64.exe"
}

Write-Host "==> Downloading $AssetUrl to $BinPath"
Invoke-WebRequest -Uri $AssetUrl -OutFile $BinPath -UseBasicParsing

# 2. Write Default Config
if (-not (Test-Path $ConfPath)) {
    $ConfigContent = @"
backend_url = "$BackendUrl"
listen_host = "0.0.0.0"
listen_port = 9500

[collectors]
sysinfo_interval_seconds = 300
network_interval_seconds = 60
logs_interval_seconds = 60

[logs]
sources = ["Application", "System", "Security"]
max_lines_per_push = 500
max_backlog = 5000
"@
    Set-Content -Path $ConfPath -Value $ConfigContent
    Write-Host "==> Created config at $ConfPath"
}

# 3. Create & Start Windows Service
$ServiceName = "CorpHubAgent"
$ServiceDisplayName = "Corp-Hub Push Agent"

$existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "==> Stopping existing service"
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    sc.exe delete $ServiceName | Out-Null
    Start-Sleep -Seconds 2
}

Write-Host "==> Registering Windows Service $ServiceName"
New-Service -Name $ServiceName -BinaryPathName "$BinPath --config `"$ConfPath`"" -DisplayName $ServiceDisplayName -StartupType Automatic | Out-Null

# Windows Defender Exclusion for bin directory (Prevents false positive blockage)
Write-Host "==> Adding Windows Defender folder exclusion"
Add-MpPreference -ExclusionPath $InstallDir -ErrorAction SilentlyContinue

Write-Host "==> Starting Service $ServiceName"
Start-Service -Name $ServiceName

Write-Host "==> Done. Service Status:"
Get-Service -Name $ServiceName
