/* Arranque de la PWA, un solo sitio: splash (una vez por sesión y al abrir la app) + registro del service worker. */
(() => {
  'use strict';
  let ya = false;
  try { ya = sessionStorage.getItem('splash') === '1'; sessionStorage.setItem('splash', '1'); } catch (e) { /* sin sessionStorage: se muestra siempre */ }
  if (!ya) {
    const s = document.createElement('div');
    s.id = 'splash'; s.setAttribute('aria-hidden', 'true');
    s.innerHTML = '<img src="img/logo.svg" alt=""><p>Certificates <b>Archive</b></p>';
    document.documentElement.appendChild(s);
    const quitar = () => s.remove();
    s.addEventListener('animationend', (e) => { if (e.target === s) quitar(); });
    setTimeout(quitar, 1500);   // por si la animación no corre (pestaña en segundo plano)
  }
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => navigator.serviceWorker.register('sw.js').catch(() => {}));
  }
})();
