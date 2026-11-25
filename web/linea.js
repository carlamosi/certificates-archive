/* Línea del tiempo: río horizontal y salas por año. Ficha: docs/features/linea-del-tiempo.md */
(() => {
  'use strict';

  const MES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
  const parse = (s) => { const [y, m, d] = String(s).split('-').map(Number); return { y, m, d }; };
  // «2025» o «2025-03» (sin día) se colocan a mitad de periodo
  const dias = (s) => { const { y, m, d } = parse(s); return Date.UTC(y, (m || 7) - 1, d || (m ? 15 : 1)) / 864e5; };
  const fmt = (s, corto) => { const { y, m, d } = parse(s); return [d, m && MES[m - 1], !corto && y].filter(Boolean).join(' ') || '—'; };
  const num = (n) => Number(n).toLocaleString('es');
  const plural = (n, a, b) => `${num(n)} ${n === 1 ? a : b}`;

  // ------------------------------------------------------------------ datos (sin DOM: se prueba con node)
  // Une eventos, viajes y objetos sueltos con fecha en una sola lista ordenada.
  function unir(A) {
    const items = [];
    (A.eventos || []).forEach((e) => {
      if (!e.fecha) return;
      const objs = e.objetos || [], fotos = e.fotos || [], charlas = e.charlas || [];
      const prem = objs.map((o) => o.premio).filter(Boolean);
      const cont = [objs.length && plural(objs.length, 'objeto', 'objetos'), fotos.length && plural(fotos.length, 'foto', 'fotos'),
        charlas.length && plural(charlas.length, 'charla', 'charlas')].filter(Boolean).join(' · ');
      items.push({ k: 'e', f: e.fecha, titulo: e.nombre, sub: [e.ciudad, e.pais].filter(Boolean).join(', '), prem: prem.length > 0, premTxt: prem[0] || '',
        fot: fotos.length, cert: objs.some((o) => o.tipo === 'certificado'), peg: e.modalidad === 'virtual' ? 'virtual' : prem.length ? 'premio' : 'evento',
        tipo: 'Evento', link: 'Ver el evento', href: `evento.html?e=${encodeURIComponent(e.slug)}`,
        imgs: [...objs.filter((o) => o.front_web).map((o) => ({ src: o.front_web, o: 1 })), ...fotos.slice(0, 2).filter((f) => f.mini).map((f) => ({ src: f.mini }))],
        det: [['Fecha', fmt(e.fecha)], ['Lugar', [e.lugar, e.ciudad, e.pais].filter(Boolean).join(', ')], ['Modalidad', e.modalidad], ['Categoría', e.categoria], ['Contiene', cont], ['Premios', prem.join(' · ')]] });
    });
    (A.viajes || []).forEach((v) => {
      if (!v.inicio) return;
      const ciu = [...new Set((v.visitas || []).map((x) => x.ciudad))], fut = v.estado === 'futuro';
      items.push({ k: 'v', f: v.inicio, fin: v.fin, titulo: v.nombre, sub: '', tag: v.km ? num(v.km) + ' km' : '', km: fut ? 0 : v.km || 0, fut, prem: false, fot: 0, cert: false,
        peg: 'viaje', tipo: fut ? 'Viaje · próximo' : 'Viaje', link: 'Ver en el mapa', href: `mapa.html#viaje=${encodeURIComponent(v.slug)}`, imgs: [],
        det: [['Fechas', v.fin && v.fin !== v.inicio ? `${fmt(v.inicio)} – ${fmt(v.fin)}` : fmt(v.inicio)], ['Distancia', v.km ? num(v.km) + ' km' : ''],
          ['Ciudades', ciu.slice(0, 8).join(', ') + (ciu.length > 8 ? ` y ${ciu.length - 8} más` : '')]] });
    });
    (A.objetos_sueltos || []).forEach((o) => {
      if (!o.fecha) return;   // los pines no tienen fecha
      items.push({ k: 'c', f: o.fecha, titulo: o.titulo, sub: o.premio || o.categoria || '', prem: !!o.premio, premTxt: o.premio, fot: 0, cert: true,
        peg: o.premio ? 'premio' : 'certificado', tipo: 'Certificado', link: 'Ver el certificado', href: 'certificados.html',
        imgs: o.front_web ? [{ src: o.front_web, o: 1 }] : [], det: [['Fecha', fmt(o.fecha)], ['Premio', o.premio], ['Categoría', o.categoria]] });
    });
    items.forEach((i) => { i.y = parse(i.f).y; });
    items.sort((a, b) => dias(a.f) - dias(b.f));
    items.forEach((i, n) => { i.n = n; });
    return { items, years: [...new Set(items.map((i) => i.y))] };
  }
  const CH = [['e', 'Eventos'], ['v', 'Viajes'], ['c', 'Certificados'], ['p', 'Premios'], ['f', 'Fotos']];
  const test = (c, i) => ({ e: i.k === 'e', v: i.k === 'v', c: i.cert, p: i.prem, f: i.fot > 0 }[c]);

  if (typeof module !== 'undefined') module.exports = { unir, dias, fmt, test, CH };
  if (typeof document === 'undefined') return;

  // ------------------------------------------------------------------ página
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const peg = (t, extra) => IDENTIDAD.pegatina(t, extra);
  const suave = matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
  let items = [], years = [], sinFecha = 0, vista = 'rio', ultimo, colocado = false;
  const on = new Set(), OFF = {}, det = $('#detalle');
  const match = (i) => !on.size || [...on].some((c) => test(c, i));

  function controles() {
    $('#filtros').insertAdjacentHTML('beforeend', CH.map(([k, t]) =>
      `<button type="button" class="chip fch" data-f="${k}" aria-pressed="false">${t} <small>${items.filter((i) => test(k, i)).length}</small></button>`).join(''));
    $('#anios').insertAdjacentHTML('beforeend', years.map((y) => `<button type="button" class="chip fch anio" data-y="${y}">${y}</button>`).join(''));
  }
  function aplicar() {
    $$('[data-id]').forEach((b) => { const ok = match(items[b.dataset.id]); b.classList.toggle('off', !ok); b.tabIndex = ok ? 0 : -1; });
    $$('.sala').forEach((s) => { s.hidden = !$('.fila:not(.off)', s); });
    $$('.vitrina').forEach((v) => { v.hidden = !$('.tile:not(.off)', v); });   // sin piezas visibles no se deja el marco vacío
    $$('[data-f]').forEach((b) => b.setAttribute('aria-pressed', on.has(b.dataset.f)));
    $('#cuenta').textContent = `${items.filter(match).length} de ${items.length} hitos con fecha · ${sinFecha} objetos sin fecha no salen aquí`;
  }

  // ---- detalle (panel inferior, compartido) ----
  function abrir(b) {
    const i = items[b.dataset.id], im = i.imgs[0];
    det.innerHTML = `<button type="button" class="x" aria-label="Cerrar">✕</button>
      <div class="cabd">${im ? `<img class="m" src="${esc(im.src)}" data-fb="1" alt="">` : peg(i.peg)}<p class="kicker">${esc(i.tipo)} · ${esc(fmt(i.f))}</p></div>
      <h3>${esc(i.titulo)}</h3><dl>${i.det.filter((d) => d[1]).map((d) => `<dt>${d[0]}</dt><dd>${esc(d[1])}</dd>`).join('')}</dl>
      <a class="btn" href="${esc(i.href)}">${esc(i.link)}</a>`;
    det.hidden = false; det.style.animation = 'none'; void det.offsetWidth; det.style.animation = '';
    ultimo = b; $('.x', det).focus();
  }
  function cerrar() { if (det.hidden) return; det.hidden = true; if (ultimo && ultimo.isConnected) ultimo.focus(); }
  // si falta una imagen, el panel cae a la pegatina del tipo
  document.addEventListener('error', (e) => {
    const t = e.target;
    if (t.tagName === 'IMG' && t.dataset.fb && t.closest('.detalle')) { t.outerHTML = peg(items[ultimo.dataset.id].peg); }
    else if (t.tagName === 'IMG' && t.dataset.fb) { t.closest('.tile')?.remove(); }
  }, true);

  // ---- A · río horizontal ----
  function construirRio() {
    const ys = []; for (let y = Math.min(...years); y <= Math.max(...years); y++) ys.push(y);
    const cnt = (y) => items.filter((i) => i.y === y).length, max = Math.max(...ys.map(cnt)), W = {}; let tot = 0;
    ys.forEach((y) => { OFF[y] = tot; W[y] = 300 + 34 * cnt(y); tot += W[y]; });
    const X = (s, y) => OFF[y] + Math.min(1, Math.max(0, (dias(s) - Date.UTC(y, 0, 1) / 864e5) / 365)) * W[y];
    items.forEach((i) => { i.x0 = X(i.f, i.y); i.x1 = i.fin ? X(i.fin, i.y) : i.x0; });
    // reparte en carriles para que nada se solape
    const carriles = (lista, izq, ancho, hueco) => { const fin = []; lista.forEach((i) => { const L = izq(i); let n = fin.findIndex((e) => e <= L); if (n < 0) n = fin.length; fin[n] = L + ancho(i) + hueco; i.l = n; }); return fin.length; };
    const T = items.filter((i) => i.k === 'v'), E = items.filter((i) => i.k === 'e'), C = items.filter((i) => i.k === 'c');
    const nt = carriles(T, (i) => i.x0, (i) => Math.max(i.x1 - i.x0, 44), 6), ne = carriles(E, (i) => i.x0 - 22, () => 150, 4), nc = carriles(C, (i) => i.x0 - 22, () => 44, 2);
    const yT = 84, eje = yT + nt * 44 + 22, yE = eje + 26, yC = yE + ne * 50 + 14, H = yC + nc * 46 + 24;
    const lbl = (i) => `aria-label="${esc(i.titulo)}, ${esc(fmt(i.f))}"`;
    $('#pista').style.cssText = `width:${tot}px;height:${H}px`;
    $('#pista').innerHTML = ys.map((y) => `<div class="est" style="left:${OFF[y]}px;width:${W[y]}px"><div class="et"><b class="num">${y}</b><span class="sub">${cnt(y) ? plural(cnt(y), 'hito', 'hitos') : 'sin hitos'}</span><i class="med"><i style="width:${cnt(y) / max * 100}%"></i></i></div>
        <div class="tk" style="top:${eje - 4}px;--mes:${W[y] / 12}px"></div></div>`).join('') + `<div class="eje" style="top:${eje}px;width:${tot}px"></div>` +
      T.map((i) => `<button type="button" class="viaje${i.fut ? ' fut' : ''}" data-id="${i.n}" title="${esc(i.titulo)}" style="left:${i.x0}px;top:${yT + i.l * 44 + 4}px;width:${Math.max(i.x1 - i.x0, 44)}px" ${lbl(i)}>${peg('viaje')}<span>${esc(i.titulo)}</span></button>`).join('') +
      E.map((i) => `<i class="stem" style="left:${i.x0}px;top:${eje}px;height:${yE + i.l * 50 - eje}px"></i><i class="dot" style="left:${i.x0}px;top:${eje}px"></i><button type="button" class="ev" data-id="${i.n}" style="left:${i.x0 - 22}px;top:${yE + i.l * 50}px" ${lbl(i)}>${peg(i.peg)}<span>${esc(i.titulo)}</span></button>`).join('') +
      C.map((i) => `<button type="button" class="ce" data-id="${i.n}" title="${esc(i.titulo)}" style="left:${i.x0 - 22}px;top:${yC + i.l * 46}px" ${lbl(i)}>${peg(i.peg)}</button>`).join('');
  }

  // ---- B · salas por año ----
  function construirSalas() {
    $('#vista-salas').innerHTML = years.map((y) => {
      const L = items.filter((i) => i.y === y), vit = L.filter((i) => i.imgs.length).sort((a, b) => b.prem - a.prem).slice(0, 6);
      const cif = [[L.filter((i) => i.k === 'e').length, 'eventos'], [L.filter((i) => i.k === 'v').length, 'viajes'], [L.reduce((s, i) => s + (i.km || 0), 0), 'km'],
        [L.filter((i) => i.cert).length, 'certificados'], [L.filter((i) => i.prem).length, 'premios'], [L.reduce((s, i) => s + i.fot, 0), 'fotos']];
      return `<article class="sala glass" id="sala-${y}" aria-label="Sala ${y}"><div class="cab"><h2 class="gran num">${y}</h2><div class="cifras">${cif.filter((c) => c[0]).map((c) => `<div><b class="num">${num(c[0])}</b><span class="sub">${c[1]}</span></div>`).join('')}</div></div>
        <div class="vitrina">${vit.map((i) => { const im = i.imgs[0]; return `<button type="button" class="tile ${im.o ? 'sello' : 'foto'}" data-id="${i.n}" aria-label="${esc(i.titulo)}"><img src="${esc(im.src)}" data-fb="1" loading="lazy" alt=""></button>`; }).join('')}</div>
        <ol class="lista">${L.map((i) => `<li><button type="button" class="fila" data-id="${i.n}"><span class="sub num">${esc(fmt(i.f, 1))}</span>${peg(i.peg)}<span class="t">${esc(i.titulo)}${i.sub ? `<small>${esc(i.sub)}</small>` : ''}</span>
          ${i.fut ? '<span class="tag prox">Próximo</span>' : i.tag || i.premTxt ? `<span class="tag">${esc(i.tag || i.premTxt)}</span>` : ''}</button></li>`).join('')}</ol></article>`;
    }).join('');
  }

  // ---- conmutador de vista: #rio / #salas, y localStorage ----
  function mostrar(v, guardar) {
    vista = v;
    $('#vista-rio').hidden = v !== 'rio'; $('#vista-salas').hidden = v !== 'salas';
    $$('[data-vista]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.vista === v)));
    if (guardar) {
      try { history.replaceState(null, '', '#' + v); } catch (e) { /* sin historial: no pasa nada */ }
      try { localStorage.setItem('linea-vista', v); } catch (e) { /* almacenamiento bloqueado */ }
    }
    // la primera vez abre en el año anterior al último; después respeta donde estabas
    if (v === 'rio' && !colocado) { colocado = true; $('#carril').scrollLeft = OFF[Math.max(...years) - 1] || 0; }
  }
  function vistaInicial() {
    const h = location.hash.slice(1);
    if (h === 'rio' || h === 'salas') return h;
    try { const g = localStorage.getItem('linea-vista'); if (g === 'rio' || g === 'salas') return g; } catch (e) { /* sin almacenamiento */ }
    return 'rio';
  }

  document.addEventListener('click', (e) => {
    const f = e.target.closest('[data-f]'), y = e.target.closest('[data-y]'), v = e.target.closest('[data-vista]'), b = e.target.closest('[data-id]');
    if (v) mostrar(v.dataset.vista, true);
    else if (f) { on.has(f.dataset.f) ? on.delete(f.dataset.f) : on.add(f.dataset.f); aplicar(); }
    else if (y) {
      if (vista === 'rio') $('#carril').scrollTo({ left: OFF[y.dataset.y], behavior: suave });
      else $('#sala-' + y.dataset.y)?.scrollIntoView({ behavior: suave, block: 'start' });
    } else if (b) abrir(b);
    else if (e.target.closest('.x')) cerrar();
    else if (!e.target.closest('#detalle')) cerrar();
  });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') cerrar(); });
  window.addEventListener('hashchange', () => { const h = location.hash.slice(1); if ((h === 'rio' || h === 'salas') && h !== vista) mostrar(h, false); });

  async function iniciar() {
    let A;
    try {
      const res = await fetch('data/archivo.json', { cache: 'no-store' });
      if (!res.ok) throw new Error(res.status);
      A = await res.json();
    } catch (err) {
      $('#count').textContent = 'Sin datos';
      const n = $('#notice'); n.hidden = false;
      n.textContent = 'No encuentro data/archivo.json. Genera el fichero con «archivo.py exportar web/data/archivo.json» y recarga.';
      return;
    }
    ({ items, years } = unir(A));
    sinFecha = (A.objetos_sueltos || []).filter((o) => !o.fecha).length;
    $('#count').textContent = `${items.length} hitos`;
    controles(); construirRio(); construirSalas(); aplicar();
    mostrar(vistaInicial(), false);
  }
  iniciar();
})();
