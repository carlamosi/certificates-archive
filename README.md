# Certificates Archive

Archivo personal, digital y físico de eventos, premios, lanyards, pines, fotos y viajes, con una web tipo museo para explorarlo.

- **Herramienta de digitalización:** `herramientas/lanyard_archive/` (Python, con calibración ArUco y medidas reales en mm).
- **Web:** `web/` (estática, pared de lanyards 3D con Three.js).
- **Base de datos:** `herramientas/archivo_db/` (SQLite: eventos, objetos, personas, fotos, charlas).
- **Datos:** `datos/` (catálogo de certificados, viajes, ciudades, aeropuertos, formato de fotos).
- **Diseño:** `docs/diseno/` (guía de la web y prompts de identidad de marca).
- **Documentación:** `docs/` (especificación, estado, decisiones, pendientes, guía de fotografía).

Para desarrollar con un agente (Claude Code, Antigravity), lee primero `AGENTS.md` (Claude Code lo carga desde `CLAUDE.md`).

## Arranque rápido
```bash
# 1. Herramienta (una vez)
cd herramientas/lanyard_archive && python -m pip install -r requirements.txt

# 2. Comprobar que todo funciona
bash tests/run_all.sh

# 3. Ver la web
cd web && python -m http.server 8000     # abre http://localhost:8000
```

## Flujo de trabajo de la persona
1. Imprime `herramientas/lanyard_archive/plantilla_calibracion_A4_v3.pdf` al 100 %.
2. Mide la regla de 100 mm impresa y ejecuta `--medir-regla <mm>` una vez.
3. Fotografía cada lanyard en parejas (anverso, reverso). Guía en `docs/FOTOGRAFIA.md`.
4. Procesa con `Iniciar.bat` (Windows) o `Iniciar.command` (Mac).
5. Sincroniza con `python web/sync.py "<ruta>/Lanyards_procesados"`.

## Privacidad
Originales, datos personales y `Lanyards_procesados/` no se suben a repositorios públicos (ver `.gitignore`).
