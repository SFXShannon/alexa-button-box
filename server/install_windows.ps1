# Run once in an *Administrator* PowerShell from this folder:
#   powershell -ExecutionPolicy Bypass -File .\install_windows.ps1
# - opens the server port in Windows Firewall (private networks only)
# - starts the server automatically at boot, hidden, even when nobody is logged in

$ErrorActionPreference = "Stop"
$here   = Split-Path -Parent $MyInvocation.MyCommand.Path
$config = Get-Content (Join-Path $here "config.json") -Raw | ConvertFrom-Json
$port   = if ($config.port) { $config.port } else { 8765 }
$pyw    = (Get-Command pythonw.exe -ErrorAction Stop).Source
$script = Join-Path $here "alexa_button_server.py"

New-NetFirewallRule -DisplayName "Alexa Button Box server" -Direction Inbound -Protocol TCP `
  -LocalPort $port -Action Allow -Profile Private -ErrorAction SilentlyContinue | Out-Null

$action   = New-ScheduledTaskAction -Execute $pyw -Argument "`"$script`"" -WorkingDirectory $here
$trigger  = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) `
  -ExecutionTimeLimit ([TimeSpan]::Zero) -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U -RunLevel Limited
Register-ScheduledTask -TaskName "Alexa Button Box server" -Action $action -Trigger $trigger `
  -Settings $settings -Principal $principal -Force | Out-Null
Start-ScheduledTask -TaskName "Alexa Button Box server"

Write-Host "Installed. Test it: http://localhost:$port/status?token=$($config.token)"
