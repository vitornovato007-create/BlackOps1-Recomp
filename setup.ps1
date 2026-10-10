Write-Host "BlackOps1-Recomp v0.1 setup"
Write-Host ""
Write-Host "This script does not download or contain game data."
Write-Host ""
Write-Host "Expected local file:"
Write-Host "  game/default.xex"
Write-Host ""

if (!(Test-Path "game/default.xex")) {
    Write-Warning "game/default.xex was not found."
    Write-Host "Place your own legally obtained Xbox 360 XEX there before codegen."
    exit 0
}

Write-Host "Found game/default.xex"
Write-Host "Ready for the ReXGlue 0.10.0 codegen step."
