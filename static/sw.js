const CACHE = 'health-v1';

// Pages and assets to cache immediately on install
const PRECACHE = [
  '/tracker/',
  '/tracker/history/',
  '/static/css/custom.css',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
];

// Install — cache core assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE).then(cache => cache.addAll(PRECACHE))
  );
  self.skipWaiting();
});

// Activate — delete old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch — network first, fall back to cache
self.addEventListener('fetch', event => {
  // Only handle GET requests, skip API/POST calls
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);

  // Skip AI and auth endpoints — always need network
  const skipPaths = ['/assistant/', '/accounts/login', '/accounts/logout',
                     '/tracker/estimate-', '/admin/'];
  if (skipPaths.some(p => url.pathname.startsWith(p))) return;

  event.respondWith(
    fetch(event.request)
      .then(response => {
        // Cache a fresh copy of pages we successfully fetch
        if (response.ok && (url.pathname.startsWith('/tracker/') || url.pathname.startsWith('/static/'))) {
          const clone = response.clone();
          caches.open(CACHE).then(cache => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => caches.match(event.request))  // offline fallback
  );
});
