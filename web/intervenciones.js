/* Intervenciones en público · docs/features/intervenciones.md */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const MES = new Intl.DateTimeFormat('es', { month: 'long' });
  const TIPOS = { speaker: 'Speaker', mesa: 'Mesa redonda', entrevista: 'Entrevista', pitch: 'Pitch', otro: 'Intervención' };
  const RESUMEN = [['mesa', 'mesa redonda', 'mesas redondas'], ['speaker', 'charla como speaker', 'charlas como speaker'], ['entrevista', 'entrevista', 'entrevistas'], ['pitch', 'pitch', 'pitch'], ['otro', 'otra', 'otras']];

  // Tipo a partir de los datos; "otro" si no se puede deducir (ver la ficha)
  function tipoDe(tipoCharla, texto, rol) {
    if (/entrevista/i.test(texto)) return 'entrevista';
    if (/mesa redonda|taula rodona/i.test(texto) || tipoCharla === 'mesa_redonda') return 'mesa';
    if (tipoCharla === 'keynote' || /speaker/i.test(rol || '')) return 'speaker';
    return tipoCharla === 'pitch' ? 'pitch' : 'otro';
  }

  function recoger(archivo) {
    const out = [];
    for (const e of archivo.eventos || []) {
      const base = { evento: e.nombre, lugar: [e.lugar, e.ciudad].filter(Boolean).join(' · ') };
      if (e.charlas && e.charlas.length) {
        for (const c of e.charlas) {
          out.push({ ...base, fecha: c.fecha || e.fecha, tipo: tipoDe(c.tipo, `${c.titulo} ${e.nombre}`), titulo: c.titulo || '', local: c.archivo_local, url: c.url });
        }
        continue;
      }
      const o = (e.objetos || []).find((x) => /ponente|speaker/i.test(`${x.rol} ${x.premio}`));
      if (o) out.push({ ...base, fecha: e.fecha, tipo: tipoDe('', e.nombre, `${o.rol} ${o.premio}`) });
    }
    return out.sort((a, b) => b.fecha.localeCompare(a.fecha));
  }

  // El navegador no abre rutas locales: la web usa web/video/<nombre sin extensión>.mp4 (H.264), que crea
  // herramientas/preparar_vercel.py desde el original (los .MOV del iPhone son HEVC y muchos navegadores no los abren)
  const srcDe = (i) => i.url || (i.local ? 'video/' + encodeURIComponent(i.local.split(/[\\/]/).pop().replace(/\.[^.]+$/, '')) + '.mp4' : '');
  // Enlaces de YouTube (también no listados) se incrustan; otros enlaces solo se abren aparte
  function youtubeId(u) { const m = /(?:youtu\.be\/|youtube\.com\/(?:watch\?(?:.*&)?v=|embed\/|shorts\/))([\w-]{11})/.exec(u || ''); return m && m[1]; }
  function fechaDe(f) {
    const [y, m, d] = f.split('-');
    const mes = MES.format(new Date(+y, +m - 1, 1));
    return { mes: mes[0].toUpperCase() + mes.slice(1), anio: y, dia: d ? +d : '' };
  }

  function resumen(items) {
    const n = (t) => items.filter((i) => i.tipo === t).length;
    const celdas = [[items.length, items.length === 1 ? 'intervención' : 'intervenciones'], ...RESUMEN.filter(([t]) => n(t)).map(([t, uno, varios]) => [n(t), n(t) === 1 ? uno : varios])];
    $('resumen').innerHTML = window.IDENTIDAD.pegatina('charla') +
      `<dl class="cifras">${celdas.map(([v, nombre]) => `<div class="cifra"><dd class="num">${v}</dd><dt>${nombre}</dt></div>`).join('')}</dl>`;
  }

  function elegir(items, k, filas) {
    const i = items[k], f = fechaDe(i.fecha), src = srcDe(i), v = $('video');
    filas.forEach((b, j) => b.setAttribute('aria-current', j === k));
    $('dFecha').textContent = `${f.mes} de ${f.anio}`;
    $('dEvento').textContent = i.evento;
    $('dLugar').textContent = [i.titulo, i.lugar, TIPOS[i.tipo]].filter(Boolean).join(' · ');   // el título distingue varias charlas del mismo evento
    const aviso = (t) => { v.innerHTML = `<span class="kick">Grabación del móvil</span><p>${t}</p>`; };
    v.innerHTML = '';
    const yt = youtubeId(i.url);
    if (!src) aviso('Sin grabación todavía');
    else if (yt) v.innerHTML = `<iframe src="https://www.youtube-nocookie.com/embed/${yt}" title="${esc(i.evento)}" allow="fullscreen; picture-in-picture" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe>`;
    else if (i.url) aviso('Esta grabación está en un enlace externo: usa «Abrir el vídeo»');
    else {
      const el = document.createElement('video');
      el.controls = true; el.preload = 'metadata'; el.src = src;
      el.addEventListener('error', () => aviso(`No encuentro el vídeo <b>${esc(decodeURIComponent(src.split('/').pop()))}</b>. Créalo con <b>python herramientas/preparar_vercel.py</b>`), { once: true });
      v.append(el);
    }
    const a = $('dAbrir');
    if (src) { a.href = src; a.removeAttribute('aria-disabled'); } else { a.removeAttribute('href'); a.setAttribute('aria-disabled', 'true'); }
  }

  async function iniciar() {
    let archivo;
    try { archivo = await (await fetch('data/archivo.json', { cache: 'no-store' })).json(); }
    catch { $('count').textContent = 'No se pudo leer data/archivo.json (abre la web con un servidor local)'; return; }
    const items = recoger(archivo);
    $('count').textContent = `${items.length} ${items.length === 1 ? 'intervención' : 'intervenciones'}`;
    resumen(items);
    if (!items.length) { $('vacio').hidden = false; return; }
    $('lista').innerHTML = items.map((i) => {
      const f = fechaDe(i.fecha);
      return `<li><button type="button" class="fila"><span class="fecha"><b>${f.mes} · ${f.anio}</b><span>día ${f.dia}</span></span>` +
        `<span class="donde"><b>${esc(i.evento)}</b>${i.titulo || i.lugar ? `<span>${esc(i.titulo || i.lugar)}</span>` : ''}</span><span class="pastilla">${TIPOS[i.tipo]}</span></button></li>`;
    }).join('');
    const filas = [...document.querySelectorAll('.fila')];
    filas.forEach((b, k) => b.addEventListener('click', () => elegir(items, k, filas)));
    $('detalle').hidden = false;
    elegir(items, 0, filas);
  }
  iniciar();
})();
