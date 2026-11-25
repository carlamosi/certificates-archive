/* Premios (vitrina). Ficha: docs/features/premios.md */
(() => {
  'use strict';

  // clave sin acentos -> estante (el orden es el de la vitrina)
  const NIVELES = [
    { clave: 'primer premio', nombre: 'Primer premio', resumen: 'primeros premios', css: 'm-primer' },
    { clave: 'podio', nombre: 'Podio', resumen: 'podio', css: 'm-podio' },
    { clave: 'finalista', nombre: 'Finalista', resumen: 'finalistas', css: 'm-finalista' },
    { clave: 'mencion', nombre: 'Mención', resumen: 'menciones', css: 'm-mencion' },
  ];
  const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
  const norm = (s) => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();

  // ------------------------------------------------------------------ datos (sin DOM: se prueba con node)
  function premios(A) {
    const todos = [...(A.eventos || []).flatMap((e) => (e.objetos || []).map((o) => ({ ...o, slug: e.slug }))), ...(A.objetos_sueltos || [])];
    return todos
      .map((o) => ({ o, n: NIVELES.find((x) => x.clave === norm(o.nivel)) }))
      .filter((x) => x.n)
      .map(({ o, n }) => ({ ...o, nivelDef: n }))
      .sort((a, b) => (b.fecha || '').localeCompare(a.fecha || ''));   // shortcut: «2025» queda tras «2025-03»; basta con los datos de hoy
  }
  function contar(lista) {
    const porAnio = {};
    lista.forEach((p) => { const a = (p.fecha || '').slice(0, 4) || 's/f'; porAnio[a] = (porAnio[a] || 0) + 1; });
    return {
      total: lista.length,
      niveles: NIVELES.map((n) => ({ ...n, n: lista.filter((p) => p.nivelDef === n).length })),
      anios: Object.entries(porAnio).sort((a, b) => b[0].localeCompare(a[0])),
    };
  }
  function fechaTxt(f) {
    const [a, m, d] = String(f || '').split('-');
    if (!a) return 'Sin fecha';
    if (!m) return a;
    return d ? `${+d} de ${MESES[+m - 1]} de ${a}` : `${MESES[+m - 1][0].toUpperCase()}${MESES[+m - 1].slice(1)} de ${a}`;
  }
  if (typeof module !== 'undefined') module.exports = { premios, contar, fechaTxt };
  if (typeof document === 'undefined') return;

  // ------------------------------------------------------------------ página
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  let lista = [], sel = null, ultimoBoton = null;

  function pintar() {
    const c = contar(lista);
    $('count').textContent = `${c.total} premios`;
    $('total').textContent = c.total;
    $('peg').innerHTML = IDENTIDAD.pegatina('premio');
    $('niveles').innerHTML = c.niveles.map((n) =>
      `<div class="${n.css}"><span class="metal-punto"></span><span><dd>${n.n}</dd><dt>${n.resumen}</dt></span></div>`).join('');
    const max = Math.max(1, ...c.anios.map((a) => a[1]));
    $('anios').innerHTML = c.anios.map(([a, n]) =>
      `<div class="anio"><b>${esc(a)}</b><span class="barra"><i style="width:${Math.round((n / max) * 100)}%"></i></span><span>${n}</span></div>`).join('');

    $('vitrina').innerHTML = NIVELES.map((nv) => {
      const ps = lista.filter((p) => p.nivelDef === nv);
      const medallas = ps.map((p) => {
        const i = lista.indexOf(p), f = fechaTxt(p.fecha);
        return `<button type="button" class="medalla ${nv.css}" data-i="${i}" aria-pressed="false" aria-label="${esc(`${nv.nombre}: ${p.titulo}, ${f}`)}">
          <span class="disco"><span class="cinta"></span><span class="oro">${p.fecha ? `’${esc(p.fecha.slice(2, 4))}` : ''}</span></span>
          <span class="nombre">${esc(p.titulo)}</span></button>`;
      }).join('');
      return `<section class="estante"><p class="kicker estante-t">${nv.nombre} <span>· ${ps.length}</span></p>
        <div class="fila">${medallas || '<p class="vacio">Aún no hay premios aquí.</p>'}</div><span class="tabla"></span></section>`;
    }).join('');
  }

  function elegir(i, btn) {
    sel = i; ultimoBoton = btn;
    const p = lista[i], nv = p.nivelDef;
    document.querySelectorAll('.medalla').forEach((b) => b.setAttribute('aria-pressed', String(+b.dataset.i === i)));
    $('fFecha').textContent = fechaTxt(p.fecha);
    $('fTitulo').textContent = p.titulo;
    $('fOrg').textContent = p.organizador || 'Organizador sin anotar';
    $('fMetal').className = `metal-punto ${nv.css}`;
    $('fNivel').textContent = nv.nombre;
    $('fPremio').textContent = p.premio ? `«${p.premio}»` : '';
    const ver = $('fVer');
    ver.disabled = !p.front_web;
    ver.textContent = p.front_web ? 'Ver el certificado' : 'Por escanear';
    $('fEvt').hidden = !p.slug; if (p.slug) $('fEvt').href = `evento.html?e=${encodeURIComponent(p.slug)}`;
    $('ficha').hidden = false;
    const r = btn.getBoundingClientRect();
    const movil = matchMedia('(max-width: 760px)').matches;   // en móvil la ficha va siempre abajo y la medalla sube
    $('ficha').classList.toggle('arriba', !movil && r.top + r.height / 2 > innerHeight / 2);
    if (movil && r.bottom > innerHeight - 300) btn.scrollIntoView({ block: 'start', behavior: 'instant' });
  }
  function cerrarFicha() {
    if (sel == null) return;
    $('ficha').hidden = true;
    document.querySelectorAll('.medalla').forEach((b) => b.setAttribute('aria-pressed', 'false'));
    if (ultimoBoton) ultimoBoton.focus();
    sel = null;
  }
  function abrirVisor() {
    const p = lista[sel];
    if (!p || !p.front_web) return;
    $('vImg').src = p.front_web;
    $('vImg').alt = `Certificado: ${p.titulo}, ${p.premio || p.nivelDef.nombre}`;
    $('visor').hidden = false;
    $('vCerrar').focus();
  }
  function cerrarVisor() { $('visor').hidden = true; $('fVer').focus(); }

  function eventos() {
    $('vitrina').addEventListener('click', (e) => {
      const b = e.target.closest('.medalla');
      if (b) elegir(+b.dataset.i, b);
    });
    // flechas: recorren todas las medallas en orden de lectura
    $('vitrina').addEventListener('keydown', (e) => {
      const d = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
      const b = e.target.closest('.medalla');
      if (!d || !b) return;
      const bs = [...document.querySelectorAll('.medalla')];
      const sig = bs[bs.indexOf(b) + d];
      if (sig) { e.preventDefault(); sig.focus(); }
    });
    $('fCerrar').addEventListener('click', cerrarFicha);
    $('fVer').addEventListener('click', abrirVisor);
    $('vCerrar').addEventListener('click', cerrarVisor);
    $('visor').addEventListener('click', (e) => { if (e.target === $('visor')) cerrarVisor(); });
    document.addEventListener('keydown', (e) => {
      if (e.key !== 'Escape') return;
      if (!$('visor').hidden) cerrarVisor(); else cerrarFicha();
    });
  }

  async function iniciar() {
    try {
      const res = await fetch('data/archivo.json', { cache: 'no-store' });
      if (!res.ok) throw new Error(res.status);
      lista = premios(await res.json());
    } catch (err) {
      $('count').textContent = 'Sin datos';
      const n = $('notice');
      n.hidden = false;
      n.textContent = 'No encuentro data/archivo.json. Genera el fichero con «archivo.py exportar web/data/archivo.json» y recarga.';
      return;
    }
    pintar();
    eventos();
  }
  iniciar();
})();
