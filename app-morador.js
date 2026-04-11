// app-morador.js

async function carregarFeed() {
    try {
        // Puxa do banco de dados do seu Python no Render
        const resposta = await fetch('https://api-sara-social.onrender.com/eventos');
        const eventos = await resposta.json();
        
        const container = document.getElementById('feed-eventos');
        container.innerHTML = ''; // Limpa o aviso de "Carregando..."

        if(eventos.length === 0) {
            container.innerHTML = '<p class="text-center text-muted">Nenhum evento rolando no bairro ainda.</p>';
            return;
        }

        eventos.forEach(evento => {
            // Lógica para as cores dinâmicas das tags
            let tagColor = 'bg-primary';
            
            if(evento.modalidade === 'Futebol') tagColor = 'bg-primary';
            if(evento.modalidade === 'Zumba') tagColor = 'bg-danger';
            if(evento.modalidade === 'Capoeira') tagColor = 'bg-warning text-dark';

            // O Card HTML sem o botão de deletar (Visão Morador)
            const cardHTML = `
                <div class="card glass-card p-3 mb-3">
                    <span class="badge ${tagColor} mb-2" style="width: fit-content;">
                        ${evento.modalidade}
                    </span>
                    <h5 class="fw-bold text-dark mb-1">${evento.titulo}</h5>
                    <p class="text-muted small mb-0">
                        <i class="bi bi-clock me-1"></i> ${evento.data} <br>
                        <i class="bi bi-geo-alt me-1"></i> Quadra Poliesportiva
                    </p>
                    <button onclick="abrirConfirmacao('${evento.titulo}', '${evento.data}')" class="btn btn-outline-success btn-sm rounded-pill mt-3 fw-bold w-100">
                        Ver Detalhes / Participar
                    </button>
                </div>
            `;
            container.innerHTML += cardHTML;
        });

    } catch (erro) {
        console.error("Erro ao buscar eventos:", erro);
        document.getElementById('feed-eventos').innerHTML = `
            <div class="alert alert-danger text-center">
                Erro ao carregar eventos. Verifique a conexão com o servidor.
            </div>
        `;
    }
}

// Roda a função assim que o arquivo for carregado pelo navegador
carregarFeed();


// Função que abre a janelinha (Modal) e preenche os dados
function abrirConfirmacao(titulo, data) {
    document.getElementById('modal-titulo').innerText = titulo;
    document.getElementById('modal-data').innerText = data;
    
    // Comando do Bootstrap para mostrar o modal
    const modal = new bootstrap.Modal(document.getElementById('modalConfirmacao'));
    modal.show();
}

// Função de quando ele clica em "Sim, Eu Vou!"
function confirmarPresenca() {
    alert("Inscrição confirmada com sucesso! Te esperamos lá.");
    
    // Esconde o modal
    const modalElement = document.getElementById('modalConfirmacao');
    const modalInstance = bootstrap.Modal.getInstance(modalElement);
    modalInstance.hide();
}