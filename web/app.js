/* Certificates Archive · pared de lanyards 3D
   Three.js r128. Hay que servir la carpeta (python -m http.server): el navegador
   bloquea data/ e imágenes cuando se abre el HTML directamente desde el disco. */
(() => {
  'use strict';

  const $ = (s) => document.querySelector(s);
  const MESES = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
  const fmtDate = (iso) => {
    if (!iso) return '—';
    const [y, m, d] = iso.split('-');
    if (!m) return y;
    if (!d) return `${MESES[+m - 1]} de ${y}`;
    return `${+d} de ${MESES[+m - 1]} de ${y}`;
  };
  const { pegatina, icono } = window.IDENTIDAD;
  const QUIETO = matchMedia('(prefers-reduced-motion: reduce)');
  // Colores de la pared: salen de los tokens CSS (claro u oscuro), ver docs/diseno/IDENTIDAD.md
  const token = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const num = (v, fallback) => (v === '' || v == null || isNaN(+v)) ? fallback : +v;

  // ------------------------------------------------------------------ datos
  function normalize(r) {
    const fecha = r.fecha || '';
    return {
      id: r.id,
      evento: r.evento || 'Sin título',
      fecha,
      year: fecha.slice(0, 4) || '—',
      lugar: r.lugar || '',
      ciudad: r.ciudad || '',
      organizador: r.organizador || '',
      rol: r.rol || '',
      tipo: r.tipo || 'lanyard',
      forma: r.forma || 'rectangular',
      ancho: num(r.ancho_mm, 85.6),
      alto: num(r.alto_mm, 54),
      agujero: r.agujero_mm || '',
      hasHole: r.anclaje_x !== '' && r.anclaje_x != null,
      ax: num(r.anclaje_x, 0.5),
      ay: num(r.anclaje_y, 0.05),
      front: r.front_web || '',
      back: r.back_web || '',
      avisos: r.avisos || '',
    };
  }

  async function loadData() {
    const res = await fetch('data/archive.json', { cache: 'no-store' });
    if (!res.ok) throw new Error('No encuentro data/archive.json. ¿Has ejecutado sync.py?');
    const raw = await res.json();
    return raw.map(normalize).sort((a, b) => a.fecha.localeCompare(b.fecha) || a.id.localeCompare(b.id));
  }

  // Datos de la base (archivo.py exportar). Opcional: sin él la pared 3D funciona igual.
  // Quedan en window.ARCHIVO para el mapa, la línea del tiempo y la página de personas.
  async function loadArchivo() {
    try {
      const res = await fetch('data/archivo.json', { cache: 'no-store' });
      return res.ok ? await res.json() : null;
    } catch (err) { return null; }
  }

  // ------------------------------------------------------------------ estado
  const S = {
    items: [], cards: [], year: 'all', hovered: null,
    renderer: null, scene: null, camera: null, ray: null, mouse: new THREE.Vector2(-9, -9),
    sheetList: [], sheetIndex: 0, lastHoverId: null, cartelaCard: null, hideTimer: 0, mats: null,
  };

  // ------------------------------------------------------------------ escena
  const SPACING = 1.75, CARD_H = 1.0, RAIL_Y = 3.6, ROW_GAP = 2.45, PER_ROW = innerWidth < 640 ? 3 : 6;
  // shortcut: las filas se fijan al cargar; si se gira el móvil hay que recargar para reordenar

  function layoutPositions(items) {
    const rows = Math.ceil(items.length / PER_ROW) || 1;
    const out = [];
    for (let row = 0; row < rows; row++) {
      const slice = items.slice(row * PER_ROW, row * PER_ROW + PER_ROW);
      slice.forEach((_, col) => {
        const x = (col - (slice.length - 1) / 2) * SPACING;
        const y = 2.2 - row * ROW_GAP;
        out.push({ x, y, rows });
      });
    }
    return out;
  }

  function buildScene(items) {
    const canvas = $('#wall');
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(32, 1, 0.1, 100);
    S.renderer = renderer; S.scene = scene; S.camera = camera; S.ray = new THREE.Raycaster();

    scene.add(new THREE.AmbientLight(0xffffff, 0.8));
    const key = new THREE.SpotLight(0xfff3e0, 1.25, 60, Math.PI / 5, 0.7, 1.1);
    key.position.set(-2, 9, 9); scene.add(key);
    const fill = new THREE.DirectionalLight(0xdfe8ff, 0.35);
    fill.position.set(4, 2, 6); scene.add(fill);

    // carril de cuadros (acero satinado)
    const railMat = new THREE.MeshStandardMaterial({ roughness: 0.35, metalness: 0.6 });
    const rail = new THREE.Mesh(new THREE.BoxGeometry(60, 0.05, 0.05), railMat);
    rail.position.set(0, RAIL_Y, -0.2); scene.add(rail);

    const loader = new THREE.TextureLoader();
    const cordMat = new THREE.LineBasicMaterial({ transparent: true, opacity: 0.85 });
    const nailMat = new THREE.MeshStandardMaterial({ roughness: 0.3, metalness: 0.8 });
    const shadowMat = new THREE.MeshBasicMaterial({ color: 0x000000, map: shadowTexture(), transparent: true, depthWrite: false });
    S.mats = { railMat, cordMat, nailMat, shadowMat };
    paintWall();
    const pos = layoutPositions(items);

    items.forEach((item, i) => {
      const { x, y } = pos[i];
      // cordel desde el carril hasta el clavo
      const cord = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(x, RAIL_Y, -0.1), new THREE.Vector3(x, y, 0.02),
      ]);
      scene.add(new THREE.Line(cord, cordMat));
      const nail = new THREE.Mesh(new THREE.SphereGeometry(0.04, 12, 10), nailMat);
      nail.position.set(x, y, 0.02); scene.add(nail);

      // pivote en el clavo (gira = balanceo) -> soporte -> hoja (gira = anverso/reverso)
      const pivot = new THREE.Group(); pivot.position.set(x, y, 0.02); scene.add(pivot);
      const flip = new THREE.Group(); pivot.add(flip);
      const faceMat = (tex) => new THREE.MeshStandardMaterial({
        map: tex, transparent: true, alphaTest: 0.04, roughness: 0.55, metalness: 0.02, side: THREE.FrontSide,
      });
      // sombra de contacto en la pared: cuelga del pivote, así se balancea con la pieza
      const shadow = new THREE.Mesh(new THREE.PlaneGeometry(1, CARD_H), shadowMat);
      pivot.add(shadow);
      const frontMesh = new THREE.Mesh(new THREE.PlaneGeometry(1, CARD_H), faceMat(null));
      const backMesh = new THREE.Mesh(new THREE.PlaneGeometry(1, CARD_H), faceMat(null));
      backMesh.rotation.y = Math.PI;
      flip.add(frontMesh, backMesh);

      const card = {
        item, i, pivot, flip, frontMesh, backMesh, shadow,
        theta: 0, omega: 0, flipTarget: 0, visibleTarget: 1, scale: 1,
        aspect: item.ancho / item.alto,
      };
      S.cards.push(card);
      setTexture(card, loader, renderer, 'front', item.front);
      setTexture(card, loader, renderer, 'back', item.back);
      applyGeometry(card);
    });

    fit();
  }

  function paintWall() {
    const { railMat, cordMat, nailMat, shadowMat } = S.mats;
    railMat.color.set(token('--wall-rail'));
    cordMat.color.set(token('--wall-cord'));
    nailMat.color.set(token('--wall-nail'));
    shadowMat.opacity = +token('--wall-shadow') || 0.22;
  }

  // mancha difusa que comparten todas las sombras
  function shadowTexture() {
    const c = document.createElement('canvas'); c.width = c.height = 128;
    const g = c.getContext('2d');
    const grad = g.createRadialGradient(64, 64, 10, 64, 64, 64);
    grad.addColorStop(0, 'rgba(255,255,255,1)'); grad.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = grad; g.fillRect(0, 0, 128, 128);
    return new THREE.CanvasTexture(c);
  }

  function setTexture(card, loader, renderer, side, url) {
    if (!url) return;
    loader.load(url, (tex) => {
      tex.minFilter = THREE.LinearFilter;          // sin mipmaps: no requiere potencias de dos
      tex.generateMipmaps = false;
      tex.anisotropy = renderer.capabilities.getMaxAnisotropy();
      const mesh = side === 'front' ? card.frontMesh : card.backMesh;
      mesh.material.map = tex;
      mesh.material.needsUpdate = true;
      if (side === 'front') {
        card.aspect = tex.image.width / tex.image.height;   // medida real de la imagen recortada
        applyGeometry(card);
      }
    }, undefined, () => { /* imagen que falta: se queda la carta en blanco */ });
  }

  // Geometría y agujero: el agujero queda exactamente en el clavo (origen del pivote).
  function applyGeometry(card) {
    const { item, aspect, frontMesh, backMesh, flip } = card;
    const W = CARD_H * aspect;
    frontMesh.geometry.dispose(); backMesh.geometry.dispose();
    frontMesh.geometry = new THREE.PlaneGeometry(W, CARD_H);
    backMesh.geometry = new THREE.PlaneGeometry(W, CARD_H);
    // posición local del agujero respecto al centro de la carta
    const holeX = item.hasHole ? (item.ax - 0.5) * W : 0;
    const holeY = item.hasHole ? (0.5 - item.ay) * CARD_H : CARD_H / 2 - 0.08;
    // el centro de la hoja queda a -hueco del clavo; el giro de la hoja es alrededor de su centro
    flip.position.set(-holeX, -holeY, 0);
    card.shadow.geometry.dispose();
    card.shadow.geometry = new THREE.PlaneGeometry(W * 1.25, CARD_H * 1.3);
    card.shadow.position.set(-holeX + 0.06, -holeY - 0.09, -0.16);   // luz desde arriba a la izquierda
    card.holeOffset = { x: holeX, y: holeY };
  }

  function fit() {
    const canvas = S.renderer.domElement;
    const w = canvas.clientWidth || window.innerWidth, h = canvas.clientHeight || window.innerHeight;
    S.renderer.setSize(w, h, false);
    S.camera.aspect = w / h;
    const rows = Math.max(1, Math.ceil(S.cards.length / PER_ROW));
    // caja que debe caber: desde el carril hasta la base de la fila inferior
    const top = RAIL_Y + 0.45;
    const bottom = 2.2 - (rows - 1) * ROW_GAP - CARD_H - 0.5;
    const cy = (top + bottom) / 2;
    const spanY = top - bottom;
    const spanX = Math.min(S.cards.length, PER_ROW) * SPACING + 1.6;
    const t = Math.tan(THREE.MathUtils.degToRad(S.camera.fov) / 2);
    const z = Math.max((spanY / 2) / t, (spanX / 2) / (t * S.camera.aspect)) + 0.8;
    S.camera.position.set(0, cy, z);
    S.camera.lookAt(0, cy, 0);
    S.camera.updateProjectionMatrix();
  }

  // ------------------------------------------------------------------ física del balanceo
  const G = 7.0, DAMP = 0.9, MAX_THETA = 0.55;
  function step(dt) {
    const damp = QUIETO.matches ? 12 : DAMP;     // menos movimiento: el péndulo se para casi al instante
    for (const c of S.cards) {
      const acc = -G * Math.sin(c.theta) - damp * c.omega;
      c.omega += acc * dt;
      c.theta = THREE.MathUtils.clamp(c.theta + c.omega * dt, -MAX_THETA, MAX_THETA);
      c.pivot.rotation.z = c.theta;
      c.flip.rotation.y += (c.flipTarget - c.flip.rotation.y) * Math.min(1, dt * 9);
      const sTarget = c.visibleTarget;
      c.scale += (sTarget - c.scale) * Math.min(1, dt * 10);
      c.pivot.scale.setScalar(Math.max(0.0001, c.scale));
      c.pivot.visible = c.scale > 0.02;
    }
  }

  // ------------------------------------------------------------------ interacción
  function pick() {
    S.ray.setFromCamera(S.mouse, S.camera);
    const meshes = [];
    for (const c of S.cards) if (c.pivot.visible) meshes.push(c.frontMesh, c.backMesh);
    const hit = S.ray.intersectObjects(meshes, false)[0];
    if (!hit) return null;
    return S.cards.find((c) => c.frontMesh === hit.object || c.backMesh === hit.object) || null;
  }

  function onPointerMove(e) {
    const rect = S.renderer.domElement.getBoundingClientRect();
    S.mouse.set(((e.clientX - rect.left) / rect.width) * 2 - 1, -((e.clientY - rect.top) / rect.height) * 2 + 1);
    const c = pick();
    S.renderer.domElement.classList.toggle('hot', !!c);
    if (c && c !== S.hovered) {
      c.omega += (e.movementX || 0) * 0.004;     // el cursor empuja al entrar: se balancea según cómo llega
      showCartela(c);
    }
    if (!c && S.hovered) hideCartela(true);
    S.hovered = c;
  }

  function onPointerDown(e) {
    const rect = S.renderer.domElement.getBoundingClientRect();
    S.mouse.set(((e.clientX - rect.left) / rect.width) * 2 - 1, -((e.clientY - rect.top) / rect.height) * 2 + 1);
    const c = pick();
    if (!c) return;
    flipCard(c);
    S.hovered = c; showCartela(c);     // en pantallas táctiles no hay hover: el toque también abre la cartela
  }

  function flipCard(c) {
    c.flipTarget = c.flipTarget === 0 ? Math.PI : 0;     // girar y ver el reverso
    c.omega += 0.8 * (Math.random() > 0.5 ? 1 : -1);
  }

  function showCartela(card) {
    clearTimeout(S.hideTimer);
    const item = card.item;
    S.cartelaCard = card;
    if (S.lastHoverId === item.id) return;
    S.lastHoverId = item.id;
    $('#cPeg').innerHTML = pegatina(item.tipo);
    $('#cFecha').textContent = fmtDate(item.fecha);
    $('#cTitle').textContent = item.evento;
    $('#cLugar').textContent = [item.lugar, item.ciudad].filter(Boolean).join(' · ') || item.organizador;
    $('#cartela').classList.add('abierta');
    $('#hint').style.opacity = '0';
  }
  // con margen: da tiempo a llevar el cursor de la pieza a los botones de la cartela
  function hideCartela(conMargen) {
    clearTimeout(S.hideTimer);
    const ocultar = () => {
      if ($('#cartela').matches(':hover, :focus-within')) return;
      S.lastHoverId = null; S.cartelaCard = null;
      $('#cartela').classList.remove('abierta');
      $('#hint').style.opacity = '';
    };
    if (conMargen) S.hideTimer = setTimeout(ocultar, 450); else ocultar();
  }

  // ------------------------------------------------------------------ filtro por año
  function buildChips(items) {
    const years = [...new Set(items.map((i) => i.year))].sort();
    const box = $('#years');
    box.innerHTML = '';
    const make = (label, value, count) => {
      const b = document.createElement('button');
      b.className = 'chip';
      b.setAttribute('aria-pressed', String(S.year === value));
      b.innerHTML = `${label}<small>${count}</small>`;
      b.onclick = () => {
        S.year = value; applyFilter(); buildChips(S.items);
        box.querySelector('[aria-pressed="true"]').focus();   // los chips se rehacen: no perder el foco del teclado
      };
      box.appendChild(b);
    };
    make('Todos', 'all', items.length);
    years.forEach((y) => make(y, y, items.filter((i) => i.year === y).length));
  }

  function applyFilter() {
    let n = 0;
    for (const c of S.cards) {
      const on = S.year === 'all' || c.item.year === S.year;
      c.visibleTarget = on ? 1 : 0;
      if (on) n++;
    }
    $('#count').textContent = `${n} de ${S.items.length} objetos · ${S.year === 'all' ? 'todos los años' : S.year}`;
    hideCartela();
  }

  // ------------------------------------------------------------------ ficha
  function openSheet(item) {
    const visible = S.cards.filter((c) => c.visibleTarget > 0).map((c) => c.item);
    S.sheetList = visible.length ? visible : S.items;
    S.sheetIndex = Math.max(0, S.sheetList.findIndex((i) => i.id === item.id));
    renderSheet();
    $('#sheet').hidden = false;
    $('#sheet .sheet-card').focus();
  }
  function renderSheet() {
    const it = S.sheetList[S.sheetIndex];
    $('#mPeg').innerHTML = pegatina(it.tipo);
    $('#mFecha').textContent = `${fmtDate(it.fecha)} · ${it.tipo}`;
    $('#mTitle').textContent = it.evento;
    const rows = [
      ['Lugar', it.lugar], ['Ciudad', it.ciudad], ['Organizador', it.organizador], ['Rol', it.rol],
      ['Medida', it.ancho && it.alto ? `${it.ancho} × ${it.alto} mm (${it.forma})` : ''],
      ['Orificio', it.agujero ? `ø ${it.agujero.replace(/;/g, ' · ')} mm` : ''],
    ].filter(([, v]) => v);
    $('#mDl').innerHTML = rows.map(([k, v]) => `<dt>${k}</dt><dd>${escapeHtml(v)}</dd>`).join('');
    $('#mWarn').hidden = !it.avisos;
    $('#mWarn').textContent = it.avisos;
    setImg('#imgFront', it.front); setImg('#imgBack', it.back);
    $('#prev').disabled = S.sheetIndex === 0;
    $('#next').disabled = S.sheetIndex >= S.sheetList.length - 1;
  }
  function setImg(sel, src) {
    const el = $(sel);
    el.src = src || ''; el.style.visibility = src ? 'visible' : 'hidden';
  }
  function closeSheet() { $('#sheet').hidden = true; }
  function escapeHtml(s) { return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }

  // ------------------------------------------------------------------ arranque
  function loop(t) {
    const dt = Math.min(0.033, (t - (loop.prev || t)) / 1000);
    loop.prev = t;
    step(dt);
    S.renderer.render(S.scene, S.camera);
    requestAnimationFrame(loop);
  }

  function noWebGL(items) {
    $('#wall').hidden = true; $('#hint').hidden = true;
    const grid = document.createElement('div');
    grid.className = 'notice';
    grid.style.cssText = 'display:flex;flex-wrap:wrap;gap:16px;justify-content:center;align-content:center;overflow:auto;position:absolute;inset:0;padding:24px';
    items.forEach((it) => {
      const img = document.createElement('img');
      img.src = it.front; img.alt = it.evento; img.title = it.evento;
      img.style.cssText = 'height:180px;object-fit:contain;cursor:pointer;filter:drop-shadow(0 10px 14px rgba(0,0,0,.25))';
      img.onclick = () => openSheet(it);
      grid.appendChild(img);
    });
    $('#stage').appendChild(grid);
  }

  function pintarBotones() {
    $('#cOpen').innerHTML = `Ver ficha ${icono('abrir')}`;
    $('#cFlip').innerHTML = icono('girar');
    $('#close').innerHTML = icono('cerrar');
    $('#prev').innerHTML = `${icono('anterior')} Anterior`;
    $('#next').innerHTML = `Siguiente ${icono('siguiente')}`;
  }

  async function start() {
    pintarBotones();
    let items;
    try {
      items = await loadData();
    } catch (err) {
      showNotice(err.message); return;
    }
    S.items = items;
    window.ARCHIVO = S.archivo = await loadArchivo();
    if (!items.length) { showNotice('Todavía no hay objetos en data/archive.json.'); return; }

    buildChips(items);
    if (!window.WebGLRenderingContext || !document.createElement('canvas').getContext('webgl')) {
      noWebGL(items); $('#count').textContent = `${items.length} objetos`; return;
    }
    buildScene(items);
    applyFilter();

    const c = S.renderer.domElement;
    c.addEventListener('pointermove', onPointerMove);
    c.addEventListener('pointerdown', onPointerDown);
    c.addEventListener('pointerleave', () => { S.hovered = null; hideCartela(true); c.classList.remove('hot'); });
    $('#cartela').addEventListener('pointerleave', () => { if (!S.hovered) hideCartela(true); });
    $('#cOpen').onclick = () => S.cartelaCard && openSheet(S.cartelaCard.item);
    $('#cFlip').onclick = () => S.cartelaCard && flipCard(S.cartelaCard);
    matchMedia('(prefers-color-scheme: dark)').addEventListener('change', paintWall);
    window.addEventListener('resize', fit);
    $('#close').onclick = closeSheet;
    $('#sheet').addEventListener('click', (e) => { if (e.target.id === 'sheet') closeSheet(); });
    $('#prev').onclick = () => { if (S.sheetIndex > 0) { S.sheetIndex--; renderSheet(); } };
    $('#next').onclick = () => { if (S.sheetIndex < S.sheetList.length - 1) { S.sheetIndex++; renderSheet(); } };
    document.addEventListener('keydown', (e) => {
      if (!$('#sheet').hidden) {
        if (e.key === 'Escape') closeSheet();
        if (e.key === 'ArrowLeft') $('#prev').click();
        if (e.key === 'ArrowRight') $('#next').click();
        return;
      }
      if (e.key === 'Enter' && S.hovered) { e.preventDefault(); openSheet(S.hovered.item); }
    });
    requestAnimationFrame(loop);
  }

  function showNotice(msg) {
    const n = $('#notice');
    n.hidden = false; n.textContent = msg;
    $('#count').textContent = 'Sin datos';
  }

  start();
})();
