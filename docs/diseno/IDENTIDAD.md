# Certificates Archive · Identidad

> Guía visual única de la web. Sustituye a `WEB_DISENO.md` (museo negro y amarillo, descartado el 2026-11-23).
> La guía viva con todos los componentes y estados está en `web/identidad.html`: si esta guía y esa página no coinciden, se corrige la página.

---

## 1. Concepto: cuaderno de viaje de cristal

La web es el **archivo central** de Carla, no solo de lanyards. Muestra todo lo que guarda la base de datos:
eventos, objetos (lanyards, certificados, pines, sellos LEGO, fotos), viajes con sus ciudades y aeropuertos,
personas y charlas grabadas.

La idea es un **cuaderno de viaje sobre papel claro**, con piezas de **cristal brillante** que flotan encima:

- **Papel:** fondo cálido y luminoso, con degradados casi imperceptibles (luz de ventana).
- **Cristal:** todo lo que flota (barra, cartela, ficha, tarjetas del mapa) es vidrio esmerilado con un reflejo arriba.
- **Sellos:** las imágenes del archivo (certificados, fotos) llevan borde perforado; los matasellos son el adorno, con moderación.
- **Pegatinas:** cada tipo de cosa del archivo tiene una pegatina 3D brillante (Fluent Emoji 3D) con borde blanco.
- **Un solo acento:** azul matasellos. Marca lo que se puede tocar o lo que está activo.

**De las referencias** (`references/`, solo inspiración): números grandes y finos, etiquetas de ciudad con icono y arcos
(Orion); mapa que se funde con el fondo (Paris Trip); foto en sello (Italy, Venecia); pegatinas y ruta discontinua
(Find your next adventure); carpetas translúcidas con fotos y sellos (carpetas de Ilya); tarjeta de vuelo (Welcome on board);
línea del tiempo con puntos (Canada plan). **No tomamos:** degradados morado-azul, barras laterales de panel de control,
fichas de mil colores, emojis de Apple (sus imágenes son de Apple), naranja como acento.

### Anti-objetivos (si pasa esto, está mal aunque funcione)
- Parece un panel de control de empresa o una plantilla de IA (aurora de colores, tarjetas blancas con sombra en todo).
- Hay más de un color que grita. Las pegatinas aportan color; la interfaz no.
- Los adornos (sellos, matasellos) tapan los objetos. **El objeto es el protagonista.**
- Animaciones en bucle, rebotes exagerados, parallax sin motivo, cursores personalizados.
- Textos de relleno. Cada palabra informa: «12 de mayo de 2026 · Barcelona».

---

## 2. Logotipo

`web/img/logo.svg` (también favicon). Un **sello postal** azul con borde perforado y, arriba, el **orificio de la anilla**
de un lanyard. Une las dos mitades del archivo: lo que se cuelga y lo que se viaja.

- Funciona a 16 px: se lee como un cuadrado azul perforado con un agujero.
- Al lado, el nombre en una línea: «Certificates» en 300 y «Archive» en 700, misma talla.
- No se deforma, no se gira, no cambia de color salvo blanco sobre azul.

---

## 3. Color (tokens en `web/style.css`)

| Token | Claro | Oscuro | Uso |
|---|---|---|---|
| `--paper` | `#F7F4EE` | `#121316` | Fondo base |
| `--paper-2` | `#EFEBE3` | `#0C0D10` | Fondo del degradado (abajo) |
| `--surface` | `#FFFFFF` | `#1C1E24` | Superficies opacas (marcos de sello) |
| `--glass` | `rgba(255,255,255,.58)` | `rgba(30,32,40,.58)` | Cristal |
| `--glass-edge` | `rgba(255,255,255,.75)` | `rgba(255,255,255,.10)` | Reflejo y borde del cristal |
| `--ink` | `#1B1A17` | `#F2EFE8` | Texto principal |
| `--ink-2` | `#5F5B53` | `#A7A39A` | Texto secundario, metadatos |
| `--line` | `rgba(27,26,23,.10)` | `rgba(255,255,255,.09)` | Separadores |
| `--accent` | `#2F5BEA` | `#7C9BFF` | Azul matasellos: foco, activo, botón principal |
| `--accent-ink` | `#FFFFFF` | `#0D1220` | Texto sobre el acento |
| `--accent-soft` | `rgba(47,91,234,.10)` | `rgba(124,155,255,.14)` | Fondos de hover y selección |
| `--danger` | `#C8372D` | `#FF7A6E` | Solo avisos de calidad de foto |
| `--glass-strong` | `--surface` al 88 % | igual | Fichas y paneles que deben leerse sobre cualquier fondo |
| `--velo` | `rgba(20,22,30,.4)` | `rgba(0,0,0,.5)` | Fondo detrás de fichas y diálogos |

**Contraste (WCAG, calculado):** claro: texto 15,9:1 · secundario 6,2:1 · acento sobre papel 5,0:1 · blanco sobre acento 5,5:1 · aviso 4,7:1.
Oscuro: texto 16,2:1 · secundario 7,4:1 · acento 7,1:1 · texto sobre acento 7,1:1 · aviso 7,3:1. Todo AA.

