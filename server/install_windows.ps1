# Run once in an *Administrator* PowerShell from this folder:
#   powershell -ExecutionPolicy Bypass -File .\install_windows.ps1
# - opens the server port in Windows Firewall (private networks only)
# - starts the server automatically at boot, hidden, even when nobody is logged in

$ErrorActionPreference = "Stop"
$here   = Split-Path -Parent $MyInvocation.MyCommand.Path
$config = Get-Content (Join-Path $here "config.json") -Raw | ConvertFrom-Json
$port   = if ($config.port) { $config.port } else { 8765 }
# find pythonw.exe even if Python isn't on PATH
$pyw = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
if (-not $pyw -and (Get-Command py.exe -ErrorAction SilentlyContinue)) {
  $exe = & py.exe -3 -c "import sys; print(sys.executable)"
  $cand = Join-Path (Split-Path $exe) "pythonw.exe"
  if (Test-Path $cand) { $pyw = $cand }
}
if (-not $pyw) {
  $pyw = Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\pythonw.exe", "$env:ProgramFiles\Python3*\pythonw.exe", "C:\Python3*\pythonw.exe" -ErrorAction SilentlyContinue |
         Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
}
if (-not $pyw) { throw "Python 3 not found. Install it from python.org, then run this again." }
Write-Host "Using $pyw"
& (Join-Path (Split-Path $pyw) "python.exe") -m pip install -q -r (Join-Path $here "requirements.txt")
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
