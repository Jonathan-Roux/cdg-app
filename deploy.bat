@echo off
echo ========================================
echo   CDG App - Deploy to Railway
echo ========================================

cd /d "%~dp0"

echo.
echo [1/4] Git add...
git add .

echo [2/4] Git commit...
git commit -m "fix: requirements UTF-8, PostgreSQL support, env vars"

echo [3/4] Git push...
git push origin main

echo [4/4] Installation Railway CLI...
npm install -g @railway/cli 2>nul || echo Railway CLI deja installe

echo.
echo ========================================
echo Push termine. Lance maintenant :
echo   railway login
echo   railway link
echo   railway up
echo ========================================
pause
