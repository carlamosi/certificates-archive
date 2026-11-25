# Buscador global
Estado: Verificada · Fecha: 2026-11-25

## Para qué
Encontrar cualquier cosa del archivo (un evento, una ciudad, una persona, un pin…) sin saber en qué página está, desde cualquier página y también en el iPhone.

## Alcance
- Se abre con **Ctrl+K / ⌘K** (en cualquier sitio), **`/`** (si no se está escribiendo), la **lupa de la barra** o el botón **Buscar** del índice del pasaporte.
- Paleta de comandos en un `<dialog>` de cristal centrado; en móvil (≤ 640 px) es una hoja a pantalla completa. Campo con foco al abrir; ↑↓ mueven, Enter abre, Esc cierra y el foco vuelve a donde estaba (o a la lupa). `role=combobox` + `listbox`, `aria-activedescendant`, filas de 44 px, sin animación con `prefers-reduced-motion`.
- Campo vacío: últimas 5 búsquedas (`localStorage`, con `try/catch`; sin almacenamiento no pasa nada). Sin resultados: «Nada con «x». Prueba con otra palabra…».
- Coincidencia sin acentos ni mayúsculas, **por palabras** (todas deben aparecer, al principio de una palabra) en título, lugar, fecha, organizador, país… Hasta 8 por grupo; los grupos van en orden fijo.

## Qué busca y adónde lleva
| Tipo | Destino |
|---|---|
| Evento | `evento.html?e=<slug>` |
| Viaje | `mapa.html?viaje=<id>` |
| Ciudad / país | `mapa.html` |
| Persona (de las fotos) | `evento.html?e=` del evento de su primera foto (`fotos.html` no admite filtro) |
| Certificado | `evento.html?e=` si tiene evento; si no, `certificados.html` |
| Premio (certificado con nivel primer premio, podio, finalista o mención) | igual, o `premios.html` |
| Pin | `mapa.html?viaje=<id>` si es de un viaje; si no, `pines.html` |
| Sello LEGO | `pasaporte-lego.html` |
| Charla | `evento.html?e=` de su evento |

## Piezas
- `web/buscador.js` (+ `buscador.css`, que él mismo enlaza). Lo carga `web/pasaporte.js` con una línea, así que no se toca ningún html. Lee `data/archivo.json` la primera vez que se abre.
- Lógica pura y exportada para Node: `norm`, `indice(A)`, `buscar(items, texto, max)`. Test: `tests/test_buscador.js` (en `tests/run_all.sh`).
- **Sin cambios de esquema.**

## No entra
Lanyards sueltos, búsqueda difusa (erratas), resaltado de la coincidencia, filtro de personas en `fotos.html`.

## Comprobado
`bash tests/run_all.sh`; navegador con servidor local a escritorio y 375 px, claro y oscuro: atajos, teclado, destinos, sin resultados, recientes, foco, consola sin errores propios.
