# PowerShell script to auto-setup and run the URL Shortener/Redirector on Windows
# Run as Administrator

$repo = "authoritydmc/redirect"
$workdir = "$env:USERPROFILE\redirect"
$py = "python"

# Check for Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python not found. Installing via winget..."
    winget install -e --id Python.Python.3 || (Write-Error 'Please install Python 3 manually and re-run this script.'; exit 1)
}

# Check for git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Git not found. Installing via winget..."
    winget install -e --id Git.Git || (Write-Error 'Please install Git manually and re-run this script.'; exit 1)
}

# Clone or update repo
if (-not (Test-Path $workdir)) { git clone https://github.com/$repo.git $workdir }
else { cd $workdir; git pull }

# Install requirements
cd $workdir
pip install -r requirements.txt

# Register Task Scheduler job
$action = New-ScheduledTaskAction -Execute $py -Argument "app.py" -WorkingDirectory $workdir
$trigger = New-ScheduledTaskTrigger -AtLogOn
Register-ScheduledTask -TaskName "URLShortenerAutoStart" -Action $action -Trigger $trigger -Force

Write-Host "Setup complete. The app will run at every logon."

# Add 'r' to hosts file if running as admin, else print instructions
$hostsPath = "$env:SystemRoot\System32\drivers\etc\hosts"
$entry = "127.0.0.1   r"
$hostsContent = Get-Content $hostsPath -ErrorAction SilentlyContinue
if ($hostsContent -and $hostsContent -match "^127\.0\.0\.1\s+r(\s|$)") {
    Write-Host "r already present in hosts file."
} elseif ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Adding 127.0.0.1   r to hosts file..."
    Add-Content -Path $hostsPath -Value $entry
    Write-Host "Added r to hosts file."
} else {
    Write-Host "To enable http://r/ shortcuts, run this script as Administrator or manually add this line to $hostsPath:"
    Write-Host $entry
}
