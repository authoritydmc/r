param(
    [string]$Version
)

if (-not $Version) {
    $Version = Read-Host "Enter the release version (e.g., v1.0.0)"
}

if (-not $Version) {
    Write-Host "No version provided. Exiting." -ForegroundColor Red
    exit 1
}

# Check if tag already exists
$tagExists = git tag --list $Version
if ($tagExists) {
    Write-Host "Tag '$Version' already exists. Exiting." -ForegroundColor Yellow
    exit 1
}

# Create the tag
Write-Host "Creating git tag: $Version" -ForegroundColor Cyan
git tag $Version

# Push the tag to origin
Write-Host "Pushing tag $Version to origin..." -ForegroundColor Cyan
git push origin $Version

Write-Host "Tag $Version created and pushed successfully!" -ForegroundColor Green
Write-Host "GitHub Actions release workflow will now be triggered if configured."
