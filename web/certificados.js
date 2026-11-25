/* Página de certificados · ficha: docs/features/certificados.md */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
  const GIROS = [-1, 0.8, -0.6, 1.2, -1.2, 0.6, -0.8, 1, -0.4, 0.9];
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const norm = (s) => String(s || '').normalize('NFD').replace(/\p{M}/g, '').toLowerCase();
  const mayus = (s) => s.charAt(0).toUpperCase() + s.slice(1);
  const fechaLarga = (f) => {
    const [a, m, d] = f.split('-');
    return m ? (d ? `${+d} de ` : '') + `${MESES[+m - 1]} de ${a}` : a;
  };
  const VISTAS = [['todos', 'Todos', () => true], ['premio', 'Con premio', (c) => c.conPremio], ['pendiente', 'Por escanear', (c) => c.pendiente]];

  const S = { todos: [], q: '', vista: 'todos', lista: [], abierto: -1, vuelta: null };

  function aviso(txt) { const n = $('notice'); n.textContent = txt; n.hidden = false; $('count').textContent = ''; }

  function preparar(A) {
    const out = [];
    const add = (o, ev) => {
      const evento = ev ? ev.nombre : '';
      if (o.tipo !== 'certificado') return;
      const img = o.front_web || '';
      out.push({
        slug: ev ? ev.slug : '', titulo: o.titulo || 'Sin título', org: o.organizador || '', fecha: o.fecha || '', premio: o.premio || '',
        nivel: o.nivel ? mayus(o.nivel) : '', num: o.num_archivo || '', img, pendiente: !img, conPremio: !!o.nivel,
        buscable: norm([o.titulo, o.organizador, o.num_archivo, evento].join(' ')),
      });
    };
    (A.eventos || []).forEach((e) => (e.objetos || []).forEach((o) => add(o, e)));
    (A.objetos_sueltos || []).forEach((o) => add(o, null));
    // más reciente primero; a igual fecha, por nº de archivo descendente
    out.sort((a, b) => b.fecha.localeCompare(a.fecha) || b.num.localeCompare(a.num));
    out.forEach((c, i) => { c.giro = GIROS[i % GIROS.length]; });
    return out;
  }

  function contadores() {
    const t = S.todos;
    const dato = (n, txt) => `<div><dd class="num">${n}</dd><dt>${txt}</dt></div>`;
    $('contadores').innerHTML = dato(t.length, 'certificados') + dato(t.filter((c) => c.conPremio).length, 'con premio') + dato(t.filter((c) => c.pendiente).length, 'por escanear');
    $('count').textContent = `${t.length} certificados`;
    $('vistas').innerHTML = VISTAS.map(([id, nombre, f]) =>
      `<button class="chip" type="button" data-vista="${id}" aria-pressed="${id === S.vista}">${nombre} <small class="num">${t.filter(f).length}</small></button>`).join('');
  }

  function hoja(c, i) {
    const medalla = c.conPremio ? IDENTIDAD.pegatina('premio', 'cert-medalla') : '';
    const papel = `<span class="hoja-papel${c.pendiente ? ' pend' : ''}">${c.pendiente ? '<span>Por escanear</span>' : `<img src="${esc(c.img)}" alt="" loading="lazy" decoding="async">`}${medalla}</span>`;
    const sub = [c.org, c.nivel].filter(Boolean).join(' · ');
    return `<button type="button" class="hoja" data-i="${i}" style="--giro:${c.giro}deg" aria-label="${esc(c.titulo)}${c.pendiente ? ' (por escanear)' : ''}">
      ${papel}
      <span class="hoja-txt"><span class="kicker">${c.num ? 'Nº ' + esc(c.num) + ' · ' : ''}${esc(c.fecha.slice(0, 4))}</span>
      <span class="hoja-t">${esc(c.titulo)}</span>${sub ? `<span class="sub">${esc(sub)}</span>` : ''}</span></button>`;
  }

  function pintar() {
    const f = VISTAS.find((v) => v[0] === S.vista)[2];
    const q = norm(S.q.trim());
    S.lista = S.todos.filter(f).filter((c) => !q || c.buscable.includes(q));
    let html = '', anio = '';
    S.lista.forEach((c, i) => {
      const a = c.fecha.slice(0, 4) || 'Sin fecha';
      if (a !== anio) { html += `${anio ? '</div></section>' : ''}<section class="anio"><h2 class="anio-t num">${esc(a)}</h2><div class="cuadricula">`; anio = a; }
      html += hoja(c, i);
    });
    $('rejilla').innerHTML = html + (anio ? '</div></section>' : '');
    $('vacio').hidden = S.lista.length > 0;
    $('resultado').textContent = S.lista.length === S.todos.length ? '' : `${S.lista.length} resultado${S.lista.length === 1 ? '' : 's'}`;
  }

  /* ---------- ficha ---------- */
  function ficha(i) {
    const c = S.lista[i];
    S.abierto = i;
    $('fHoja').innerHTML = c.pendiente
      ? '<div class="cfi-vacia"><b>Todavía sin escanear</b><span>El original está en el archivo físico</span></div>'
      : `<img src="${esc(c.img)}" alt="Certificado: ${esc(c.titulo)}">`;
    $('fHoja').classList.toggle('pend', c.pendiente);
    $('fFecha').textContent = c.fecha ? fechaLarga(c.fecha) : 'Sin fecha';
    $('fTitulo').textContent = c.titulo;
    $('fOrg').textContent = c.org || 'Organizador sin anotar';
    const p = $('fPremio');
    p.hidden = !c.conPremio;
    p.innerHTML = c.conPremio ? `${IDENTIDAD.pegatina('premio')}<span><b>${esc(c.nivel)}</b>${c.premio ? `<span class="sub">${esc(c.premio)}</span>` : ''}</span>` : '';
    $('fNum').textContent = c.num ? `Nº ${c.num} en el archivo` : 'Sin número de archivo';
    $('fEvt').hidden = !c.slug; if (c.slug) $('fEvt').href = `evento.html?e=${encodeURIComponent(c.slug)}`;
    $('fAnt').disabled = $('fSig').disabled = S.lista.length < 2;
  }
  function abrir(i, desde) {
    if (S.abierto < 0) S.vuelta = desde;
    ficha(i);
    $('ficha').hidden = false;
    $('fDatos').focus({ preventScroll: true });   // no un botón: Enter volvería a pulsarlo
  }
  function cerrar() {
    if (S.abierto < 0) return;
    $('ficha').hidden = true;
    const i = S.abierto; S.abierto = -1;
    (document.querySelector(`.hoja[data-i="${i}"]`) || S.vuelta)?.focus({ preventScroll: false });
  }
  const mover = (d) => { if (S.lista.length > 1) ficha((S.abierto + d + S.lista.length) % S.lista.length); };

  function eventos() {
    $('q').addEventListener('input', (e) => { S.q = e.target.value; pintar(); });
    $('vistas').addEventListener('click', (e) => {
      const b = e.target.closest('[data-vista]'); if (!b) return;
      S.vista = b.dataset.vista;
      document.querySelectorAll('#vistas .chip').forEach((x) => x.setAttribute('aria-pressed', x === b));
      pintar();
    });
    $('rejilla').addEventListener('click', (e) => { const h = e.target.closest('.hoja'); if (h) abrir(+h.dataset.i, h); });
    $('fCerrar').addEventListener('click', cerrar);
    $('ficha').querySelector('[data-cerrar]').addEventListener('click', cerrar);
    $('fAnt').addEventListener('click', () => mover(-1));
    $('fSig').addEventListener('click', () => mover(1));
    document.addEventListener('keydown', (e) => {
      if (S.abierto < 0) return;
      if (e.key === 'Escape') cerrar();
      else if (e.key === 'ArrowLeft') mover(-1);
      else if (e.key === 'ArrowRight') mover(1);
      else if (e.key === 'Tab') {   // el foco no sale de la ficha
        const f = [...$('ficha').querySelectorAll('button:not(:disabled), a[href]:not([hidden])')];
        const dentro = f.includes(document.activeElement);
        if (!dentro || (e.shiftKey ? document.activeElement === f[0] : document.activeElement === f[f.length - 1])) { e.preventDefault(); (e.shiftKey ? f[f.length - 1] : f[0]).focus(); }
      }
    });
  }

  async function iniciar() {
    try {
      const r = await fetch('data/archivo.json', { cache: 'no-store' });
      if (!r.ok) throw new Error(r.status);
      S.todos = preparar(await r.json());
    } catch {
      return aviso('No encuentro data/archivo.json. Genera el fichero con «archivo.py exportar web/data/archivo.json» y recarga (sirve la web con un servidor local).');
    }
    contadores(); pintar(); eventos();
  }
  iniciar();
})();
