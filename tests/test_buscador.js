// Prueba de la búsqueda global (web/buscador.js). Uso: node tests/test_buscador.js
const assert = require('assert');
const { norm, indice, buscar } = require('../web/buscador.js');

assert.strictEqual(norm('  Ciència, ÑU-Zürich! '), 'ciencia nu zurich');

const A = {
  eventos: [
    { slug: 'e1', nombre: 'Women in Tech Global Europe Awards', fecha: '2026-11-20', ciudad: 'París', pais: 'Francia',
      objetos: [{ uid: 'c1', tipo: 'certificado', titulo: 'Aspiring Teen Award', nivel: 'primer premio', fecha: '2026-11-20' }],
      charlas: [{ titulo: 'Entrega del premio', fecha: '2026-11-20' }],
      fotos: [{ personas: ['Íria Prueba'] }] },
  ],
  viajes: [{ id: 7, nombre: 'Premios (París)', inicio: '2026-11-18',
    visitas: [{ ciudad: 'París', pais: 'Francia' }],
    objetos: [{ uid: 'p1', tipo: 'pin', titulo: 'Torre Eiffel', fecha: '2026-11-19' }, { uid: 's1', tipo: 'sello', titulo: '', sitio: 'LEGO Store Paris' }] }],
  objetos_sueltos: [{ uid: 'c1', tipo: 'certificado', titulo: 'Duplicado' }, { uid: 'c2', tipo: 'certificado', titulo: 'Curso de robótica' }],
  personas: [{ nombre: 'Íria Prueba', fotos: 1 }, { nombre: 'Sin Fotos', fotos: 0 }],
  totales: { ciudades: [{ nombre: 'París', pais: 'Francia', visitas: 2 }], paises: [{ pais: 'Francia' }] },
};
const items = indice(A);
const de = (txt) => Object.fromEntries(buscar(items, txt).map((g) => [g.tipo, g.items]));
const una = (txt, tipo) => de(txt)[tipo][0];

assert.deepStrictEqual(buscar(items, '   '), []);                              // vacío: sin resultados
assert.deepStrictEqual(buscar(items, 'zzzz'), []);                             // nada que coincida
assert.strictEqual(items.filter((i) => i.titulo === 'Duplicado').length, 0);   // mismo uid = un solo objeto
assert.ok(de('PARIS').viaje && de('paris').lugar);                             // sin acentos ni mayúsculas
assert.ok(de('paris').evento);                                                 // el evento es de París (campo secundario)
assert.strictEqual(una('iria', 'persona').href, 'evento.html?e=e1');          // persona -> evento de su foto
assert.strictEqual(una('aspiring', 'premio').href, 'evento.html?e=e1');        // certificado con nivel = premio
assert.strictEqual(una('robotica', 'certificado').href, 'certificados.html');
assert.strictEqual(una('eiffel', 'pin').href, 'mapa.html?viaje=7');
assert.strictEqual(una('lego', 'sello').titulo, 'LEGO Store Paris');           // sin título: usa el sitio
assert.strictEqual(una('entrega', 'charla').href, 'evento.html?e=e1');
assert.ok(una('2026 women', 'evento').titulo.startsWith('Women'));             // por palabras, en cualquier campo
assert.strictEqual(de('women xyz').evento, undefined);                         // todas las palabras deben coincidir
assert.ok(buscar(items, 'a', 1).every((g) => g.items.length <= 1));            // máximo por grupo
console.log('test_buscador: OK');
