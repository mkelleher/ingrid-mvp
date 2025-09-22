// Service Worker for PWA functionality
const CACHE_NAME = 'ingrid-pwa-v1';
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cached version or fetch from network
        return response || fetch(event.request);
      })
  );
});

// Background sync for offline scanning
self.addEventListener('sync', event => {
  if (event.tag === 'background-sync') {
    console.log('Background sync triggered');
  }
});

// Push notifications for scan results
self.addEventListener('push', event => {
  const options = {
    body: event.data ? event.data.text() : 'Scan completed!',
    icon: '/logo192.png',
    badge: '/logo192.png'
  };
  
  event.waitUntil(
    self.registration.showNotification('Ingrid', options)
  );
});