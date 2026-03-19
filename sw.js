const CACHE = 'mealplan-v1773916886';
const ASSETS = ['./ep6-burger.png', './y18-panang.png'];

self.addEventListener('install', e => {
  // Cache static assets only — no skipWaiting, so new SW never interrupts a live session
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
});

self.addEventListener('activate', e => {
  // Clean up old caches — no clients.claim, so existing pages are never forcibly taken over
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
});

self.addEventListener('fetch', e => {
  // HTML: always network-first so users always get the latest version
  if (e.request.mode === 'navigate') {
    e.respondWith(
      fetch(e.request)
        .then(r => { caches.open(CACHE).then(c => c.put(e.request, r.clone())); return r; })
        .catch(() => caches.match(e.request))
    );
    return;
  }
  // Static assets: cache-first
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});
