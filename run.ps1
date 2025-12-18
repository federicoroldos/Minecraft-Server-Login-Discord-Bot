$ErrorActionPreference = "Stop"

function Read-Secret([string]$Prompt) {
  $secure = Read-Host -Prompt $Prompt -AsSecureString
  $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try {
    return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
  } finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
  }
}

function Ensure-EnvFile {
  if (!(Test-Path ".\.env")) {
    "DISCORD_TOKEN=" | Out-File -Encoding utf8 -NoNewline ".\.env"
    "`n" | Out-File -Encoding utf8 -Append ".\.env"
  }

  $envText = Get-Content ".\.env" -Raw -ErrorAction SilentlyContinue
  if ($envText -notmatch "(?m)^\s*DISCORD_TOKEN\s*=\s*\S+") {
    Write-Host "Discord token missing in .env."
    $token = Read-Secret "Paste your Discord bot token"
    if ([string]::IsNullOrWhiteSpace($token)) { throw "DISCORD_TOKEN is required." }
    "DISCORD_TOKEN=$token" | Out-File -Encoding utf8 -Append ".\.env"
    Write-Host "Wrote DISCORD_TOKEN to .env"
  }
}

function Ensure-ConfigJson {
  if (!(Test-Path ".\config.json")) {
    Copy-Item ".\config.example.json" ".\config.json"
    Write-Host "Created config.json from config.example.json."
  }

  $config = Get-Content ".\config.json" -Raw | ConvertFrom-Json

  if (-not $config.channel_id -or [int64]$config.channel_id -le 0) {
    $channelId = Read-Host "Discord channel ID (right-click channel -> Copy Channel ID)"
    if ([string]::IsNullOrWhiteSpace($channelId)) { throw "channel_id is required." }
    $config.channel_id = [int64]$channelId
  }

  if (-not $config.log_path -or [string]::IsNullOrWhiteSpace($config.log_path)) {
    $logPath = Read-Host "Path to Minecraft latest.log (example: C:\Servers\Minecraft\logs\latest.log)"
    if ([string]::IsNullOrWhiteSpace($logPath)) { throw "log_path is required." }
    $config.log_path = $logPath
  }

  $config | ConvertTo-Json -Depth 10 | Out-File -Encoding utf8 ".\config.json"
}

if (!(Test-Path ".\.venv")) {
  python -m venv .venv
}

.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt

Ensure-EnvFile
Ensure-ConfigJson

.\.venv\Scripts\python .\bot.py
