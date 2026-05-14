# Conecta Bairro

Plataforma comunitária para divulgar eventos de bairro (esportes, cultura, lazer) e gerenciar inscrições. Inclui área pública, área do morador autenticado e painel administrativo completo.

Construído com **FastAPI + SQLModel + SQLite** no backend e **HTML/CSS/JS puro** no frontend (sem build, sem dependência de bundler).

---

## ✨ O que está pronto

### Backend (FastAPI)
- Cadastro e login de usuários com **senha protegida por bcrypt**.
- Autenticação via **JWT** (válido por 7 dias).
- Dois papéis: `morador` (padrão) e `admin`.
- CRUD completo de eventos (criar, listar, atualizar, deletar).
- Sistema de **inscrição/cancelamento** em eventos com controle de vagas.
- Painel administrativo: estatísticas, gestão de usuários, gestão de eventos, lista de inscritos por evento.
- Banco SQLite criado automaticamente na primeira execução, com **admin padrão e eventos de exemplo**.
- Documentação interativa em `/docs` (Swagger UI) e `/redoc`.

### Frontend
- **Landing page** (`/`) com chamada para cadastro/login.
- **Cadastro** (`/cadastro`) e **login** (`/login`).
- **Área do morador** (`/app`): feed de eventos, filtros por modalidade, inscrição com um toque, aba "Meus eventos", perfil.
- **Painel admin** (`/admin`): dashboard com KPIs e gráficos, gestão de eventos (criar/editar/deletar), gestão de usuários (promover, desativar, excluir), lista de inscritos por evento.
- Design system próprio (verde-teal + coral) com tipografia Fraunces + Plus Jakarta Sans, responsivo, com toasts e modais de confirmação.

---

## 🚀 Como rodar localmente

### Pré-requisitos
- **Python 3.10+** instalado
- **pip** funcionando

### Passo a passo

1. **Extraia o projeto** (ou clone o repositório) e abra um terminal na pasta `conecta-bairro/`.

2. **Crie e ative um ambiente virtual** (recomendado):

   No Linux / macOS:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

   No Windows (PowerShell):
   ```powershell
   python -m venv venv
   venv\Scripts\Activate.ps1
   ```

3. **Instale as dependências**:
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Rode o servidor**:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

   Ou use o script pronto na raiz do projeto:
   - Linux/macOS: `./start.sh`
   - Windows: `start.bat`

5. **Abra no navegador**: <http://localhost:8000>

Na primeira execução, o banco `conecta_bairro.db` é criado automaticamente, com o admin padrão e 5 eventos de exemplo.

---

## 🔐 Credenciais padrão

Um administrador é criado automaticamente na primeira execução:

| Campo | Valor |
|-------|-------|
| E-mail | `admin@conectabairro.com` |
| Senha  | `admin123` |

> **Importante:** troque essas credenciais antes de subir para produção. Você pode mudar a senha criando outro admin pelo painel e desativando o padrão, ou alterando direto no banco.

---

## 🗂️ Estrutura do projeto

```
conecta-bairro/
├── backend/
│   ├── main.py                 # Aplicação FastAPI (rotas de página + API)
│   ├── database.py             # Engine SQLite, criação de tabelas, sessão
│   ├── models.py               # Modelos SQLModel (Usuario, Evento, Inscricao)
│   ├── auth.py                 # Hash bcrypt, JWT, dependências, seed inicial
│   ├── requirements.txt
│   └── routers/
│       ├── auth_router.py      # /auth/registro, /auth/login, /auth/me
│       ├── eventos_router.py   # /eventos, inscrições, CRUD admin
│       └── admin_router.py     # /admin/estatisticas, gestão de usuários
├── frontend/
│   ├── pages/
│   │   ├── index.html          # Landing
│   │   ├── login.html
│   │   ├── cadastro.html
│   │   ├── app.html            # Área do morador
│   │   └── admin.html          # Painel admin
│   ├── css/style.css           # Design system + componentes
│   └── js/
│       ├── api.js              # Wrapper da API (token, fetch)
│       └── ui.js               # toast, modal, helpers
├── start.sh
├── start.bat
└── README.md
```

---

## 🛠️ Principais endpoints

### Públicos
- `GET  /eventos` — lista eventos (filtro opcional `?modalidade=`)
- `GET  /eventos/{id}` — detalhe
- `POST /auth/registro` — cria conta
- `POST /auth/login` — devolve `access_token`

### Autenticados (header `Authorization: Bearer <token>`)
- `GET    /auth/me` — dados do usuário logado
- `GET    /eventos/meus` — eventos em que estou inscrito
- `POST   /eventos/{id}/inscrever` — inscreve
- `DELETE /eventos/{id}/inscrever` — cancela inscrição

### Apenas admin
- `POST   /eventos` — cria evento
- `PUT    /eventos/{id}` — atualiza
- `DELETE /eventos/{id}` — exclui
- `GET    /admin/estatisticas` — KPIs e agregados
- `GET    /admin/usuarios` — lista usuários
- `PUT    /admin/usuarios/{id}` — altera role/ativo
- `DELETE /admin/usuarios/{id}` — exclui usuário
- `GET    /admin/eventos/{id}/inscritos` — lista inscritos no evento

Documentação interativa completa em <http://localhost:8000/docs>.

---

## 🔒 Sobre segurança

- Senhas **nunca** são armazenadas em texto puro — apenas o hash bcrypt.
- Tokens JWT assinados com chave secreta. **Em produção**, defina a variável de ambiente `JWT_SECRET`:
  ```bash
  export JWT_SECRET="uma-chave-bem-longa-e-aleatoria"
  ```
  Caso contrário, um valor de fallback inseguro é usado (apenas para desenvolvimento).
- CORS está liberado (`*`) para facilitar o desenvolvimento. Restrinja antes de publicar.

---

## 🚢 Deploy

O projeto é uma única aplicação ASGI — backend e frontend rodam no mesmo processo `uvicorn`. Para subir em serviços como Render, Railway ou Fly.io:

1. Comando de build: `pip install -r backend/requirements.txt`
2. Comando de start: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Configure a variável de ambiente `JWT_SECRET`.

> O banco SQLite vive em arquivo local. Em produção de verdade, considere migrar para PostgreSQL — basta trocar a `DATABASE_URL` em `database.py`.

---

## 📋 Próximos passos sugeridos

- Upload de imagem por evento
- Notificações por e-mail para inscritos
- Filtros mais ricos (data, bairro, distância)
- Migração para PostgreSQL em produção
- Recuperação de senha via e-mail
- Testes automatizados (pytest + httpx)

---

Feito com carinho para a comunidade. 🌿
