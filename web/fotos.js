/* Fotos con personas · docs/features/fotos.md. Lee data/archivo.json (nunca SQLite). */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const norma = (t) => t.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
  const esc = (t) => String(t).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const pl = (n, uno, varios) => `${n} ${n === 1 ? uno : varios}`;
  const fechaLarga = (f) => {   // 'AAAA-MM-DD' (o AAAA-MM) -> '9 de noviembre de 2025'
    const [y, m, d] = f.split('-');
    return m ? `${d ? Number(d) + ' de ' : ''}${MESES[m - 1]} de ${y}` : y;
  };
  const mesTitulo = (ym) => { const [y, m = 1] = ym.split('-'); return `${MESES[m - 1][0].toUpperCase()}${MESES[m - 1].slice(1)} de ${y}`; };
  const GIROS = [-1.5, 1, -.5, 1.5, .8, -1.2, 1.2, -.8];

  let instagram = {};      // nombre -> usuario de Instagram
  let fotos = [];          // todas las que tienen WebP, más recientes primero
  let visibles = [];       // las que pasan el filtro
  let anio = null, q = '', evento = null;   // evento: clave del evento cuyas fotos se ven todas
  let actual = -1, origen = null;   // índice en `visibles` y botón que abrió el visor

  function reunir(d) {
    const out = [];
    const add = (f, ev, viaje) => {
      if (f.web) out.push({ ...f, evento: ev ? ev.nombre : (viaje ? viaje.nombre : 'Foto suelta'), ciudad: ev ? ev.ciudad : '', clave: f.personas.map(norma),
        slug: ev ? ev.slug : '', evKey: ev ? ev.slug : (viaje ? 'viaje:' + viaje.slug : 'suelta'), mapa: !!(ev && ev.lat != null && ev.lng != null) });
    };
    (d.eventos || []).forEach((e) => (e.fotos || []).forEach((f) => add(f, e)));
    (d.viajes || []).forEach((v) => (v.fotos || []).forEach((f) => add(f, null, v)));
    (d.fotos_sueltas || []).forEach((f) => add(f));
    // fotos por evento (para «4 fotos»)
    const porEvento = {};
    out.forEach((f) => { porEvento[f.evKey] = (porEvento[f.evKey] || 0) + 1; });
    out.forEach((f) => { f.nEvento = porEvento[f.evKey]; });
    return out.sort((a, b) => b.fecha.localeCompare(a.fecha) || a.archivo.localeCompare(b.archivo));
  }

  const coincide = (toks, nombres) => toks.every((t) => nombres.some((n) => n.split(/[\s_-]+/).some((w) => w.startsWith(t))));

  function filtrar() {
    const toks = norma(q).split(/\s+/).filter(Boolean);
    if (evento) { visibles = fotos.filter((f) => f.evKey === evento); return; }
    visibles = fotos.filter((f) => toks.length
      ? coincide(toks, f.clave)   // principio de palabra; ignora el año
      : (anio === 'todas' || f.fecha.slice(0, 4) === anio));
  }

  function pintar() {
    filtrar();
    const buscando = q.trim() !== '';
    // chips de año
    const porAnio = {};
    fotos.forEach((f) => { const y = f.fecha.slice(0, 4); porAnio[y] = (porAnio[y] || 0) + 1; });
    const activo = !buscando && !evento;
    $('anios').innerHTML = [['todas', 'Todas', fotos.length], ...Object.keys(porAnio).sort().reverse().map((y) => [y, y, porAnio[y]])].map(([k, nombre, n]) =>
      `<button type="button" class="chip anio" data-anio="${k}" aria-pressed="${activo && k === anio}">${nombre}<small class="num">${n}</small></button>`).join('');
    // resultado
    const eventos = new Set(visibles.map((f) => f.evKey)).size;
    $('quitar').hidden = !evento;
    $('resultado').textContent = evento
      ? `${pl(visibles.length, 'foto', 'fotos')} de «${visibles[0] ? visibles[0].evento : ''}»`
      : buscando
      ? `${pl(visibles.length, 'foto', 'fotos')} con «${q.trim()}»`
      : `${pl(eventos, 'evento', 'eventos')} · ${pl(visibles.length, 'foto', 'fotos')}`;
    // meses
    const meses = {};
    visibles.forEach((f, i) => { (meses[f.fecha.slice(0, 7)] = meses[f.fecha.slice(0, 7)] || []).push(i); });
    const vistos = new Set();
    $('meses').innerHTML = Object.keys(meses).sort().reverse().map((ym) => `
      <section class="mes" aria-label="${mesTitulo(ym)}">
        <h2>${mesTitulo(ym)}</h2>
        <div class="rejilla">${meses[ym].map((i) => {
          const f = visibles[i];
          const marca = f.ciudad && !vistos.has(f.evKey + ym) && vistos.add(f.evKey + ym);   // matasellos solo en la primera foto de cada evento
          return `<button type="button" class="tarjeta" data-i="${i}" style="--giro:${GIROS[i % GIROS.length]}deg" aria-label="Ampliar foto de ${esc(f.evento)}, ${fechaLarga(f.fecha)}">
            <span class="marco"><span class="sello"><img src="${esc(f.mini || f.web)}" alt="" loading="lazy" decoding="async"></span>${marca
              ? `<span class="matasellos" aria-hidden="true">${esc(f.ciudad.length > 11 ? f.ciudad.slice(0, 10).trimEnd() + '…' : f.ciudad)}<br>${f.fecha.slice(0, 4)}</span>` : ''}</span>
            <span class="pie"><span class="kicker">${fechaLarga(f.fecha).replace(/ de \d{4}$/, '')}</span><span class="nom">${esc(f.evento)}</span></span>
          </button>`;
        }).join('')}</div>
      </section>`).join('');
    const vacio = $('vacio');
    vacio.hidden = visibles.length > 0;
    vacio.textContent = buscando ? `Nadie llamado «${q.trim()}» sale en las fotos.` : 'No hay fotos de este año.';
  }

  // ---------- visor ----------
  function abrir(i, boton) {
    if (boton) origen = boton;
    actual = i;
    const f = visibles[i];
    const img = $('vImg');
    img.src = f.web;
    img.alt = `Foto de ${f.evento}${f.personas.length ? ' con ' + f.personas.join(', ') : ''}`;
    $('vFecha').textContent = fechaLarga(f.fecha);
    $('vEvento').textContent = f.evento;
    $('vNota').hidden = !f.nota; $('vNota').textContent = f.nota || '';
    $('vLugar').textContent = [f.ciudad, pl(f.nEvento, 'foto', 'fotos')].filter(Boolean).join(' · ');
    $('vPersonas').innerHTML = f.personas.length
      ? f.personas.map((n) => instagram[n]
        ? `<a class="persona" href="https://www.instagram.com/${instagram[n]}/" target="_blank" rel="noopener noreferrer" aria-label="${esc(n)} en Instagram (se abre en otra pestaña)">${esc(n)}${window.IDENTIDAD ? window.IDENTIDAD.icono('abrir') : ''}</a>`
        : `<button type="button" class="persona" data-nombre="${esc(n)}">${esc(n)}</button>`).join('')
      : '<p class="sub">Sin personas anotadas.</p>';
    $('vPos').textContent = `${i + 1} de ${visibles.length}`;
    $('vEv').hidden = !!evento || f.nEvento < 2;   // «ver las N fotos del evento» solo si hay más de una
    $('vEv').textContent = `Ver las ${f.nEvento} fotos del evento`;
    $('vEvt').hidden = !f.slug; if (f.slug) $('vEvt').href = `evento.html?e=${encodeURIComponent(f.slug)}`;
    $('vMapa').hidden = !f.mapa;
    $('vBajar').href = f.web;
    $('vBajar').download = `${f.fecha}_${norma(f.evento).replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}.webp`;
    resetZoom();
    $('vAnt').disabled = $('vSig').disabled = visibles.length < 2;
    if ($('visor').hidden) {
      $('visor').hidden = false;
      document.body.classList.add('visor-abierto');
      document.querySelectorAll('.bar, .album').forEach((e) => { e.inert = true; });
      $('visorCard').focus({ preventScroll: true });   // el foco no va a un botón que Enter pulsaría
    }
  }
  function cerrar() {
    if ($('visor').hidden) return;
    $('visor').hidden = true;
    document.body.classList.remove('visor-abierto'); resetZoom();
    document.querySelectorAll('.bar, .album').forEach((e) => { e.inert = false; });
    const b = origen && origen.isConnected ? origen : document.querySelector(`.tarjeta[data-i="${actual}"]`);
    if (b) b.focus({ preventScroll: true });
  }
  const mover = (d) => { if (visibles.length > 1) abrir((actual + d + visibles.length) % visibles.length); };

  // ---------- zoom (doble toque, pellizco, rueda, + - 0) y deslizar para cambiar de foto ----------
  const Z = { s: 1, x: 0, y: 0 };
  const caja = $('vCaja'), img = $('vImg');
  const ptrs = new Map();
  let gesto = null;   // pellizco: {d0, s0}; un dedo: {x0, y0, zx, zy}
  function aplicar() {
    const r = caja.getBoundingClientRect();
    const mx = (r.width * (Z.s - 1)) / 2, my = (r.height * (Z.s - 1)) / 2;   // la foto no sale de la caja
    Z.x = Math.max(-mx, Math.min(mx, Z.x)); Z.y = Math.max(-my, Math.min(my, Z.y));
    img.style.transform = Z.s === 1 ? '' : `translate(${Z.x}px, ${Z.y}px) scale(${Z.s})`;
    caja.classList.toggle('ampliada', Z.s > 1);
  }
  function resetZoom() { Z.s = 1; Z.x = Z.y = 0; ptrs.clear(); gesto = null; aplicar(); }
  function zoomEn(s, cx, cy) {   // cx, cy: punto bajo el dedo, relativo al centro de la caja
    s = Math.max(1, Math.min(4, s)); const k = s / Z.s;
    Z.x = cx - (cx - Z.x) * k; Z.y = cy - (cy - Z.y) * k; Z.s = s; aplicar();
  }
  const centro = (e) => { const r = caja.getBoundingClientRect(); return [e.clientX - r.left - r.width / 2, e.clientY - r.top - r.height / 2]; };
  caja.addEventListener('pointerdown', (e) => {
    caja.setPointerCapture(e.pointerId); ptrs.set(e.pointerId, e);
    if (ptrs.size === 2) { const [a, b] = [...ptrs.values()]; gesto = { d0: Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY), s0: Z.s }; }
    else gesto = { x0: e.clientX, y0: e.clientY, zx: Z.x, zy: Z.y };
  });
  caja.addEventListener('pointermove', (e) => {
    if (!ptrs.has(e.pointerId)) return; ptrs.set(e.pointerId, e);
    if (ptrs.size === 2 && gesto && gesto.d0) {
      const [a, b] = [...ptrs.values()]; const r = caja.getBoundingClientRect();
      zoomEn(gesto.s0 * Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY) / gesto.d0,
        (a.clientX + b.clientX) / 2 - r.left - r.width / 2, (a.clientY + b.clientY) / 2 - r.top - r.height / 2);
    } else if (ptrs.size === 1 && gesto && Z.s > 1) {   // arrastrar la foto ampliada
      Z.x = gesto.zx + e.clientX - gesto.x0; Z.y = gesto.zy + e.clientY - gesto.y0; aplicar();
    }
  });
  const soltar = (e) => {
    if (!ptrs.has(e.pointerId)) return;
    const g = gesto, uno = ptrs.size === 1; ptrs.delete(e.pointerId); gesto = null;
    if (!uno || !g || g.x0 === undefined) return;
    const dx = e.clientX - g.x0, dy = e.clientY - g.y0;
    if (Z.s === 1 && e.type === 'pointerup' && Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) mover(dx < 0 ? 1 : -1);   // deslizar
  };
  caja.addEventListener('pointerup', soltar); caja.addEventListener('pointercancel', soltar);
  caja.addEventListener('dblclick', (e) => { const [cx, cy] = centro(e); if (Z.s > 1) resetZoom(); else zoomEn(2.5, cx, cy); });
  caja.addEventListener('wheel', (e) => { e.preventDefault(); const [cx, cy] = centro(e); zoomEn(Z.s * (e.deltaY < 0 ? 1.2 : 1 / 1.2), cx, cy); }, { passive: false });

  // ---------- álbum / mesa ----------
  function modo(m) {
    $('meses').classList.toggle('mesa', m === 'mesa');
    document.querySelectorAll('[data-modo]').forEach((b) => b.setAttribute('aria-pressed', b.dataset.modo === m));
    try { localStorage.setItem('fotos-modo', m); } catch (_) { /* sin almacenamiento: no pasa nada */ }
  }
  document.querySelectorAll('[data-modo]').forEach((b) => b.addEventListener('click', () => modo(b.dataset.modo)));
  try { modo(localStorage.getItem('fotos-modo') === 'mesa' ? 'mesa' : 'album'); } catch (_) { modo('album'); }

  // ---------- sugerencias de nombres ----------
  const lista = $('sugerencias'), campo = $('q');
  let sugs = [], activa = -1;
  function sugerir() {
    const toks = norma(campo.value).split(/\s+/).filter(Boolean);
    const cuenta = {};
    fotos.forEach((f) => f.personas.forEach((n) => { cuenta[n] = (cuenta[n] || 0) + 1; }));
    sugs = toks.length ? Object.keys(cuenta).filter((n) => coincide(toks, [norma(n)]) && norma(n) !== toks.join(' '))
      .sort((a, b) => cuenta[b] - cuenta[a] || a.localeCompare(b)).slice(0, 6).map((n) => [n, cuenta[n]]) : [];
    activa = -1;
    lista.innerHTML = sugs.map(([n, c], i) => `<li role="option" id="sug${i}" data-i="${i}" aria-selected="false">${esc(n)}<small class="num">${pl(c, 'foto', 'fotos')}</small></li>`).join('');
    cerrarSug(!sugs.length);
    if (sugs.length) { lista.hidden = false; campo.setAttribute('aria-expanded', 'true'); }
  }
  function cerrarSug(vacia = true) {
    lista.hidden = true; campo.setAttribute('aria-expanded', 'false'); campo.removeAttribute('aria-activedescendant');
    if (vacia) { sugs = []; activa = -1; }
  }
  function elegir(i) {
    q = campo.value = sugs[i][0]; evento = null; cerrarSug(); pintar(); $('galeria').scrollTop = 0;
  }
  function marcar(i) {
    activa = i; lista.querySelectorAll('li').forEach((li, k) => li.setAttribute('aria-selected', k === i));
    if (i >= 0) campo.setAttribute('aria-activedescendant', `sug${i}`); else campo.removeAttribute('aria-activedescendant');
  }
  campo.addEventListener('input', sugerir);
  campo.addEventListener('focus', () => { if (campo.value) sugerir(); });
  campo.addEventListener('blur', () => cerrarSug());
  campo.addEventListener('keydown', (e) => {
    if (lista.hidden) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); marcar((activa + 1) % sugs.length); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); marcar((activa - 1 + sugs.length) % sugs.length); }
    else if (e.key === 'Enter' && activa >= 0) { e.preventDefault(); elegir(activa); }
    else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); cerrarSug(); }
  });
  lista.addEventListener('pointerdown', (e) => { e.preventDefault(); const li = e.target.closest('li'); if (li) elegir(Number(li.dataset.i)); });   // preventDefault: el campo no pierde el foco antes

  // ---------- eventos ----------
  $('meses').addEventListener('click', (e) => {
    const t = e.target.closest('.tarjeta'); if (t) abrir(Number(t.dataset.i), t);
  });
  $('anios').addEventListener('click', (e) => {
    const b = e.target.closest('.anio'); if (!b) return;
    anio = b.dataset.anio; evento = null; q = $('q').value = ''; pintar(); $('galeria').scrollTop = 0;
  });
  $('q').addEventListener('input', (e) => { q = e.target.value; evento = null; pintar(); $('galeria').scrollTop = 0; });
  $('vEv').addEventListener('click', () => {
    evento = visibles[actual].evKey; q = $('q').value = ''; origen = null; cerrar(); pintar(); $('galeria').scrollTop = 0;
    $('quitar').focus({ preventScroll: true });
  });
  $('quitar').addEventListener('click', () => {
    evento = null; pintar(); const a = $('anios').querySelector('[aria-pressed="true"]'); if (a) a.focus({ preventScroll: true });
  });
  $('vCerrar').addEventListener('click', cerrar);
  $('visor').addEventListener('click', (e) => { if (e.target === $('visor') || e.target === $('visorCard')) cerrar(); });
  $('vAnt').addEventListener('click', () => mover(-1));
  $('vSig').addEventListener('click', () => mover(1));
  $('vPersonas').addEventListener('click', (e) => {   // tocar un nombre = buscarlo
    const b = e.target.closest('.persona'); if (!b) return;
    q = $('q').value = b.dataset.nombre; evento = null; origen = null; cerrar(); pintar(); $('galeria').scrollTop = 0;
    $('q').focus({ preventScroll: true });
  });
  document.addEventListener('keydown', (e) => {
    if ($('visor').hidden) return;
    if (e.key === 'Escape') { e.preventDefault(); cerrar(); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); mover(-1); }
    else if (e.key === 'ArrowRight') { e.preventDefault(); mover(1); }
    else if (e.key === '+' || e.key === '=') { e.preventDefault(); zoomEn(Z.s * 1.4, 0, 0); }
    else if (e.key === '-') { e.preventDefault(); zoomEn(Z.s / 1.4, 0, 0); }
    else if (e.key === '0') { e.preventDefault(); resetZoom(); }
    else if (e.key === 'Tab') {   // el foco no se escapa del visor
      const t = [...$('visor').querySelectorAll('button:not(:disabled), a[href]')];
      const i = t.indexOf(document.activeElement);
      if (e.shiftKey && i <= 0) { e.preventDefault(); t[t.length - 1].focus(); }
      else if (!e.shiftKey && i === t.length - 1) { e.preventDefault(); t[0].focus(); }
    }
  });

  // ---------- arranque ----------
  $('pegFoto').innerHTML = window.IDENTIDAD ? window.IDENTIDAD.pegatina('foto', 'grande') : '';
  $('vPeg').innerHTML = window.IDENTIDAD ? window.IDENTIDAD.pegatina('evento') : '';
  const aviso = (t) => { $('count').textContent = ''; $('total').textContent = '0'; $('resultado').textContent = ''; $('vacio').hidden = false; $('vacio').textContent = t; };
  fetch('data/archivo.json').then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); }).then((d) => {
    (d.personas || []).forEach((p) => { if (/^[A-Za-z0-9._]{1,30}$/.test(p.instagram || '')) instagram[p.nombre] = p.instagram; });
    fotos = reunir(d);
    if (!fotos.length) return aviso('Todavía no hay fotos preparadas para la web. Ejecuta «archivo.py fotos-web» y vuelve a exportar.');
    anio = fotos[0].fecha.slice(0, 4);
    $('total').textContent = fotos.length;
    $('count').textContent = `${pl(fotos.length, 'foto', 'fotos')} · ${pl(new Set(fotos.flatMap((f) => f.personas)).size, 'persona', 'personas')}`;
    pintar();
  }).catch(() => aviso('No se pudo cargar data/archivo.json. Sirve la carpeta web con «python -m http.server» y exporta los datos.'));
})();
