# Premios
Estado: Verificada · Fecha: 2026-11-23

## Para qué
Ver de un vistazo todo lo que Carla ha ganado: cuántos premios, de qué nivel y en qué año, en una vitrina de cristal con una medalla por premio, y abrir el certificado de cada uno.

## Alcance
- Entra: página `web/premios.html` (+ `premios.js`, `premios.css`; usa los tokens de `style.css` sin editarlo). Izquierda: pegatina de medalla, total en grande, reparto por nivel (con su metal) y barra por año. Derecha: vitrina con cuatro estantes (Primer premio, Podio, Finalista, Mención); cada premio es una medalla con cinta, de oro, bronce, plata o azul matasellos, con el año abreviado y el nombre debajo.
- Al tocar una medalla: ficha de cristal con fecha, evento, organizador, nivel, texto original del premio y «Ver el certificado» (abre `front_web` en grande, en marco de sello). Sin imagen: botón «Por escanear», desactivado. Esc cierra (primero la imagen, luego la ficha); con Tab y con las flechas se recorren las medallas.
- Móvil (390 px): resumen arriba y estantes debajo; la ficha sube desde abajo.
- No entra (de momento): `participación` y `ponente` (no son premios), filtros, orden alternativo, enlace desde otras páginas (la navegación común llegará después).

## Datos
Lee `web/data/archivo.json` (sin cambios de esquema): todos los objetos con `nivel` ∈ {primer premio, podio, finalista, mención}, tanto de `eventos[].objetos` como de `objetos_sueltos`. Orden: del más reciente al más antiguo dentro de cada estante. Texto de la ficha: `titulo`, `organizador` (si falta: «Organizador sin anotar»), `premio` (texto original), `fecha`. No se inventa nada.

## Criterios de aceptación
| # | Criterio | Cómo se verifica |
|---|---|---|
| 1 | Total = 23 con los datos de hoy (7 primer premio, 2 podio, 8 finalista, 6 mención); barra por año cuadra | ✔ navegador + `contar()` con node |
| 2 | Cada estante ordenado de más reciente a más antiguo; si no caben, saltan de línea | ✔ navegador (escritorio y 390 px) |
| 3 | Al tocar una medalla sale la ficha con sus datos; Esc la cierra | ✔ navegador, ratón y teclado |
| 4 | «Ver el certificado» abre la imagen; sin imagen, «Por escanear» desactivado | ✔ navegador (con y sin imagen) |
| 5 | Teclado: Tab y flechas recorren las medallas, foco visible, foco vuelve a la medalla | ✔ navegador |
| 6 | Claro y oscuro; 390 px con el resumen arriba | ✔ navegador |
| 7 | «Reducir movimiento»: nada se mueve al pasar el ratón | ✔ revisión del CSS (el navegador integrado no lo emula) |

## Diseño
Aprobado en Claude Design (mesa «Premios»). Identidad: `docs/diseno/IDENTIDAD.md`. Metales por nivel: oro, bronce, plata y azul matasellos (únicos colores nuevos, solo en las medallas).
