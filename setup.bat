@echo off
echo ============================================
echo   ClearClause - One-Click Setup Script
echo   by Kirti Kumari ^& Kushagra Srivastava
echo ============================================
echo.

cd /d "%~dp0"

echo [1/6] Creating Python virtual environment...
cd backend
if not exist venv (
    python -m venv venv
)
echo      Done.

echo.
echo [2/6] Upgrading pip...
venv\Scripts\python -m pip install --upgrade pip --timeout 300 --retries 5
echo      Done.

echo.
echo [3/6] Installing Python dependencies (this may take 5-10 minutes)...
venv\Scripts\pip install --timeout 300 --retries 5 ^
    flask==3.1.1 flask-cors==5.0.1 python-dotenv==1.0.1 ^
    PyPDF2==3.0.1 pdfplumber python-docx==1.1.2 ^
    beautifulsoup4==4.13.3 requests==2.32.3 ^
    numpy scikit-learn rank-bm25==0.2.2 nltk==3.9.1 ^
    sentence-transformers==3.4.1 faiss-cpu ^
    transformers huggingface-hub ^
    torch --index-url https://download.pytorch.org/whl/cpu
echo      Done.

echo.
echo [4/6] Building legal knowledge base...
venv\Scripts\python scraper\build_knowledge_base.py
echo      Done.

cd ..

echo.
echo [5/6] Installing frontend dependencies...
cd artifacts\legal-document-analyzer
call npm install
cd ..\..
echo      Done.

echo.
echo ============================================
echo   Setup complete! To run the app:
echo.
echo   Terminal 1 (Backend):
echo     cd backend
echo     venv\Scripts\python app.py
echo.
echo   Terminal 2 (Frontend):
echo     cd artifacts\legal-document-analyzer
echo     npm run dev
echo.
echo   Then open: http://localhost:5173
echo ============================================
pause
