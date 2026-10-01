# Builds the Windows installer and creates a DRAFT GitHub release with it (publish it on GitHub by hand).
# Needs `gh auth login`. No auto-update feed.
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
  npm run package
  if ($LASTEXITCODE -ne 0) { exit 1 }

  $version = (Get-Content (Join-Path $PSScriptRoot 'package.json') -Raw | ConvertFrom-Json).version
  $exe = Join-Path $PSScriptRoot "dist\Career-Tailor-Setup-$version.exe"
  if (-not (Test-Path $exe)) { throw "Installer not found: $exe" }

  gh release create "v$version" --draft --title "v$version" --generate-notes $exe
  if ($LASTEXITCODE -ne 0) { exit 1 }
} finally {
  Pop-Location
}