**Modo oscuro:** sigue al sistema (`prefers-color-scheme`). Es «el cuaderno de noche»: mismas piezas, papel azul noche.

### Degradados y luz (susurros)
```css
/* Fondo: luz de ventana arriba a la izquierda y un tinte azul casi invisible abajo a la derecha */
background:
  radial-gradient(70% 55% at 10% -10%, rgba(255,255,255,.9), transparent 60%),
  radial-gradient(60% 50% at 100% 110%, rgba(47,91,234,.06), transparent 70%),
  linear-gradient(180deg, var(--paper), var(--paper-2));
```
- Máximo tres capas; ninguna mancha de color supera el 8 % de opacidad.
- **Cristal:** `backdrop-filter: blur(20px) saturate(1.6)`, fondo `--glass`, borde 1 px `--glass-edge` y un reflejo
  interior arriba (`inset 0 1px 0 --glass-edge`). Solo en lo que flota.
- **Botón principal:** acento con un degradado vertical de un 6 % de luz (brillo de cristal), nunca dos colores.

---

## 4. Tipografía: Open Sauce One

Una sola familia. Fontsource `@fontsource/open-sauce-one@5.3.0` desde jsDelivr (pesos 300, 400, 500, 700 y 400 itálica).

| Rol | Tamaño / línea | Peso | Tracking |
|---|---|---|---|
| Display (contadores) | 44 / 48 (móvil 32 / 36) | 300 | −0.03em |
| Display grande (portada, total de premios) | 56–96 | 300 | −0.03em |
| H1 (título de ficha) | 32 / 38 | 700 | −0.02em |
| H2 (cartela) | 22 / 28 | 700 | −0.01em |
| Cuerpo | 15 / 24 | 400 | 0 |
| Metadatos | 13 / 20 | 500 | 0 |
| Etiqueta | 11 / 16 | 700, MAYÚSCULAS | +0.12em |
| Voz de museo | 15 / 24 | 400 itálica | 0 |

- Grande = fino; pequeño = firme. Una negrita por bloque.
- `font-variant-numeric: tabular-nums` en contadores, fechas y medidas.
- Etiquetas en `--accent` (lo activo) o `--ink-2` (lo demás).

---

## 5. Iconos: dos capas, un sistema

### 5.1 Pegatinas (qué es cada cosa) · Fluent Emoji 3D
Microsoft Fluent Emoji 3D (licencia MIT), desde jsDelivr con el commit fijo
`microsoft/fluentui-emoji@1ffb34c752ecf5d402f04cfb4b392c77f57c54bc`. Se muestran como **pegatina**: borde blanco
(`drop-shadow` en cuatro direcciones), sombra suave y giro de ±4°.

| Entidad de la base | Pegatina |
|---|---|
| Evento | Spiral calendar |
| Evento virtual (desde casa) | Laptop |
| Lanyard | Identification card |
| Certificado | Scroll |
| Premio | Sports medal |
| Pin | Round pushpin |
| Sello LEGO | Brick |
| Foto | Camera with flash |
| Charla / grabación | Microphone |
| Viaje | Airplane |
| Ciudad / lugar | Cityscape |
| Aeropuerto | Airplane departure |
| Persona | Busts in silhouette |
| País / continente | Globe showing Europe-Africa |

La tabla vive en código en `web/iconos.js` (`PEGATINAS`); si se añade una entidad, se añade allí y aquí.
**Una pegatina por elemento**, nunca como viñeta de lista ni decoración suelta.

### 5.2 Iconos de interfaz (qué puedo hacer) · SVG propio
`web/img/iconos.svg`, sprite de `<symbol>`. Rejilla de 24 px, trazo 1,75 px, extremos redondeados, `currentColor`.
Solo los que se usan: `cerrar`, `anterior`, `siguiente`, `girar`, `abrir`. Uno nuevo sigue la misma rejilla y trazo.

---

## 6. Espacio, forma y elevación

- **Rejilla de 4/8 px:** 4, 8, 12, 16, 24, 32, 48, 64 (`--s-1` … `--s-8`). Aire lateral: 24 px escritorio, 16 px móvil.
- **Radios:** `--r-1` 10 px (botones, pegatinas), `--r-2` 18 px (cartela, tarjetas), `--r-3` 28 px (ficha), `--r-pill` 999.
  Radio interior = radio exterior − separación.
- **Sombras:** `--sh-1` reposo (pegatinas, sellos), `--sh-2` flotante (cristal). Nada más.
- **Sello:** marco `--surface` de 10 px con borde perforado (máscara CSS `.sello`), sombra `--sh-1`.
- **Áreas táctiles:** mínimo 44 × 44 px.

---

## 7. Movimiento

