/* Página de evento · docs/features/evento.md. Versión B «Página de cuaderno» (maqueta del lienzo). */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const MES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
  const fecha = (f) => { const [y, m, d] = (f || '').split('-'); return !y ? '' : d ? `${+d} de ${MES[m - 1]} de ${y}` : m ? `${MES[m - 1]} de ${y}` : y; };
  const dur = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
  const peg = (t, extra) => window.IDENTIDAD.pegatina(t, extra);
  const premio = (o) => [o.premio, o.rol, o.nivel].filter(Boolean).join(' · ');
  const tipoObj = (o) => (o.premio ? 'premio' : o.tipo === 'lanyard' ? 'lanyard' : o.tipo === 'pin' ? 'pin' : 'certificado');
  const giro = (i) => ((i * 37) % 7 - 3) * 0.9;   // inclinación fija por posición (no aleatoria: no cambia al recargar)

  // Mismas reglas que intervenciones.js: vídeo local en video/<nombre>.mp4 (H.264) o YouTube si hay url
  const srcDe = (c) => c.url || (c.archivo_local ? 'video/' + encodeURIComponent(c.archivo_local.split(/[\\/]/).pop().replace(/\.[^.]+$/, '')) + '.mp4' : '');
  const youtubeId = (u) => { const m = /(?:youtu\.be\/|youtube\.com\/(?:watch\?(?:.*&)?v=|embed\/|shorts\/))([\w-]{11})/.exec(u || ''); return m && m[1]; };

  // Si una imagen no carga se cambia por la pegatina de su tipo, para no dejar huecos
  document.addEventListener('error', (e) => {
    const i = e.target;
    if (i.tagName !== 'IMG' || !i.dataset.fb || i.dataset.hecho) return;
    i.dataset.hecho = '1'; i.src = window.IDENTIDAD.pegatinaUrl(i.dataset.fb); i.classList.add('ph-img');
  }, true);
  const img = (src, alt, fb) => `<img src="${esc(src)}" alt="${esc(alt)}" loading="lazy" decoding="async" data-fb="${fb}">`;

  function modelo(e, A) {
    const v = (A.viajes || []).find((x) => x.id === e.trip_id) || null;
    e.fotos = e.fotos || []; e.charlas = e.charlas || [];
    const objs = (e.objetos || []).map((o) => ({ ...o, img: o.front_web || '' }));
    const personas = [...new Set((e.fotos || []).flatMap((f) => f.personas || []))];
    const principal = objs.find((o) => o.img);
    const total = objs.length + e.fotos.length + e.charlas.length;
    return { e, v, objs, personas, principal, total, tipo: e.modalidad === 'virtual' ? 'virtual' : 'evento' };
  }

  // «ampl» recoge lo que se puede ampliar: [src grande, texto]; el índice sirve para pasar con las flechas
  function cuaderno(m) {
    const { e, v } = m, ampl = [];
    const abrir = (src, pie) => `data-ampl="${ampl.push([src, pie]) - 1}"`;
    const piezas = [
      ...m.objs.map((o) => {
        const pie = esc(o.titulo) + (premio(o) ? ' · ' + esc(premio(o)) : '');
        if (!o.img) return `<figure class="pola obj sin"><span class="ph">${peg(tipoObj(o))}</span><figcaption>${pie}<span class="sub">${o.tipo === 'certificado' ? 'Certificado por escanear' : 'Sin imagen todavía'}</span></figcaption></figure>`;
        return `<figure class="pola obj"><button type="button" class="ampliar" ${abrir(o.img, o.titulo)} aria-label="Ampliar ${esc(o.titulo)}">${img(o.img, o.titulo, tipoObj(o))}</button><figcaption>${pie}</figcaption></figure>`;
      }),
      ...e.fotos.map((f) => {
        const pie = (f.personas || []).join(' y ') || fecha(f.fecha);
        return `<figure class="pola"><button type="button" class="ampliar" ${abrir(f.web || f.mini, pie)} aria-label="Ampliar foto: ${esc(pie)}">${img(f.mini || f.web, 'Foto del ' + fecha(f.fecha), 'foto')}</button><figcaption>${esc(pie)}</figcaption></figure>`;
      }),
    ].map((h, i) => h.replace('<figure', `<figure style="--r:${giro(i)}deg;--t:${giro(i + 3) * 3}deg"`));

    const notas = e.charlas.map((c, i) => {
      const hay = !!srcDe(c);
      return `<button type="button" class="nota" data-charla="${i}" ${hay ? '' : 'disabled'} aria-expanded="false">${peg('charla')}<b>${esc(c.titulo)}</b><span class="sub num">${esc(fecha(c.fecha))}${c.duracion_s ? ' · ' + dur(c.duracion_s) : ''}${hay ? '' : ' · sin grabación'}</span>${hay ? '<span class="ver">▶ Ver la grabación</span>' : ''}</button>`;
    }).join('');

    const datos = [['Lugar', [e.lugar, e.ciudad, e.pais].filter(Boolean).join(', ')], ['Organizador', e.organizador], ['Categoría', e.categoria], ['Modalidad', e.modalidad]].filter((d) => d[1]);
    const sello = m.principal ? img(m.principal.img, e.nombre, m.tipo) : `<span class="ph">${peg(m.tipo)}</span>`;
    const vuelos = v && (v.vuelos || []).map((x) => `${esc(x.origen.iata)} → ${esc(x.destino.iata)}`).join(' · ');
    const tira = v ? `<aside class="tira glass" aria-label="Viaje"><p class="kicker">Viaje</p><div class="km num">${v.km.toLocaleString('es')} <small>km</small></div><p class="sub">${v.dias} ${v.dias === 1 ? 'día' : 'días'} · ${esc(fecha(v.inicio))}</p><ol>${v.visitas.map((x) => `<li>${esc(x.ciudad)}<span class="sub"> · ${esc(x.pais)}</span></li>`).join('')}</ol>${vuelos ? `<p class="sub">${vuelos}</p>` : ''}</aside>` : '';
    const pobre = m.total < 3;   // variante compacta: una sola columna, la pieza única se ve grande
    const nada = m.total ? '' : '<div class="collage"><p class="nota-suelta">Aún no hay fotos, objetos ni charlas de este evento.</p></div>';
    const html = `<article class="pagina${pobre ? ' compacta' : ''}${tira ? ' con-tira' : ''}"><div class="cuerpo">
      <div class="tit"><div class="sello">${sello}</div>
        <div class="tit-txt"><p class="kicker">${esc(fecha(e.fecha))}</p><h1 id="nombre">${esc(e.nombre)}</h1>
          ${datos.length ? `<dl class="datos">${datos.map((d) => `<div><dt>${d[0]}</dt><dd>${esc(d[1])}</dd></div>`).join('')}</dl>` : ''}</div>
        <div class="peg-flot">${m.principal ? peg(m.tipo) : ''}${m.objs.some((o) => o.premio) ? peg('premio') : ''}</div></div>
      ${piezas.length ? `<div class="collage">${piezas.join('')}</div>` : ''}${nada}
      ${notas ? `<div class="collage notas">${notas}</div><div id="video" class="video" hidden></div>` : ''}
      ${m.personas.length ? `<div class="sec"><p class="kicker gris">${m.personas.length} ${m.personas.length === 1 ? 'persona' : 'personas'} en las fotos</p><div class="personas">${m.personas.map((p) => `<span class="chip">${esc(p)}</span>`).join('')}</div></div>` : ''}
    </div>${tira}</article>`;
    return { html, ampl };
  }

  function video(c, cont) {
    const src = srcDe(c), yt = youtubeId(c.url);
    cont.innerHTML = '';
    if (yt) cont.innerHTML = `<iframe src="https://www.youtube-nocookie.com/embed/${yt}" title="${esc(c.titulo)}" allow="fullscreen; picture-in-picture" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe>`;
    else if (c.url) cont.innerHTML = `<p>Grabación en un enlace externo: <a href="${esc(c.url)}" target="_blank" rel="noopener">abrir el vídeo</a></p>`;
    else {
      const el = document.createElement('video');
      el.controls = true; el.preload = 'metadata'; el.src = src;
      el.addEventListener('error', () => { cont.innerHTML = `<p>No encuentro el vídeo <b>${esc(decodeURIComponent(src.split('/').pop()))}</b>. Créalo con <b>python herramientas/preparar_vercel.py</b></p>`; }, { once: true });
      cont.append(el);
    }
    cont.hidden = false;
  }

  function vacio(txt) {
    $('count').textContent = '';
    $('evento').innerHTML = `<div class="pagina compacta"><div class="cuerpo vacio">${peg('evento')}<h1>${esc(txt)}</h1><p class="sub">Puede que el enlace esté mal o que el evento ya no esté en el archivo.</p><a class="btn" href="index.html">Ir al inicio</a></div></div>`;
  }

  function visor(ampl) {
    const d = $('visor'); let k = 0;
    const ver = (i) => { k = (i + ampl.length) % ampl.length; $('visorImg').src = ampl[k][0]; $('visorImg').alt = ampl[k][1]; $('visorPie').textContent = ampl[k][1]; };
    document.querySelectorAll('[data-ampl]').forEach((b) => b.addEventListener('click', () => { ver(+b.dataset.ampl); d.showModal(); }));
    $('visorCerrar').onclick = () => d.close();
    d.onclick = (e) => { const r = d.getBoundingClientRect(); if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) d.close(); };   // clic fuera de la hoja (el relleno cuenta como dentro)
    d.onkeydown = (e) => { if (ampl.length > 1 && e.key === 'ArrowRight') ver(k + 1); else if (ampl.length > 1 && e.key === 'ArrowLeft') ver(k - 1); };
    d.onclose = () => { const b = document.querySelector(`[data-ampl="${k}"]`); if (b) b.focus({ preventScroll: true }); };
  }

  async function iniciar() {
    let A;
    try { A = await (await fetch('data/archivo.json', { cache: 'no-store' })).json(); }
    catch { $('count').textContent = 'No se pudo leer data/archivo.json (abre la web con un servidor local)'; return; }
    const slug = new URLSearchParams(location.search).get('e');
    const e = slug && (A.eventos || []).find((x) => x.slug === slug);
    if (!e) return vacio(slug ? 'No encuentro ese evento' : 'Falta elegir un evento');
    const { html, ampl } = cuaderno(modelo(e, A));
    document.title = `${e.nombre} · Certificates Archive`;
    $('count').textContent = fecha(e.fecha);
    $('evento').innerHTML = html;
    if (ampl.length) visor(ampl);
    document.querySelectorAll('[data-charla]').forEach((b) => b.addEventListener('click', () => {
      const cont = $('video'), abierta = b.getAttribute('aria-expanded') === 'true';
      document.querySelectorAll('[data-charla]').forEach((x) => x.setAttribute('aria-expanded', 'false'));
      if (abierta) { cont.hidden = true; cont.innerHTML = ''; return; }
      b.setAttribute('aria-expanded', 'true'); video(e.charlas[+b.dataset.charla], cont);
      cont.scrollIntoView({ block: 'nearest', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
    }));
  }
  iniciar();
})();
