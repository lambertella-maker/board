const CACHE = 'mealplan-v1776157764';
const ASSETS = ['./ep6-burger.png', './y18-panang.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
});

self.addEventListener('fetch', e => {
  // Never intercept HTML — goes straight to network so changes are always visible on refresh
  if (e.request.mode === 'navigate') return;
  // Static assets only: cache-first
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});
