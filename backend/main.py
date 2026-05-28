import os
import logging
import json
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlmodel import Session

from database import engine, criar_banco
from auth import garantir_admin_padrao

# ── Logging estruturado ────────────────────────────────────────────────────────
class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)

_handler = logging.StreamHandler()
_handler.setFormatter(_JsonFormatter())
logging.basicConfig(handlers=[_handler], level=logging.INFO, force=True)
logger = logging.getLogger("conecta_bairro")

# ── Sentry (opcional — só ativa se SENTRY_DSN estiver configurado) ─────────────
_sentry_dsn = os.getenv("SENTRY_DSN")
if _sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    sentry_sdk.init(
        dsn=_sentry_dsn,
        traces_sample_rate=0.2,
        integrations=[FastApiIntegration(), SqlalchemyIntegration()],
        environment=os.getenv("RAILWAY_ENVIRONMENT", "development"),
    )
    logger.info("Sentry inicializado")

from routers.auth_router import router as auth_router
from routers.eventos_router import router as eventos_router
from routers.admin_router import router as admin_router
from routers.comentarios_router import router as comentarios_router
from routers.avaliacoes_router import router as avaliacoes_router

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
UPLOADS_DIR = Path(__file__).resolve().parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    criar_banco()
    with Session(engine) as session:
        garantir_admin_padrao(session)
    logger.info("Conecta Bairro API iniciada — banco pronto")
    yield


app = FastAPI(
    title="Conecta Bairro API",
    description="API para conectar a comunidade através de eventos locais.",
    version="2.1.0",
    lifespan=lifespan,
)

_raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
_origins = [o.strip() for o in _raw_origins.split(",")] if _raw_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def _log_requests(request: Request, call_next):
    response = await call_next(request)
    if not request.url.path.startswith(("/static", "/uploads", "/sw.js", "/manifest")):
        logger.info(
            "%s %s %s",
            request.method,
            request.url.path,
            response.status_code,
        )
    return response


app.include_router(auth_router)
app.include_router(eventos_router)
app.include_router(admin_router)
app.include_router(comentarios_router)
app.include_router(avaliacoes_router)

# Servir imagens de eventos enviadas por upload
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Servir os arquivos estáticos do frontend
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

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

    @app.get("/redefinir-senha", include_in_schema=False)
    def redefinir_senha_page():
        return _pagina("redefinir-senha.html")

    @app.get("/manifest.json", include_in_schema=False)
    def manifest():
        return FileResponse(str(FRONTEND_DIR / "manifest.json"), media_type="application/manifest+json")

    @app.get("/sw.js", include_in_schema=False)
    def service_worker():
        return FileResponse(str(FRONTEND_DIR / "sw.js"), media_type="application/javascript")


@app.get("/api", tags=["Status"])
def status():
    return {
        "servico": "Conecta Bairro API",
        "status": "online",
        "versao": "2.1.0",
    }