| Token | Valor | Uso |
|---|---|---|
| `--d-1` | 120 ms | Pulsar (press) |
| `--d-2` | 200 ms | Hover, salida de cartela |
| `--d-3` | 280 ms | Entrada de cartela y ficha |
| `--d-4` | 480 ms | Giro del lanyard |
| `--ease-out` | `cubic-bezier(.2,.8,.2,1)` | Entradas y casi todo |
| `--ease-spring` | `cubic-bezier(.34,1.4,.64,1)` | Pegatinas, chip activo (rebote leve) |
| `--ease-in` | `cubic-bezier(.4,0,1,1)` | Salidas |

### Reglas de microinteracción
- **Hover** (solo con puntero fino, `@media (hover: hover)`): botones y chips aclaran el fondo (`--accent-soft`); las pegatinas se levantan 2 px y enderezan su giro.
- **Press:** todo lo pulsable se hunde a `scale(.96)` en `--d-1`.
- **Foco con teclado:** anillo de 2 px `--accent` con 2 px de separación (`:focus-visible`), inmediato.
- **Cartela:** aparece desde abajo (8 px) y escala .96 → 1 en `--d-3`; sale en `--d-2` con `--ease-in`.
- **Ficha:** el fondo se desenfoca (0 → 8 px) y la hoja sube 16 px en `--d-3`. Las caras entran con 40 ms de retardo entre ellas.
- **Chip de año activo:** el fondo azul aparece con `--ease-spring`; el contador usa cifras tabulares para no saltar.
- **Las animaciones solo responden a algo que hace la persona.** Única excepción: el indicador de carga.
- **`prefers-reduced-motion: reduce`:** sin desplazamientos ni escalas; solo cambios de opacidad de 120 ms. El péndulo 3D se amortigua al instante.

---

## 8. Componentes (aplicados en la pared)

- **Barra:** cristal, logo + nombre a la izquierda, contador en metadatos, chips de año a la derecha (desplazables en móvil).
- **Chips de año:** píldora de 36 px (44 px de área táctil). Activo: acento con texto blanco y `aria-pressed`.
- **Cartela:** cristal; pegatina del tipo + fecha en etiqueta; evento en H2; lugar en metadatos; botón «Ver ficha».
- **Ficha:** cristal grande; anverso y reverso en marcos de sello; pares etiqueta/valor; avisos en `--danger` sin icono.
- **Botones:** principal (acento, uno por vista), secundario (borde `--line`), icono (círculo de cristal de 40 px).
  Un enlace con forma de botón (`a.btn`) no se subraya.

### Componentes comunes de las páginas (`web/style.css`; repaso en `REPASO_UI.md`)
- **Cerrar:** `.btn.ghost.redondo.close` con el icono `cerrar`, arriba a la derecha a 12 px. Nunca «✕» de texto.
- **Ficha / diálogo:** fondo `--velo` con desenfoque de 8 px; hoja `--glass-strong` (cristal al 88 %), radio `--r-3`.
  Esc cierra; al abrir, el foco va al contenedor; al cerrar, vuelve a lo que la abrió.
- **Móvil:** lo que flota abajo se coloca sobre la barra de pestañas (`--sobre-pestanas`, incluye la zona segura del iPhone);
  las hojas modales van por encima de todo (z-index 40).
- **Campo de búsqueda** (`.campo`): píldora de cristal de 44 px, letra de 16 px (con menos, el iPhone amplía al escribir).
- **Control segmentado** (`.segmento`): vista o modo; la opción activa es una pastilla `--surface` con `--sh-1`.
- **Contadores** (`.contadores`): Display 300, separados por una línea `--line`.
- **Título de página** (`.titulo`): H1 32/38 (26/32 en móvil).
- **Estado vacío** (`.vacio`): una frase centrada en `--ink-2`. **Carga y avisos:** `.notice`.
- Cada página solo añade su CSS propio (`<página>.css`); nada con nombre genérico fuera de su página.
- **Pared 3D:** pared de galería clara (o azul noche en oscuro), carril de acero satinado, cordón fino en tinta, luz cálida desde arriba a la izquierda. Los colores se leen de los tokens CSS.

## 9. Lo que heredan el mapa y la página de personas
- Chinchetas = pegatinas (ciudad, aeropuerto, evento); al pasar, tarjeta de cristal como la cartela.
- Arcos de vuelo en `--accent` con trazo de 1,5 px; rutas en tierra, discontinuas.
- Contadores héroe en Display 300 con cifras tabulares: ciudades, países, continentes, aeropuertos y **km recorridos** (pendiente en la base de datos).
- Fotos con personas en marco de sello.

## 10. Comprobación antes de dar algo por bueno
- [ ] Solo colores de los tokens; un único acento visible por zona.
- [ ] Una familia tipográfica; pesos de la escala.
- [ ] Pegatinas de la tabla, una por elemento; iconos de interfaz del sprite.
- [ ] Hover, press y foco en todo lo pulsable; teclado completo.
- [ ] `prefers-reduced-motion` respetado.
- [ ] Contraste AA en claro y oscuro.
- [ ] Probado a 390 px y en escritorio.
