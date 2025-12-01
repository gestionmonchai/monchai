# Script PowerShell pour redémarrer Ollama
# Usage: .\restart_ollama.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "REDÉMARRAGE D'OLLAMA" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Étape 1 : Arrêter Ollama
Write-Host "[1/4] Arrêt d'Ollama..." -ForegroundColor Yellow
try {
    $processes = Get-Process ollama -ErrorAction SilentlyContinue
    if ($processes) {
        Stop-Process -Name ollama -Force
        Write-Host "  -> Ollama arrêté" -ForegroundColor Green
    } else {
        Write-Host "  -> Ollama n'était pas en cours d'exécution" -ForegroundColor Gray
    }
} catch {
    Write-Host "  -> Erreur lors de l'arrêt : $_" -ForegroundColor Red
}

# Étape 2 : Attendre
Write-Host ""
Write-Host "[2/4] Attente de 5 secondes..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
Write-Host "  -> OK" -ForegroundColor Green

# Étape 3 : Redémarrer Ollama
Write-Host ""
Write-Host "[3/4] Redémarrage d'Ollama..." -ForegroundColor Yellow
try {
    Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden
    Write-Host "  -> Ollama redémarré" -ForegroundColor Green
} catch {
    Write-Host "  -> Erreur lors du redémarrage : $_" -ForegroundColor Red
    Write-Host "  -> Essayez de démarrer Ollama manuellement" -ForegroundColor Yellow
    exit 1
}

# Étape 4 : Attendre le démarrage
Write-Host ""
Write-Host "[4/4] Attente du démarrage (10 secondes)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10
Write-Host "  -> OK" -ForegroundColor Green

# Test de vérification
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VÉRIFICATION" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Test de l'API Ollama..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "  -> API Ollama fonctionne !" -ForegroundColor Green
        
        # Afficher les modèles disponibles
        $data = $response.Content | ConvertFrom-Json
        Write-Host ""
        Write-Host "Modèles disponibles :" -ForegroundColor Cyan
        foreach ($model in $data.models) {
            $size = [math]::Round($model.size / 1GB, 2)
            Write-Host "  - $($model.name) ($size GB)" -ForegroundColor White
        }
    } else {
        Write-Host "  -> Erreur : Status $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "  -> Erreur : Ollama ne répond pas" -ForegroundColor Red
    Write-Host "  -> Vérifiez que Ollama est bien installé" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TERMINÉ" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Vous pouvez maintenant tester l'aide :" -ForegroundColor White
Write-Host "  python test_help_performance.py" -ForegroundColor Gray
Write-Host ""
