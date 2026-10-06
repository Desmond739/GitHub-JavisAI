const CACHE="naya-v3";
const ASSETS=["/app/","/app/styles.css","/app/app.js","/app/manifest.webmanifest"];
self.addEventListener("install",event=>event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(ASSETS))));
self.addEventListener("activate",event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key!==CACHE).map(key=>caches.delete(key))))));
self.addEventListener("fetch",event=>{if(event.request.method==="GET")event.respondWith(fetch(event.request).catch(()=>caches.match(event.request)))});
