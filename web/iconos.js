/* Pegatinas (Fluent Emoji 3D, MIT) e iconos de interfaz. Tabla y reglas: docs/diseno/IDENTIDAD.md §5. */
(() => {
  'use strict';
  const FLUENT = 'https://cdn.jsdelivr.net/gh/microsoft/fluentui-emoji@1ffb34c752ecf5d402f04cfb4b392c77f57c54bc/assets/';
  // entidad -> carpeta de Fluent (el nombre del archivo se deduce de la carpeta)
  const PEGATINAS = {
    evento: 'Spiral calendar', virtual: 'Laptop', lanyard: 'Identification card', certificado: 'Scroll',
    premio: 'Sports medal', pin: 'Round pushpin', sello: 'Brick', foto: 'Camera with flash',
    charla: 'Microphone', viaje: 'Airplane', ciudad: 'Cityscape', aeropuerto: 'Airplane departure',
    persona: 'Busts in silhouette', pais: 'Globe showing europe-africa', estrella: 'Glowing star',
  };
  const url = (tipo) => {
    const carpeta = PEGATINAS[tipo] || PEGATINAS.evento;
    const archivo = carpeta.toLowerCase().replace(/ /g, '_') + '_3d.png';
    return FLUENT + encodeURI(`${carpeta}/3D/${archivo}`);
  };
  // alt vacío: la pegatina acompaña a un texto que ya dice qué es
  const pegatina = (tipo, extra = '') =>
    `<img class="pegatina ${extra}" src="${url(tipo)}" alt="" width="64" height="64" loading="lazy" decoding="async">`;
  const icono = (id) => `<svg class="icono" aria-hidden="true"><use href="img/iconos.svg#${id}"/></svg>`;

  window.IDENTIDAD = { PEGATINAS, pegatinaUrl: url, pegatina, icono };
})();
