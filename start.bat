@echo off
REM Inicia o Conecta Bairro em modo desenvolvimento (Windows).
REM Cria venv, instala deps e roda o uvicorn.

cd /d "%~dp0"

if not exist venv (
    echo ==^> Criando ambiente virtual...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo ==^> Instalando dependencias...
pip install --quiet --upgrade pip
pip install --quiet -r backend\requirements.txt

echo ==^> Subindo servidor em http://localhost:8000
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
