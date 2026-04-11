from fastapi import FastAPI, HTTPException # ADICIONADO HTTPException AQUI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, select

# Nossa Tabela no Banco de Dados
class Evento(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    titulo: str
    modalidade: str
    cor: str
    data: str

# Modelo para receber os dados de login (Não precisa de table=True se não for salvar no banco ainda)
class LoginRequest(SQLModel):
    email: str
    senha: str

# Configurando o SQLite
sqlite_file_name = "banco_de_dados.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=True)

app = FastAPI(title="API Conecta Bairro")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Criar o banco ao iniciar
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.get("/")
def home():
    return {"mensagem": "Servidor do Conecta Bairro está online!"}

# --- ROTAS DE EVENTOS ---

@app.get("/eventos")
def listar_eventos():
    with Session(engine) as session:
        eventos = session.exec(select(Evento)).all()
        return eventos

@app.post("/eventos")
def criar_evento(evento: Evento):
    with Session(engine) as session:
        session.add(evento)
        session.commit()
        session.refresh(evento)
        return evento

@app.delete("/eventos/{evento_id}")
def deletar_evento(evento_id: int):
    with Session(engine) as session:
        evento = session.get(Evento, evento_id)
        if not evento:
            raise HTTPException(status_code=404, detail="Evento não encontrado")
        
        session.delete(evento)
        session.commit()
        return {"mensagem": "Evento excluido com sucesso"}

# --- ROTA DE LOGIN ---

@app.post("/login")
def login(dados: LoginRequest):
    # Verificação simples conforme solicitado
    if dados.email == "admin@teste.com" and dados.senha == "123456":
        return {"status": "sucesso", "mensagem": "Login autorizado"}
    else:
        # Agora o HTTPException vai funcionar porque foi importado!
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")