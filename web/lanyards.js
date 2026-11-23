/* Lanyards en línea de tiempo · ficha: docs/features/lanyards.md */
(() => {
  'use strict';
  const { pegatina } = window.IDENTIDAD;
  const $ = (s) => document.querySelector(s);
  // Destinos de los botones de la ficha. null = el botón no se muestra (aún no hay página de eventos).
  const DESTINO = {
    evento: null,
    mapa: (slug) => `mapa.html#evento=${encodeURIComponent(slug)}`,
  };
  const PULSACION_LARGA = 500;   // ms, móvil

  const norm = (s) => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  const num = (v, d) => (v === '' || v == null || isNaN(+v)) ? d : +v;
  const fecha = (f, largo) => {
    const [y, m, d] = String(f || '').split('-').map(Number);
    if (!y) return '';
    const opts = largo
      ? (d ? { day: 'numeric', month: 'long', year: 'numeric' } : { month: 'long', year: 'numeric' })
      : { month: 'short', year: 'numeric' };
    return new Intl.DateTimeFormat('es', { ...opts, timeZone: 'UTC' }).format(Date.UTC(y, (m || 1) - 1, d || 1)).replace('.', '');
  };

  // Crea un nodo sin tocar innerHTML: los textos vienen de ficheros de datos
  const h = (tag, props = {}, ...hijos) => {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(props)) {
      if (v == null || v === false) continue;
      if (k === 'class') el.className = v; else if (k === 'text') el.textContent = v;
      else el.setAttribute(k, v === true ? '' : v);
    }
    el.append(...hijos.flat().filter(Boolean));
    return el;
  };

  // ------------------------------------------------------------------ datos
  function normalizar(r) {
    return {
      id: r.id, evento: r.evento || 'Sin título', fecha: r.fecha || '', ciudad: r.ciudad || '', lugar: r.lugar || '',
      rol: r.rol || '', front: r.front_web || '', back: r.back_web || '',
      ratio: num(r.ancho_mm, 85.6) / num(r.alto_mm, 54),
    };
  }

  async function cargar(url) {
    try { const r = await fetch(url, { cache: 'no-store' }); return r.ok ? await r.json() : null; } catch { return null; }
  }

  // Une cada lanyard con su evento: por uid del objeto y, si no, mismo mes y nombre contenido.
  function evento(l, A) {
    const evs = (A && A.eventos) || [];
    const porUid = evs.find((e) => (e.objetos || []).some((o) => o.uid === l.id));
    if (porUid) return porUid;
    const nom = norm(l.evento), mes = l.fecha.slice(0, 7);
    return evs.filter((e) => e.nombre && String(e.fecha || '').slice(0, 7) === mes && nom.includes(norm(e.nombre)))
      .sort((a, b) => b.nombre.length - a.nombre.length)[0] || null;
  }

  function enriquecer(l, A) {
    const e = evento(l, A);
    const premio = e && (e.objetos || []).map((o) => o.premio).find(Boolean);
    const sitio = [l.lugar || (e && e.lugar), l.ciudad || (e && e.ciudad), e && e.pais].filter(Boolean);
    return { ...l, slug: e ? e.slug : '', premio: premio || l.rol, gana: !!premio || /premio|prize|ganad|primer|1st|finalist/i.test(l.rol), lugarTxt: [...new Set(sitio)].join(' · ') };
  }

  // ------------------------------------------------------------------ tarjetas
  const S = { items: [], abierta: null, desde: null };

  const cara = (src, clase, etiqueta, nombre) => src
    ? h('span', { class: `cara ${clase}` }, h('img', { src, alt: '', draggable: 'false', decoding: 'async' }))
    : h('span', { class: `cara ${clase} vacia` }, h('span', { class: 'etiqueta', text: etiqueta }), clase === 'anverso' ? h('b', { text: nombre }) : null);

  // pegatina fija de iconos.js (no viene de datos)
  const medalla = () => { const m = h('span', { class: 'medalla', title: 'Premio' }); m.innerHTML = pegatina('premio'); return m; };

  function colgante(l, i) {
    const tarjeta = h('button', { type: 'button', class: 'tarjeta', 'aria-pressed': 'false', 'data-i': i,
      'aria-label': `${l.evento}, ${fecha(l.fecha, true)}. Enter gira la tarjeta, F abre la ficha.`, style: `--ratio:${l.ratio}` },
      h('span', { class: 'giro' }, cara(l.front, 'anverso', 'Sin anverso', l.evento), cara(l.back, 'reverso', 'Sin reverso')));
    const fichaBtn = h('button', { type: 'button', class: 'btn ghost ver-ficha', 'aria-label': `Abrir la ficha: ${l.evento}`, text: 'Ficha' });
    const el = h('div', { class: 'colgante', 'data-i': i }, h('span', { class: 'cuerda' }), tarjeta,
      h('span', { class: 'pie' }, h('span', { class: 'mes', text: fecha(l.fecha) }), l.gana ? medalla() : null, h('span', { class: 'nombre', text: l.evento })), fichaBtn);

    tarjeta.addEventListener('dblclick', () => abrir(i, tarjeta));
    fichaBtn.addEventListener('click', () => abrir(i, fichaBtn));
    // toque: gira; mantener pulsado abre la ficha
    let t = 0, largo = false, x0 = 0, y0 = 0;
    const parar = () => clearTimeout(t);
    tarjeta.addEventListener('pointerdown', (e) => {
      if (e.pointerType === 'mouse') return;
      largo = false; x0 = e.clientX; y0 = e.clientY;
      t = setTimeout(() => { largo = true; abrir(i, tarjeta); }, PULSACION_LARGA);
    });
    tarjeta.addEventListener('pointermove', (e) => { if (Math.hypot(e.clientX - x0, e.clientY - y0) > 10) parar(); });
    ['pointerup', 'pointercancel', 'pointerleave'].forEach((ev) => tarjeta.addEventListener(ev, parar));
    tarjeta.addEventListener('contextmenu', (e) => { if (largo) e.preventDefault(); });
    tarjeta.addEventListener('click', () => {
      if (largo) { largo = false; return; }
      tarjeta.setAttribute('aria-pressed', String(tarjeta.getAttribute('aria-pressed') !== 'true'));
    });
    return el;
  }

  function pintar() {
    const pista = $('#pista');
    pista.replaceChildren();
    let grupo = null, anio = '';
    S.items.forEach((l, i) => {
      const y = l.fecha.slice(0, 4) || '—';
      if (y !== anio) {
        anio = y;
        const tarjetas = h('div', { class: 'tarjetas' });
        grupo = tarjetas;
        pista.append(h('section', { class: 'anio', 'aria-label': y }, h('h3', { class: 'anio-t num', text: y }), tarjetas));
      }
      grupo.append(colgante(l, i));
    });
    $('#count').textContent = `${S.items.length} lanyard${S.items.length === 1 ? '' : 's'}`;
  }

  // ------------------------------------------------------------------ ficha
  const ficha = $('#ficha');
  function abrir(i, desde) {
    const l = S.items[i];
    S.abierta = i; S.desde = desde || S.desde;
    document.querySelectorAll('.colgante').forEach((c) => c.classList.toggle('sel', +c.dataset.i === i));
    $('#fCaras').replaceChildren(
      ...[[l.front, 'Anverso'], [l.back, 'Reverso']].map(([src, nom]) => src
        ? h('img', { class: 'lamina', src, alt: `${nom} de ${l.evento}`, style: `--ratio:${l.ratio}` })
        : h('span', { class: 'lamina vacia', style: `--ratio:${l.ratio}`, text: `Sin ${nom.toLowerCase()}` })));
    $('#fFecha').textContent = fecha(l.fecha, true);
    $('#fTitulo').textContent = l.evento;
    $('#fLugar').textContent = l.lugarTxt; $('#fLugar').hidden = !l.lugarTxt;
    const p = $('#fPremio');
    p.hidden = !l.premio; $('#fPremioTxt').textContent = l.premio;
    const acc = [];
    if (DESTINO.evento && l.slug) acc.push(h('a', { class: 'btn', href: DESTINO.evento(l.slug), text: 'Ver el evento' }));
    if (l.slug) acc.push(h('a', { class: acc.length ? 'btn ghost' : 'btn', href: DESTINO.mapa(l.slug), text: 'En el mapa' }));
    $('#fAcciones').replaceChildren(...acc); $('#fAcciones').hidden = !acc.length;
    ficha.hidden = false;
    $('.linea').classList.add('con-ficha');   // el carril deja sitio al panel
    (desde && desde.closest('.colgante') || document.querySelector(`.colgante[data-i="${i}"]`)).scrollIntoView({ inline: 'nearest', block: 'nearest' });
    ficha.focus({ preventScroll: true });   // el foco va al contenedor, no a un botón que Enter pulsaría
  }

  function cerrar() {
    if (ficha.hidden) return;
    ficha.hidden = true;
    $('.linea').classList.remove('con-ficha');
    document.querySelectorAll('.colgante.sel').forEach((c) => c.classList.remove('sel'));
    S.abierta = null;
    if (S.desde && S.desde.isConnected) S.desde.focus();
  }

  // ------------------------------------------------------------------ entrada: rueda, arrastre, teclado
  function entrada() {
    const carril = $('#carril');
    carril.addEventListener('wheel', (e) => {   // la rueda vertical mueve el carril en horizontal
      if (Math.abs(e.deltaY) <= Math.abs(e.deltaX) || carril.scrollWidth <= carril.clientWidth) return;
      e.preventDefault();
      carril.scrollLeft += e.deltaY;
    }, { passive: false });

    let x0 = 0, s0 = 0, abajo = false, arrastro = false;
    carril.addEventListener('pointerdown', (e) => {
      if (e.pointerType !== 'mouse' || e.button !== 0) return;
      abajo = true; arrastro = false; x0 = e.clientX; s0 = carril.scrollLeft;
    });
    window.addEventListener('pointermove', (e) => {
      if (!abajo) return;
      if (Math.abs(e.clientX - x0) > 5) { arrastro = true; carril.classList.add('arrastrando'); }
      if (arrastro) carril.scrollLeft = s0 - (e.clientX - x0);
    });
    window.addEventListener('pointerup', () => { abajo = false; carril.classList.remove('arrastrando'); });
    carril.addEventListener('click', (e) => { if (arrastro) { e.stopPropagation(); e.preventDefault(); arrastro = false; } }, true);

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') { const d = $('.teclas'); if (d.open) d.open = false; return cerrar(); }
      const t = e.target.closest && e.target.closest('.tarjeta');
      if (!t || e.altKey || e.ctrlKey || e.metaKey) return;
      const todas = [...document.querySelectorAll('.tarjeta')], k = todas.indexOf(t);
      const ir = { ArrowRight: k + 1, ArrowLeft: k - 1, Home: 0, End: todas.length - 1 }[e.key];
      if (ir != null) { e.preventDefault(); todas[Math.max(0, Math.min(todas.length - 1, ir))].focus(); }
      else if (e.key === 'f' || e.key === 'F') { e.preventDefault(); abrir(+t.dataset.i, t); }
    });
    $('#fCerrar').addEventListener('click', cerrar);
  }

  // ------------------------------------------------------------------ arranque
  async function main() {
    $('#cabPeg').innerHTML = pegatina('lanyard');   // pegatina: cadena fija de iconos.js, no viene de datos
    $('#fPeg').innerHTML = pegatina('lanyard'); $('#fPremioPeg').innerHTML = pegatina('premio');
    const [raw, A] = await Promise.all([cargar('data/archive.json'), cargar('data/archivo.json')]);
    if (!raw) { const n = $('#notice'); n.hidden = false; n.textContent = 'No encuentro data/archive.json. ¿Has ejecutado sync.py?'; $('#count').textContent = ''; return; }
    S.items = raw.map(normalizar).sort((a, b) => a.fecha.localeCompare(b.fecha) || a.id.localeCompare(b.id)).map((l) => enriquecer(l, A));
    if (!S.items.length) { const n = $('#notice'); n.hidden = false; n.textContent = 'Todavía no hay lanyards en data/archive.json.'; $('#count').textContent = '0 lanyards'; return; }
    pintar(); entrada();
  }
  main();
})();
