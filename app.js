// app.js

// Variável global para guardar todos os eventos na memória do navegador
let todosOsEventos = [];

// Função que vai no Python buscar os dados (Só roda 1 vez ao abrir o app)
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

// Função que desenha os cartões na tela (Recebe a lista já filtrada ou completa)
function renderizarLista(lista) {
    const container = document.getElementById('lista-eventos');
    container.innerHTML = ''; // Limpa a tela

    // Se não tiver nenhum evento para aquele filtro, mostra um aviso
    if (lista.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted my-4 py-4 bg-white rounded-4 shadow-sm border">
                <i class="bi bi-calendar-x fs-1 mb-2"></i>
                <p class="mb-0">Nenhum evento agendado para esta categoria.</p>
            </div>
        `;
        return;
    }

    // Desenha os cartões
    lista.forEach(evento => {
        let borderClass = evento.cor === 'pink' ? 'border-danger' : (evento.cor === 'orange' ? 'border-warning' : 'border-primary');
        let textClass = evento.cor === 'pink' ? 'text-danger' : (evento.cor === 'orange' ? 'text-warning' : 'text-primary');
        
        // Um ícone dinâmico diferente para cada modalidade
        let iconClass = 'bi-people'; // Padrão
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

// A mágica dos Botões de Filtro
const botoesFiltro = document.querySelectorAll('.btn-filtro');

botoesFiltro.forEach(botao => {
    botao.addEventListener('click', function() {
        
        // Tira a cor sólida de TODOS os botões
        botoesFiltro.forEach(b => {
            b.classList.remove('btn-primary');
            b.classList.add('btn-outline-primary');
        });

        // Coloca a cor sólida APENAS no botão clicado
        this.classList.remove('btn-outline-primary');
        this.classList.add('btn-primary');

        // Descobre qual palavra está no botão clicado
        const modalidadeEscolhida = this.getAttribute('data-filtro');

        // Filtra a lista
        if (modalidadeEscolhida === 'Todos') {
            renderizarLista(todosOsEventos); 
        } else {
            const listaFiltrada = todosOsEventos.filter(evento => evento.modalidade === modalidadeEscolhida);
            renderizarLista(listaFiltrada); 
        }
    });
});

// Faz o app carregar os eventos assim que abre
carregarEventos();


// Captura o formulário
const formNovoEvento = document.getElementById('form-novo-evento');

// Quando o formulário for enviado (submit)
formNovoEvento.addEventListener('submit', async function(event) {
    event.preventDefault(); // Evita que a página recarregue

    const botaoSalvar = formNovoEvento.querySelector('button[type="submit"]');
    botaoSalvar.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Salvando...';
    botaoSalvar.disabled = true;

    // Pegando os valores do HTML
    const modalidadeEscolhida = document.getElementById('categoria-evento').value;
    const dataEscolhida = document.getElementById('data-evento').value;
    const horaEscolhida = document.getElementById('hora-evento').value;
    
    // Definindo a cor baseada na modalidade (como no seu código original)
    let corEscolhida = 'blue'; // Padrão
    if (modalidadeEscolhida === 'Zumba') corEscolhida = 'pink';
    if (modalidadeEscolhida === 'Capoeira') corEscolhida = 'orange';

    // Formatando a data para ficar bonitinha: "DD/MM/AAAA às HH:MM"
    const dataFormatada = dataEscolhida.split('-').reverse().join('/') + ' às ' + horaEscolhida;

    // Montando o pacote com os nomes exatos que o seu Python espera
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
            // Fecha a janelinha do Bootstrap
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalNovoEvento'));
            modal.hide();
            
            // Limpa o que foi digitado no formulário
            formNovoEvento.reset();

            // Atualiza a lista na tela na mesma hora!
            carregarEventos(); 
            
            alert('Evento criado com sucesso!');
        } else {
            alert('Ops! Erro ao salvar o evento no banco de dados.');
        }
    } catch (erro) {
        console.error('Erro na requisição:', erro);
        alert('Erro ao tentar conectar com a API.');
    } finally {
        botaoSalvar.innerHTML = 'Salvar Evento';
        botaoSalvar.disabled = false;
    }
});