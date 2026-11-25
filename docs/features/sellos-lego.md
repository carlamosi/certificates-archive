# Sellos LEGO (pasaporte)
Estado: Verificada · Fecha: 2026-11-24

## Para qué
Guardar cada sello del pasaporte LEGO con su tienda, su viaje y su imagen recortada, y verlos en la web como una colección por tienda.

## Alcance
- Entra:
  - `archivo.py sello` admite **varios sellos por tienda y día** con `--diseno` (nombre del sello). Clave: `sello-<fecha>-<tienda>-<diseno>`.
  - Recorte de cada sello de los escaneos (`datos/lego/pag1.jpg`, `pag2.jpg`) a WebP con transparencia (solo la tinta, sin el fondo de colores), con `--imagen`.
  - Exportación: los sellos salen en `viajes[].objetos` (ya ocurre) y un nuevo `totales.sellos` por tienda.
  - Web (otra sesión): página «Pasaporte» con los sellos agrupados por tienda; en la ficha de cada viaje, sus sellos; en el mapa, la tienda como punto.
- No entra (de momento): la primera página del pasaporte (nombre, fecha de nacimiento y ciudad: datos personales, no se guardan), las ilustraciones de instrucciones de `pag1.jpg`, reconocer sellos automáticamente.

## Datos
Sin cambio de esquema: `objects` con `tipo = 'sello'`, `titulo` = diseño, `sitio` = tienda, `place_id`, `trip_id`, `fecha` = día del viaje (si no se sabe el día, el inicio del viaje), `front_web` = recorte.

Inventario leído de los escaneos (18 sellos):
| Tienda (`sitio`) | Ciudad | Viaje | Diseños |
|---|---|---|---|
| LEGO Store Tivoli | Copenhague | Copenhague, ago 2026 | Guardia real «Copenhagen» · Ladrillo «2026» · «København» · «Tivoli Gardens» · «Everyone is Awesome» · Escena de minifiguras (óvalo) |
| LEGO Store Aeropuerto CPH T3 | Copenhague | Copenhague | Triángulo «CPH-T3» |
| LEGO Store Aeropuerto CPH T2 | Copenhague | Copenhague | Triángulo «CPH-T2» · Avión «Airport T2» · Flor (sello cuadrado, tinta débil) |
| LEGO Store Aeropuerto de Barcelona | Barcelona | Copenhague (confirmado por Carla) | Avión «Barcelona Airport» · Minifigura con trofeo (tinta débil) |
| LEGO Store Paris Les Halles | París | París, nov 2026 | «Paris» (mimo) · Cabeza con gorro de fiesta · Ladrillo «Les Halles» · «The LEGO Store Paris» (baguette) · Escena con león · Notre-Dame |

El reparto de la flor, la minifigura del trofeo y la escena ovalada es por su posición en la página: lo revisa Carla.

## Criterios de aceptación
| # | Criterio | Cómo se verifica |
|---|---|---|
| 1 | Dos sellos de la misma tienda y día se guardan los dos; repetir no duplica | test `tests/test_archivo_db.py::test_sello_varios_por_tienda` |
| 2 | 18 sellos en la base real, cada uno con viaje, lugar e imagen | `archivo.py resumen` (sellos: 18) y `archivo.json` |
| 3 | Recortes legibles, sin fondo de colores, también los de tinta débil | revisión de Carla |
| 4 | `datos/lego/` no va a git | `git check-ignore datos/lego/page0.jpg` |

## Diseño
`docs/diseno/WEB_DISENO.md` e `IDENTIDAD.md`. Los sellos son tinta negra: en tema oscuro se invierten (blanco sobre cristal) para que se lean.
