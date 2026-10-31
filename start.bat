@echo off
echo ============================================
echo   ClearClause - Starting Platform
echo   by Kirti Kumari ^& Kushagra Srivastava
echo ============================================
echo.

cd /d "%~dp0"

echo Starting Flask backend...
cd backend
start "ClearClause Backend" cmd /k "venv\Scripts\python app.py"
cd ..

echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo Starting React frontend...
cd artifacts\legal-document-analyzer
start "ClearClause Frontend" cmd /k "npm run dev"
cd ..\..

echo.
echo ============================================
echo   ClearClause is starting!
echo.
echo   Backend:  http://localhost:5000
echo   Frontend: http://localhost:5173
echo.
echo   Open http://localhost:5173 in your browser
echo ============================================
echo.

timeout /t 8 /nobreak >nul
start http://localhost:5173
