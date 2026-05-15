# Conecta Bairro

Plataforma comunitária para divulgar eventos de bairro (esportes, cultura, lazer) e gerenciar inscrições. Inclui área pública, área do morador autenticado e painel administrativo completo.

Construído com **FastAPI + SQLModel + SQLite/PostgreSQL** no backend e **HTML/CSS/JS puro** no frontend (sem build, sem bundler).

---

## Funcionalidades

### Backend
- Cadastro e login com **senha protegida por bcrypt**
- Autenticação via **JWT** (válido por 7 dias)
- Dois papéis: `morador` (padrão) e `admin`
- CRUD completo de eventos com controle de vagas
- **Upload de imagem** por evento (JPG/PNG/WebP/GIF, máx. 5 MB)
- **Filtros avançados**: modalidade, bairro, local, data inicial e final
- Sistema de inscrição/cancelamento com notificação por e-mail
- **Notificações por e-mail** para inscrição confirmada, cancelamento, evento atualizado e evento excluído
- **Recuperação de senha** via e-mail (link com token de 1 hora)
- Painel administrativo: KPIs, gestão de eventos e usuários
- Suporte a **SQLite** (dev) e **PostgreSQL** (produção) via variável de ambiente
- Documentação interativa em `/docs` (Swagger UI)

### Frontend
- **Landing page** (`/`) com chamada para cadastro/login
- **Cadastro** (`/cadastro`) e **login** (`/login`) com link "Esqueci minha senha"
- **Redefinição de senha** (`/redefinir-senha`) — solicitar link e definir nova senha
- **Área do morador** (`/app`): feed de eventos com imagens, filtros por categoria, filtros avançados (data, bairro, local), inscrição com um toque, aba "Meus eventos"
- **Painel admin** (`/admin`): dashboard com KPIs, gestão de eventos (criar/editar/deletar + upload de imagem), gestão de usuários
- Design responsivo — verde-teal + coral, tipografia Fraunces + Plus Jakarta Sans

---

## Como rodar localmente

### Pré-requisitos
- **Python 3.10+**

### Passo a passo

**Windows:**
```bat
start.bat
```

**Linux / macOS:**
```bash
chmod +x start.sh
./start.sh
```

Ou manualmente:

```bash
# 1. Criar e ativar venv
python -m venv venv
source venv/bin/activate          # Linux/macOS
venv\Scripts\Activate.ps1         # Windows (PowerShell)

# 2. Instalar dependências
pip install -r backend/requirements.txt

# 3. Subir o servidor
cd backend
uvicorn main:app --reload
```

Acesse **http://localhost:8000**. Na primeira execução o banco é criado automaticamente com o admin padrão e 5 eventos de exemplo.

---

## Credenciais padrão

| Campo  | Valor                        |
|--------|------------------------------|
| E-mail | `admin@conectabairro.com`    |
| Senha  | `admin123`                   |

> Troque antes de publicar em produção.

---

## Estrutura do projeto

```
conecta-bairro/
├── backend/
│   ├── main.py               # Aplicação FastAPI (rotas de página + API)
│   ├── database.py           # Engine SQLite/PostgreSQL, sessão, migração
│   ├── models.py             # Modelos SQLModel (Usuario, Evento, Inscricao, PasswordResetToken)
│   ├── auth.py               # bcrypt, JWT, dependências, seed inicial
│   ├── email_service.py      # Serviço SMTP para notificações e reset de senha
│   ├── requirements.txt
│   ├── uploads/              # Imagens enviadas por upload (gerado em runtime)
│   ├── routers/
│   │   ├── auth_router.py    # /auth/* — registro, login, esqueci-senha, redefinir-senha
│   │   ├── eventos_router.py # /eventos/* — CRUD, inscrições, upload de imagem
│   │   └── admin_router.py   # /admin/* — estatísticas, gestão de usuários
│   └── tests/
│       ├── conftest.py       # Fixtures compartilhadas (banco em memória)
│       ├── test_auth.py      # Testes de autenticação e reset de senha
│       ├── test_eventos.py   # Testes de eventos, filtros e inscrições
│       └── test_admin.py     # Testes do painel administrativo
├── frontend/
│   ├── pages/
│   │   ├── index.html            # Landing page
│   │   ├── login.html            # Login (com link "esqueci minha senha")
│   │   ├── cadastro.html         # Cadastro de novo morador
│   │   ├── app.html              # Área do morador
│   │   ├── admin.html            # Painel admin
│   │   └── redefinir-senha.html  # Fluxo de redefinição de senha
│   ├── css/style.css             # Design system + componentes
│   └── js/
│       ├── api.js                # Cliente HTTP (fetch + JWT + upload)
│       └── ui.js                 # toast, modal, helpers
├── pytest.ini                    # Configuração do pytest
├── start.sh                      # Script de inicialização (Linux/macOS)
├── start.bat                     # Script de inicialização (Windows)
└── README.md
```

