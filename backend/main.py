"""
main.py
-------
Ponto de entrada da API Conecta Bairro.

Responsabilidades:
1. Cria a instância FastAPI
2. Configura CORS
3. Registra todos os routers
4. Cria as tabelas + admin padrão na inicialização
5. Serve o frontend (HTML/CSS/JS) na raiz '/'
   → assim você roda UMA coisa só (uvicorn) e tem app + API juntos

Como rodar:
    cd backend
    uvicorn main:app --reload

Em seguida abra http://localhost:8000

Credenciais padrão do admin:
    email: admin@conectabairro.com
    senha: admin123
"""

from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlmodel import Session

from database import engine, criar_banco
from auth import garantir_admin_padrao

from routers.auth_router import router as auth_router
from routers.eventos_router import router as eventos_router
from routers.admin_router import router as admin_router


# Pasta do frontend (../frontend, relativo a este arquivo)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


# --------- Ciclo de vida da aplicação ---------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cria o banco e o admin padrão na inicialização."""
    criar_banco()
    with Session(engine) as session:
        garantir_admin_padrao(session)
    print("=" * 60)
    print(" Conecta Bairro - API iniciada")
    print(" Banco de dados: pronto")
    print(" Admin padrão:  admin@conectabairro.com / admin123")
    print(" Acesse:        http://localhost:8000")
    print(" API docs:      http://localhost:8000/docs")
    print("=" * 60)
    yield


app = FastAPI(
    title="Conecta Bairro API",
    description="API para conectar a comunidade através de eventos locais.",
    version="2.0.0",
    lifespan=lifespan,
)


# --------- CORS ---------
# Em produção restrinja allow_origins para os domínios oficiais.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------- Routers ---------
app.include_router(auth_router)
app.include_router(eventos_router)
app.include_router(admin_router)


# --------- Frontend estático ---------
# Tudo dentro de /frontend é servido em /static.
# As páginas HTML têm rotas explícitas pra ficar com URLs limpas (/, /login, etc).
if FRONTEND_DIR.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(FRONTEND_DIR)),
        name="static",
    )

    def _pagina(arquivo: str) -> FileResponse:
        return FileResponse(str(FRONTEND_DIR / "pages" / arquivo))

    @app.get("/", include_in_schema=False)
    def home_page():
        return _pagina("index.html")

    @app.get("/login", include_in_schema=False)
    def login_page():
        return _pagina("login.html")

    @app.get("/cadastro", include_in_schema=False)
    def cadastro_page():
        return _pagina("cadastro.html")

    @app.get("/app", include_in_schema=False)
    def app_page():
        return _pagina("app.html")

    @app.get("/admin", include_in_schema=False)
    def admin_page():
        return _pagina("admin.html")


# --------- Healthcheck ---------
@app.get("/api", tags=["Status"])
def status():
    return {
        "servico": "Conecta Bairro API",
        "status": "online",
        "versao": "2.0.0",
    }
