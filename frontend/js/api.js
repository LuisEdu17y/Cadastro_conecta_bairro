/**
 * api.js
 * ------
 * Cliente HTTP central da aplicação.
 *
 * - Detecta a base URL automaticamente (usa a mesma origem onde o
 *   frontend foi servido). Em dev, isso vira http://localhost:8000.
 * - Anexa o JWT (Bearer) salvo em localStorage automaticamente.
 * - Erros do backend são propagados como Error com .status e .detail.
 *
 * Uso:
 *   import API
 *   const eventos = await API.get('/eventos')
 *   await API.post('/eventos', { titulo: '...' })
 */

const API = (() => {
    const TOKEN_KEY = 'cb_token';
    const USER_KEY = 'cb_user';

    // Mesma origem do frontend (resolvido em runtime)
    const baseURL = window.location.origin;

    function setToken(token) { localStorage.setItem(TOKEN_KEY, token); }
    function getToken()      { return localStorage.getItem(TOKEN_KEY); }
    function clearToken()    { localStorage.removeItem(TOKEN_KEY); localStorage.removeItem(USER_KEY); }

    function setUser(user) { localStorage.setItem(USER_KEY, JSON.stringify(user)); }
    function getUser()     {
        try { return JSON.parse(localStorage.getItem(USER_KEY)); }
        catch { return null; }
    }

    async function request(method, path, body) {
        const headers = { 'Content-Type': 'application/json' };
        const token = getToken();
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const opts = { method, headers };
        if (body !== undefined) opts.body = JSON.stringify(body);

        let resposta;
        try {
            resposta = await fetch(`${baseURL}${path}`, opts);
        } catch (e) {
            const err = new Error('Não foi possível conectar ao servidor');
            err.status = 0;
            throw err;
        }

        // 204 No Content
        if (resposta.status === 204) return null;

        let dados;
        const tipo = resposta.headers.get('content-type') || '';
        if (tipo.includes('application/json')) {
            dados = await resposta.json();
        } else {
            dados = await resposta.text();
        }

        if (!resposta.ok) {
            const msg = (dados && dados.detail) || dados || 'Erro inesperado';
            const err = new Error(typeof msg === 'string' ? msg : 'Erro inesperado');
            err.status = resposta.status;
            err.detail = dados;
            // 401 com token: token expirou ou inválido -> sai
            if (resposta.status === 401 && token) {
                clearToken();
            }
            throw err;
        }
        return dados;
    }

    async function upload(path, formData) {
        const token = getToken();
        const headers = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;

        let resposta;
        try {
            resposta = await fetch(`${baseURL}${path}`, { method: 'POST', headers, body: formData });
        } catch (e) {
            const err = new Error('Não foi possível conectar ao servidor');
            err.status = 0;
            throw err;
        }

        let dados;
        const tipo = resposta.headers.get('content-type') || '';
        if (tipo.includes('application/json')) dados = await resposta.json();
        else dados = await resposta.text();

        if (!resposta.ok) {
            const msg = (dados && dados.detail) || dados || 'Erro no upload';
            const err = new Error(typeof msg === 'string' ? msg : 'Erro no upload');
            err.status = resposta.status;
            throw err;
        }
        return dados;
    }

    return {
        baseURL,
        get:    (path)        => request('GET', path),
        post:   (path, body)  => request('POST', path, body),
        put:    (path, body)  => request('PUT', path, body),
        delete: (path)        => request('DELETE', path),
        upload,
        setToken, getToken, clearToken,
        setUser,  getUser,
        isAuthenticated: () => !!getToken(),
    };
})();

// Disponível globalmente (não é módulo, são scripts simples)
window.API = API;
