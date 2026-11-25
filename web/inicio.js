/* Inicio «Tu año en cifras» (recorrido narrado). Ficha: docs/features/cifras-e-hitos.md */
(() => {
  'use strict';

  const MODULOS = [
    ['Pared de lanyards', 'lanyard', 'Colgados en 3D', 'pared.html'],
    ['Mapa', 'pais', 'Viajes y km', 'mapa.html'],
    ['Fotos', 'foto', 'Con personas', 'fotos.html'],
    ['Certificados', 'certificado', 'Todo el papel', 'certificados.html'],
    ['Premios', 'premio', 'Por nivel', 'premios.html'],
    ['Pines', 'pin', 'Colección', 'pines.html'],
    ['Intervenciones', 'charla', 'Charlas y vídeos', 'intervenciones.html'],
  ];
  const nf = (n, d = 0) => new Intl.NumberFormat('es-ES', { useGrouping: 'always', minimumFractionDigits: d, maximumFractionDigits: d }).format(n);
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const pl = (n, s, p) => `${nf(n)} ${n === 1 ? s : p}`;
  const yr = (f) => (f || '').slice(0, 4);
  const porFecha = (a, b) => (a.fecha < b.fecha ? -1 : a.fecha > b.fecha ? 1 : 0);

  // ------------------------------------------------------------------ datos (sin DOM: se prueba con node)
  // Las cifras (`anual`, `hitos`, `km_perspectiva`) las calcula el exportador; aquí solo se agrupan por mes.
  // Solo cuenta lo pasado: las fechas «AAAA» o «AAAA-MM» valen si no superan a `hoy` (AAAA-MM-DD).
  function calcular(A, hoy) {
    const pasado = (f) => !!f && f <= hoy;
    const V = (A.viajes || []).filter((v) => v.estado !== 'futuro' && pasado(v.inicio)).sort((a, b) => (a.inicio < b.inicio ? -1 : 1));
    const E = (A.eventos || []).filter((e) => pasado(e.fecha));
    const slugs = new Set((A.eventos || []).map((e) => e.slug));
    const viajeDe = new Map((A.viajes || []).map((v) => [v.slug, v.id]));   // slug de viaje -> id, para abrir el mapa en él
    const P = [...E.flatMap((e) => (e.objetos || []).map((o) => ({ ...o, fecha: o.fecha || e.fecha, ev: e }))), ...(A.objetos_sueltos || [])]
      .filter((o) => o.nivel && pasado(o.fecha)).sort(porFecha);
    const FOTOS = [...E.flatMap((e) => e.fotos || []), ...(A.fotos_sueltas || [])].filter((f) => f.mini && pasado(f.fecha));
    const HITOS = (A.hitos || []).filter((h) => pasado(h.fecha));
    const PINES = (A.objetos_sueltos || []).filter((o) => o.tipo === 'pin').length;   // los pines no tienen fecha: solo cuentan en «Todo»
    const en = (y) => (f) => (y === 'all' ? pasado(f) : yr(f) === y);

    function stats(y) {
      // «Todo» suma todos los bloques anuales (incluido «sin_fecha»)
      const bloques = Object.entries(A.anual || {}).filter(([k]) => y === 'all' || k === y).map(([, b]) => b);
      const s = { km: 0, viajes: 0, paises: 0, ciudades: 0, eventos: 0, premios: {}, personas: 0, pines: y === 'all' ? PINES : null, hitos: HITOS.filter((h) => en(y)(h.fecha)) };
      bloques.forEach((b) => {
        s.km += b.km; s.viajes += b.viajes; s.paises += b.paises_nuevos; s.ciudades += b.ciudades_nuevas; s.eventos += b.eventos; s.personas += b.personas_nuevas;
        Object.entries(b.premios || {}).forEach(([n, c]) => { s.premios[n] = (s.premios[n] || 0) + c; });
        if (y !== 'all' && b.pines) s.pines = b.pines;
      });
      s.nPremios = Object.values(s.premios).reduce((a, b) => a + b, 0);
      s.vueltas = s.km / 40075; s.luna = (s.km / 384400) * 100;
      return s;
    }
    // Un periodo = un mes (o un año en «Todo») con lo que pasó dentro
    function periodos(y) {
      const dentro = en(y);
      const clave = (f) => (y === 'all' ? yr(f) : f.length >= 7 ? f.slice(0, 7) : yr(f) + '-00');
      const m = new Map();
      const get = (k) => { if (!m.has(k)) m.set(k, { k, v: [], e: [], p: [], h: [], f: null }); return m.get(k); };
      V.filter((v) => dentro(v.inicio)).forEach((v) => get(clave(v.inicio)).v.push(v));
      E.filter((e) => dentro(e.fecha)).forEach((e) => get(clave(e.fecha)).e.push(e));
      P.filter((p) => dentro(p.fecha)).forEach((p) => get(clave(p.fecha)).p.push(p));
      HITOS.filter((h) => dentro(h.fecha)).forEach((h) => get(clave(h.fecha)).h.push(h));
      FOTOS.filter((f) => dentro(f.fecha)).forEach((f) => { const p = get(clave(f.fecha)); p.f ||= f; });
      return [...m.values()].sort((a, b) => (a.k < b.k ? -1 : 1));
    }
    // La suma de km por año debe cuadrar con totales.km
    const kmAnios = Object.values(A.anual || {}).reduce((s, b) => s + b.km, 0);
    return { stats, periodos, slugs, viajeDe, kmAnios, kmTotal: (A.totales || {}).km, hayCifras: !!A.anual };
  }
  if (typeof module !== 'undefined') module.exports = { calcular };
  if (typeof document === 'undefined') return;

  // ------------------------------------------------------------------ pantalla
  const $ = (id) => document.getElementById(id);
  const HOY = new Date().toISOString().slice(0, 10);
  const AÑO_ACTUAL = HOY.slice(0, 4);
  const AÑOS = []; for (let a = 2018; a <= +AÑO_ACTUAL; a++) AÑOS.push(String(a));
  const peg = (t, c = '') => (window.IDENTIDAD ? IDENTIDAD.pegatina(t, c) : '');
  const ev = (slug, texto) => `<a href="evento.html?e=${encodeURIComponent(slug)}">${esc(texto)}</a>`;
  const titulo = (y) => (y === 'all' ? 'Todo el archivo' : y);

  function etiqueta(k) {
    if (k.length === 4) return k;
    if (k.endsWith('-00')) return k.slice(0, 4) + ' · sin mes';
    return new Date(k + '-01T00:00:00Z').toLocaleDateString('es-ES', { month: 'long', year: 'numeric', timeZone: 'UTC' });
  }
  const accesos = () => `<nav class="accesos" aria-label="Módulos">${MODULOS.map(([n, t, s, u]) =>
    `<a class="acceso glass" href="${u}">${peg(t)}<span>${esc(n)}<br><span class="sub">${esc(s)}</span></span></a>`).join('')}</nav>`;

  let kmMostrado = 0;   // el contador parte del último valor, no de cero, al cambiar de año
  function contar(el, fin) {
    const ini = kmMostrado; kmMostrado = fin;
    if (!el || ini === fin || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const t0 = performance.now();
    setTimeout(() => { if (el.isConnected) el.textContent = nf(fin); }, 700);   // si la pestaña está oculta, rAF se pausa: el valor final no puede quedarse a medias
    (function paso(t) {
      const k = Math.min(1, (t - t0) / 600);
      if (!el.isConnected) return;   // se cambió de año a mitad: el siguiente render lleva su propio contador
      el.textContent = nf(Math.round(ini + (fin - ini) * (1 - Math.pow(1 - k, 3))));
      if (k < 1) requestAnimationFrame(paso);
    })(t0);
  }

  function pintar(D, y) {
    const s = D.stats(y);
    const lin = (t, h, sub = '') => `<div class="linea">${peg(t)}<p>${h}${sub ? `<br><span class="sub">${sub}</span>` : ''}</p></div>`;
    let acum = 0;
    const pasos = D.periodos(y).map((p, i) => {
      const kmP = p.v.reduce((a, v) => a + (v.km || 0), 0);
      acum += kmP;
      const enViaje = new Set(p.v.map((v) => v.id));
      const lineas = [
        ...p.v.map((v) => {
          const ciu = [...new Set((v.visitas || []).map((x) => x.ciudad))].slice(0, 4).join(', ');
          const evs = p.e.filter((e) => e.trip_id === v.id).map((e) => 'Evento: ' + ev(e.slug, e.nombre));
          return lin('viaje', `<a href="mapa.html?viaje=${v.id}">${esc(v.nombre)}</a>${v.km ? ` · <b class="n">${nf(v.km)} km</b>` : ''}`, [esc(ciu), ...evs].filter(Boolean).join(' · '));
        }),
        ...p.e.filter((e) => !enViaje.has(e.trip_id)).map((e) => lin('evento', `<b>${ev(e.slug, e.nombre)}</b>`, esc([e.ciudad, e.pais].filter(Boolean).join(', ')))),
        ...p.p.map((o) => lin('premio', `${o.ev ? ev(o.ev.slug, o.titulo) : esc(o.titulo)} · <b>${esc(o.nivel)}</b>`)),
        ...p.h.map((h) => lin('sello', `<b>Primera vez.</b> ${D.slugs.has(h.enlace) ? ev(h.enlace, h.texto) : D.viajeDe.has(h.enlace) ? `<a href="mapa.html?viaje=${D.viajeDe.get(h.enlace)}">${esc(h.texto)}</a>` : esc(h.texto)}`)),
      ].join('');
      const foto = p.f ? `<div class="sello foto"><img src="${esc(p.f.mini)}" alt="Foto de ${esc(etiqueta(p.k))}" loading="lazy" width="116" height="145"></div>` : '';
      return `<article class="paso" style="--i:${Math.min(i, 8)}"><header><h3>${esc(etiqueta(p.k))}</h3>${kmP ? `<span class="sub">acumulado <b class="n">${nf(acum)} km</b></span>` : ''}</header><div class="cuerpo glass">${lineas}${foto}</div></article>`;
    }).join('');
    const cuando = y === 'all' ? 'En todo el archivo' : 'En ' + y;
    $('relato').innerHTML = `
      <p class="kicker">Tu año en cifras · ${titulo(y)}</p>
      ${pasos ? `<p class="lead">${cuando} recorriste <span class="r"><span id="kmN">${nf(s.km)}</span> km</span>, ${nf(s.vueltas, 2)} vueltas a la Tierra, en <span class="r">${pl(s.viajes, 'viaje', 'viajes')}</span>${s.paises ? `, con <span class="r">${pl(s.paises, 'país nuevo', 'países nuevos')}</span>` : ''}. Así fue.</p>
      <div class="rel">${pasos}</div>` : '<p class="vacio">No hay nada registrado en este año.</p>'}
      <div class="cierre glass"><h2>Al cerrar ${y === 'all' ? 'el archivo' : 'el año'}</h2>
        <div class="cierre-chips"><span class="chip">${pl(s.eventos, 'evento', 'eventos')}</span><span class="chip">${pl(s.nPremios, 'premio', 'premios')}</span><span class="chip">${pl(s.ciudades, 'ciudad nueva', 'ciudades nuevas')}</span><span class="chip">${pl(s.personas, 'persona nueva', 'personas nuevas')}</span><span class="chip">${s.pines === null ? 'pines: ver «Todo»' : pl(s.pines, 'pin', 'pines')}</span><span class="chip">${nf(s.luna, 1)} % hasta la Luna</span></div>
        ${accesos()}</div>`;
    $('count').textContent = titulo(y);
    contar($('kmN'), s.km);
  }

  async function main() {
    let D;
    try {
      const res = await fetch('data/archivo.json', { cache: 'no-store' });
      if (!res.ok) throw new Error(res.status);
      D = calcular(await res.json(), HOY);
    } catch (err) {
      $('count').textContent = 'Sin datos';
      $('relato').innerHTML = '<p class="vacio">No se pudo leer <code>data/archivo.json</code>. Abre la web con un servidor local.</p>';
      return;
    }
    if (!D.hayCifras) { $('count').textContent = 'Sin cifras'; $('relato').innerHTML = '<p class="vacio">Faltan las cifras anuales: ejecuta «archivo.py exportar web/data/archivo.json».</p>'; return; }
    if (D.kmTotal != null && D.kmAnios !== D.kmTotal) console.warn(`Los km por año (${D.kmAnios}) no cuadran con totales.km (${D.kmTotal})`);
    const sel = $('anios');
    sel.innerHTML = [...AÑOS, 'all'].map((a) => `<button type="button" class="chip" data-a="${a}">${a === 'all' ? 'Todo' : a}</button>`).join('');
    const elegir = (a, mover) => {
      sel.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', b.dataset.a === a));
      pintar(D, a);
      history.replaceState(null, '', '#' + a);
      if (mover) sel.querySelector(`[data-a="${a}"]`).scrollIntoView({ inline: 'center', block: 'nearest' });
    };
    sel.addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) elegir(b.dataset.a, true); });
    const h = location.hash.slice(1);
    elegir([...AÑOS, 'all'].includes(h) ? h : AÑO_ACTUAL, true);
  }
  main();
})();
