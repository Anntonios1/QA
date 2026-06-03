/**
 * ============================================================
 *  SERVICE WORKER - ControlCash PWA
 * ============================================================
 *  Normas aplicadas:
 *    - ISO/IEC 25000: Fiabilidad - Disponibilidad
 *    - ISO/IEC 20000: Continuidad del servicio
 *    - ISO 9126: Eficiencia - Tiempo de respuesta
 *    - ISO/IEC 27001: Seguridad - Integridad de datos en cache
 * ============================================================
 *  Estrategia: Network First con fallback a Cache
 *  - API requests: Network only (datos deben ser frescos)
 *  - Static assets: Cache First, luego Network
 *  - Offline: Muestra versión cacheada si disponible
 * ============================================================
 */

const CACHE_NAME = 'controlcash-v4';
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/styles.css',
    '/app.js',
    '/manifest.json'
];

const OPTIONAL_ASSETS = [
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap',
    'https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500&display=swap'
];

const APP_SHELL_PATHS = new Set([
    '/',
    '/index.html',
    '/app.js',
    '/styles.css',
    '/manifest.json'
]);

// ============================================================
//  INSTALL — Pre-cachear assets estáticos
// ============================================================
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[SW] Pre-cacheando assets estáticos');
            return cache.addAll(STATIC_ASSETS).then(() =>
                Promise.allSettled(
                    OPTIONAL_ASSETS.map((asset) => cache.add(asset))
                )
            );
        })
    );
    self.skipWaiting();
});

// ============================================================
//  ACTIVATE — Limpiar caches antiguos
// ============================================================
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(
                keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
            )
        )
    );
    self.clients.claim();
});

// ============================================================
//  FETCH — Estrategia de caché inteligente
// ============================================================
// [NORMA: ISO/IEC 25000 - Fiabilidad] Continuidad de servicio y disponibilidad local mediante service worker
// [NORMA: ISO 9126 - Eficiencia] Optimización de tiempos de respuesta mediante almacenamiento en caché local
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // API requests → Network only (datos siempre frescos)
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(request).catch(() =>
                new Response(
                    JSON.stringify({
                        status: 'error',
                        mensaje: 'Sin conexión. Intente más tarde.'
                    }),
                    {
                        status: 503,
                        headers: { 'Content-Type': 'application/json' }
                    }
                )
            )
        );
        return;
    }

    // App shell -> Network First para evitar UI obsoleta en actualizaciones
    if (request.mode === 'navigate' || APP_SHELL_PATHS.has(url.pathname)) {
        event.respondWith(
            fetch(request)
                .then((response) => {
                    if (response.ok) {
                        const clone = response.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(request, clone);
                        });
                    }
                    return response;
                })
                .catch(async () => {
                    const cached = await caches.match(request);
                    return cached || caches.match('/index.html');
                })
        );
        return;
    }

    // Static assets → Cache First, Network Fallback
    event.respondWith(
        caches.match(request).then((cached) => {
            const networkFetch = fetch(request)
                .then((response) => {
                    // Actualizar cache con respuesta fresca
                    if (response.ok) {
                        const clone = response.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(request, clone);
                        });
                    }
                    return response;
                })
                .catch(() => cached);

            return cached || networkFetch;
        })
    );
});

// ============================================================
//  PUSH — Notificaciones Push (preparado para F3)
// ============================================================
self.addEventListener('push', (event) => {
    if (!event.data) return;
    const payload = event.data.json();
    event.waitUntil(
        self.registration.showNotification(payload.titulo || 'ControlCash', {
            body: payload.mensaje || '',
            icon: '/icons/icon-192.svg',
            badge: '/icons/icon-72.svg',
            tag: payload.tag || 'default',
            data: payload.data || {}
        })
    );
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    event.waitUntil(
        self.clients.matchAll({ type: 'window' }).then((clients) => {
            if (clients.length > 0) {
                return clients[0].focus();
            }
            return self.clients.openWindow('/');
        })
    );
});
