# Define hosts file path
$hostsPath = "$env:SystemRoot\System32\drivers\etc\hosts"
$entry = "127.0.0.1   r"

# Check if hosts file exists
if (!(Test-Path $hostsPath)) {
    Write-Host "Hosts file not found at $hostsPath. Exiting..."
    exit 1
}

# Read hosts file content
$hostsContent = Get-Content $hostsPath -ErrorAction SilentlyContinue

# Check if 'r' is already in hosts file
if ($hostsContent -match "^\s*127\.0\.0\.1\s+r(\s|$)") {
    Write-Host "'r' is already present in the hosts file."
}
else {
    # Check if script is running with admin privileges
    $isAdmin = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    $isAdmin = $isAdmin.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

    if ($isAdmin) {
        Write-Host "Adding '127.0.0.1   r' to hosts file..."
        $entry | Out-File -Append -Encoding utf8 $hostsPath
        Write-Host "Successfully added 'r' to the hosts file."
    }
    else {
        # Properly format the variable output in Write-Host
        Write-Host "To enable http://r/ shortcuts, run this script as Administrator or manually add this line to `$hostsPath`:"
        Write-Host "`n$entry`n"
    }
}
