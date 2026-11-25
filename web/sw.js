/* Service worker sencillo. Sube VERSION para invalidar todo lo cacheado. */
const VERSION = 'v2';
const CASCARON = 'cascaron-' + VERSION, IMAGENES = 'imagenes-' + VERSION;
const PAGINAS = ['index', 'pared', 'mapa', 'linea', 'pasaporte-lego', 'lanyards', 'pines', 'fotos', 'certificados', 'intervenciones', 'premios', 'evento'];
const PRECACHE = [
  './', ...PAGINAS.map((p) => p + '.html'),
  'style.css', 'mapa.css', 'inicio.css', 'evento.css', 'fotos.css', 'certificados.css', 'intervenciones.css', 'lanyards.css', 'linea.css', 'pasaporte-lego.css', 'pines.css', 'premios.css', 'splash.css', 'buscador.css',
  'app.js', 'iconos.js', 'pasaporte.js', 'splash.js', 'inicio.js', 'evento.js', 'fotos.js', 'certificados.js', 'intervenciones.js', 'lanyards.js', 'linea.js', 'mapa.js', 'pasaporte-lego.js', 'pines.js', 'premios.js', 'buscador.js',
  'data/archivo.json', 'img/logo.svg', 'img/iconos.svg', 'img/app/icon-192.png', 'manifest.webmanifest',
];

self.addEventListener('install', (e) => {
  // uno a uno: si falta alguno, los demás se guardan igual
  e.waitUntil(caches.open(CASCARON).then((c) => Promise.all(PRECACHE.map((u) => c.add(u).catch(() => {})))).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CASCARON && k !== IMAGENES).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});

const redPrimero = (req, nombre) => fetch(req).then((r) => {
  if (r.ok) { const copia = r.clone(); caches.open(nombre).then((c) => c.put(req, copia)); }
  return r;
}).catch(() => caches.match(req, { ignoreSearch: true }).then((r) => r || Response.error()));

const cachePrimero = (req) => caches.match(req).then((r) => r || fetch(req).then((n) => {
  if (n.ok) { const copia = n.clone(); caches.open(IMAGENES).then((c) => c.put(req, copia)); }
  return n;
}));

self.addEventListener('fetch', (e) => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== location.origin || req.headers.has('range')) return;   // vídeos y CDN: directos
  if (/\/(img\/(?!app\/|logo|iconos)|video\/)/.test(url.pathname)) {
    if (url.pathname.includes('/video/')) return;   // shortcut: los vídeos no se guardan (pesan mucho)
    return e.respondWith(cachePrimero(req));        // imágenes: caché tras la primera vez
  }
  e.respondWith(redPrimero(req, CASCARON));        // html, css, js, datos: red primero, caché si no hay red
});
