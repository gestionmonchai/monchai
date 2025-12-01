#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'
Write-Host "[pre-push] Smoke tests…"
$env:E2E_BASE_URL = $env:E2E_BASE_URL -ne $null ? $env:E2E_BASE_URL : 'http://127.0.0.1:8000'

# Unitaires rapides
if (Get-Command pytest -ErrorAction SilentlyContinue) {
  pytest -q -k "not slow"
} else {
  Write-Host "pytest not found, skipping unit tests"
}

# E2E smoke (bloquant)
if (Get-Command npx -ErrorAction SilentlyContinue) {
  npx playwright test tests/e2e/smoke.spec.ts --reporter=line
  if (Get-Command promptfoo -ErrorAction SilentlyContinue) {
    try { npx promptfoo eval -c prompt-tests/promptfooconfig.yaml --max-concurrency=2 } catch { Write-Host "Prompt tests failed (non-blocking)" }
  }
} else {
  Write-Host "npx not found, skipping Playwright/Prompt tests"
}
