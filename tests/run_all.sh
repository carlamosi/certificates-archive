#!/usr/bin/env bash
# Comprobaciones rápidas. Deben pasar siempre antes de dar un cambio por bueno.
set -euo pipefail
export PYTHONUTF8=1  # acentos bien en la consola de Windows (cp1252)
cd "$(dirname "$0")/.."
echo "1/5 Sintaxis Python"
python3 -m py_compile herramientas/lanyard_archive/lanyard_core.py herramientas/lanyard_archive/lanyard_archive.py web/sync.py herramientas/archivo_db/archivo.py
echo "2/5 Sintaxis JavaScript"
node --check web/app.js
node --check web/linea.js
node tests/test_linea.js
node --check web/inicio.js
node tests/test_inicio.js
echo "3/5 Pruebas de precisión rápidas (fotos sintéticas)"
python3 herramientas/lanyard_archive/extras/selftest.py --rapido | tail -3
echo "4/5 Base de datos (esquema, importaciones repetidas, integridad)"
TMPDB="$(mktemp -d)/test.sqlite"
export ARCHIVO_DB="$TMPDB"
A=herramientas/archivo_db/archivo.py
python3 $A init >/dev/null
python3 $A importar-catalogo tests/fixtures/catalogo_sin_evento.csv >/dev/null
SALIDA="$(python3 $A importar-catalogo tests/fixtures/catalogo_sin_evento.csv)"; echo "$SALIDA" | grep -q "0 nuevos" || { echo "FALLO: importación repetida duplica"; exit 1; }
python3 $A importar-viajes datos/mis_viajes.xlsx >/dev/null
python3 $A importar-fotos datos/fotos_personas_EJEMPLO.txt >/dev/null
SALIDA="$(python3 $A importar-fotos datos/fotos_personas_EJEMPLO.txt)"; echo "$SALIDA" | grep -q "0 nuevas" || { echo "FALLO: fotos repetidas"; exit 1; }
python3 $A evento --nombre "HealthTech 2030 Innovation Challenge" --fecha 2026-10-23 >/dev/null  # lo usa charlas_EJEMPLO.txt
python3 $A importar-charlas datos/entrada/charlas_EJEMPLO.txt >/dev/null
SALIDA="$(python3 $A importar-charlas datos/entrada/charlas_EJEMPLO.txt)"; echo "$SALIDA" | grep -q "procesadas" || { echo "FALLO: charlas"; exit 1; }
SALIDA="$(python3 $A resumen)"; echo "$SALIDA" | grep -q "integridad referencial: OK" || { echo "FALLO: integridad"; exit 1; }
unset ARCHIVO_DB
python3 tests/test_archivo_db.py
python3 tests/test_preparar_vercel.py
echo "   base de datos de prueba: OK"
echo "5/5 Datos de la web"
python3 - << 'PY'
import json, os
d = json.load(open("web/data/archive.json", encoding="utf-8"))
faltan = [p for r in d for p in (r.get("front_web"), r.get("back_web")) if p and not os.path.exists(os.path.join("web", p))]
assert not faltan, f"faltan imágenes: {faltan}"
print(f"   {len(d)} objeto(s), todas las imágenes presentes")
PY
echo "OK"
