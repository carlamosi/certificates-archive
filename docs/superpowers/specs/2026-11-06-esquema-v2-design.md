# Esquema v2 · viajes, lugares, sellos y objetos sin evento

Fecha: 2026-11-06 · Estado: **implementado (06/11/2026)**. Histórico: el esquema vigente es `schema.sql`.

## Objetivo
Una sola base de datos (`datos/archivo.sqlite`) que conecte todo el archivo: eventos, viajes (también los familiares),
lugares, fotos de personas, charlas, lanyards, certificados, pines y sellos LEGO.
**La base de datos es la fuente de verdad.** `mis_viajes.xlsx` se importa una vez y queda como histórico.

## Decisiones (dichas por Carla)
- Dos ejes: **eventos** y **viajes**. Un viaje puede ser familiar (sin eventos) o tener eventos.
- Las fotos pueden ir a un evento, a un viaje o a ninguno (foto suelta con fecha y personas).
- Los certificados pueden tener evento o no (curso online, por ejemplo).
- Pines: van a su ciudad. Sellos LEGO: van a su sitio, su fecha y su viaje; hay diseños nuevos cada mes.
- El seguimiento (días, años, países, pasado/futuro) se **calcula**, no se guarda.

## Modelo
```
viaje ──► visitas (ciudad + fechas) ──► lugar (lat/lng)
  │  ▲                                    ▲
  │  └── foto · sello · pin               │
  ▼                                       │
evento ──────────── place_id ─────────────┘
  ▲   ▲   ▲
  │   │   └── lanyard / certificado
  │   └── charla ◄── personas
  └── foto ◄── personas
foto suelta ◄── personas · certificado suelto
```

### Tablas nuevas
| Tabla | Campos clave | Origen |
|---|---|---|
| `places` | nombre, region, pais, continente, lat, lng, coord_confianza · UNIQUE(nombre, pais) | Ciudades + `ciudades_geo.csv` |
| `airports` | iata (PK), nombre, place_id, lat, lng | Aeropuertos + `aeropuertos_geo.csv` |
| `trips` | slug UNIQUE, nombre, inicio, fin (pueden faltar), transporte, salida/llegada/escala (IATA), motivo, notas | hoja Viajes |
| `visits` | place_id, trip_id (opcional), inicio, fin, nota | hoja Ciudades (una fila = una visita; Andorra 2021 no tiene viaje) |

### Cambios en tablas existentes
- `events`: + `place_id`, + `trip_id` (opcionales).
- `photos`: + `trip_id` (opcional; `event_id` ya lo era).
- `objects` (se reconstruye, procedimiento oficial de SQLite):
  - `tipo` admite `sello`.
  - `event_id` pasa a opcional; + `trip_id`, `place_id`, `fecha`, `sitio` ("LEGO Store Tivoli"), `titulo`, `organizador`.
  - `CHECK`: al menos uno de evento, viaje, lugar o título.
  - `pin_city` se sustituye por `place_id`; `pin_id` se mantiene.
  - Si hay evento, título/organizador/fecha vacíos = se usan los del evento.

### Vistas (cálculos, nada guardado)
`v_viajes` (días, año, pasado/futuro según hoy) · `v_paises` · `v_continentes` · `v_aeropuertos` (veces usado).

## Migración v1 → v2
- `archivo.py migrar`: copia de seguridad automática antes, todo en una transacción, `PRAGMA user_version = 2`.
- No se pierde nada: las 26 fotos, 17 eventos y 42 personas siguen igual; `pin_city` pasa a `place_id`.
- `init` crea directamente v2.

## Comandos
| Comando | Qué hace |
|---|---|
| `migrar` | v1 → v2 con copia previa |
| `importar-viajes datos/mis_viajes.xlsx` | viajes, visitas, lugares, aeropuertos y pines (☑ + ID pin). Idempotente |
| `importar-catalogo` | nueva columna `evento` (slug); vacía = certificado suelto |
| `importar-fotos` | además de `#evento`: `#viaje Nombre` y `#sin-evento`. Reimportar actualiza las personas de la foto |
| `sello --fecha --sitio --ciudad [--viaje] [--imagen]` | alta de un sello LEGO |
| `copia` | copia de seguridad de la base (API de backup de SQLite) a `datos/copias/` con fecha |
| `resumen` | añade totales de viajes |

Para los 45 certificados: propongo la columna `evento` comparando fechas y nombres con la base; Carla revisa solo las dudas.

Sellos: la imagen es una foto o escaneo del sello (sin ArUco ni mm).

## Pruebas (en `tests/run_all.sh`, con base temporal)
1. Migrar una base v1 con datos: mismos recuentos antes y después; `integrity_check` ok.
2. `importar-viajes` dos veces: 0 nuevos la segunda.
3. Los totales coinciden con la hoja Resumen del Excel: **39 ciudades, 16 viajes, 11 países, 3 continentes, 9 aeropuertos, 16 con pin**.
4. Un objeto sin evento, viaje, lugar ni título se rechaza.
5. Reimportar una foto con una persona más la añade (test ya escrito).

## Fuera de alcance (ahora)
Web (mapa, páginas), exportar a Excel, recorte automático de sellos, enlazar foto con lugar directamente.

## Se actualiza en el mismo cambio
`schema.sql`, `archivo.py`, `herramientas/archivo_db/README.md`, `docs/DECISIONES.md`, `docs/ESTADO.md`, `CLAUDE.md`/`AGENTS.md` (el Excel deja de ser la fuente de verdad).
