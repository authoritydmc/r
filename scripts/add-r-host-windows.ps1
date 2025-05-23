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
