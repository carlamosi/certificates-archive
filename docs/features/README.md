# Fichas de funcionalidad

Una ficha por funcionalidad, **antes de construirla** (`docs/features/<nombre>.md`). Es el único sitio para especificaciones nuevas.
Corta: si no cabe en una pantalla, la funcionalidad es demasiado grande y se parte.

## Plantilla

```markdown
# <Nombre>
Estado: Acordada | En construcción | Verificada · Fecha: AAAA-MM-DD

## Para qué
Una o dos frases: qué gana Carla con esto.

## Alcance
- Entra: ...
- No entra (de momento): ...

## Datos
Qué lee de la base / de archivo.json y si necesita cambios de esquema (entonces: migración, ver docs/data-model.md).

## Criterios de aceptación
| # | Criterio | Cómo se verifica |
|---|---|---|
| 1 | ... | test `tests/...::test_...` · navegador (escritorio y 390 px) · revisión de Carla |

## Diseño
Referencia a `docs/diseno/WEB_DISENO.md` y lo específico de esta pantalla.
```

Al terminar: todos los criterios verificados → Estado «Verificada» y una línea en `docs/ESTADO.md`.
