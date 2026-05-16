<div align="center">

# Conecta Bairro

**Plataforma comunitária para conectar moradores através de eventos locais**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-ready-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Deploy](https://img.shields.io/badge/deploy-Render-46E3B7?style=flat-square&logo=render&logoColor=white)](https://render.com)

[Demo ao vivo](https://cadastro-conecta-bairro.onrender.com) · [Documentação da API](https://cadastro-conecta-bairro.onrender.com/docs)

</div>

---

## Sobre o projeto

O **Conecta Bairro** é uma aplicação web full-stack voltada para comunidades locais. Moradores podem descobrir e se inscrever em eventos do bairro — esportes, cultura, lazer — enquanto administradores gerenciam tudo por um painel dedicado.

**Stack:** FastAPI + SQLModel no backend · HTML/CSS/JS puro no frontend (sem framework, sem build step)

---

## Funcionalidades

### Para moradores
- Cadastro e login com autenticação **JWT**
- Feed de eventos com **busca por texto**, filtros por categoria, bairro, data e ordenação
- Inscrição e cancelamento em eventos com controle de vagas
- Seção **"Meus eventos"** para acompanhar participações
- **Comentários** por evento
- **Compartilhar evento** via Web Share API (ou copiar link)
- Perfil editável (nome, bairro, telefone, senha)
- Redefinição de senha por e-mail

### Para administradores
- Dashboard com KPIs: total de usuários, eventos, inscrições e admins
- Gráfico de eventos por categoria e ranking por inscrições
- CRUD completo de eventos com **upload de imagem** (Cloudinary em produção)
- Gestão de usuários: ativar/desativar, promover/rebaixar role
- **Exportar lista de inscritos em CSV** por evento
- Notificações automáticas por e-mail ao atualizar ou cancelar eventos

### Técnicas
- Banco **SQLite** em desenvolvimento · **PostgreSQL** em produção
- Migrações com **Alembic**
- Imagens persistentes via **Cloudinary** (fallback para filesystem local)
- E-mails transacionais via **Brevo API** (fallback SMTP)
- CORS configurável por variável de ambiente
- Senha do admin configurável via `ADMIN_PASSWORD`
- Suite de testes com **pytest** (banco em memória, sem efeitos colaterais)

---

## Estrutura do projeto

```
conecta-bairro/
├── backend/
│   ├── main.py                   # Ponto de entrada FastAPI
│   ├── database.py               # Engine, sessão e migração Alembic
│   ├── models.py                 # Modelos SQLModel
│   ├── auth.py                   # bcrypt, JWT, dependências
│   ├── email_service.py          # Brevo API / SMTP
│   ├── cloudinary_service.py     # Upload de imagens (Cloudinary)
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── migrations/               # Versões Alembic
│   ├── routers/
│   │   ├── auth_router.py        # /auth/* — registro, login, reset de senha
│   │   ├── eventos_router.py     # /eventos/* — CRUD, inscrições, upload
│   │   ├── admin_router.py       # /admin/* — KPIs, usuários, CSV
│   │   └── comentarios_router.py # /eventos/{id}/comentarios
│   └── tests/
│       ├── conftest.py
│       ├── test_auth.py
│       ├── test_eventos.py
│       └── test_admin.py
├── frontend/
│   ├── pages/
│   │   ├── index.html            # Landing page
│   │   ├── login.html
│   │   ├── cadastro.html
│   │   ├── app.html              # Área do morador
│   │   ├── admin.html            # Painel administrativo
│   │   └── redefinir-senha.html
│   ├── css/style.css             # Design system
│   └── js/
│       ├── api.js                # Cliente HTTP + JWT
│       └── ui.js                 # Toast, modal, helpers
├── start.sh                      # Inicialização Linux/macOS
├── start.bat                     # Inicialização Windows
└── pytest.ini
```

---

## Como rodar localmente

### Pré-requisitos

- Python 3.10+

### Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/LuisEdu17y/Cadastro_conecta_bairro.git
cd Cadastro_conecta_bairro

# 2. Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\Activate.ps1      # Windows

# 3. Instale as dependências
pip install -r backend/requirements.txt

# 4. Inicie o servidor
cd backend
uvicorn main:app --reload
```

Acesse **http://localhost:8000**

Na primeira execução o banco SQLite é criado automaticamente com o admin padrão.

**Ou use os scripts prontos:**

```bash
# Linux/macOS
./start.sh

# Windows
start.bat
```

---

## Variáveis de ambiente

Crie um arquivo `.env` na pasta `backend/` ou configure no painel do seu serviço de hospedagem.

### Banco de dados

| Variável | Descrição | Padrão |
|---|---|---|
| `DATABASE_URL` | URL PostgreSQL para produção | SQLite local |

### Autenticação

| Variável | Descrição | Padrão |
|---|---|---|
| `JWT_SECRET` | Chave de assinatura dos tokens JWT | `dev-secret` |
| `ADMIN_EMAIL` | E-mail do admin padrão | `admin@conectabairro.com` |
| `ADMIN_PASSWORD` | Senha do admin padrão | `admin123` |

### E-mail — Brevo (recomendado)

| Variável | Descrição |
|---|---|
| `BREVO_API_KEY` | Chave da API do Brevo (começa com `xkeysib-`) |
| `EMAIL_FROM` | E-mail remetente verificado no Brevo |

### E-mail — SMTP (alternativa)

| Variável | Descrição |
|---|---|
| `SMTP_HOST` | Servidor SMTP (ex: `smtp.gmail.com`) |
| `SMTP_PORT` | Porta SMTP (ex: `587`) |
| `SMTP_USER` | Usuário SMTP |
| `SMTP_PASS` | Senha ou App Password |
| `EMAIL_FROM` | E-mail remetente |

> Sem configuração de e-mail, os envios são apenas logados no terminal.

### Imagens — Cloudinary (produção)

| Variável | Descrição |
|---|---|
| `CLOUDINARY_CLOUD_NAME` | Nome do cloud no Cloudinary |
| `CLOUDINARY_API_KEY` | Chave da API |
| `CLOUDINARY_API_SECRET` | Segredo da API |

> Sem Cloudinary, as imagens são salvas no filesystem local (não persistente no Render free tier).

### CORS

| Variável | Descrição | Padrão |
|---|---|---|
| `ALLOWED_ORIGINS` | Origins permitidas separadas por vírgula | `*` |

---

## Deploy no Render

| Campo | Valor |
|---|---|
| **Build Command** | `pip install -r backend/requirements.txt` |
| **Start Command** | `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT` |

Configure as variáveis de ambiente no painel do Render conforme as tabelas acima. O banco PostgreSQL é provisionado pelo add-on **Render PostgreSQL** — basta definir `DATABASE_URL`.

---

## API — Referência rápida

### Públicos

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/auth/registro` | Cria conta de morador |
| `POST` | `/auth/login` | Retorna `access_token` JWT |
| `POST` | `/auth/esqueci-senha` | Envia e-mail de reset |
| `POST` | `/auth/redefinir-senha` | Define nova senha via token |
| `GET` | `/eventos` | Lista eventos paginados com filtros |
| `GET` | `/eventos/{id}` | Detalhes do evento |
| `GET` | `/eventos/{id}/comentarios` | Comentários do evento |

### Autenticados

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/auth/me` | Dados do usuário logado |
| `PUT` | `/auth/me` | Atualiza perfil |
| `GET` | `/eventos/meus` | Eventos do usuário |
| `POST` | `/eventos/{id}/inscrever` | Inscrever-se |
| `DELETE` | `/eventos/{id}/inscrever` | Cancelar inscrição |
| `POST` | `/eventos/{id}/comentarios` | Comentar |
| `DELETE` | `/comentarios/{id}` | Remover comentário próprio |

### Admin

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/eventos` | Criar evento |
| `PUT` | `/eventos/{id}` | Editar evento |
| `DELETE` | `/eventos/{id}` | Excluir evento |
| `POST` | `/eventos/{id}/imagem` | Upload de imagem |
| `GET` | `/admin/estatisticas` | KPIs do dashboard |
| `GET` | `/admin/usuarios` | Listar usuários |
| `PUT` | `/admin/usuarios/{id}` | Alterar role/status |
| `DELETE` | `/admin/usuarios/{id}` | Remover usuário |
| `GET` | `/admin/eventos/{id}/inscritos` | Listar inscritos |
| `GET` | `/admin/eventos/{id}/inscritos/csv` | Exportar inscritos em CSV |

Documentação interativa completa disponível em **`/docs`** (Swagger UI).

---

## Testes

```bash
# Na raiz do projeto (venv ativado)
pytest -v
```

Suite cobrindo autenticação, eventos, inscrições e painel admin. Utiliza banco SQLite em memória — rápido e sem efeitos colaterais.

---

## Segurança

- Senhas armazenadas como **hash bcrypt** — nunca em texto puro
- Tokens JWT assinados com `JWT_SECRET` — defina um valor forte em produção
- Tokens de reset expiram em **1 hora** e são invalidados após o uso
- Admin não pode desativar a si mesmo nem rebaixar sua própria role
- Endpoints admin protegidos por verificação de role no servidor

---

## Licença

Distribuído sob a licença MIT.
