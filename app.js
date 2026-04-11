// app.js

// Variável global para guardar todos os eventos na memória do navegador
let todosOsEventos = [];

// 1. Função que busca os dados no Back-end (Render)
async function carregarEventos() {
    try {
        const resposta = await fetch('https://api-sara-social.onrender.com/eventos');
        todosOsEventos = await resposta.json();
        
        // Assim que chegar, renderiza mostrando "Todos"
        renderizarLista(todosOsEventos);
    } catch (erro) {
        console.error("Erro:", erro);
        document.getElementById('lista-eventos').innerHTML = `
            <div class="alert alert-danger shadow-sm border-0 border-start border-4 border-danger">
                <i class="bi bi-wifi-off me-2"></i> Erro ao conectar com o servidor.
            </div>
        `;
    }
}

// 2. Função que desenha os cartões na tela
function renderizarLista(lista) {
    const container = document.getElementById('lista-eventos');
    container.innerHTML = ''; // Limpa a tela

    if (lista.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted my-4 py-4 bg-white rounded-4 shadow-sm border">
                <i class="bi bi-calendar-x fs-1 mb-2"></i>
                <p class="mb-0">Nenhum evento agendado para esta categoria.</p>
            </div>
        `;
        return;
    }

    lista.forEach(evento => {
        // Define cores dinâmicas
        let borderClass = evento.cor === 'pink' ? 'border-danger' : (evento.cor === 'orange' ? 'border-warning' : 'border-primary');
        let textClass = evento.cor === 'pink' ? 'text-danger' : (evento.cor === 'orange' ? 'text-warning' : 'text-primary');
        
        // Define ícones dinâmicos
        let iconClass = 'bi-people'; 
        if (evento.modalidade === 'Futebol') iconClass = 'bi-trophy';
        if (evento.modalidade === 'Zumba') iconClass = 'bi-music-note-beamed';
        if (evento.modalidade === 'Capoeira') iconClass = 'bi-person-arms-up';

        const card = `
            <div class="card border-0 shadow-sm border-start border-4 ${borderClass} mb-3">
                <div class="card-body py-3">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <span class="badge bg-light ${textClass} fw-bold px-2 py-1">
                            <i class="bi ${iconClass} me-1"></i> ${evento.modalidade}
                        </span>
                        
                        <button class="btn btn-link text-danger p-0" onclick="deletarEvento(${evento.id})">
                            <i class="bi bi-trash3"></i>
                        </button>
                    </div>
                    <h5 class="card-title fw-bold text-dark mb-1">${evento.titulo}</h5>
                    <p class="card-text text-muted small mb-0">
                        <i class="bi bi-calendar-event me-1"></i> ${evento.data}
                    </p>
                </div>
            </div>
        `;
        container.innerHTML += card;
    });
}

// 3. Lógica dos Botões de Filtro
const botoesFiltro = document.querySelectorAll('.btn-filtro');

botoesFiltro.forEach(botao => {
    botao.addEventListener('click', function() {
        botoesFiltro.forEach(b => {
            b.classList.remove('btn-primary');
            b.classList.add('btn-outline-primary');
        });

        this.classList.remove('btn-outline-primary');
        this.classList.add('btn-primary');

        const modalidadeEscolhida = this.getAttribute('data-filtro');

        if (modalidadeEscolhida === 'Todos') {
            renderizarLista(todosOsEventos); 
        } else {
            const listaFiltrada = todosOsEventos.filter(evento => evento.modalidade === modalidadeEscolhida);
            renderizarLista(listaFiltrada); 
        }
    });
});

// 4. Lógica para Criar Novo Evento (POST)
const formNovoEvento = document.getElementById('form-novo-evento');

formNovoEvento.addEventListener('submit', async function(event) {
    event.preventDefault();

    const botaoSalvar = formNovoEvento.querySelector('button[type="submit"]');
    botaoSalvar.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Salvando...';
    botaoSalvar.disabled = true;

    const modalidadeEscolhida = document.getElementById('categoria-evento').value;
    const dataEscolhida = document.getElementById('data-evento').value;
    const horaEscolhida = document.getElementById('hora-evento').value;
    
    let corEscolhida = 'blue';
    if (modalidadeEscolhida === 'Zumba') corEscolhida = 'pink';
    if (modalidadeEscolhida === 'Capoeira') corEscolhida = 'orange';

    const dataFormatada = dataEscolhida.split('-').reverse().join('/') + ' às ' + horaEscolhida;

    const novoEvento = {
        titulo: document.getElementById('nome-evento').value,
        modalidade: modalidadeEscolhida,
        cor: corEscolhida,
        data: dataFormatada
    };

    try {
        const resposta = await fetch('https://api-sara-social.onrender.com/eventos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(novoEvento)
        });

        if (resposta.ok) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalNovoEvento'));
            modal.hide();
            formNovoEvento.reset();
            carregarEventos(); 
            alert('Evento criado com sucesso!');
        } else {
            alert('Erro ao salvar o evento.');
        }
    } catch (erro) {
        console.error('Erro:', erro);
        alert('Erro ao conectar com a API.');
    } finally {
        botaoSalvar.innerHTML = 'Salvar Evento';
        botaoSalvar.disabled = false;
    }
});

// 5. Função para Deletar Evento (DELETE)
async function deletarEvento(id) {
    if (!confirm("Tem certeza que deseja excluir este evento?")) return;

    try {
        const resposta = await fetch(`https://api-sara-social.onrender.com/eventos/${id}`, {
            method: 'DELETE'
        });

        if (resposta.ok) {
            alert("Evento excluído!");
            carregarEventos(); 
        } else {
            alert("Erro ao excluir o evento.");
        }
    } catch (erro) {
        console.error("Erro ao deletar:", erro);
        alert("Erro ao conectar com o servidor.");
    }
}

// Inicialização
carregarEventos();