/* Buscador global (Ctrl/⌘+K, «/», lupa de la barra). Ficha: docs/features/buscador.md
   Lo carga pasaporte.js en todas las páginas. La lógica (norm, indice, buscar) es pura y la prueba tests/test_buscador.js. */
(() => {
  'use strict';

  // ---------- lógica pura ----------
  // [tipo, etiqueta del grupo, pegatina]
  const GRUPOS = [
    ['evento', 'Eventos', 'evento'], ['viaje', 'Viajes', 'viaje'], ['lugar', 'Ciudades y países', 'ciudad'],
    ['persona', 'Personas', 'persona'], ['certificado', 'Certificados', 'certificado'], ['premio', 'Premios', 'premio'],
    ['pin', 'Pines', 'pin'], ['sello', 'Sellos LEGO', 'sello'], ['charla', 'Charlas', 'charla'],
  ];
  const NIVELES_PREMIO = ['primer premio', 'podio', 'finalista', 'mención'];   // igual que pasaporte.js
  const MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];

  // sin acentos ni mayúsculas, solo letras y cifras separadas por un espacio
  const norm = (s) => String(s ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();

  const fecha = (f) => {
    const [a, m, d] = String(f || '').split('-');
    if (!a) return '';
    return [d && +d, m && MESES[+m - 1], a].filter(Boolean).join(' ');
  };

  // Convierte archivo.json en una lista plana de resultados posibles.
  function indice(A) {
    const out = [];
    const nuevo = (tipo, titulo, sub, href, extra = '', f = '', peg = '') => {
      if (!String(titulo || '').trim()) return;
      out.push({ tipo, titulo, sub: sub.filter(Boolean).join(' · '), href, peg, f: f || '', t: norm(titulo), r: norm(`${extra} ${sub.join(' ')} ${f}`) });
    };
    const vistos = new Set();
    const objeto = (o, e, v) => {
      const clave = o.uid || `${o.tipo}-${o.id}`;
      if (vistos.has(clave)) return;
      vistos.add(clave);
      const tit = o.titulo || o.sitio;
      const hacia = e ? `evento.html?e=${encodeURIComponent(e.slug)}` : null;
      const donde = [fecha(o.fecha), e && e.ciudad];
      if (o.tipo === 'pin') nuevo('pin', tit, [fecha(o.fecha), v && v.nombre], v ? `mapa.html?viaje=${v.id}` : 'pines.html', o.sitio, o.fecha);
      else if (o.tipo === 'sello') nuevo('sello', tit, [fecha(o.fecha), o.sitio !== tit && o.sitio], 'pasaporte-lego.html', o.sitio, o.fecha);
      else if (o.tipo === 'certificado' || o.tipo === 'otro') {
        const gana = NIVELES_PREMIO.includes(o.nivel);
        nuevo(gana ? 'premio' : 'certificado', tit, [o.nivel || o.premio, ...donde], hacia || (gana ? 'premios.html' : 'certificados.html'), `${o.organizador} ${o.premio} ${o.nivel}`, o.fecha);
      }
    };
    for (const e of A.eventos || []) {
      const href = `evento.html?e=${encodeURIComponent(e.slug)}`;
      nuevo('evento', e.nombre, [fecha(e.fecha), e.ciudad, e.lugar], href, `${e.organizador} ${e.pais} ${e.categoria}`, e.fecha, e.modalidad === 'virtual' ? 'virtual' : 'evento');
      (e.objetos || []).forEach((o) => objeto(o, e));
      (e.charlas || []).forEach((c) => nuevo('charla', c.titulo, [fecha(c.fecha), e.nombre], href, c.tipo, c.fecha));
    }
    for (const v of A.viajes || []) {
      const ciudades = [...new Set((v.visitas || []).map((x) => x.ciudad))];
      const paises = [...new Set((v.visitas || []).map((x) => x.pais))];
      nuevo('viaje', v.nombre, [fecha(v.inicio), ciudades.slice(0, 3).join(', ')], `mapa.html?viaje=${v.id}`, `${ciudades.join(' ')} ${paises.join(' ')}`, v.inicio);
      (v.objetos || []).forEach((o) => objeto(o, null, v));
    }
    (A.objetos_sueltos || []).forEach((o) => objeto(o, null, null));
    const T = A.totales || {};
    for (const c of T.ciudades || []) nuevo('lugar', c.nombre, [c.pais, c.visitas > 1 && `${c.visitas} visitas`], 'mapa.html', `${c.continente}`, c.primera_visita, 'ciudad');
    for (const p of T.paises || []) nuevo('lugar', p.pais, ['País', p.continente], 'mapa.html', '', '', 'pais');
    for (const p of A.personas || []) {
      const e = (A.eventos || []).find((x) => (x.fotos || []).some((f) => (f.personas || []).includes(p.nombre)));
      nuevo('persona', p.nombre, [p.fotos && `${p.fotos} ${p.fotos === 1 ? 'foto' : 'fotos'}`, e && e.nombre], e ? `evento.html?e=${encodeURIComponent(e.slug)}` : 'fotos.html', p.instagram);
    }
    return out;
  }

  // 0 = no coincide. Todas las palabras de la búsqueda deben aparecer (al principio de una palabra).
  function puntuar(it, tokens, q) {
    let s = 0;
    const tw = it.t.split(' '), rw = it.r.split(' ');
    for (const k of tokens) {
      if (tw.some((w) => w.startsWith(k))) s += 3;
      else if (it.t.includes(k)) s += 2;
      else if (rw.some((w) => w.startsWith(k))) s += 1;
      else return 0;
    }
    return s + (it.t.startsWith(q) ? 2 : 0);
  }

  // -> [{ tipo, etiqueta, peg, items }] en el orden de GRUPOS, hasta `max` por grupo
  function buscar(items, texto, max = 8) {
    const q = norm(texto);
    if (!q) return [];
    const tokens = q.split(' ');
    const punt = items.map((it) => [it, puntuar(it, tokens, q)]).filter(([, s]) => s > 0);
    return GRUPOS.map(([tipo, etiqueta, peg]) => ({
      tipo, etiqueta, peg,
      items: punt.filter(([it]) => it.tipo === tipo)
        .sort((a, b) => b[1] - a[1] || b[0].f.localeCompare(a[0].f)).slice(0, max).map(([it]) => it),
    })).filter((g) => g.items.length);
  }

  if (typeof module !== 'undefined') module.exports = { norm, indice, buscar, fecha };
  if (typeof document === 'undefined') return;

  // ---------- interfaz ----------
  const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const P = (t) => (window.IDENTIDAD ? IDENTIDAD.pegatina(t) : '');
  const CLAVE = 'buscador.recientes';
  const LUPA = '<svg class="icono" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/></svg>';
  document.head.appendChild(Object.assign(document.createElement('link'), { rel: 'stylesheet', href: 'buscador.css' }));
  let items = null, cargando = null, opener = null, activo = -1, opciones = [];

  const recientes = () => { try { return JSON.parse(localStorage.getItem(CLAVE)) || []; } catch (e) { return []; } };
  const guardar = (q) => {
    q = q.trim();
    if (!q) return;
    try { localStorage.setItem(CLAVE, JSON.stringify([q, ...recientes().filter((x) => x !== q)].slice(0, 5))); } catch (e) { /* sin almacenamiento: no pasa nada */ }
  };

  const dlg = document.createElement('dialog');
  dlg.className = 'buscador';
  dlg.setAttribute('aria-label', 'Buscar en el archivo');
  dlg.innerHTML = `
    <div class="buscador-caja glass">
      <div class="buscador-campo">${LUPA}
        <input type="text" id="buscadorQ" role="combobox" aria-expanded="true" aria-controls="buscadorLista" aria-autocomplete="list" aria-label="Buscar en el archivo" placeholder="Evento, ciudad, persona, pin…" autocomplete="off" autocapitalize="off" spellcheck="false" enterkeyhint="go">
        <button type="button" class="btn ghost redondo buscador-cerrar" aria-label="Cerrar el buscador"><svg class="icono" aria-hidden="true"><use href="img/iconos.svg#cerrar"/></svg></button>
      </div>
      <ul id="buscadorLista" role="listbox" aria-label="Resultados"></ul>
      <p class="buscador-estado" role="status" aria-live="polite"></p>
      <p class="buscador-pie" aria-hidden="true"><kbd>↑</kbd><kbd>↓</kbd> moverse · <kbd>Enter</kbd> abrir · <kbd>Esc</kbd> cerrar</p>
    </div>`;
  document.body.appendChild(dlg);
  const q = dlg.querySelector('#buscadorQ'), lista = dlg.querySelector('#buscadorLista'), estado = dlg.querySelector('.buscador-estado');

  const marcar = (i) => {
    activo = opciones.length ? (i + opciones.length) % opciones.length : -1;
    opciones.forEach((o, n) => o.setAttribute('aria-selected', n === activo ? 'true' : 'false'));
    if (activo >= 0) { q.setAttribute('aria-activedescendant', opciones[activo].id); opciones[activo].scrollIntoView({ block: 'nearest' }); }
    else q.removeAttribute('aria-activedescendant');
  };

  const pintar = () => {
    const txt = q.value;
    let html = '', n = 0;
    if (!items) { lista.innerHTML = ''; estado.textContent = cargando ? 'Cargando el archivo…' : 'No se pudo cargar el archivo.'; opciones = []; return; }
    if (!norm(txt)) {
      const r = recientes();
      estado.textContent = r.length ? 'Búsquedas recientes' : 'Escribe para buscar eventos, viajes, ciudades, personas, certificados, premios, pines, sellos y charlas.';
      html = r.map((x) => `<li role="option" id="bo${n++}" class="b-op b-reciente" data-q="${esc(x)}"><span class="b-txt"><b>${esc(x)}</b></span></li>`).join('');
    } else {
      const grupos = buscar(items, txt);
      estado.textContent = grupos.length ? '' : `Nada con «${txt.trim()}». Prueba con otra palabra: un evento, una ciudad, una persona o un año.`;
      html = grupos.map((g) => `<li role="presentation" class="b-grupo"><span>${esc(g.etiqueta)}</span></li>${g.items.map((it) =>
        `<li role="option" id="bo${n++}" class="b-op" data-href="${esc(it.href)}"><span class="b-peg">${P(it.peg || g.peg)}</span><span class="b-txt"><b>${esc(it.titulo)}</b><small>${esc(it.sub)}</small></span></li>`).join('')}`).join('');
    }
    lista.innerHTML = html;
    opciones = [...lista.querySelectorAll('[role=option]')];
    marcar(opciones.length ? 0 : -1);
  };

  const cargar = () => {
    if (!cargando) {
      cargando = fetch('data/archivo.json').then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then((A) => { items = indice(A); }).catch(() => { cargando = null; });
    }
    return cargando;
  };

  const ir = (o) => {
    if (!o) return;
    if (o.dataset.q !== undefined) { q.value = o.dataset.q; pintar(); q.focus(); return; }
    guardar(q.value);
    location.href = o.dataset.href;
  };

  const abrir = (desde) => {
    if (dlg.open) return;
    opener = desde || (document.activeElement !== document.body && document.activeElement) || boton;
    q.value = '';
    dlg.showModal();
    q.focus();
    pintar();
    cargar().then(pintar);
  };

  q.addEventListener('input', pintar);
  q.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); marcar(activo + 1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); marcar(activo - 1); }
    else if (e.key === 'Enter') { e.preventDefault(); ir(opciones[activo]); }
  });
  lista.addEventListener('click', (e) => ir(e.target.closest('[role=option]')));
  lista.addEventListener('mousemove', (e) => { const o = e.target.closest('[role=option]'); if (o && opciones.indexOf(o) !== activo) marcar(opciones.indexOf(o)); });
  dlg.querySelector('.buscador-cerrar').addEventListener('click', () => dlg.close());
  dlg.addEventListener('click', (e) => { if (e.target === dlg) dlg.close(); });
  dlg.addEventListener('close', () => { (opener && opener.isConnected ? opener : boton || document.body).focus(); });

  // atajos: Ctrl/⌘+K en cualquier sitio; «/» solo si no se está escribiendo
  document.addEventListener('keydown', (e) => {
    const escribiendo = /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName) || e.target.isContentEditable;
    if (((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') || (e.key === '/' && !escribiendo && !e.ctrlKey && !e.metaKey && !e.altKey)) {
      e.preventDefault();
      dlg.open ? q.select() : abrir();
    }
  });

  // botón de lupa en la barra
  const bar = document.querySelector('header.bar');
  const boton = document.createElement('button');
  boton.type = 'button';
  boton.className = 'lupa-btn';
  boton.setAttribute('aria-label', 'Buscar en el archivo (Ctrl+K)');
  boton.setAttribute('aria-haspopup', 'dialog');
  boton.innerHTML = LUPA;
  boton.addEventListener('click', () => abrir(boton));
  if (bar) bar.appendChild(boton);

  // y en el índice del pasaporte (móvil: se llega desde las pestañas de abajo)
  const cab = document.querySelector('dialog.pasaporte .pp-cabeza');
  if (cab) {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'btn herr pp-buscar';
    b.innerHTML = `${LUPA}<span>Buscar</span>`;
    b.addEventListener('click', () => { const d = b.closest('dialog'); d.close(); abrir(boton); });
    cab.insertBefore(b, cab.querySelector('.pp-cerrar'));
  }
})();
