/**
 * ui.js
 * -----
 * Utilitários de UI compartilhados:
 *   - toast(mensagem, tipo)
 *   - confirmar(opções) -> Promise<boolean>
 *   - exigirLogin(nivel) -> redireciona se faltar (chamado no topo das páginas)
 *   - sair() -> remove token e volta pra raiz
 */

(function() {
    // -------- TOASTS --------
    let toastWrap = null;
    function ensureWrap() {
        if (toastWrap) return toastWrap;
        toastWrap = document.createElement('div');
        toastWrap.className = 'toast-wrap';
        document.body.appendChild(toastWrap);
        return toastWrap;
    }

    window.toast = function(mensagem, tipo = 'info', duracao = 3200) {
        const wrap = ensureWrap();
        const el = document.createElement('div');
        el.className = `toast toast--${tipo}`;
        const ic = tipo === 'success' ? 'bi-check-circle-fill'
                : tipo === 'error'   ? 'bi-exclamation-triangle-fill'
                : 'bi-info-circle-fill';
        el.innerHTML = `<i class="bi ${ic}"></i><span>${mensagem}</span>`;
        wrap.appendChild(el);
        setTimeout(() => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(10px)';
            el.style.transition = 'all 0.25s ease';
            setTimeout(() => el.remove(), 260);
        }, duracao);
    };

    // -------- CONFIRMAR (modal) --------
    window.confirmar = function(opts) {
        const {
            titulo = 'Confirmar?',
            mensagem = '',
            textoOk = 'Confirmar',
            textoCancelar = 'Cancelar',
            perigoso = false,
        } = opts || {};

        return new Promise((resolve) => {
            const bd = document.createElement('div');
            bd.className = 'cb-modal-backdrop';
            bd.innerHTML = `
                <div class="cb-modal">
                    <h3>${titulo}</h3>
                    <p class="text-muted-soft">${mensagem}</p>
                    <div class="flex gap-2 mt-3">
                        <button class="btn-cb btn-cb--soft btn-cb--block" data-act="no">${textoCancelar}</button>
                        <button class="btn-cb ${perigoso ? 'btn-cb--accent' : 'btn-cb--primary'} btn-cb--block" data-act="yes">${textoOk}</button>
                    </div>
                </div>
            `;
            document.body.appendChild(bd);
            const close = (val) => { bd.remove(); resolve(val); };
            bd.addEventListener('click', (e) => {
                if (e.target === bd) close(false);
                const act = e.target.closest('[data-act]')?.dataset.act;
                if (act === 'yes') close(true);
                if (act === 'no')  close(false);
            });
        });
    };

    // -------- GUARDS de página --------
    /**
     * exigirLogin('qualquer'|'admin') — redireciona para /login se faltar.
     * Chamar no topo da página.
     */
    window.exigirLogin = function(nivel = 'qualquer') {
        if (!API.isAuthenticated()) {
            window.location.href = '/login';
            return null;
        }
        const usuario = API.getUser();
        if (nivel === 'admin' && (!usuario || usuario.role !== 'admin')) {
            toast('Acesso restrito a administradores', 'error');
            setTimeout(() => window.location.href = '/app', 1500);
            return null;
        }
        return usuario;
    };

    // -------- SAIR --------
    window.sair = async function(silencioso = false) {
        API.clearToken();
        if (!silencioso) toast('Você saiu. Até logo!', 'info', 1500);
        setTimeout(() => window.location.href = '/login', silencioso ? 0 : 600);
    };

    // -------- HELPER: iniciais do nome --------
    window.iniciais = function(nome) {
        if (!nome) return '?';
        const partes = nome.trim().split(/\s+/);
        if (partes.length === 1) return partes[0][0].toUpperCase();
        return (partes[0][0] + partes[partes.length - 1][0]).toUpperCase();
    };
})();
