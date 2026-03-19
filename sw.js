const CACHE = 'mealplan-v1773917677';
const ASSETS = ['./ep6-burger.png', './y18-panang.png'];

self.addEventListener('install', e => {
  // skipWaiting: new SW activates immediately so next page load/refresh gets fresh HTML
  // (clients.claim removed — so existing live sessions are never interrupted)
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
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
