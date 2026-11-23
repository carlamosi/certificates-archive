/* Navegación común «pasaporte» (diseño B del lienzo). Una sola fuente para todas las páginas:
   el logo se convierte en un sello que abre el índice; en móvil, barra de pestañas abajo. */
(() => {
  'use strict';
  const P = (t) => (window.IDENTIDAD ? IDENTIDAD.pegatina(t) : '');
  // [id, nombre, página, pegatina, grupo, ¿existe ya?]
  const MODULOS = [
    ['pared', 'Pared 3D', 'index.html', 'lanyard', 'Inicio', true],
    ['mapa', 'Mapa', 'mapa.html', 'pais', 'Viajes', true],
    ['tiempo', 'Línea del tiempo', '', 'evento', 'Viajes', false],
    ['lanyards', 'Lanyards', 'lanyards.html', 'lanyard', 'Colección', true],
    ['pines', 'Pines', 'pines.html', 'pin', 'Colección', true],
    ['fotos', 'Fotos', 'fotos.html', 'foto', 'Colección', true],
    ['certificados', 'Certificados', 'certificados.html', 'certificado', 'Colección', true],
    ['intervenciones', 'Intervenciones', 'intervenciones.html', 'charla', 'Trayectoria', true],
    ['premios', 'Premios', 'premios.html', 'premio', 'Trayectoria', true],
    ['personas', 'Personas', '', 'persona', 'Trayectoria', false],
  ];
  const pagina = location.pathname.split('/').pop() || 'index.html';
  const actual = MODULOS.find((m) => m[2] === pagina) || MODULOS[0];
  const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  // ---- barra: sello + «Archivo / sección»
  const bar = document.querySelector('header.bar');
  if (!bar) return;
  bar.classList.add('pasaporte-bar');
  bar.querySelector('nav.chips[aria-label="Secciones"]')?.remove();
  const logo = bar.querySelector('.brand img');
  const titulo = bar.querySelector('.brand h1');
  const sello = document.createElement('button');
  sello.type = 'button';
  sello.className = 'sello-btn';
  sello.setAttribute('aria-label', 'Abrir el índice del archivo');
  sello.setAttribute('aria-haspopup', 'dialog');
  if (logo) { logo.replaceWith(sello); sello.appendChild(logo); }
  if (titulo) titulo.innerHTML = `<span class="miga">Archivo</span><span class="miga-sep" aria-hidden="true">/</span><b>${esc(actual[1])}</b>`;

  // ---- índice pasaporte
  const dlg = document.createElement('dialog');
  dlg.className = 'pasaporte';
  dlg.setAttribute('aria-label', 'Índice del archivo');
  const sellos = MODULOS.map(([id, nombre, url, peg, , hecho], i) => {
    const giro = ['-2deg', '1.5deg', '-1deg', '2deg', '1deg', '-1.5deg', '2deg', '-2deg', '1deg', '-1deg'][i];
    const aqui = id === actual[0];
    const dentro = `<span class="estampa-marco"><span class="estampa-cara">${P(peg)}<b>${esc(nombre)}</b><small data-cifra="${id}">${hecho ? '' : 'pronto'}</small></span></span>${aqui ? '<span class="matasellos" aria-hidden="true">AQUÍ</span>' : ''}`;
    return hecho
      ? `<a class="estampa${aqui ? ' aqui' : ''}" href="${url}" style="--giro:${giro}"${aqui ? ' aria-current="page"' : ''}>${dentro}</a>`
      : `<span class="estampa pronto" style="--giro:${giro}" aria-disabled="true">${dentro}</span>`;
  }).join('');
  dlg.innerHTML = `
    <div class="pasaporte-libro">
      <section class="pasaporte-portada">
        <p class="pp-kicker">Pasaporte del archivo</p>
        <p class="pp-nombre">Certificates<br><b>Archive</b></p>
        <span class="pp-globo">${P('pais')}</span>
        <dl class="pp-cifras" id="ppCifras"></dl>
      </section>
      <section class="pasaporte-hoja">
        <div class="pp-cabeza">
          <p class="kicker">Elige dónde ir</p>
          <button type="button" class="btn ghost redondo pp-cerrar" aria-label="Cerrar el índice"><svg class="icono" aria-hidden="true"><use href="img/iconos.svg#cerrar"/></svg></button>
        </div>
        <nav class="pp-sellos" aria-label="Secciones del archivo">${sellos}</nav>
      </section>
    </div>`;
  document.body.appendChild(dlg);
  const abrir = () => { dlg.showModal(); dlg.querySelector('.estampa.aqui, .estampa[href]')?.focus(); };
  sello.addEventListener('click', abrir);
  dlg.querySelector('.pp-cerrar').addEventListener('click', () => dlg.close());
  dlg.addEventListener('click', (e) => { if (e.target === dlg) dlg.close(); });   // clic fuera del libro
  dlg.addEventListener('close', () => sello.focus());

  // ---- móvil: pestañas abajo con una hoja por grupo
  const grupos = ['Inicio', 'Viajes', 'Colección', 'Trayectoria'];
  const nombreTab = { Inicio: 'Pared', Viajes: 'Viajes', 'Colección': 'Colección', Trayectoria: 'Trayectoria' };
  const pegTab = { Inicio: 'lanyard', Viajes: 'pais', 'Colección': 'pin', Trayectoria: 'charla' };
  const tabs = document.createElement('nav');
  tabs.className = 'pestanas';
  tabs.setAttribute('aria-label', 'Secciones');
  tabs.innerHTML = grupos.map((g) => {
    const activo = actual[4] === g;
    return g === 'Inicio'
      ? `<a class="pestana${activo ? ' activa' : ''}" href="index.html"${activo ? ' aria-current="page"' : ''}>${P(pegTab[g])}<span>${nombreTab[g]}</span></a>`
      : `<button type="button" class="pestana${activo ? ' activa' : ''}" data-grupo="${g}" aria-expanded="false">${P(pegTab[g])}<span>${nombreTab[g]}</span></button>`;
  }).join('');
  const hoja = document.createElement('div');
  hoja.className = 'pestanas-hoja';
  hoja.hidden = true;
  document.body.append(hoja, tabs);
  tabs.addEventListener('click', (e) => {
    const b = e.target.closest('button[data-grupo]');
    if (!b) return;
    const abierta = b.getAttribute('aria-expanded') === 'true';
    tabs.querySelectorAll('button[data-grupo]').forEach((x) => x.setAttribute('aria-expanded', 'false'));
    if (abierta) { hoja.hidden = true; return; }
    b.setAttribute('aria-expanded', 'true');
    const g = b.dataset.grupo;
    hoja.innerHTML = `<p class="kicker">${esc(g)}</p><div class="pp-sellos">${
      dlg.querySelectorAll('.estampa').length ? MODULOS.map((m, i) => (m[4] === g ? dlg.querySelectorAll('.estampa')[i].outerHTML : '')).join('') : ''}</div>`;
    hoja.hidden = false;
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !hoja.hidden) { hoja.hidden = true; tabs.querySelectorAll('[aria-expanded="true"]').forEach((x) => x.setAttribute('aria-expanded', 'false')); }
  });

  // ---- cifras del archivo (opcional: sin archivo.json el índice funciona igual)
  const pon = (id, txt) => document.querySelectorAll(`[data-cifra="${id}"]`).forEach((el) => { el.textContent = txt; });
  fetch('data/archivo.json', { cache: 'no-store' }).then((r) => (r.ok ? r.json() : null)).then((A) => {
    if (!A) return;
    const objs = [...(A.eventos || []).flatMap((e) => e.objetos || []), ...(A.viajes || []).flatMap((v) => v.objetos || []), ...(A.objetos_sueltos || [])];
    const unicos = [...new Map(objs.map((o) => [o.uid || o.id, o])).values()];
    const n = (f) => unicos.filter(f).length;
    const viajes = (A.viajes || []).length;
    pon('mapa', `${viajes} viajes`);
    pon('pines', `${n((o) => o.tipo === 'pin')}`);
    pon('fotos', `${(A.eventos || []).reduce((s, e) => s + (e.fotos || []).length, 0) + (A.fotos_sueltas || []).length}`);
    pon('certificados', `${n((o) => o.tipo === 'certificado')}`);
    pon('premios', `${n((o) => ['primer premio', 'podio', 'finalista', 'mención'].includes(o.nivel))}`);
    pon('pared', 'la entrada');
    const t = A.totales || {};
    const paises = (t.paises || []).filter((p) => p.ciudades > 0).length;
    const cifras = [[viajes, 'viajes'], [paises, 'países'], [t.km, 'km recorridos'], [(A.eventos || []).length, 'eventos']]
      .filter(([v]) => Number.isFinite(v));
    document.getElementById('ppCifras').innerHTML = cifras.map(([v, txt]) => `<div><dd>${Math.round(v).toLocaleString('es-ES')}</dd><dt>${txt}</dt></div>`).join('');
  }).catch(() => {});
})();
