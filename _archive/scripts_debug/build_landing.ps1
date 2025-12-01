# Script PowerShell pour builder la landing page React et l'intégrer dans Django

Write-Host "🍷 Mon Chai - Build Landing Page" -ForegroundColor Magenta
Write-Host "=================================" -ForegroundColor Magenta
Write-Host ""

# 1. Vérifier que Node.js est installé
Write-Host "📋 Vérification de Node.js..." -ForegroundColor Cyan
$nodeVersion = node --version 2>$null
if (-not $nodeVersion) {
    Write-Host "❌ Node.js n'est pas installé. Installez-le depuis https://nodejs.org" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Node.js $nodeVersion détecté" -ForegroundColor Green
Write-Host ""

# 2. Naviguer vers le dossier landing-page
Write-Host "📂 Navigation vers landing-page..." -ForegroundColor Cyan
Set-Location -Path "landing-page"

# 3. Installer les dépendances si nécessaire
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Installation des dépendances npm..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Échec de l'installation des dépendances" -ForegroundColor Red
        Set-Location ..
        exit 1
    }
    Write-Host "✅ Dépendances installées" -ForegroundColor Green
    Write-Host ""
}

# 4. Builder la landing page
Write-Host "🔨 Build de la landing page React..." -ForegroundColor Cyan
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Échec du build" -ForegroundColor Red
    Set-Location ..
    exit 1
}
Write-Host "✅ Build terminé avec succès" -ForegroundColor Green
Write-Host ""

# 5. Vérifier que les fichiers ont été générés
Set-Location ..
if (Test-Path "staticfiles/landing/index.html") {
    Write-Host "✅ Fichiers générés dans staticfiles/landing/" -ForegroundColor Green
    
    # Lister les fichiers générés
    Write-Host ""
    Write-Host "📁 Fichiers générés:" -ForegroundColor Cyan
    Get-ChildItem -Path "staticfiles/landing" -Recurse | Where-Object { -not $_.PSIsContainer } | ForEach-Object {
        Write-Host "   - $($_.FullName.Replace($PWD.Path + '\', ''))" -ForegroundColor Gray
    }
} else {
    Write-Host "⚠️  Fichiers non trouvés dans staticfiles/landing/" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Build terminé !" -ForegroundColor Green
Write-Host ""
Write-Host "📌 Prochaines étapes :" -ForegroundColor Magenta
Write-Host "   1. Lancer le serveur Django : python manage.py runserver" -ForegroundColor White
Write-Host "   2. Visiter : http://127.0.0.1:8000/monchai/" -ForegroundColor White
Write-Host "   3. Cliquer sur 'Me connecter à Mon Chai' pour accéder à l'app" -ForegroundColor White
Write-Host ""
