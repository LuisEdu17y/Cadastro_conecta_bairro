// admin.js

// Função para carregar os eventos na tabela do Admin
async function carregarEventosAdmin() {
    try {
        const resposta = await fetch('https://api-sara-social.onrender.com');
        const eventos = await resposta.json();
        
        const tabela = document.getElementById('tabela-eventos');
        tabela.innerHTML = ''; // Limpa a tabela antes de preencher

        eventos.forEach(evento => {
            // Cria uma linha para cada evento
            const linha = `
                <tr>
                    <td class="fw-bold">${evento.titulo}</td>
                    <td><span class="badge bg-secondary">${evento.modalidade}</span></td>
                    <td class="text-muted small">${evento.data}</td>
                    <td class="text-end">
                        <button onclick="deletarEvento(${evento.id})" class="btn btn-sm btn-outline-danger">
                            <i class="bi bi-trash-fill"></i>
                        </button>
                    </td>
                </tr>
            `;
            tabela.innerHTML += linha;
        });
    } catch (erro) {
        console.error("Erro ao carregar tabela:", erro);
    }
}

// Função para Deletar o Evento
async function deletarEvento(id) {
    if (confirm("Tem certeza que deseja apagar este evento?")) {
        try {
            const resposta = await fetch(`https://api-sara-social.onrender.com${id}`, {
                method: 'DELETE'
            });

            if (resposta.ok) {
                carregarEventosAdmin(); // Recarrega a tabela para atualizar a tela
            } else {
                alert("Erro ao excluir o evento.");
            }
        } catch (erro) {
            console.error("Erro:", erro);
        }
    }
}

// 3. O Formulário de Cadastro
document.getElementById('formCadastro').addEventListener('submit', async function(event) {
    event.preventDefault(); 
    
    const novoEvento = {
        titulo: document.getElementById('titulo').value,
        modalidade: document.getElementById('modalidade').value,
        cor: document.getElementById('cor').value,
        data: document.getElementById('data').value
    };

    try {
        const resposta = await fetch('https://api-sara-social.onrender.com', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(novoEvento)
        });

        if (resposta.ok) {
            document.getElementById('alerta-sucesso').classList.remove('d-none');
            document.getElementById('formCadastro').reset();
            
            // Recarrega a tabela assim que salva!
            carregarEventosAdmin();

            setTimeout(() => {
                document.getElementById('alerta-sucesso').classList.add('d-none');
            }, 3000);
        }
    } catch (erro) {
        console.error("Erro de conexão:", erro);
    }
});

// 4. Faz a tabela carregar assim que a página abre
carregarEventosAdmin();