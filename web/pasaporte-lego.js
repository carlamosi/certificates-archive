/* Pasaporte LEGO: una página por tienda. Ficha: docs/features/sellos-lego.md · Identidad: docs/diseno/IDENTIDAD.md */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const fmt = (iso, o) => new Date(iso + 'T12:00').toLocaleDateString('es', o);
  const rango = (v) => (v ? `${fmt(v.inicio, { day: 'numeric', month: 'short' })} – ${fmt(v.fin, { day: 'numeric', month: 'short', year: 'numeric' })}` : '');
  const km = (v) => (v && v.km ? ` · ${Math.round(v.km).toLocaleString('es')} km` : '');
  const plural = (n, uno, varios) => `${n} ${n === 1 ? uno : varios}`;
  const hoja = $('hoja'), ficha = $('ficha');
  let tiendas = [], paginas = [], cur = 0;

  // Sellos agrupados por tienda (sitio), en el orden en que se registraron
  function tiendasDe(A) {
    const ciudades = new Map(((A.totales || {}).ciudades || []).map((c) => [c.id, c.nombre]));
    const por = new Map();
    for (const v of A.viajes || []) {
      for (const o of v.objetos || []) {
        if (o.tipo !== 'sello') continue;
        if (!por.has(o.sitio)) por.set(o.sitio, { nombre: o.sitio, ciudad: ciudades.get(o.place_id) || '', v, sellos: [], id: o.id });
        por.get(o.sitio).sellos.push(o);
      }
    }
    return [...por.values()].sort((a, b) => a.id - b.id);
  }

  const pegDe = (t) => (t.nombre.includes('Aeropuerto') ? 'aeropuerto' : 'sello');
  const cabecera = (t) => `${IDENTIDAD.pegatina(pegDe(t))}
    <div><p class="kicker">${esc(t.ciudad)}${t.v ? ` · <span class="num">${fmt(t.v.inicio, { day: 'numeric', month: 'short', year: 'numeric' })}</span>` : ''}</p><h2>${esc(t.nombre)}</h2></div>
    <span class="n num" aria-label="${plural(t.sellos.length, 'sello', 'sellos')}">${t.sellos.length}</span>`;

  function pintar(dir) {
    const t = paginas[cur];
    hoja.className = 'hoja' + (t === 'portada' ? ' portada' : '');
    hoja.replaceChildren();
    if (t === 'portada') {
      const n = tiendas.reduce((s, x) => s + x.sellos.length, 0), c = new Set(tiendas.map((x) => x.ciudad)).size;
      hoja.innerHTML = `${IDENTIDAD.pegatina('sello')}<p class="kicker">Pasaporte</p><h2>Pasaporte LEGO</h2>
        <p class="sub">${plural(n, 'sello', 'sellos')} · ${plural(tiendas.length, 'tienda', 'tiendas')} · ${plural(c, 'ciudad', 'ciudades')}</p>
        <p class="sub">Pasa página con ← → o desliza.</p>`;
    } else {
      const zona = document.createElement('div'); zona.className = 'estampas';
      t.sellos.forEach((s, i) => {
        const b = document.createElement('button'); b.type = 'button'; b.className = 'est';
        b.setAttribute('aria-label', `${s.titulo}, ${t.nombre}`);
        // rotación, desvío y tinta fijos por posición: cada sello sale «estampado» distinto pero siempre igual
        b.style.cssText = `--rot:${(i * 47 % 17) - 8}deg;--dx:${(i * 13 % 9) - 4}px;--dy:${(i * 7 % 7) - 3}px;--op:${(0.84 + (i * 29 % 24) / 150).toFixed(2)}`;
        const img = new Image(); img.alt = ''; img.src = s.front_web;
        img.onload = () => { b.style.width = Math.round(40 * Math.sqrt(img.naturalWidth / img.naturalHeight)) + '%'; }; // más ancho, más sitio
        img.onerror = () => b.remove(); // recorte que falta: sin icono de imagen rota
        b.append(img); b.onclick = () => abrir(s, t); zona.append(b);
      });
      const pie = document.createElement('p'); pie.className = 'pie';
      pie.innerHTML = t.v ? `${esc(t.v.nombre)} · <span class="num">${rango(t.v)}</span>` : '';
      const cab = document.createElement('header'); cab.innerHTML = cabecera(t);
      hoja.append(cab, zona, pie);
    }
    if (dir && !matchMedia('(prefers-reduced-motion: reduce)').matches) { void hoja.offsetWidth; hoja.classList.add(dir > 0 ? 'sig' : 'ant'); }
    $('pag').textContent = `${cur + 1} / ${paginas.length}`;
    $('ant').disabled = cur === 0; $('sig').disabled = cur === paginas.length - 1;
  }
  function ir(d) { const n = cur + d; if (n < 0 || n >= paginas.length) return; cur = n; pintar(d); }

  function abrir(s, t) {
    ficha.innerHTML = `<div class="caja"><img class="tinta" src="${esc(s.front_web)}" alt="${esc(s.titulo)}"></div>
      <p class="kicker">${esc(t.ciudad)}</p><h2 id="f-t">${esc(s.titulo)}</h2>
      <dl><dt>Tienda</dt><dd>${esc(t.nombre)}</dd><dt>Ciudad</dt><dd>${esc(t.ciudad)}</dd><dt>Viaje</dt><dd>${t.v ? esc(t.v.nombre) : '—'}</dd>
      <dt>Fechas</dt><dd class="num">${rango(t.v)}${km(t.v)}</dd></dl>
      <button class="btn" type="button">Cerrar</button>`;
    ficha.querySelector('.btn').onclick = () => ficha.close();
    ficha.showModal();
    ficha.focus(); // el foco al contenedor, no a «Cerrar»: Espacio/Enter con el que se abrió no debe cerrarlo
  }
  ficha.addEventListener('click', (e) => { if (e.target === ficha) ficha.close(); });
  $('ant').onclick = () => ir(-1); $('sig').onclick = () => ir(1);
  window.addEventListener('keydown', (e) => {
    if (document.querySelector('dialog[open]') || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return; // ni con la ficha ni con el índice abierto
    if (e.key === 'ArrowLeft') ir(-1); else if (e.key === 'ArrowRight') ir(1);
  });
  let x0 = null; // deslizar: ≥ 50 px horizontales
  hoja.addEventListener('pointerdown', (e) => { x0 = e.clientX; });
  hoja.addEventListener('pointerup', (e) => { if (x0 != null && Math.abs(e.clientX - x0) > 50) ir(e.clientX < x0 ? 1 : -1); x0 = null; });

  async function iniciar() {
    try {
      const res = await fetch('data/archivo.json', { cache: 'no-store' });
      if (!res.ok) throw new Error();
      tiendas = tiendasDe(await res.json());
    } catch (e) {
      $('count').textContent = '';
      $('notice').textContent = 'No encuentro data/archivo.json. Genera el fichero con «archivo.py exportar web/data/archivo.json» y recarga.';
      $('notice').hidden = false; return;
    }
    if (!tiendas.length) { $('count').textContent = ''; $('notice').textContent = 'Todavía no hay sellos en el archivo.'; $('notice').hidden = false; return; }
    paginas = ['portada', ...tiendas];
    $('count').textContent = plural(tiendas.reduce((s, x) => s + x.sellos.length, 0), 'sello', 'sellos');
    pintar();
  }
  iniciar();
})();
