from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, select

# Nossa Tabela no Banco de Dados
class Evento(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    titulo: str
    modalidade: str
    cor: str
    data: str

# Configurando o SQLite (ele vai criar um arquivo banco_de_dados.db na sua pasta)
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

# Mágica para criar o banco assim que o servidor ligar
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.get("/")
def home():
    return {"mensagem": "Servidor do Conecta Bairro está online e com Banco de Dados!"}

# Rota para LER os eventos (Agora puxa do banco!)
@app.get("/eventos")
def listar_eventos():
    with Session(engine) as session:
        eventos = session.exec(select(Evento)).all()
        return eventos

# NOVA ROTA: Para CRIAR novos eventos
@app.post("/eventos")
def criar_evento(evento: Evento):
    with Session(engine) as session:
        session.add(evento)
        session.commit()
        session.refresh(evento)
        return evento
    
# NOVA ROTA: Para DELETAR um evento

@app.delete("/eventos/{evento_id}")
def deletar_evento(evento_id: int):
    with Session(engine) as session:
              
        evento = session.get(Evento, evento_id)
        if not evento:
            return{"erro": "Evento não encontrado"}
        
        session.delete(evento)
        session.commit()
        
        return {"mensagem": "Evento excluido com sucesso"}
        