/* Pines por ciudad. Ficha: docs/features/pines.md · Identidad: docs/diseno/IDENTIDAD.md */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const quitaAcentos = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '');
  const mesAnio = (s) => {
    const t = new Intl.DateTimeFormat('es-ES', { month: 'long', year: 'numeric' }).format(new Date(s + 'T12:00'));
    return t.charAt(0).toUpperCase() + t.slice(1).replace(' de ', ' de ');
  };
  const plural = (n, uno, varios) => `${n} ${n === 1 ? uno : varios}`;
  const movil = matchMedia('(max-width: 760px)');

  // Pines con su ciudad, país, fecha y viaje. Medidas y caja física no se leen: no se muestran.
  function pinesDe(A) {
    const ciudades = new Map(((A.totales || {}).ciudades || []).map((c) => [c.id, c]));
    const lista = [];
    for (const v of A.viajes || []) {
      for (const o of v.objetos || []) {
        if (o.tipo !== 'pin') continue;
        const c = ciudades.get(o.place_id) || {};
        const nombre = c.nombre || 'Sin ciudad';
        const visita = (v.visitas || []).find((x) => x.ciudad === nombre && x.inicio);
        const ini = (visita && visita.inicio) || v.inicio;
        const corto = (o.pin_id || '').split('-')[0];
        lista.push({
          uid: o.uid, ciudad: nombre, pais: c.pais || '', viaje: v, foto: o.front_web || '',
          codigo: corto && corto.length <= 4 ? corto : quitaAcentos(nombre).slice(0, 3).toUpperCase(),
          fecha: ini ? mesAnio(ini) : v.anio || '', place: o.place_id,
        });
      }
    }
    return lista;
  }

  // Un país con un solo pin no merece grupo propio: van juntos en «Otros países»
  function agrupar(pines) {
    const porPais = new Map();
    for (const p of pines) { if (!porPais.has(p.pais)) porPais.set(p.pais, []); porPais.get(p.pais).push(p); }
    const grupos = [], sueltos = [];
    for (const [pais, ps] of porPais) (ps.length > 1 ? grupos.push({ nombre: pais, pines: ps }) : sueltos.push(...ps));
    grupos.sort((a, b) => b.pines.length - a.pines.length || a.nombre.localeCompare(b.nombre, 'es'));
    if (sueltos.length) grupos.push({ nombre: 'Otros países', pines: sueltos, otros: true });
    return grupos;
  }

  const S = { pines: [], sel: null, viaje: null };

  const chapa = (p, cls) => p.foto
    ? `<span class="chapa ${cls}"><img src="${esc(p.foto)}" alt="" loading="lazy"></span>`
    : `<span class="chapa ${cls}" data-t="${S.pines.indexOf(p) % 5}">${esc(p.codigo)}</span>`;

  function pintar() {
    $('grupos').innerHTML = agrupar(S.pines).map((g) => `
      <section class="grupo-pais">
        <div class="grupo-cabeza"><h2>${esc(g.nombre)}</h2><span class="num">${g.pines.length}</span></div>
        <div class="fichas-pin">${g.pines.map((p) => `
          <button type="button" class="pin-btn" data-i="${S.pines.indexOf(p)}">
            ${chapa(p, '')}
            <span class="pin-ciudad">${esc(p.ciudad)}</span>
            ${g.otros ? `<span class="pin-pais">${esc(p.pais)}</span>` : ''}
          </button>`).join('')}
        </div>
      </section>`).join('');
    marcar();
  }

  // activo (aria-pressed) y, si se pidió, los del mismo viaje
  function marcar() {
    for (const b of document.querySelectorAll('.pin-btn')) {
      const p = S.pines[+b.dataset.i];
      b.setAttribute('aria-pressed', String(p === S.sel));
      b.classList.toggle('del-viaje', !!S.viaje && p.viaje.id === S.viaje);
    }
  }

  function ficha() {
    const f = $('ficha'), p = S.sel;
    f.hidden = !p;
    if (!p) return;
    const resaltado = S.viaje === p.viaje.id;
    f.innerHTML = `
      <button type="button" class="btn ghost redondo ficha-cerrar" aria-label="Cerrar">${IDENTIDAD.icono('cerrar')}</button>
      <div class="sello"><div class="marco">${chapa(p, 'grande')}</div></div>
      <div class="ficha-texto">
        <p class="kicker">${esc(p.fecha || 'Sin fecha')}</p>
        <h2>${esc(p.ciudad)}</h2>
        <p class="sub">${esc([p.pais, p.viaje.nombre].filter(Boolean).join(' · '))}</p>
      </div>
      <div class="ficha-botones">
        <a class="btn" href="mapa.html?viaje=${p.viaje.id}">Ver en el mapa</a>
        <button type="button" class="btn ghost" id="suViaje" aria-pressed="${resaltado}">Su viaje</button>
      </div>`;
  }

  function elegir(i) {
    S.sel = S.pines[i] || null;
    S.viaje = null;
    ficha();
    marcar();
  }

  async function iniciar() {
    let A;
    try {
      const res = await fetch('data/archivo.json', { cache: 'no-store' });
      if (!res.ok) throw new Error();
      A = await res.json();
    } catch (e) {
      $('count').textContent = '';
      $('notice').textContent = 'No encuentro data/archivo.json. Genera el fichero con «archivo.py exportar web/data/archivo.json» y recarga.';
      $('notice').hidden = false;
      return;
    }
    S.pines = pinesDe(A);
    const ciudades = new Set(S.pines.map((p) => p.place)).size;
    const paises = new Set(S.pines.map((p) => p.pais)).size;
    $('count').textContent = plural(S.pines.length, 'pin', 'pines');
    $('peg').innerHTML = IDENTIDAD.pegatina('pin', 'grande');
    $('contadores').innerHTML = [[S.pines.length, 'pines'], [ciudades, 'ciudades'], [paises, 'países']]
      .map(([n, t]) => `<div><dd class="num">${n}</dd><dt>${t}</dt></div>`).join('');
    if (!S.pines.length) { $('notice').textContent = 'Todavía no hay pines en el archivo.'; $('notice').hidden = false; return; }
    pintar();
    if (!movil.matches) elegir(+document.querySelector('.pin-btn').dataset.i); // en móvil la ficha es una hoja que sale al tocar
  }

  $('grupos').addEventListener('click', (e) => {
    const b = e.target.closest('.pin-btn');
    if (b) elegir(+b.dataset.i);
  });
  $('ficha').addEventListener('click', (e) => {
    if (e.target.closest('.ficha-cerrar')) { elegir(-1); return; }
    if (e.target.closest('#suViaje')) { S.viaje = S.viaje === S.sel.viaje.id ? null : S.sel.viaje.id; ficha(); marcar(); $('suViaje').focus(); }
  });
  addEventListener('keydown', (e) => { if (e.key === 'Escape' && movil.matches && S.sel) elegir(-1); });

  iniciar();
})();
