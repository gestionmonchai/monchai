@echo off
echo.
echo =========================================
echo 🍷 Mon Chai - Build Landing Page
echo =========================================
echo.

echo 📋 Verification de Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js n'est pas installe
    echo Installez-le depuis https://nodejs.org
    pause
    exit /b 1
)
echo ✅ Node.js detecte
echo.

echo 📂 Navigation vers landing-page...
cd landing-page

if not exist node_modules (
    echo 📦 Installation des dependances npm...
    call npm install
    if errorlevel 1 (
        echo ❌ Echec de l'installation
        cd ..
        pause
        exit /b 1
    )
    echo ✅ Dependances installees
    echo.
)

echo 🔨 Build de la landing page React...
call npm run build
if errorlevel 1 (
    echo ❌ Echec du build
    cd ..
    pause
    exit /b 1
)
echo ✅ Build termine avec succes
echo.

cd ..

if exist staticfiles\landing\index.html (
    echo ✅ Fichiers generes dans staticfiles/landing/
) else (
    echo ⚠️  Fichiers non trouves dans staticfiles/landing/
)

echo.
echo 🎉 Build termine !
echo.
echo 📌 Prochaines etapes :
echo    1. Lancer le serveur Django : python manage.py runserver
echo    2. Visiter : http://127.0.0.1:8000/monchai/
echo    3. Cliquer sur 'Me connecter a Mon Chai'
echo.
pause
