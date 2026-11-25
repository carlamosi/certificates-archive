// Prueba de la unión de datos de la línea del tiempo (web/linea.js). Uso: node tests/test_linea.js
const assert = require('assert');
const { unir, test } = require('../web/linea.js');

const A = {
  eventos: [
    { slug: 'b', nombre: 'B', fecha: '2025-03', modalidad: 'virtual', objetos: [{ tipo: 'certificado', premio: 'Oro', front_web: 'img/x.webp' }], fotos: [{ mini: 'img/f.webp' }], charlas: [] },
    { slug: 'sin-fecha', nombre: 'S', fecha: '', objetos: [], fotos: [], charlas: [] },
  ],
  viajes: [{ slug: 'v', nombre: 'V', inicio: '2024-08', fin: '2024-08', estado: 'futuro', km: 100, visitas: [] }],
  objetos_sueltos: [{ titulo: 'C', fecha: '2019-02-10', tipo: 'certificado' }, { titulo: 'Pin', fecha: '', tipo: 'pin' }],
};
const { items, years } = unir(A);
assert.deepStrictEqual(years, [2019, 2024, 2025]);                 // ordenados, sin fechas vacías
assert.deepStrictEqual(items.map((i) => i.titulo), ['C', 'V', 'B']);
assert.strictEqual(items[2].href, 'evento.html?e=b');
assert.strictEqual(items[2].peg, 'virtual');
assert.ok(test('p', items[2]) && test('c', items[2]) && test('f', items[2]) && !test('v', items[2]));
assert.strictEqual(items[1].km, 0);                                // un viaje futuro no suma km
console.log('test_linea: OK');