---

## Principais endpoints

### Públicos
| Método | Rota | Descrição |
|--------|------|-----------|
| `GET`  | `/eventos` | Lista eventos (filtros: `modalidade`, `bairro`, `local`, `data_inicio`, `data_fim`) |
| `GET`  | `/eventos/{id}` | Detalhes do evento |
| `POST` | `/auth/registro` | Cria conta |
| `POST` | `/auth/login` | Retorna `access_token` |
| `POST` | `/auth/esqueci-senha` | Envia e-mail de reset |
| `POST` | `/auth/redefinir-senha` | Define nova senha via token |

### Autenticados (`Authorization: Bearer <token>`)
| Método | Rota | Descrição |
|--------|------|-----------|
| `GET`    | `/auth/me` | Dados do usuário logado |
| `GET`    | `/eventos/meus` | Eventos inscritos |
| `POST`   | `/eventos/{id}/inscrever` | Confirma presença |
| `DELETE` | `/eventos/{id}/inscrever` | Cancela inscrição |

### Apenas admin
| Método | Rota | Descrição |
|--------|------|-----------|
| `POST`   | `/eventos` | Cria evento |
| `PUT`    | `/eventos/{id}` | Atualiza evento (notifica inscritos) |
| `DELETE` | `/eventos/{id}` | Exclui evento (notifica inscritos) |
| `POST`   | `/eventos/{id}/imagem` | Upload de imagem (multipart/form-data) |
| `GET`    | `/admin/estatisticas` | KPIs do dashboard |
| `GET`    | `/admin/usuarios` | Lista usuários |
| `PUT`    | `/admin/usuarios/{id}` | Altera role/ativo |
| `DELETE` | `/admin/usuarios/{id}` | Remove usuário |
| `GET`    | `/admin/eventos/{id}/inscritos` | Lista inscritos |

Documentação interativa completa em **http://localhost:8000/docs**.

---

## Testes

```bash
# Na raiz do projeto (venv ativado)
pytest -v
```

38 testes cobrindo autenticação, eventos e painel admin. Roda com banco SQLite em memória — sem efeitos colaterais.

---

## Configuração de e-mail

Configure as variáveis de ambiente para habilitar o envio real de e-mails:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu@email.com
SMTP_PASS=sua-app-password
EMAIL_FROM=Conecta Bairro <seu@email.com>
```

Sem configuração, os e-mails são apenas logados no terminal (modo desenvolvimento).

> **Gmail**: use uma [App Password](https://myaccount.google.com/apppasswords) — não a senha da conta.

---

## PostgreSQL em produção

Defina a variável de ambiente `DATABASE_URL` para usar PostgreSQL:

```bash
DATABASE_URL=postgresql://usuario:senha@host:5432/nome_do_banco
```

Sem ela, o SQLite local é usado automaticamente.

### Deploy (Render / Railway / Fly.io)

| Campo | Valor |
|-------|-------|
| Comando de build | `pip install -r backend/requirements.txt` |
| Comando de start | `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Variáveis | `DATABASE_URL`, `JWT_SECRET`, `SMTP_*` |

---

## Segurança

- Senhas armazenadas apenas como **hash bcrypt** (nunca em texto puro)
- Tokens JWT assinados — defina `JWT_SECRET` em produção:
  ```bash
  JWT_SECRET=uma-chave-longa-e-aleatoria-aqui
  ```
- Tokens de reset de senha expiram em **1 hora** e são invalidados após uso
- CORS liberado (`*`) para dev — restrinja em produção

---


