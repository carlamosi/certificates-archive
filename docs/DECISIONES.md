# Decisiones de diseño

Cada decisión, con su motivo. Si cambias algo, añade una línea aquí.

| Decisión | Motivo |
|---|---|
| Web estática, sin servidor ni base de datos | Privada, gratis, portable, sin mantenimiento |
| Three.js r128 desde cdnjs, sin build | Sencillo; sin Node ni bundler para la persona |
| Plantilla con marcadores ArUco (no cruces) | Identificación robusta y sin ambigüedad; el orden de las esquinas lo resuelve el código |
| Plantilla A4 completa (no la de 150×210) | Cabe un A5/A6; los marcadores quedan más separados y la calibración mejora |
| Una pareja de fotos = un lanyard | La persona lo pidió: los lanyards siempre tienen dos caras; no preguntar el tipo |
| Medida única para anverso y reverso si son rectangulares | Son la misma tarjeta; evita dos medidas distintas por ruido |
| Formas libres sin envolvente convexa | La medalla de África se recortaba mal con la envolvente |
| Orificios solo arriba, máx. 2 | Los falsos positivos eran números y franjas laterales |
| Péndulo simple (no simulación física completa) | Suficiente para el efecto; la física completa no aporta al archivo |
| Salida junto a las fotos (`Lanyards_procesados`) | Ella no encontraba la carpeta en el escritorio (OneDrive) |
| Escala de impresora como corrección global | Mide la regla impresa una vez; no hace falta calibrar por foto |
| SQLite para el archivo completo (revisado) | Al añadir personas en fotos, charlas y eventos hacen falta relaciones muchos-a-muchos y claves. Para solo lanyards bastaba JSON; el modelo completo no |
| Esquema v2: la base de datos es la fuente de verdad (06/11/2026) | El Excel de viajes, los CSV y la base no se hablaban. Ahora eventos y viajes son los dos ejes; objetos (lanyards, certificados, pines, sellos LEGO) y fotos cuelgan de evento, viaje, lugar o de nada. Los totales (días, países, aeropuertos, pasado/futuro) son vistas: nunca se desincronizan. País = ciudad visitada o aeropuerto usado, como el Excel |
| Clave de personas = nombre normalizado | Evita duplicados por acentos o mayúsculas; los parecidos se avisan, no se fusionan |
| Importaciones idempotentes | Repetir un archivo nunca duplica datos: la persona puede volver a importar sin miedo |
| Vídeos por ruta local, sin URL | Son grabaciones del móvil, privadas y pesadas; la base guarda la ruta y no el vídeo |
| Entrada en `datos/entrada/` | Un único sitio para lo que se importa; fuera de git |
| Sin frameworks en la web | Evitar complejidad; reconsiderar al llegar al mapa |
| Lanzadores `.bat` y `.command` | La persona no usa terminal |
