# Datos reales en la web
Estado: Verificada · Fecha: 2026-11-23

## Para qué
La web deja de depender de los 6 lanyards de demostración y puede leer todo el archivo real. Es el requisito del mapa de viajes y de la página de personas.

## Alcance
- Entra: `archivo.py exportar` genera `web/data/archivo.json` con todo lo que necesitan las próximas páginas; `web/app.js` lo carga (opcional) y lo deja en `window.ARCHIVO`.
- No entra (de momento): pintar esos datos (mapa, línea del tiempo, personas); eso es de cada página. La pared 3D sigue leyendo `archive.json`.

## Datos
Sin cambios de esquema. `archivo.json` (base → web, la web nunca lee SQLite) contiene:
- `eventos[]`: campos del evento + `lat`/`lng` (del lugar, o null) + `objetos`, `charlas`, `fotos` (con `personas`).
- `viajes[]`: `v_viajes` + `visitas` (ciudad, país, `lat`, `lng`, fechas) + `eventos` (slugs) + `objetos` + `fotos`.
- `objetos` con `front_web` (p. ej. `img/certificados/…jpg`); `objetos_sueltos` (certificados online) y `fotos_sueltas`.
- `personas[]` con nº de fotos y charlas.
- `totales`: filas de `v_paises`, `v_ciudades`, `v_continentes`, `v_aeropuertos` (calculadas, lo futuro no cuenta).
- El fichero lleva nombres de personas: está en `.gitignore`.

## Criterios de aceptación
| # | Criterio | Cómo se verifica |
|---|---|---|
| 1 | El export incluye `totales` (países, ciudades, continentes, aeropuertos) | `tests/test_archivo_db.py::test_exportar_para_la_web` |
| 2 | Los eventos con lugar llevan `lat`/`lng` | mismo test |
| 3 | Los objetos exportados conservan `front_web` | mismo test |
| 4 | `web/data/archivo.json` no va a git | `git check-ignore web/data/archivo.json` |
| 5 | La web carga `archivo.json` sin romper la pared; si falta, la pared funciona igual | navegador: `window.ARCHIVO` con datos y pared visible, escritorio y 390 px |
| 6 | `bash tests/run_all.sh` termina en OK | ejecución |

## Diseño
Sin cambios visuales (`docs/diseno/WEB_DISENO.md` no aplica).
