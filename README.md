<div align="center">

# Conecta Bairro

**Plataforma comunitária para conectar moradores através de eventos locais**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-ready-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Railway](https://img.shields.io/badge/deploy-Railway-0B0D0E?style=flat-square&logo=railway&logoColor=white)](https://railway.app)
[![PWA](https://img.shields.io/badge/PWA-enabled-5A0FC8?style=flat-square&logo=pwa&logoColor=white)](#)

[Demo ao vivo](https://cadastroconectabairro-production.up.railway.app) · [Documentação da API](https://cadastroconectabairro-production.up.railway.app/docs)

</div>

---

## Sobre o projeto

O **Conecta Bairro** é uma aplicação web full-stack para comunidades locais. Moradores descobrem e participam de eventos do bairro — esportes, cultura, lazer — enquanto administradores gerenciam tudo por um painel dedicado.

**Stack:** FastAPI + SQLModel · HTML/CSS/JS puro · PostgreSQL · Railway

---

## Funcionalidades

### Moradores
- Cadastro e login com autenticação **JWT**
- **Foto de perfil** com upload e preview ao vivo
- Feed paginado com busca por texto, filtros por categoria, bairro, data e ordenação
- **Lista de espera** automática quando vagas esgotam — promoção automática ao cancelar
- Inscrição/cancelamento em eventos com controle de vagas e barra de progresso
- **Avaliações** com nota de 1–5 estrelas e comentário por evento
- Seção **"Meus eventos"** para acompanhar participações
- Comentários por evento
- Compartilhar via Web Share API (ou copiar link)
- Perfil editável: nome, bairro, telefone, foto e senha
- Campo opcional **"Preciso de cesta básica"** no cadastro e no perfil
- Redefinição de senha por e-mail
- Suporte a **dark mode** automático

### Administradores
- Dashboard com KPIs: usuários, eventos, inscrições, lista de espera, avaliações e admins
- **Feed de atividade recente**: inscrições e avaliações em tempo real
- Gráfico de eventos por categoria e ranking por inscrições
- CRUD completo de eventos com **upload de imagem** (Cloudinary em produção)
- Gestão de usuários: ativar/desativar, promover/rebaixar role
- Badge de cesta básica na lista de usuários
- **Exportar inscritos em CSV** por evento
- Notificações automáticas por e-mail ao atualizar ou cancelar eventos
- E-mail automático para próximo da fila quando vaga abre

### Técnicas
- **SQLite** em desenvolvimento · **PostgreSQL** em produção
- Migrações com **Alembic**
- Imagens persistentes via **Cloudinary** (fallback para filesystem local)
- E-mails transacionais via **Brevo API** (fallback SMTP)
- **PWA** com service worker, cache offline e manifest
- Deploy containerizado com **Dockerfile**
- CORS configurável por variável de ambiente

---

## Estrutura do projeto

```
conecta-bairro/
├── backend/
│   ├── main.py                    # Ponto de entrada FastAPI + rotas estáticas
│   ├── database.py                # Engine, sessão e migrações SQLite
│   ├── models.py                  # Modelos SQLModel (Usuario, Evento, etc.)
│   ├── auth.py                    # bcrypt, JWT, dependências de autenticação
│   ├── email_service.py           # Brevo API / fallback SMTP
│   ├── cloudinary_service.py      # Upload de imagens
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── migrations/
│   │   └── versions/              # Histórico de migrações Alembic
│   ├── routers/
│   │   ├── auth_router.py         # /auth/* — registro, login, perfil, foto, reset
│   │   ├── eventos_router.py      # /eventos/* — CRUD, inscrições, lista de espera
│   │   ├── avaliacoes_router.py   # /eventos/{id}/avaliacoes — notas e estrelas
│   │   ├── comentarios_router.py  # /eventos/{id}/comentarios
│   │   └── admin_router.py        # /admin/* — KPIs, usuários, atividade, CSV
│   └── tests/
│       ├── conftest.py
│       ├── test_auth.py
│       ├── test_eventos.py
│       └── test_admin.py
├── frontend/
│   ├── pages/
│   │   ├── index.html             # Landing page
│   │   ├── login.html
│   │   ├── cadastro.html
│   │   ├── app.html               # Área do morador
│   │   ├── admin.html             # Painel administrativo
│   │   └── redefinir-senha.html
│   ├── css/style.css              # Design system completo + dark mode
│   ├── js/
│   │   ├── api.js                 # Cliente HTTP + JWT
│   │   └── ui.js                  # Toast, modal, helpers, service worker
│   ├── manifest.json              # PWA manifest
│   └── sw.js                      # Service worker (cache offline)
├── Dockerfile                     # Build de produção
├── railway.toml                   # Configuração Railway
└── .gitignore
```

---

## Rodando localmente

### Pré-requisitos

- Python 3.12+

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

Na primeira execução o banco SQLite é criado automaticamente com o admin padrão:
- **E-mail:** `admin@conectabairro.com`
- **Senha:** `admin123`

---

## Variáveis de ambiente

Configure no painel do Railway (ou em um arquivo `.env` local — nunca commite esse arquivo).

| Variável | Descrição | Obrigatória em prod |
|---|---|:---:|
| `DATABASE_URL` | URL PostgreSQL | ✅ |
| `JWT_SECRET` | Chave de assinatura JWT | ✅ |
| `SECRET_KEY` | Chave de sessão | ✅ |
| `ADMIN_EMAIL` | E-mail do admin padrão | — |
| `ADMIN_PASSWORD` | Senha do admin padrão | — |
| `BREVO_API_KEY` | API do Brevo para e-mails | — |
| `EMAIL_FROM` | E-mail remetente | — |
| `CLOUDINARY_CLOUD_NAME` | Nome do cloud (Cloudinary) | — |
| `CLOUDINARY_API_KEY` | Chave Cloudinary | — |
| `CLOUDINARY_API_SECRET` | Segredo Cloudinary | — |
| `ALLOWED_ORIGINS` | Origins CORS (separadas por vírgula) | — |

> Sem e-mail configurado, os envios são apenas logados no terminal.
> Sem Cloudinary, imagens são salvas no filesystem local.

---

## Deploy no Railway

O projeto está pronto para Railway via **Dockerfile**.

1. Crie um projeto no [Railway](https://railway.app) e conecte o repositório GitHub
2. Adicione um serviço **PostgreSQL** ao projeto
3. No serviço da aplicação, vá em **Variables** e adicione:
   - `DATABASE_URL = ${{Postgres.DATABASE_URL}}`
   - As demais variáveis da tabela acima
4. Vá em **Settings → Networking → Generate Domain**
5. Adicione `ALLOWED_ORIGINS=https://seu-dominio.railway.app`

O Railway detecta o `Dockerfile` automaticamente e faz o build e deploy.

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
| `GET` | `/eventos/{id}/avaliacoes` | Avaliações do evento |

### Autenticados

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/auth/me` | Dados do usuário logado |
| `PUT` | `/auth/me` | Atualiza perfil |
| `POST` | `/auth/me/foto` | Upload de foto de perfil |
| `GET` | `/eventos/meus` | Eventos do usuário |
| `POST` | `/eventos/{id}/inscrever` | Inscrever / entrar na lista de espera |
| `DELETE` | `/eventos/{id}/inscrever` | Cancelar inscrição |
| `DELETE` | `/eventos/{id}/espera` | Sair da lista de espera |
| `POST` | `/eventos/{id}/avaliacoes` | Avaliar evento (1–5 estrelas) |
| `DELETE` | `/avaliacoes/{id}` | Remover avaliação |
| `POST` | `/eventos/{id}/comentarios` | Comentar |
| `DELETE` | `/comentarios/{id}` | Remover comentário |

### Admin

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/eventos` | Criar evento |
| `PUT` | `/eventos/{id}` | Editar evento |
| `DELETE` | `/eventos/{id}` | Excluir evento |
| `POST` | `/eventos/{id}/imagem` | Upload de imagem do evento |
| `GET` | `/admin/estatisticas` | KPIs do dashboard |
| `GET` | `/admin/atividade` | Feed de atividade recente |
| `GET` | `/admin/usuarios` | Listar usuários |
| `PUT` | `/admin/usuarios/{id}` | Alterar role/status |
| `DELETE` | `/admin/usuarios/{id}` | Remover usuário |
| `GET` | `/admin/eventos/{id}/inscritos` | Listar inscritos |
| `GET` | `/admin/eventos/{id}/inscritos/csv` | Exportar inscritos em CSV |

Documentação interativa completa disponível em **`/docs`** (Swagger UI).

---

## Testes

```bash
cd backend
pytest -v
```

Suite cobrindo autenticação, eventos, inscrições e painel admin. Utiliza banco SQLite em memória — sem efeitos colaterais.

---

## Segurança

- Senhas armazenadas como **hash bcrypt**
- Tokens JWT assinados e com expiração configurável
- Tokens de reset expiram em **1 hora** e são invalidados após o uso
- Admin não pode desativar nem rebaixar a própria conta
- Endpoints admin protegidos por verificação de role no servidor
- Uploads validados por extensão e tamanho máximo

---

## Licença

Distribuído sob a licença MIT.
