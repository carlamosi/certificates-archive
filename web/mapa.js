/* Mapa de viajes (estilo Been). Ficha: docs/features/mapa.md · Identidad: docs/diseno/IDENTIDAD.md §9 */
(() => {
  'use strict';

  const ATLAS = 'https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-50m.json';
  const CASA = { nombre: 'Barcelona', lat: 41.3874, lng: 2.1686 };
  // nombre del país en la base -> id ISO 3166 numérico de world-atlas. Si sale un país nuevo, añadirlo aquí.
  const ISO = {
    'Andorra': '020', 'Bélgica': '056', 'Catar': '634', 'Chequia': '203', 'República Checa': '203',
    'Dinamarca': '208', 'España': '724', 'Francia': '250', 'Países Bajos': '528', 'Portugal': '620',
    'Sudáfrica': '710', 'Suecia': '752', 'Suiza': '756', 'Italia': '380', 'Alemania': '276',
    'Reino Unido': '826', 'Estados Unidos': '840', 'Austria': '040', 'Grecia': '300', 'Irlanda': '372',
  };
  // Fondos de mapa con teselas (Web Mercator, sin clave). «papel» es el mapa propio sin teselas.
  const BASES = {
    papel: null,
    satelite: {
      url: (z, x, y) => `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/${z}/${y}/${x}`,
      max: 18, credito: 'Imágenes © Esri, Maxar, Earthstar Geographics',
    },
    noche: {
      url: (z, x, y) => `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/VIIRS_Black_Marble/default/2016-01-01/GoogleMapsCompatible_Level8/${z}/${y}/${x}.png`,
      max: 8, credito: 'Luces de noche: NASA Black Marble',
    },
  };
  const CAPAS = [['paises', 'Países'], ['vuelos', 'Vuelos'], ['rutas', 'Rutas por tierra'], ['ciudades', 'Ciudades'], ['aeropuertos', 'Aeropuertos'], ['eventos', 'Eventos']];

  // ------------------------------------------------------------------ datos (sin DOM: se prueba con node)
  function estados(A) {
    const t = A.totales || {};
    const paises = t.paises || [];
    const visitados = paises.filter((p) => p.ciudades > 0);
    const transito = paises.filter((p) => !(p.ciudades > 0) && p.aeropuertos > 0);
    const conocidos = new Set(paises.map((p) => p.pais));
    const futuros = [...new Set((A.viajes || []).filter((v) => v.estado === 'futuro')
      .flatMap((v) => (v.visitas || []).map((x) => x.pais)))].filter((p) => p && !conocidos.has(p));
    const contadores = [
      ['ciudad', 'ciudades', (t.ciudades || []).length],
      ['país', 'países', visitados.length],
      ['continente', 'continentes', new Set(visitados.map((p) => p.continente)).size],
      ['aeropuerto', 'aeropuertos', (t.aeropuertos || []).length],
    ];
    if (Number.isFinite(t.km)) contadores.push(['km recorrido', 'km recorridos', Math.round(t.km)]);
    return { visitados: visitados.map((p) => p.pais), transito: transito.map((p) => p.pais), futuros, contadores };
  }

  // Ciudades únicas (una chincheta aunque se visite en varios viajes)
  function ciudades(A) {
    const m = new Map();
    for (const v of A.viajes || []) {
      for (const x of v.visitas || []) {
        if (x.lat == null || x.lng == null) continue;
        const k = `${x.ciudad}|${x.pais}`;
        if (!m.has(k)) m.set(k, { tipo: 'ciudad', nombre: x.ciudad, pais: x.pais, lat: x.lat, lng: x.lng, visitas: [] });
        m.get(k).visitas.push({ viaje: v, inicio: x.inicio, fin: x.fin });
      }
    }
    for (const c of m.values()) c.futuro = c.visitas.every((x) => x.viaje.estado === 'futuro');
    return [...m.values()];
  }

  // Viajes en orden: futuros primero, luego del más reciente al más antiguo; sin fecha al final
  const ordenViajes = (vs) => vs.slice().sort((a, b) =>
    (b.estado === 'futuro') - (a.estado === 'futuro') || (b.inicio || '0').localeCompare(a.inicio || '0'));

  // Paradas de un viaje en orden de fechas (las que no tienen fecha, al final, en su orden)
  const paradas = (v) => (v.visitas || []).map((x, i) => ({ x, i }))
    .sort((a, b) => (a.x.inicio || '9999').localeCompare(b.x.inicio || '9999') || a.i - b.i).map((o) => o.x);

  if (typeof module === 'object') { module.exports = { estados, ciudades, ordenViajes, paradas }; return; }

  // ------------------------------------------------------------------ utilidades
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  const dur = (ms) => (reduce.matches ? 0 : ms);
  const fmtDia = new Intl.DateTimeFormat('es-ES', { day: 'numeric', month: 'long', year: 'numeric' });
  const fmtCorto = new Intl.DateTimeFormat('es-ES', { day: 'numeric', month: 'short' });
  const fmtMes = new Intl.DateTimeFormat('es-ES', { month: 'long', year: 'numeric' });
  const dia = (s) => new Date(s + 'T12:00');
  const fecha = (s) => (s ? fmtDia.format(dia(s)) : '');
  const num = (n) => Math.round(n).toLocaleString('es-ES');
  const plural = (n, uno, varios) => `${num(n)} ${n === 1 ? uno : varios}`;

  function rango(a, b) {
    if (!a) return '';
    if (!b || a === b) return fecha(a);
    const [da, db] = [dia(a), dia(b)];
    if (da.getMonth() === db.getMonth() && da.getFullYear() === db.getFullYear()) return `${da.getDate()}–${db.getDate()} de ${fmtMes.format(db)}`;
    return `${fecha(a)} – ${fecha(b)}`;
  }
  const rangoCorto = (a, b) => (!a ? '' : !b || a === b ? fmtCorto.format(dia(a)) : `${fmtCorto.format(dia(a))} – ${fmtCorto.format(dia(b))}`);

  async function cargar(url) {
    const res = await fetch(url, { cache: url.startsWith('http') ? 'force-cache' : 'no-store' });
    if (!res.ok) throw new Error(url);
    return res.json();
  }

  // ------------------------------------------------------------------ estado
  const S = {
    A: null, mundo: null, zoom: null, t: d3.zoomIdentity, proj: null, pines: [], ocultar: 0,
    base: 'papel', capas: new Set(CAPAS.map((c) => c[0])), viaje: null, w: 0, h: 0, origenFoco: null,
  };

  async function iniciar() {
    try {
      S.A = window.ARCHIVO = await cargar('data/archivo.json');
    } catch (e) {
      return aviso('No encuentro data/archivo.json. Genera el fichero con «archivo.py exportar web/data/archivo.json» y recarga.');
    }
    try {
      S.mundo = await cargar(ATLAS);
    } catch (e) {
      return aviso('No he podido cargar las formas de los países. Comprueba la conexión y recarga.');
    }
    S.E = estados(S.A);
    S.viajes = ordenViajes(S.A.viajes || []);
    pintarContadores(S.E);
    pintarLeyenda(S.E);
    pintarControlCapas();
    S.lugares = [...ciudades(S.A), ...eventos(S.A), ...aeropuertos(S.A)];
    dibujar();
    const q = new URLSearchParams(location.search).get('viaje'); // viene de pines.html
    if (S.proj) abrirPanel(S.A.viajes.find((v) => String(v.id) === q)); // sin proj = pestaña oculta, no se dibujó
    let t = 0;
    addEventListener('resize', () => { clearTimeout(t); t = setTimeout(dibujar, 150); });
    addEventListener('keydown', (e) => {
      if (e.key !== 'Escape') return;
      if (!$('capasMenu').hidden) return cerrarCapas(true);
      if (!$('panel').hidden) return cerrarPanel();
      cerrar();
    });
  }

  function aviso(txt) { $('notice').textContent = txt; $('notice').hidden = false; $('count').textContent = ''; }

  const eventos = (A) => (A.eventos || []).filter((e) => e.lat != null && e.lng != null).map((e) => ({
    tipo: 'evento', nombre: e.nombre, pais: e.pais, ciudad: e.ciudad, lugar: e.lugar, lat: e.lat, lng: e.lng, fecha: e.fecha, viaje: (A.viajes || []).find((v) => v.id === e.trip_id),
  }));

  const vuelosDe = (v) => (v.vuelos || []).filter((f) => f.origen?.lat != null && f.destino?.lat != null);
  const vuelos = (A) => (A.viajes || []).flatMap((v) => vuelosDe(v).map((f) => ({ ...f, viaje: v })));
  const nombreAeropuerto = (iata) => (((S.A || {}).totales || {}).aeropuertos || []).find((x) => x.iata === iata)?.nombre || iata;

  function aeropuertos(A) {
    const m = new Map();
    for (const f of vuelos(A)) for (const a of [f.origen, f.destino]) {
      if (!m.has(a.iata)) m.set(a.iata, { tipo: 'aeropuerto', nombre: a.nombre || nombreAeropuerto(a.iata), iata: a.iata, lat: a.lat, lng: a.lng, viajes: [] });
      m.get(a.iata).viajes.push(f.viaje);
    }
    return [...m.values()];
  }

  // ------------------------------------------------------------------ cabecera, leyenda, capas
  function pintarContadores(E) {
    $('contadores').innerHTML = E.contadores.map(([uno, varios, n]) =>
      `<div><dt>${n === 1 ? uno : varios}</dt><dd class="num">${num(n)}</dd></div>`).join('');
    const anios = (S.A.viajes || []).map((v) => v.anio).filter(Boolean).sort();
    const n = (S.A.viajes || []).length;
    $('count').textContent = `${plural(n, 'viaje', 'viajes')}${anios.length ? ` · ${anios[0]}–${anios[anios.length - 1]}` : ''}`;
    $('nViajes').textContent = n;
  }

  function pintarLeyenda(E) {
    const filas = [
      ['visitado', E.visitados.length === 1 ? 'país visitado' : 'países visitados', E.visitados],
      ['transito', 'en tránsito', E.transito],
      ['futuro', 'próximo', E.futuros],
    ].filter((f) => f[2].length);
    $('leyenda').innerHTML = filas.map(([cls, txt, l]) =>
      `<li title="${esc(l.join(', '))}"><i class="muestra ${cls}"></i><b class="num">${l.length}</b> ${txt}</li>`).join('');
    for (const p of [...E.visitados, ...E.transito, ...E.futuros]) if (!ISO[p]) console.warn(`Mapa: falta el código ISO de «${p}» en mapa.js`);
  }

  function pintarControlCapas() {
    const bases = [['papel', 'Papel'], ['satelite', 'Satélite'], ['noche', 'Noche']];
    $('capasMenu').innerHTML = `
      <p class="kicker">Fondo</p>
      <div class="segmento" role="radiogroup" aria-label="Fondo del mapa">
        ${bases.map(([id, txt]) => `<button type="button" role="radio" data-base="${id}" aria-checked="${id === S.base}">${txt}</button>`).join('')}
      </div>
      <p class="kicker">Mostrar</p>
      <ul class="interruptores">
        ${CAPAS.map(([id, txt]) => `<li><label><input type="checkbox" data-capa="${id}" checked><span>${txt}</span></label></li>`).join('')}
      </ul>`;
    $('capasMenu').addEventListener('click', (e) => {
      const b = e.target.closest('[data-base]');
      if (b) cambiarBase(b.dataset.base);
    });
    $('capasMenu').addEventListener('change', (e) => {
      const id = e.target.dataset.capa;
      if (!id) return;
      if (e.target.checked) S.capas.add(id); else S.capas.delete(id);
      $('mapa').classList.toggle(`sin-${id}`, !e.target.checked);
    });
    $('capasBtn').addEventListener('click', () => ($('capasMenu').hidden ? abrirCapas() : cerrarCapas()));
    document.addEventListener('pointerdown', (e) => {
      if (!$('capasMenu').hidden && !e.target.closest('#capasMenu, #capasBtn')) cerrarCapas();
    });
  }

  function abrirCapas() {
    $('capasMenu').hidden = false;
    $('capasBtn').setAttribute('aria-expanded', 'true');
    $('capasMenu').querySelector('[aria-checked="true"]').focus();
  }
  function cerrarCapas(devolverFoco) {
    $('capasMenu').hidden = true;
    $('capasBtn').setAttribute('aria-expanded', 'false');
    if (devolverFoco) $('capasBtn').focus();
  }

  function cambiarBase(id) {
    S.base = id;
    for (const b of $('capasMenu').querySelectorAll('[data-base]')) b.setAttribute('aria-checked', String(b.dataset.base === id));
    $('mapa').dataset.base = id;
    $('credito').textContent = BASES[id]?.credito || '';
    pintarTeselas();
  }

  // ------------------------------------------------------------------ mapa
  function dibujar() {
    cerrar();
    const main = $('mapa');
    const w = main.clientWidth, h = main.clientHeight;
    if (!w || !h) return;   // pestaña oculta o sin tamaño: se dibuja en el próximo resize
    S.w = w; S.h = h;
    const r = $('resumen').getBoundingClientRect(), m = main.getBoundingClientRect();
    const arriba = r.bottom - m.top + 24;
    const abajo = 80, lado = innerWidth < 640 ? 24 : 64;
    const svg = d3.select('#lienzo').attr('viewBox', `0 0 ${w} ${h}`);
    svg.selectAll('*').remove();

    // sin la Antártida: en Mercator ocupa media pantalla y no aporta
    const paises = topojson.feature(S.mundo, S.mundo.objects.countries).features.filter((f) => f.id !== '010');
    // encuadre inicial: lo que está a menos de 3500 km de casa (lo lejano se ve alejando o en el panel de su viaje)
    const casaLL = [CASA.lng, CASA.lat];
    let cerca = S.lugares.map((l) => [l.lng, l.lat]).filter((p) => d3.geoDistance(casaLL, p) * 6371 < 3500);
    if (cerca.length < 2) cerca = S.lugares.map((l) => [l.lng, l.lat]);
    const puntos = { type: 'MultiPoint', coordinates: cerca.concat([casaLL]) };
    S.proj = d3.geoMercator().fitExtent([[lado, arriba], [w - lado, Math.max(arriba + 80, h - abajo)]], puntos);
    const path = d3.geoPath(S.proj);

    const defs = svg.append('defs');
    defs.append('pattern').attr('id', 'rayado').attr('patternUnits', 'userSpaceOnUse')
      .attr('width', 3).attr('height', 3).attr('patternTransform', 'rotate(45)')
      .append('rect').attr('class', 'raya').attr('width', 1.2).attr('height', 3);
    // lo visitado: degradado vertical (luz arriba, como el cristal) en cada país
    const grad = defs.append('linearGradient').attr('id', 'grad-visitado').attr('x1', 0).attr('y1', 0).attr('x2', 0).attr('y2', 1);
    grad.append('stop').attr('offset', '0%').attr('class', 'vis-a');
    grad.append('stop').attr('offset', '100%').attr('class', 'vis-b');
    // efectos en píxeles de pantalla (los filtros van fuera del zoom para no crecer al acercar)
    const filtro = (id, f) => { const el = defs.append('filter').attr('id', id).attr('x', '-20%').attr('y', '-20%').attr('width', '140%').attr('height', '140%'); f(el); };
    filtro('sombra-tierra', (f) => f.append('feDropShadow').attr('class', 'fx-sombra').attr('dx', 0).attr('dy', 2).attr('stdDeviation', 2.5));
    filtro('brillo-visitado', (f) => f.append('feDropShadow').attr('class', 'fx-brillo').attr('dx', 0).attr('dy', 0).attr('stdDeviation', 7));
    filtro('brillo-arco', (f) => {
      f.append('feGaussianBlur').attr('in', 'SourceGraphic').attr('stdDeviation', 2.2).attr('result', 'b');
      const m = f.append('feMerge'); m.append('feMergeNode').attr('in', 'b'); m.append('feMergeNode').attr('in', 'SourceGraphic');
    });

    const estadoDe = new Map();
    for (const p of S.E.visitados) estadoDe.set(ISO[p], 'visitado');
    for (const p of S.E.transito) estadoDe.set(ISO[p], 'transito');
    for (const p of S.E.futuros) estadoDe.set(ISO[p], 'futuro');

    S.gTeselas = svg.append('g').attr('class', 'teselas');
    // cada capa: un envoltorio con su efecto y, dentro, el grupo que se mueve con el zoom
    const capaCon = (cls, fx) => svg.append('g').attr('class', `fx ${cls}`).attr('filter', fx ? `url(#${fx})` : null)
      .append('g').attr('class', 'zoomable');
    const tierra = capaCon('g-paises g-tierra', 'sombra-tierra');
    const marcados = capaCon('g-paises g-marcados', 'brillo-visitado');
    const orden = (f) => ({ visitado: 1, transito: 2, futuro: 3 }[estadoDe.get(f.id)] || 0);
    tierra.selectAll('path').data(paises.filter((f) => !estadoDe.has(f.id))).join('path').attr('class', 'pais').attr('d', path);
    marcados.selectAll('path').data(paises.filter((f) => estadoDe.has(f.id)).sort((a, b) => orden(a) - orden(b))).join('path')
      .attr('class', (f) => `pais ${estadoDe.get(f.id)}`).attr('d', path);

    const trazos = capaCon('g-trazos', 'brillo-arco').classed('trazos', true);
    const linea = (cls, viaje, d) => {
      const g = trazos.append('g').attr('class', `trazo ${cls}${viaje.estado === 'futuro' ? ' futuro' : ''}`).attr('data-viaje', viaje.id);
      g.append('path').attr('class', 'ver').attr('d', d);
      g.append('path').attr('class', 'tocar').attr('d', d);   // área de clic ancha e invisible
    };
    for (const r of rutas()) linea('ruta', r.viaje, r.d);
    for (const a of arcos()) linea('arco', a.viaje, a.d);
    trazos.on('click', (e) => {
      const g = e.target.closest('.trazo');
      if (g) abrirPanel(S.A.viajes.find((v) => String(v.id) === g.dataset.viaje), null);
    });
    const casa = S.proj(casaLL);
    trazos.append('circle').attr('class', 'casa').attr('cx', casa[0]).attr('cy', casa[1]).attr('r', 3.5);

    pintarPines();

    S.zoom = d3.zoom().scaleExtent([0.5, 80])
      .filter((e) => (!e.ctrlKey || e.type === 'wheel') && !e.button)
      .on('zoom', (e) => {
        S.t = e.transform;
        svg.selectAll('.zoomable').attr('transform', S.t);
        moverPines();
        pintarTeselas();
      });
    svg.call(S.zoom).on('click', (e) => { if (!e.defaultPrevented && !e.target.closest('.trazo')) cerrar(); });
    S.t = d3.zoomIdentity;
    moverPines();
    pintarTeselas();
    if (S.viaje) resaltar(S.viaje), encuadrar(S.viaje, false);
  }

  // Teselas del fondo (satélite, noche). Por encima de su zoom máximo se estira la tesela madre.
  function pintarTeselas() {
    const g = S.gTeselas;
    if (!g) return;
    const base = BASES[S.base];
    if (!base) { g.selectAll('image').remove(); return; }
    const k = S.t.k, [tx, ty] = S.proj.translate();
    const tiles = d3.tile().size([S.w, S.h]).scale(2 * Math.PI * S.proj.scale() * k).translate([S.t.x + k * tx, S.t.y + k * ty])();
    if (!tiles.length) return;
    const z = tiles[0][2], d = Math.max(0, z - base.max), f = 2 ** d, [ox, oy] = tiles.translate, sc = tiles.scale;
    const madres = new Map();
    for (const [x, y] of tiles) {
      const px = Math.floor(x / f), py = Math.floor(y / f), n = 2 ** (z - d);
      const key = `${z - d}/${px}/${py}`;
      if (py < 0 || py >= n || madres.has(key)) continue;
      madres.set(key, { key, href: base.url(z - d, ((px % n) + n) % n, py), x: (px * f + ox) * sc, y: (py * f + oy) * sc, s: sc * f });
    }
    g.selectAll('image').data([...madres.values()], (t) => t.key).join('image')
      .attr('href', (t) => t.href).attr('x', (t) => t.x).attr('y', (t) => t.y)
      .attr('width', (t) => t.s + 0.5).attr('height', (t) => t.s + 0.5).attr('preserveAspectRatio', 'none');
  }

  // Curva en el plano proyectado (estilo arco de vuelo): siempre se comba hacia el norte
  function curva(a, b) {
    const [x0, y0] = S.proj(a), [x1, y1] = S.proj(b);
    const dx = x1 - x0, dy = y1 - y0, len = Math.hypot(dx, dy) || 1;
    let nx = -dy / len, ny = dx / len;
    if (ny > 0) { nx = -nx; ny = -ny; }
    const k = len * 0.22;
    return `M${x0},${y0} Q${(x0 + x1) / 2 + nx * k},${(y0 + y1) / 2 + ny * k} ${x1},${y1}`;
  }

  function arcos() {
    const fl = vuelos(S.A);
    if (fl.length) return fl.map((f) => ({ viaje: f.viaje, d: curva([f.origen.lng, f.origen.lat], [f.destino.lng, f.destino.lat]) }));
    // sin vuelos exportados: un arco de casa a la ciudad más lejana de cada viaje
    const casa = [CASA.lng, CASA.lat];
    return (S.A.viajes || []).flatMap((v) => {
      const vs = (v.visitas || []).filter((x) => x.lat != null);
      if (!vs.length) return [];
      const lejos = vs.reduce((m, x) => (d3.geoDistance(casa, [x.lng, x.lat]) > d3.geoDistance(casa, [m.lng, m.lat]) ? x : m));
      if (d3.geoDistance(casa, [lejos.lng, lejos.lat]) * 6371 < 50) return [];
      return [{ viaje: v, d: curva(casa, [lejos.lng, lejos.lat]) }];
    });
  }

  function rutas() {
    return (S.A.viajes || []).flatMap((v) => {
      const vs = paradas(v).filter((x) => x.lat != null);
      if (vs.length < 2) return [];
      return [{ viaje: v, d: 'M' + vs.map((x) => S.proj([x.lng, x.lat]).join(',')).join('L') }];
    });
  }

  // ------------------------------------------------------------------ chinchetas
  function pintarPines() {
    const cont = $('chinchetas');
    cont.innerHTML = '';
    // orden de tabulación de oeste a este
    S.pines = S.lugares.slice().sort((a, b) => a.lng - b.lng).map((l) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = `pin ${l.tipo}${l.futuro ? ' futuro' : ''}`;
      b.setAttribute('aria-label', etiqueta(l));
      b.innerHTML = `${IDENTIDAD.pegatina(l.tipo)}<span class="pin-nombre">${esc(l.iata || l.nombre)}</span>`;
      b.addEventListener('pointerenter', (e) => { if (e.pointerType === 'mouse') abrir(l, b); });
      b.addEventListener('pointerleave', (e) => { if (e.pointerType === 'mouse') cerrarPronto(); });
      b.addEventListener('focus', () => { asegurarVisible(l); abrir(l, b); });
      b.addEventListener('blur', cerrarPronto);
      b.addEventListener('click', () => { const v = viajesDe(l)[0]; if (v) abrirPanel(v, b); else abrir(l, b); });
      cont.appendChild(b);
      return { l, b, xy: S.proj([l.lng, l.lat]) };
    });
  }

  function moverPines() {
    $('chinchetas').classList.toggle('cerca', S.t.k >= 3);
    for (const p of S.pines) {
      const [x, y] = S.t.apply(p.xy);
      p.b.style.transform = `translate(${x}px, ${y}px)`;
    }
  }

  function asegurarVisible(l) {
    const [x, y] = S.t.apply(S.proj([l.lng, l.lat]));
    if (x < 40 || y < 40 || x > S.w - 40 || y > S.h - 140) {
      d3.select('#lienzo').transition().duration(dur(280)).ease(d3.easeCubicOut).call(S.zoom.translateTo, ...S.proj([l.lng, l.lat]));
    }
  }

  function etiqueta(l) {
    if (l.tipo === 'aeropuerto') return `Aeropuerto ${l.iata}: ver su viaje`;
    if (l.tipo === 'evento') return [l.nombre, l.ciudad || l.pais].filter(Boolean).join(', ');
    return `${l.nombre}, ${l.pais}${l.futuro ? ' (próximo viaje)' : ''}: ver su viaje`;
  }

  // viajes de una chincheta, del más reciente al más antiguo
  function viajesDe(l) {
    const vs = l.tipo === 'ciudad' ? l.visitas.map((x) => x.viaje) : l.tipo === 'aeropuerto' ? l.viajes : [l.viaje].filter(Boolean);
    return ordenViajes([...new Set(vs)]);
  }

  // ------------------------------------------------------------------ cartela (vista rápida al pasar)
  function abrir(l, b) {
    clearTimeout(S.ocultar);
    let kicker = '', sub = '';
    const viajes = viajesDe(l);
    if (l.tipo === 'ciudad') {
      if (viajes.length === 1) {
        const x = l.visitas[0];
        kicker = (l.futuro ? 'Próximo · ' : '') + (rango(x.inicio, x.fin) || rango(x.viaje.inicio, x.viaje.fin) || 'Sin fecha');
      } else {
        const anios = viajes.map((v) => v.anio).filter(Boolean).sort();
        kicker = `${viajes.length} viajes` + (anios.length ? ` · ${anios[0]}${anios[0] !== anios[anios.length - 1] ? '–' + anios[anios.length - 1] : ''}` : '');
      }
      const nombres = viajes.map((v) => v.nombre);
      sub = `${l.pais} · ${nombres.slice(0, 2).join(' · ')}${nombres.length > 2 ? ` y ${nombres.length - 2} más` : ''}`;
    } else if (l.tipo === 'aeropuerto') {
      kicker = `Aeropuerto · ${l.iata}`;
      sub = `${plural(l.viajes.length, 'vuelo', 'vuelos')} · ${plural(viajes.length, 'viaje', 'viajes')}`;
    } else {
      kicker = l.fecha ? (l.fecha.length > 7 ? fecha(l.fecha) : l.fecha) : '';
      sub = [l.lugar, l.ciudad, l.pais].filter(Boolean).join(' · ');
    }
    $('cPeg').innerHTML = IDENTIDAD.pegatina(l.tipo);
    $('cFecha').textContent = kicker;
    $('cTitle').textContent = l.nombre;
    $('cLugar').textContent = sub;
    $('cartela').classList.add('abierta');
    for (const p of S.pines) p.b.classList.toggle('activo', p.b === b);
    if (!S.viaje) resaltar(...viajes);
  }

  function cerrarPronto() { clearTimeout(S.ocultar); S.ocultar = setTimeout(cerrar, 160); }

  function cerrar() {
    clearTimeout(S.ocultar);
    $('cartela').classList.remove('abierta');
    for (const p of S.pines) p.b.classList.remove('activo');
    if (S.viaje) resaltar(S.viaje); else resaltar();
  }

  // resalta los arcos, rutas y chinchetas de unos viajes (sin viajes: todo normal)
  function resaltar(...viajes) {
    const ids = new Set(viajes.map((v) => String(v.id)));
    $('mapa').classList.toggle('resaltando', ids.size > 0);
    for (const g of $('lienzo').querySelectorAll('.trazo')) g.classList.toggle('activo', ids.has(g.dataset.viaje));
    for (const p of S.pines) p.b.classList.toggle('del-viaje', viajesDe(p.l).some((v) => ids.has(String(v.id))));
  }

  // ------------------------------------------------------------------ panel lateral de viajes
  function abrirPanel(v, origen) {
    if (!v) return;
    if (origen) S.origenFoco = origen;
    S.viaje = v;
    cerrarCapas();
    $('cartela').classList.remove('abierta');
    $('panelCuerpo').innerHTML = fichaViaje(v);
    $('panelVolver').hidden = false;
    mostrarPanel();
    resaltar(v);
    encuadrar(v, true);
  }

  function abrirLista(origen) {
    if (origen) S.origenFoco = origen;
    S.viaje = null;
    cerrarCapas();
    resaltar();
    $('panelCuerpo').innerHTML = listaViajes();
    $('panelVolver').hidden = true;
    mostrarPanel();
  }

  function mostrarPanel() {
    const p = $('panel');
    const nuevo = p.hidden;
    p.hidden = false;
    $('mapa').classList.add('con-panel');
    $('viajesBtn').setAttribute('aria-expanded', 'true');
    p.scrollTop = 0;
    $('panelCuerpo').scrollTop = 0;
    if (nuevo) p.classList.remove('entra'), void p.offsetWidth, p.classList.add('entra');
    p.querySelector('.panel-cabeza').focus({ preventScroll: true });
  }

  function cerrarPanel() {
    $('panel').hidden = true;
    $('mapa').classList.remove('con-panel');
    $('viajesBtn').setAttribute('aria-expanded', 'false');
    S.viaje = null;
    resaltar();
    (S.origenFoco && document.contains(S.origenFoco) ? S.origenFoco : $('viajesBtn')).focus({ preventScroll: true });
    S.origenFoco = null;
  }

  // Encaja el viaje en la parte del mapa que no tapa el panel
  function encuadrar(v, animar) {
    const pts = [...(v.visitas || []).filter((x) => x.lat != null).map((x) => [x.lng, x.lat]),
      ...vuelosDe(v).flatMap((f) => [[f.origen.lng, f.origen.lat], [f.destino.lng, f.destino.lat]])].map((p) => S.proj(p));
    if (!pts.length) return;
    const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
    const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
    const movil = innerWidth < 760;
    const panel = $('panel').getBoundingClientRect(), m = $('mapa').getBoundingClientRect();
    const arriba = $('resumen').getBoundingClientRect().bottom - m.top;   // sin quedar bajo el resumen
    const zona = movil
      ? { x: 0, y: arriba, w: S.w, h: Math.max(160, panel.top - m.top - arriba) }
      : { x: 0, y: arriba, w: Math.max(200, panel.left - m.left), h: S.h - arriba };
    const pad = 72;
    const k = Math.min(10, 0.9 * Math.min((zona.w - pad * 2) / Math.max(1, x1 - x0), (zona.h - pad * 2) / Math.max(1, y1 - y0)));
    const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
    const t = d3.zoomIdentity.translate(zona.x + zona.w / 2 - k * cx, zona.y + zona.h / 2 - k * cy).scale(k);
    const svg = d3.select('#lienzo');
    (animar ? svg.transition().duration(dur(480)).ease(d3.easeCubicOut) : svg).call(S.zoom.transform, t);
  }

  function listaViajes() {
    const grupos = new Map();
    for (const v of S.viajes) {
      const g = v.estado === 'futuro' ? 'Próximos' : v.anio || 'Sin fecha';
      if (!grupos.has(g)) grupos.set(g, []);
      grupos.get(g).push(v);
    }
    const kmTotal = S.A.totales?.km;
    return `
      <div class="panel-cabeza" tabindex="-1">
        ${IDENTIDAD.pegatina('viaje', 'grande')}
        <p class="kicker">${plural(S.viajes.length, 'viaje', 'viajes')}</p>
        <h2 id="panelTitulo">Mis viajes</h2>
        ${Number.isFinite(kmTotal) ? `<p class="sub">${num(kmTotal)} km recorridos</p>` : ''}
      </div>
      ${[...grupos].map(([g, vs]) => `
        <section class="grupo">
          <h3 class="kicker gris">${esc(g)}</h3>
          <ul class="lista-viajes">
            ${vs.map((v) => `<li><button type="button" class="fila-viaje" data-viaje="${v.id}">
              <span class="fila-nombre">${esc(v.nombre)}</span>
              <span class="fila-meta num">${esc([rangoCorto(v.inicio, v.fin), v.km ? `${num(v.km)} km` : '', plural((v.visitas || []).length, 'ciudad', 'ciudades')].filter(Boolean).join(' · '))}</span>
            </button></li>`).join('')}
          </ul>
        </section>`).join('')}`;
  }

  function fichaViaje(v) {
    const ps = paradas(v);
    const fl = vuelosDe(v);
    const ev = (v.eventos || []).map((slug) => (S.A.eventos || []).find((e) => e.slug === slug)).filter(Boolean);
    const objs = v.objetos || [];
    const porTipo = d3.rollups(objs, (l) => l.length, (o) => o.tipo);
    const paises = [...new Set(ps.map((x) => x.pais))];
    const i = S.viajes.indexOf(v);
    const datos = [
      v.dias ? [v.dias, v.dias === 1 ? 'día' : 'días'] : null,
      v.km ? [num(v.km), 'km'] : null,
      [ps.length, ps.length === 1 ? 'ciudad' : 'ciudades'],
      fl.length ? [fl.length, fl.length === 1 ? 'vuelo' : 'vuelos'] : null,
    ].filter(Boolean);
    const nombreTipo = { pin: ['pin', 'pines'], lanyard: ['lanyard', 'lanyards'], certificado: ['certificado', 'certificados'], premio: ['premio', 'premios'], sello: ['sello LEGO', 'sellos LEGO'], foto: ['foto', 'fotos'] };
    return `
      <div class="panel-cabeza" tabindex="-1">
        ${IDENTIDAD.pegatina('viaje', 'grande')}
        <p class="kicker">${v.estado === 'futuro' ? 'Próximo · ' : ''}${esc(rango(v.inicio, v.fin) || 'Sin fecha')}</p>
        <h2 id="panelTitulo">${esc(v.nombre)}</h2>
        <p class="sub">${esc(paises.join(' · '))}</p>
      </div>
      <dl class="datos-viaje">${datos.map(([n, t]) => `<div><dd class="num">${n}</dd><dt>${t}</dt></div>`).join('')}</dl>

      ${fl.length ? `<section><h3 class="kicker gris">Vuelos</h3><ol class="vuelos">
        ${fl.map((f) => `<li class="billete">
          <span class="iata"><b>${esc(f.origen.iata)}</b><small>${esc(nombreAeropuerto(f.origen.iata))}</small></span>
          <svg class="icono avion" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12h15M14 7l5 5-5 5"/></svg>
          <span class="iata"><b>${esc(f.destino.iata)}</b><small>${esc(nombreAeropuerto(f.destino.iata))}</small></span>
        </li>`).join('')}</ol></section>` : ''}

      <section><h3 class="kicker gris">Recorrido</h3><ol class="recorrido">
        ${ps.map((x) => `<li><span class="parada">${esc(x.ciudad)}</span><span class="sub">${esc([rangoCorto(x.inicio, x.fin), x.nota].filter(Boolean).join(' · ') || x.pais)}</span></li>`).join('')}
      </ol></section>

      ${ev.length || objs.length ? `<section><h3 class="kicker gris">Del archivo</h3><ul class="del-archivo">
        ${ev.map((e) => `<li>${IDENTIDAD.pegatina('evento')}<span><b><a href="evento.html?e=${encodeURIComponent(e.slug)}">${esc(e.nombre)}</a></b><span class="sub">${esc([e.fecha, e.organizador].filter(Boolean).join(' · '))}</span></span></li>`).join('')}
        ${porTipo.map(([t, n]) => `<li>${IDENTIDAD.pegatina(IDENTIDAD.PEGATINAS[t] ? t : 'evento')}<span><b>${plural(n, ...(nombreTipo[t] || [t, t + 's']))}</b><span class="sub">${esc(objetosDe(objs, t))}</span></span></li>`).join('')}
      </ul></section>` : ''}

      <div class="nav panel-nav">
        <button type="button" class="btn ghost" data-ir="${i + 1}" ${i >= S.viajes.length - 1 ? 'disabled' : ''}>${IDENTIDAD.icono('anterior')}Viaje anterior</button>
        <button type="button" class="btn ghost" data-ir="${i - 1}" ${i <= 0 ? 'disabled' : ''}>Viaje siguiente${IDENTIDAD.icono('siguiente')}</button>
      </div>`;
  }

  // «Lisboa, Fátima…»: dónde se consiguió cada objeto, por su ciudad
  function objetosDe(objs, tipo) {
    const lugares = objs.filter((o) => o.tipo === tipo).map((o) => o.titulo || o.sitio
      || (S.A.totales?.ciudades || []).find((c) => c.id === o.place_id)?.nombre).filter(Boolean);
    return [...new Set(lugares)].join(', ');
  }

  // ------------------------------------------------------------------ controles
  const zoomBoton = (f) => d3.select('#lienzo').transition().duration(dur(280)).ease(d3.easeCubicOut).call(S.zoom.scaleBy, f);
  $('zMas').addEventListener('click', () => S.zoom && zoomBoton(1.8));
  $('zMenos').addEventListener('click', () => S.zoom && zoomBoton(1 / 1.8));
  $('viajesBtn').addEventListener('click', (e) => ($('panel').hidden ? abrirLista(e.currentTarget) : cerrarPanel()));
  $('panelCerrar').addEventListener('click', cerrarPanel);
  $('panelVolver').addEventListener('click', () => abrirLista());
  $('panelCuerpo').addEventListener('click', (e) => {
    const fila = e.target.closest('[data-viaje]');
    if (fila) return abrirPanel(S.A.viajes.find((v) => String(v.id) === fila.dataset.viaje));
    const ir = e.target.closest('[data-ir]');
    if (ir) abrirPanel(S.viajes[+ir.dataset.ir]);
  });

  iniciar();
})();
