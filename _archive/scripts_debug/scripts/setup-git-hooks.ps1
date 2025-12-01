#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'
Write-Host "Configuring git hooks path to .githooks"
git config core.hooksPath .githooks
Write-Host "Done. Ensure Node.js is installed, then run: npm install"
