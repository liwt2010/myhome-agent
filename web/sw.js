// myhome-agent Service Worker (v0.8)
// §59 PWA 完整形态：离线缓存 + Web Push 监听

const CACHE_NAME = 'myhome-agent-v0.8';
const RUNTIME_CACHE = 'myhome-runtime-v0.8';

const PRECACHE_URLS = [
  '/',
  '/manifest.json'
];

const CACHE_STRATEGIES = {
  '/': 'network-first',
  '/static/': 'cache-first',
  '/api/rules': 'stale-while-revalidate',
  '/api/devices': 'stale-while-revalidate',
  '/api/readings': 'stale-while-revalidate',
  '/api/chat': 'network-only',
  '/api/control': 'network-only'
};

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(PRECACHE_URLS))
      .catch(err => console.warn('[SW] precache failed', err))
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys
        .filter(k => k !== CACHE_NAME && k !== RUNTIME_CACHE)
        .map(k => caches.delete(k)))
    )
  );
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  const strategy = Object.entries(CACHE_STRATEGIES)
    .find(([prefix]) => url.pathname.startsWith(prefix))?.[1] || 'network-first';
  event.respondWith(handleFetch(event.request, strategy));
});

async function handleFetch(request, strategy) {
  const cache = await caches.open(RUNTIME_CACHE);
  switch (strategy) {
    case 'cache-first':
      const cached = await cache.match(request);
      if (cached) return cached;
      const fresh = await fetch(request);
      if (fresh.ok) cache.put(request, fresh.clone());
      return fresh;
    case 'stale-while-revalidate':
      const stale = await cache.match(request);
      const networkPromise = fetch(request).then(resp => {
        if (resp.ok) cache.put(request, resp.clone());
        return resp;
      }).catch(() => stale);
      return stale || networkPromise;
    case 'network-only':
    default:
      return fetch(request);
  }
}

// Web Push 监听（v0.8 新增）
self.addEventListener('push', event => {
  if (!event.data) return;
  const payload = event.data.json();
  const options = {
    body: payload.body || '',
    icon: payload.icon || '/static/icons/icon-192.png',
    badge: payload.badge || '/static/icons/icon-96.png',
    data: payload.data || {},
    actions: payload.actions || [],
    tag: payload.tag || 'default',
    requireInteraction: payload.severity === 'safety'
  };
  event.waitUntil(
    self.registration.showNotification(payload.title || 'myhome-agent', options)
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const targetUrl = event.notification.data?.url || '/';
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then(clientList => {
      for (const client of clientList) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.focus();
          return;
        }
      }
      if (clients.openWindow) return clients.openWindow(targetUrl);
    })
  );
});