# 📍 Projeto Sara Sol Nascente Social

> **Conectando a comunidade através de eventos locais, esportes e cultura.**

O **Conecta Bairro** é uma aplicação Web Full-Stack projetada para facilitar a organização e a descoberta de eventos comunitários (como aulas de Zumba, escolinhas de Futebol, rodas de Capoeira, etc.). A plataforma possui uma interface pública com filtros dinâmicos de alta performance para os moradores e um painel administrativo seguro para a gestão do conteúdo.

---

## ✨ Funcionalidades

### 📱 Área do Morador (App)
* **Visualização de Eventos:** Lista limpa e responsiva (Mobile-First) de todos os eventos agendados.
* **Filtros Dinâmicos em Memória:** Os usuários podem filtrar os eventos por modalidade (Futebol, Zumba, etc.) instantaneamente, sem recarregar a página ou sobrecarregar o servidor.
* **UI/UX Intuitiva:** Cartões de eventos coloridos e categorizados com ícones visuais para fácil identificação.

### ⚙️ Painel de Administração (Admin)
* **CRUD Completo:** Criação, Leitura e Exclusão (Create, Read, Delete) de eventos diretamente pelo navegador.
* **Comunicação Assíncrona:** Formulários integrados com a API via `fetch`, garantindo atualizações na tela em tempo real sem recarregar a página.
* **Prevenção de Erros:** Alertas de confirmação antes de ações críticas (como deletar um evento) e tratamento de erros de conexão.

---

## 🛠️ Tecnologias Utilizadas

O projeto foi construído seguindo a arquitetura de separação entre Frontend e Backend (API RESTful):

**Frontend (Client-Side)**
* **HTML5 & CSS3:** Estruturação semântica e estilização.
* **JavaScript (Vanilla):** Lógica de consumo de API, manipulação do DOM e gerenciamento de estado local para filtros rápidos.
* **Bootstrap 5 & Bootstrap Icons:** Framework CSS para um design responsivo, moderno e componentes prontos.

**Backend (Server-Side)**
* **Python 3:** Linguagem principal do servidor.
* **FastAPI:** Framework moderno e de altíssimo desempenho para a construção da API REST.
* **SQLModel & SQLAlchemy:** ORM (Object-Relational Mapping) para comunicação com o banco de dados de forma segura e elegante.
* **SQLite:** Banco de dados relacional leve e embutido.
* **Uvicorn:** Servidor ASGI para rodar a aplicação Python.
* **CORS Middleware:** Configurado para permitir requisições seguras do frontend local.

---

## 🚀 Como rodar este projeto na sua máquina

Para clonar e executar este aplicativo, você precisará do [Git](https://git-scm.com) e do [Python](https://www.python.org/downloads/) instalados no seu computador.

### 1. Clone o repositório e acesse a pasta
```bash
git clone [https://github.com/SEU_USUARIO/conecta-bairro.git](https://github.com/SEU_USUARIO/conecta-bairro.git)
cd conecta-bairro
