const CACHE = 'mealplan-v1000000007';
const ASSETS = [
  './ep6-burger.png',
  './y18-panang.png',
  './o4-verenas-potato-salad.webp',
  './o5-chaat-masala-potatoes.webp',
  './o6-kale-tahini-caesar.jpg',
  './ep4-creamy-ramen-tofu.webp',
  './ep5-spicy-peanut-noodles.jpg',
  './ms1-pasta-fake-sauce.jpg',
  './ms2-miso-shiitake-kimchi-soup.jpg',
  './b12-blueberry-buttermilk-pancakes.jpg',
  './b13-challah.jpg'
];

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
