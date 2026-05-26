const CACHE = 'cb-v1';
const SHELL = [
    '/',
    '/app',
    '/login',
    '/static/css/style.css',
    '/static/js/api.js',
    '/static/js/ui.js',
];

self.addEventListener('install', e => {
    e.waitUntil(
        caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', e => {
    e.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
        ).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', e => {
    const url = new URL(e.request.url);

    // Requisições de API: sempre rede (network-first)
    if (url.pathname.startsWith('/eventos') || url.pathname.startsWith('/auth') || url.pathname.startsWith('/admin')) {
        e.respondWith(
            fetch(e.request).catch(() => new Response(JSON.stringify({ erro: 'offline' }), {
                headers: { 'Content-Type': 'application/json' },
            }))
        );
        return;
    }

    // Assets estáticos: cache-first
    e.respondWith(
        caches.match(e.request).then(cached => cached || fetch(e.request).then(resp => {
            if (resp.ok && e.request.method === 'GET') {
                caches.open(CACHE).then(c => c.put(e.request, resp.clone()));
            }
            return resp;
        }))
    );
});
