// Pruebas de la agrupación de web/inicio.js con un archivo.json sintético (el real no va a git).
// Las cifras (anual, hitos) las calcula y prueba el exportador: tests/test_archivo_db.py.
const assert = require('assert');
const { calcular } = require('../web/inicio.js');
const A = {
  viajes: [
    { id: 1, slug: 'a', nombre: 'A', inicio: '2024-05-01', estado: 'pasado', km: 600, vuelos: [{}], visitas: [] },
    { id: 2, slug: 'b', nombre: 'B', inicio: '2025-03-10', estado: 'pasado', km: 11000, vuelos: [], visitas: [] },
    { id: 3, slug: 'c', nombre: 'C', inicio: '2099-01-01', estado: 'futuro', km: 999, vuelos: [], visitas: [] },
  ],
  eventos: [{ id: 9, slug: 'e1', nombre: 'E1', fecha: '2025-03', trip_id: 2, objetos: [{ titulo: 'T', fecha: '2025-03', nivel: 'primer premio' }], fotos: [{ mini: 'x.webp', fecha: '2025-03-11' }] }],
  objetos_sueltos: [{ tipo: 'pin' }, { tipo: 'pin' }],
  totales: { km: 11600 },
  anual: {
    2024: { km: 600, viajes: 1, paises_nuevos: 1, ciudades_nuevas: 1, eventos: 0, premios: {}, personas_nuevas: 0, pines: 0, sellos: 0 },
    2025: { km: 11000, viajes: 1, paises_nuevos: 1, ciudades_nuevas: 0, eventos: 1, premios: { 'primer premio': 1 }, personas_nuevas: 1, pines: 0, sellos: 0 },
  },
  hitos: [{ fecha: '2025-03-10', tipo: 'viaje', texto: 'Cruzaste los 10.000 km', enlace: 'b' }, { fecha: '2099-01-01', tipo: 'viaje', texto: 'futuro', enlace: 'c' }],
};
const D = calcular(A, '2026-11-25');
assert(D.hayCifras && D.kmAnios === D.kmTotal, 'km por año = totales.km');
assert.strictEqual(D.stats('2025').km, 11000);
assert.strictEqual(D.stats('2025').pines, null);                                 // pines sin fecha: solo en «Todo»
assert.strictEqual(D.stats('all').pines, 2);
assert.strictEqual(D.stats('all').km, 11600);
assert.strictEqual(D.stats('all').nPremios, 1);
assert.strictEqual(D.stats('2025').hitos.length, 1);                             // el hito futuro no sale
assert.strictEqual(D.stats('2020').km, 0);                                       // año sin bloque: ceros, no fallo
assert.strictEqual(D.viajeDe.get('b'), 2);
assert.strictEqual(D.periodos('2025').map((p) => p.k).join(), '2025-03');
assert.strictEqual(calcular({}, '2026-01-01').hayCifras, false);
console.log('inicio: OK');
