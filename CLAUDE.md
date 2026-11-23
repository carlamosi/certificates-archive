@AGENTS.md

# Notas solo para Claude Code

- **Skills por tarea** (una por necesidad; no cargar varias que se solapan):
  - Funcionalidad nueva: `superpowers:brainstorming` → ficha en `docs/features/` (no en `docs/superpowers/`) → `superpowers:writing-plans` si es grande.
  - Web: `frontend-design` para la dirección visual, `make-interfaces-feel-better` para el repaso final, `ux-motion` solo si hay movimiento nuevo.
  - Documentación de librerías (Leaflet, Three.js r128): context7, con la versión exacta.
  - Bugs: `superpowers:systematic-debugging` con un test que reproduzca el fallo.
- **Subagentes:** para leer webs, búsquedas amplias y una revisión final independiente (opus) en cambios grandes. No para tareas de pocas llamadas.
- **Sesiones en paralelo:** solo para tareas independientes que no tocan los mismos ficheros (p. ej. una página de la web mientras aquí se cargan datos); cada una en su worktree.
- **Comandos repetibles:** como skills en `.claude/skills/`, no en `.claude/commands/`.
- **Modelo según la tarea** (créditos justos; subir de modelo solo cuando el error sale caro):
  | Modelo | Para qué | Ejemplos aquí |
  |---|---|---|
  | Haiku (`_`) | Mecánico y guiado por una skill o una lista | cargar sellos, rellenar columnas del catálogo, importar con `importar-gente`, renombrar, resúmenes |
  | Sonnet | Implementar con ficha o plan claros; tests; auditorías de docs; subagentes de búsqueda | conectar la web a `archivo.json`, página siguiendo su ficha, revisar incoherencias |
  | Opus (`+`) | Diseño y decisiones caras de deshacer | dirección visual de una página nueva, cambios de esquema y migraciones, depuración difícil, revisión final independiente |
  Subagentes: indicar siempre `model` (Haiku/Sonnet por defecto; Opus solo para la revisión final).
