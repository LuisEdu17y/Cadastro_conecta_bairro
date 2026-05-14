#!/usr/bin/env bash
# Inicia o Conecta Bairro em modo desenvolvimento (Linux/macOS).
# Cria venv, instala deps e roda o uvicorn.

set -e

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "==> Criando ambiente virtual..."
    python3 -m venv venv
fi

# shellcheck disable=SC1091
source venv/bin/activate

echo "==> Instalando dependências..."
pip install --quiet --upgrade pip
pip install --quiet -r backend/requirements.txt

echo "==> Subindo servidor em http://localhost:8000"
cd backend
exec uvicorn main:app --reload --host 0.0.0.0 --port 8000
