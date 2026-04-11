// login.js

const form = document.querySelector('form');
const btnLogin = document.getElementById('btn-login');

form.addEventListener('submit', async (e) => {
    e.preventDefault(); 

    const email = document.getElementById('floatingInput').value;
    const senha = document.getElementById('floatingPassword').value;

    btnLogin.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Verificando...';
    btnLogin.disabled = true;

    try {
        const resposta = await fetch('https://api-sara-social.onrender.com/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, senha })
        });

        const dados = await resposta.json();

        if (resposta.ok) {
            localStorage.setItem('usuarioLogado', 'true');
            window.location.href = 'home.html';
        } else {
            alert(dados.detail || 'E-mail ou senha incorretos!');
        }
    } catch (erro) {
        console.error('Erro ao logar:', erro);
        alert('Erro ao conectar com o servidor.');
    } finally {
        btnLogin.innerHTML = 'Entrar';
        btnLogin.disabled = false;
    }
});