// BhashaSandhi Service Worker for App Shell Caching & Offline Fallback
const CACHE_NAME = "bhashasandhi-shell-v1";
const ASSETS_TO_CACHE = [
  "/",
  "/static/style.css",
  "/static/app.js",
  "/api/languages"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("[Service Worker] Caching app shell assets");
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log("[Service Worker] Removing old cache", key);
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  // Pass through non-GET and API streaming requests directly
  if (event.request.method !== "GET" || event.request.url.includes("/api/chat")) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request).catch(() => {
        // Fallback for document navigation
        if (event.request.mode === "navigate") {
          return caches.match("/");
        }
      });
    })
  );
});
