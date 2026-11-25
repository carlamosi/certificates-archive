"""Pruebas de la base de datos del archivo (herramientas/archivo_db). Sin pytest: python tests/test_archivo_db.py"""
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
A = ROOT / "herramientas" / "archivo_db" / "archivo.py"


def base_temporal() -> dict:
    t = Path(tempfile.mkdtemp())
    return dict(os.environ, ARCHIVO_DB=str(t / "a.sqlite"), ARCHIVO_FOTOS=str(t / "fotos"), PYTHONIOENCODING="utf-8")


def run(env, *args) -> str:
    r = subprocess.run([sys.executable, str(A), *map(str, args)], env=env, capture_output=True,
                       text=True, encoding="utf-8", cwd=ROOT)
    return r.stdout + r.stderr


def db(env):
    return sqlite3.connect(env["ARCHIVO_DB"])


def test_reimportar_actualiza_personas():
    env = base_temporal(); t = Path(env["ARCHIVO_DB"]).parent
    run(env, "init")
    with zipfile.ZipFile(t / "g.zip", "w") as z:
        z.writestr("a/foto.jpg", b"x")
    txt = t / "f.txt"
    for personas in ("Ana Uno", "Ana Uno | Bea Dos"):
        txt.write_text(f"#evento Prueba | | | | 2025-01-01\n2025/01/01 - {personas} => foto.jpg\n", encoding="utf-8")
        run(env, "importar-fotos", txt, "--zip", t / "g.zip")
    n = db(env).execute("SELECT COUNT(*) FROM photo_people pp JOIN photos p ON p.id = pp.photo_id "
                        "WHERE p.archivo = 'foto.jpg'").fetchone()[0]
    assert n == 2, f"reimportar no actualiza las personas (tiene {n})"


def test_copia():
    env = base_temporal()
    run(env, "init")
    out = run(env, "copia")
    copias = list((Path(env["ARCHIVO_DB"]).parent / "copias").glob("archivo_*.sqlite"))
    assert len(copias) == 1, f"no hay copia\n{out}"
    assert sqlite3.connect(copias[0]).execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def base_v1() -> dict:
    """Base en el esquema v1 con algo de datos: 2 eventos, 1 pin con ciudad, 1 foto con 2 personas."""
    env = base_temporal()
    con = sqlite3.connect(env["ARCHIVO_DB"])
    con.executescript((ROOT / "tests" / "fixtures" / "schema_v1.sql").read_text(encoding="utf-8"))
    con.executescript("""
        INSERT INTO events (slug, nombre, fecha) VALUES ('2025-01-01_a', 'A', '2025-01-01'), ('2025-02-01_b', 'B', '2025-02-01');
        INSERT INTO objects (uid, event_id, tipo, pin_city, pin_id) VALUES ('pin-1', 1, 'pin', 'Lisboa', 'LIS-1');
        INSERT INTO people (nombre, clave) VALUES ('Ana Uno', 'ana uno'), ('Bea Dos', 'bea dos');
        INSERT INTO photos (event_id, fecha, archivo) VALUES (1, '2025-01-01', 'f.jpg');
        INSERT INTO photo_people VALUES (1, 1), (1, 2);
    """)
    con.commit(); con.close()
    return env


def recuentos(env):
    con = db(env)
    return {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            for t in ("events", "objects", "people", "photos", "photo_people")}


def test_migrar_conserva_datos():
    env = base_v1()
    antes = recuentos(env)
    out = run(env, "migrar")
    con = db(env)
    assert recuentos(env) == antes, f"la migración cambia los recuentos\n{out}"
    assert con.execute("PRAGMA user_version").fetchone()[0] == 5
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    lugar = con.execute("SELECT p.nombre FROM objects o JOIN places p ON p.id = o.place_id WHERE o.uid = 'pin-1'").fetchone()
    assert lugar == ("Lisboa",), f"el pin no tiene su lugar: {lugar}"
    assert list((Path(env["ARCHIVO_DB"]).parent / "copias").glob("*_antes-v5.sqlite")), "no hay copia antes de migrar"


def test_migrar_dos_veces():
    env = base_v1()
    run(env, "migrar")
    assert "ya está en v5" in run(env, "migrar")


def estructura(env):
    con = db(env)
    tablas = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view') ORDER BY name")]
    idx = sorted(r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'index' AND sql IS NOT NULL"))
    return {t: sorted(r[1] for r in con.execute(f"PRAGMA table_info({t})")) for t in tablas}, idx


def test_schema_igual_a_migracion():
    nueva = base_temporal(); run(nueva, "init")
    migrada = base_v1(); run(migrada, "migrar")
    assert estructura(nueva) == estructura(migrada), "schema.sql y la migración no dan la misma estructura"


def test_objeto_sin_ancla_rechazado():
    env = base_temporal(); run(env, "init")
    try:
        db(env).execute("INSERT INTO objects (uid, tipo) VALUES ('x', 'certificado')")
    except sqlite3.IntegrityError:
        return
    raise AssertionError("se acepta un objeto sin evento, viaje, lugar ni título")


EXCEL = ROOT / "datos" / "mis_viajes.xlsx"


def base_con_viajes():
    env = base_temporal(); run(env, "init")
    return env, run(env, "importar-viajes", EXCEL)


def test_viajes_totales_excel():
    env, out = base_con_viajes()
    con = db(env); q = lambda s: con.execute(s).fetchone()[0]
    assert q("SELECT COUNT(*) FROM trips") == 18, out
    assert q("SELECT COUNT(*) FROM visits") == 46, out
    assert q("SELECT COUNT(DISTINCT place_id) FROM visits") == 41
    assert q("SELECT COUNT(*) FROM airports") == 11
    assert q("SELECT COUNT(*) FROM objects WHERE tipo = 'pin'") == 16
    # shortcut: cifras de la hoja Resumen (sin París ni Praga, futuros); a partir del 20/11/2026 cambian solas
    if q("SELECT date('now') < '2026-11-20'"):
        assert q("SELECT COUNT(*) FROM v_ciudades") == 39
        assert q("SELECT COUNT(*) FROM v_viajes WHERE estado <> 'futuro'") == 16
        assert q("SELECT COUNT(*) FROM v_paises") == 11
        assert q("SELECT COUNT(*) FROM v_continentes") == 3
        assert q("SELECT COUNT(*) FROM v_aeropuertos") == 9
        assert q("SELECT veces FROM v_aeropuertos WHERE iata = 'BCN'") == 6


def test_viajes_idempotente():
    env, _ = base_con_viajes()
    assert "viajes: 0 nuevos" in run(env, "importar-viajes", EXCEL)
    assert db(env).execute("SELECT COUNT(*) FROM visits").fetchone()[0] == 46


def test_viaje_sin_fechas():
    env, _ = base_con_viajes()
    r = db(env).execute("SELECT inicio FROM trips WHERE nombre LIKE 'Vacaciones familiares en Bruselas%'").fetchone()
    assert r == (None,), r


def test_viajes_avisos():
    import openpyxl
    env = base_temporal(); run(env, "init"); t = Path(env["ARCHIVO_DB"]).parent
    wb = openpyxl.Workbook(); wb.remove(wb.active)
    for nombre, fila, cab, datos in [
        ("Viajes", 4, ["Nº", "Viaje", "Fecha inicio", "Fecha fin", "Días", "Transporte", "Salida", "Llegada", "Escala",
                       "Motivo / Descripción", "Notas", "Año"], [[1, "Viaje real", None, None]]),
        ("Ciudades", 4, ["Nº", "Ciudad", "Región", "País", "Continente", "Viaje", "Fecha inicio", "Fecha fin", "Días",
                         "Nota", "Pin", "ID pin"], [[1, "Villa Inventada", "", "España", "Europa", "Viaje que no existe"]]),
        ("Aeropuertos", 3, ["Aeropuerto", "IATA", "Ciudad", "País", "Veces usado"], []),
        ("Países", 3, ["Bandera", "País", "Continente"], []),
    ]:
        ws = wb.create_sheet(nombre)
        for i, v in enumerate(cab, 1):
            ws.cell(fila, i, v)
        for j, d in enumerate(datos, fila + 1):
            for i, v in enumerate(d, 1):
                ws.cell(j, i, v)
    wb.save(t / "v.xlsx")
    out = run(env, "importar-viajes", t / "v.xlsx")
    assert "fila 5" in out and "Viaje que no existe" in out, out
    assert "Villa Inventada" in out and "coordenadas" in out, out
    con = db(env)
    assert con.execute("SELECT trip_id FROM visits").fetchone() == (None,)
    assert con.execute("SELECT lat FROM places WHERE nombre = 'Villa Inventada'").fetchone() == (None,)


def test_v1_pide_migrar():
    env = base_v1()
    assert "Ejecuta: python archivo.py migrar" in run(env, "importar-viajes", EXCEL)


def catalogo(env, filas):
    t = Path(env["ARCHIVO_DB"]).parent / "cat.csv"
    t.write_text("uid,num_archivo,tipo,titulo,organizador,fecha,rol_premio,evento\n" + "\n".join(filas) + "\n", encoding="utf-8")
    return run(env, "importar-catalogo", t)


def test_catalogo_certificado_suelto():
    env = base_temporal(); run(env, "init")
    out = catalogo(env, ["c-1,003,certificado,Roblox Coding,CodeLearn,2022-07,,"])
    con = db(env)
    r = con.execute("SELECT event_id, titulo, organizador, fecha FROM objects WHERE uid = 'c-1'").fetchone()
    assert r == (None, "Roblox Coding", "CodeLearn", "2022-07"), f"{r}\n{out}"
    assert con.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0


def test_catalogo_con_evento():
    env = base_temporal(); run(env, "init")
    s = run(env, "evento", "--nombre", "Women Startup Challenge", "--fecha", "2025-11-07").split("evento: ")[1].strip()
    catalogo(env, [f"c-2,040,certificado,Women Startup Challenge,,2025-11,,{s}"])
    r = db(env).execute("SELECT e.slug FROM objects o JOIN events e ON e.id = o.event_id WHERE o.uid = 'c-2'").fetchone()
    assert r == (s,), r
    out = catalogo(env, ["c-3,041,certificado,X,,2025-11,,no-existe"])
    assert "fila 2" in out and "no-existe" in out, out


def test_objetos_pin_con_lugar():
    env = base_temporal(); run(env, "init"); t = Path(env["ARCHIVO_DB"]).parent / "archive.json"
    t.write_text('[{"id": "p-1", "tipo": "pin", "ciudad": "Lisboa", "pin_id": "LIS-1", "evento": "Viaje", "fecha": "2023-08-16"}]',
                 encoding="utf-8")
    out = run(env, "importar-objetos", t)
    r = db(env).execute("SELECT p.nombre FROM objects o JOIN places p ON p.id = o.place_id WHERE o.uid = 'p-1'").fetchone()
    assert r == ("Lisboa",), f"{r}\n{out}"


def test_sello_alta_e_idempotencia():
    env, _ = base_con_viajes()
    viaje = db(env).execute("SELECT slug FROM trips WHERE nombre = 'Vacaciones familiares en Copenhague'").fetchone()[0]
    args = ["sello", "--fecha", "2026-08-25", "--sitio", "Aeropuerto de Barcelona", "--ciudad", "Barcelona", "--viaje", viaje]
    run(env, *args); out = run(env, *args)
    run(env, "sello", "--fecha", "2026-11-20", "--sitio", "Aeropuerto de Barcelona", "--ciudad", "Barcelona")
    con = db(env)
    assert con.execute("SELECT COUNT(*) FROM objects WHERE tipo = 'sello'").fetchone()[0] == 2, out
    r = con.execute("SELECT p.nombre, t.slug FROM objects o JOIN places p ON p.id = o.place_id "
                    "JOIN trips t ON t.id = o.trip_id WHERE o.uid = 'sello-2026-08-25-aeropuerto-de-barcelona'").fetchone()
    assert r == ("Barcelona", viaje), r


def test_sello_varios_por_tienda():
    env, _ = base_con_viajes()
    base = ["sello", "--fecha", "2026-08-25", "--sitio", "LEGO Store Tivoli", "--ciudad", "Copenhague"]
    run(env, *base, "--diseno", "Guardia real", "--imagen", "img/sellos/a.webp")
    run(env, *base, "--diseno", "Ladrillo 2026"); run(env, *base, "--diseno", "Ladrillo 2026")
    con = db(env)
    r = con.execute("SELECT titulo, front_web FROM objects WHERE tipo = 'sello' ORDER BY uid").fetchall()
    assert r == [("Guardia real", "img/sellos/a.webp"), ("Ladrillo 2026", "")], r
    d = Path(env["ARCHIVO_DB"]).parent / "x.json"; run(env, "exportar", d)
    t = json.loads(d.read_text(encoding="utf-8"))["totales"]["sellos"]
    assert t == [{"tienda": "LEGO Store Tivoli", "ciudad": "Copenhague", "sellos": 2}], t


def fotos(env, texto):
    t = Path(env["ARCHIVO_DB"]).parent / "fp.txt"
    t.write_text(texto, encoding="utf-8")
    return run(env, "importar-fotos", t)


def test_foto_de_viaje():
    env, _ = base_con_viajes()
    out = fotos(env, "#viaje Vacaciones familiares en Copenhague\n2026/08/27 - Ana Uno | Bea Dos => cph.jpg\n")
    r = db(env).execute("SELECT p.event_id, t.nombre FROM photos p JOIN trips t ON t.id = p.trip_id "
                        "WHERE p.archivo = 'cph.jpg'").fetchone()
    assert r == (None, "Vacaciones familiares en Copenhague"), f"{r}\n{out}"
    assert "no existe el viaje" in fotos(env, "#viaje Viaje inventado\n2026/01/01 - Ana Uno => x.jpg\n")


def test_foto_suelta():
    env = base_temporal(); run(env, "init")
    out = fotos(env, "#sin-evento\n2026/02/14 - Ana Uno | Bea Dos => suelta.jpg\n")
    con = db(env)
    assert con.execute("SELECT event_id, trip_id FROM photos WHERE archivo = 'suelta.jpg'").fetchone() == (None, None), out
    assert con.execute("SELECT COUNT(*) FROM photo_people").fetchone()[0] == 2


def test_resumen_viajes():
    env, _ = base_con_viajes()
    out = run(env, "resumen")
    assert "viajes: 18" in out and "pines: 16" in out and "sellos: 0" in out, out


def test_exportar_incluye_viajes():
    import json
    env, _ = base_con_viajes()
    catalogo(env, ["c-1,003,certificado,Roblox Coding,CodeLearn,2022-07,,"])
    fotos(env, "#sin-evento\n2026/02/14 - Ana Uno | Bea Dos\n")
    salida = Path(env["ARCHIVO_DB"]).parent / "web.json"
    run(env, "exportar", salida)
    d = json.loads(salida.read_text(encoding="utf-8"))
    cph = next(v for v in d["viajes"] if v["nombre"] == "Vacaciones familiares en Copenhague")
    assert {c["ciudad"] for c in cph["visitas"]} >= {"Copenhague", "Malmö"}, cph
    assert any(o["uid"] == "c-1" for o in d["objetos_sueltos"])
    assert d["fotos_sueltas"][0]["archivo"] is None and d["fotos_sueltas"][0]["personas"] == ["Ana Uno", "Bea Dos"]


def test_exportar_para_la_web():
    """La web necesita totales de las vistas, coordenadas de los eventos y front_web en los objetos."""
    import json
    env, _ = base_con_viajes()
    catalogo(env, ["c-1,003,certificado,Roblox Coding,CodeLearn,2022-07,,"])
    con = db(env)
    con.execute("UPDATE objects SET front_web='img/certificados/c-1.jpg' WHERE uid='c-1'")
    con.execute("INSERT INTO events(slug,nombre,fecha,place_id) SELECT '2026-01-01_x','X','2026-01-01',id FROM places WHERE nombre='Copenhague'")
    con.commit(); con.close()
    salida = Path(env["ARCHIVO_DB"]).parent / "web.json"
    run(env, "exportar", salida)
    d = json.loads(salida.read_text(encoding="utf-8"))
    t = d["totales"]
    assert {"paises", "ciudades", "continentes", "aeropuertos"} <= set(t), t
    assert t["paises"] and t["paises"][0]["pais"] and t["aeropuertos"][0]["iata"]
    assert next(o for o in d["objetos_sueltos"] if o["uid"] == "c-1")["front_web"] == "img/certificados/c-1.jpg"
    ev = next(e for e in d["eventos"] if e["slug"] == "2026-01-01_x")
    assert ev["lat"] is not None and ev["lng"] is not None, ev


def test_fotos_web():
    """fotos-web crea WebP grande y miniatura; exportar enlaza las rutas solo si el fichero existe."""
    import json
    from PIL import Image
    env = base_temporal(); t = Path(env["ARCHIVO_DB"]).parent
    env["ARCHIVO_FOTOS_WEB"] = str(t / "web_fotos")
    run(env, "init")
    fotos(env, "#sin-evento\n2025/01/01 - Ana Uno => a.jpg\n2025/01/02 - Bea Dos => b.jpg\n")
    (t / "fotos").mkdir()
    Image.new("RGB", (3200, 2000), "red").save(t / "fotos" / "a.jpg")   # b.jpg no existe
    out = run(env, "fotos-web")
    assert "1 nuevas" in out and "b.jpg" in out, out        # avisa de la que falta
    assert "0 nuevas" in run(env, "fotos-web")               # repetible
    salida = t / "w.json"; run(env, "exportar", salida)
    f = {x["archivo"]: x for x in json.loads(salida.read_text(encoding="utf-8"))["fotos_sueltas"]}
    assert f["b.jpg"]["web"] is None and f["b.jpg"]["mini"] is None
    web, mini = (t / "web_fotos" / Path(f["a.jpg"][k]).name for k in ("web", "mini"))
    assert f["a.jpg"]["web"].startswith("img/fotos/") and "a.jpg" not in f["a.jpg"]["web"]   # sin nombres en la ruta
    assert Image.open(web).size == (1600, 1000) and max(Image.open(mini).size) == 480


def test_instagram_de_persona():
    """persona --instagram guarda solo el usuario (acepta URL) y exportar lo lleva a la web."""
    import json
    env = base_temporal(); run(env, "init")
    fotos(env, "#sin-evento\n2025/01/01 - Persona F | Bea Dos => a.jpg\n")
    run(env, "persona", "--nombre", "persona f", "--instagram", "https://www.instagram.com/personaf/")
    assert db(env).execute("SELECT instagram FROM people WHERE clave='persona f'").fetchone() == ("personaf",)
    assert "no vale" in run(env, "persona", "--nombre", "Bea Dos", "--instagram", "javascript:alert(1)")
    assert "no existe" in run(env, "persona", "--nombre", "Nadie Mas", "--instagram", "x")
    salida = Path(env["ARCHIVO_DB"]).parent / "w.json"; run(env, "exportar", salida)
    p = {x["nombre"]: x for x in json.loads(salida.read_text(encoding="utf-8"))["personas"]}
    assert p["Persona F"]["instagram"] == "personaf" and p["Bea Dos"]["instagram"] == ""


def test_nota_de_foto():
    """foto --nota guarda el pie de foto (por nombre de fichero o parte única) y exportar lo lleva a la web."""
    import json
    env = base_temporal(); run(env, "init")
    fotos(env, "#sin-evento\n2025/01/01 - Ana Uno => 2025_01_01 - Ana.jpg\n2025/01/02 - Bea Dos => 2025_01_02 - Bea.jpg\n")
    run(env, "foto", "--archivo", "ana.jpg", "--nota", "Con Ana, tras la charla")
    assert db(env).execute("SELECT notas FROM photos WHERE archivo LIKE '%Ana.jpg'").fetchone() == ("Con Ana, tras la charla",)
    assert "varias" in run(env, "foto", "--archivo", "2025_01", "--nota", "x")      # ambigua: no toca nada
    assert "ninguna" in run(env, "foto", "--archivo", "zzz", "--nota", "x")
    salida = Path(env["ARCHIVO_DB"]).parent / "w.json"; run(env, "exportar", salida)
    f = {x["archivo"]: x for x in json.loads(salida.read_text(encoding="utf-8"))["fotos_sueltas"]}
    assert f["2025_01_01 - Ana.jpg"]["nota"] == "Con Ana, tras la charla" and f["2025_01_02 - Bea.jpg"]["nota"] == ""


def test_init_no_toca_base_existente():
    env = base_v1()
    out = run(env, "init")
    assert "migrar" in out, out
    assert db(env).execute("PRAGMA user_version").fetchone()[0] == 1, "init ha marcado como v2 una base v1"


def test_fotos_archivo_repetido_en_el_texto():
    env = base_temporal(); run(env, "init")
    out = fotos(env, "#evento A | | | | 2025-01-01\n2025/01/01 - Ana Uno => IMG_1.heic\n"
                     "#evento B | | | | 2025-02-01\n2025/02/01 - Bea Dos => IMG_1.heic\n")
    assert "IMG_1.heic" in out and "repetido" in out, out
    assert db(env).execute("SELECT COUNT(*) FROM photos").fetchone()[0] == 0, "se ha importado a medias"


def test_evento_con_viaje():
    env, _ = base_con_viajes()
    viaje = db(env).execute("SELECT slug FROM trips WHERE nombre LIKE 'Viaje al Congreso de Química%'").fetchone()[0]
    out = run(env, "evento", "--nombre", "10th EuChemS Chemistry Congress", "--fecha", "2026-07-12", "--viaje", viaje)
    r = db(env).execute("SELECT t.slug FROM events e JOIN trips t ON t.id = e.trip_id").fetchone()
    assert r == (viaje,), f"{r}\n{out}"


def test_catalogo_genera_imagen():
    import pymupdf
    env = base_temporal(); run(env, "init"); t = Path(env["ARCHIVO_DB"]).parent
    (t / "orig").mkdir()
    doc = pymupdf.open(); doc.new_page().insert_text((72, 72), "Certificado de prueba"); doc.save(t / "orig" / "cert.pdf")
    csv_ = t / "cat.csv"
    csv_.write_text("uid,num_archivo,tipo,titulo,organizador,fecha,rol_premio,evento,archivo\n"
                    "c-1,,certificado,Prueba,Org,2025-07,,,cert.pdf\n", encoding="utf-8")
    out = run(env, "importar-catalogo", csv_, "--originales", t / "orig", "--imagenes", t / "img")
    img = db(env).execute("SELECT front_web FROM objects WHERE uid = 'c-1'").fetchone()[0]
    assert img.endswith("c-1.jpg") and (t / "img" / "c-1.jpg").stat().st_size > 1000, f"{img}\n{out}"
    falta = t / "cat2.csv"
    falta.write_text("uid,num_archivo,tipo,titulo,organizador,fecha,rol_premio,evento,archivo\n"
                     "c-2,,certificado,Otra,Org,2025-07,,,no_existe.pdf\n", encoding="utf-8")
    assert "no_existe.pdf" in run(env, "importar-catalogo", falta, "--originales", t / "orig", "--imagenes", t / "img")


def test_catalogo_imagen_escaneada_despues():
    import pymupdf
    env = base_temporal(); run(env, "init"); t = Path(env["ARCHIVO_DB"]).parent
    cab = "uid,num_archivo,tipo,titulo,organizador,fecha,rol_premio,evento,archivo\n"
    csv_ = t / "cat.csv"; args = ["--originales", t / "orig", "--imagenes", t / "img"]
    csv_.write_text(cab + "c-1,001,certificado,Prueba,Org,2018-06,,,\n", encoding="utf-8")
    run(env, "importar-catalogo", csv_, *args)
    (t / "orig").mkdir()
    doc = pymupdf.open(); doc.new_page().insert_text((72, 72), "Escaneado"); doc.save(t / "orig" / "c1.pdf")
    csv_.write_text(cab + "c-1,001,certificado,Prueba,Org,2018-06,,,c1.pdf\n", encoding="utf-8")
    out = run(env, "importar-catalogo", csv_, *args)
    assert db(env).execute("SELECT front_web FROM objects WHERE uid = 'c-1'").fetchone()[0].endswith("c-1.jpg"), out
    assert db(env).execute("SELECT COUNT(*) FROM objects").fetchone()[0] == 1


def test_salida_utf8_sin_variables():
    """En Windows la consola es cp1252: sin forzar UTF-8 los acentos salen como '�' o rompen el programa."""
    env = base_temporal()
    for k in ("PYTHONIOENCODING", "PYTHONUTF8"):
        env.pop(k, None)
    subprocess.run([sys.executable, str(A), "init"], env=env, capture_output=True)
    r = subprocess.run([sys.executable, str(A), "importar-catalogo", ROOT / "tests" / "fixtures" / "catalogo_sin_evento.csv"],
                       env=env, capture_output=True)
    assert "catálogo:" in r.stdout.decode("utf-8", errors="replace"), r.stdout


def test_km_viajes():
    """Km por círculo máximo: Barcelona -> aeropuertos -> ciudades y vuelta; el manual manda; lo futuro no suma."""
    import json
    env = base_temporal(); run(env, "init")
    con = db(env)
    con.executescript("""
        INSERT INTO places (id, nombre, pais, lat, lng) VALUES (1, 'Barcelona', 'España', 41.3874, 2.1686),
          (2, 'Madrid', 'España', 40.4168, -3.7038), (3, 'Ciudad del Cabo', 'Sudáfrica', -33.9249, 18.4241);
        INSERT INTO airports (iata, lat, lng) VALUES ('BCN', 41.2974, 2.0833), ('DOH', 25.2731, 51.6081), ('CPT', -33.9715, 18.6021);
        INSERT INTO trips (id, slug, nombre, inicio, transporte, salida, escala, llegada, km_manual) VALUES
          (1, 'coche', 'Coche', '2020-01-01', 'Coche', NULL, NULL, NULL, NULL),
          (2, 'avion', 'Avión', '2021-01-01', 'Avión', 'BCN', 'DOH', 'CPT', NULL),
          (3, 'manual', 'Manual', '2022-01-01', 'Coche', NULL, NULL, NULL, 1234),
          (4, 'futuro', 'Futuro', '2999-01-01', 'Coche', NULL, NULL, NULL, NULL);
        INSERT INTO visits (place_id, trip_id, inicio) VALUES (2, 1, '2020-01-01'), (3, 2, '2021-01-02'), (2, 3, NULL), (2, 4, NULL);
    """)
    con.commit(); con.close()
    salida = Path(env["ARCHIVO_DB"]).parent / "web.json"
    out = run(env, "exportar", salida)
    d = json.loads(salida.read_text(encoding="utf-8"))
    km = {v["slug"]: v["km"] for v in d["viajes"]}
    assert 1000 <= km["coche"] <= 1020, km          # Barcelona-Madrid ~505 km, ida y vuelta
    assert 24000 <= km["avion"] <= 25500, km        # BCN-DOH ~4950 + DOH-CPT ~7380, ida y vuelta
    assert km["manual"] == 1234 and km["futuro"] == km["coche"], km
    assert d["totales"]["km"] == km["coche"] + km["avion"] + 1234, (d["totales"]["km"], out)
    vuelos = next(v for v in d["viajes"] if v["slug"] == "avion")["vuelos"]
    assert [(x["origen"]["iata"], x["destino"]["iata"]) for x in vuelos] == [("BCN", "DOH"), ("DOH", "CPT")], vuelos
    assert vuelos[0]["origen"]["lat"] == 41.2974
    assert next(v for v in d["viajes"] if v["slug"] == "coche")["vuelos"] == []


def test_viaje_alta_y_edicion():
    env = base_temporal(); run(env, "init")
    con = db(env)
    con.executescript("""INSERT INTO places (nombre, pais, lat, lng) VALUES ('Barcelona', 'España', 41.3874, 2.1686), ('París', 'Francia', 48.8566, 2.3522);
                         INSERT INTO airports (iata, lat, lng) VALUES ('BCN', 41.2974, 2.0833), ('ORY', 48.7262, 2.3652);""")
    con.commit(); con.close()
    args = ["viaje", "--nombre", "Premios (París)", "--inicio", "2026-12-03", "--fin", "2026-12-04", "--transporte", "Avión",
            "--salida", "BCN", "--llegada", "ORY", "--ciudad", "París"]
    run(env, *args); out = run(env, *args)
    con = db(env)
    assert con.execute("SELECT COUNT(*) FROM trips").fetchone()[0] == 1, out
    v = con.execute("SELECT t.slug, t.salida, t.llegada, vi.inicio, vi.fin FROM trips t JOIN visits vi ON vi.trip_id = t.id "
                    "JOIN places p ON p.id = vi.place_id WHERE p.nombre = 'París'").fetchall()
    assert v == [("premios-paris", "BCN", "ORY", "2026-12-03", "2026-12-04")], (v, out)
    out = run(env, "viaje", "--slug", "premios-paris", "--nombre", "Otros premios (París)", "--notas", "")
    r = con.execute("SELECT nombre, inicio, notas FROM trips").fetchall()
    assert r == [("Otros premios (París)", "2026-12-03", "")], (r, out)  # solo cambia lo que se pasa
    assert "no existe el aeropuerto" in run(env, "viaje", "--nombre", "X", "--salida", "ZZZ")


def base_pulir():
    env = base_temporal(); run(env, "init")
    con = db(env)
    con.executescript("""
        INSERT INTO places (id, nombre, pais, lat, lng) VALUES (1, 'Barcelona', 'España', 41.39, 2.17), (2, 'Madrid', 'España', 40.42, -3.70),
                                                               (3, 'Toledo', 'España', 39.86, -4.03);
        INSERT INTO trips (id, slug, nombre, inicio, fin, notas) VALUES (1, 'uno', 'Uno', '2020-05-01', '2020-05-03', 'Próximo viaje'),
                                                                 (2, 'dos', 'Dos', '2020-06-01', '2020-06-02', ''),
                                                                 (3, 'fut', 'Futuro', '2999-01-01', NULL, 'Próximo viaje');
        INSERT INTO visits (place_id, trip_id, inicio, fin, nota) VALUES (2, 1, NULL, NULL, 'Próximo viaje: Premios'),
                                                                         (2, 2, '2020-06-01', NULL, ''), (3, 2, '2020-06-02', NULL, ''),
                                                                         (2, 3, NULL, NULL, 'Próximo viaje: X');
        INSERT INTO events (slug, nombre, fecha, ciudad, trip_id) VALUES ('a', 'A', '2020-01-01', 'Barcelona', NULL),
               ('b', 'B', '2020-05-01', '', 1), ('c', 'C', '2020-06-01', '', 2), ('d', 'D', '2020-07-01', 'Sitio raro', NULL);
    """)
    con.commit(); con.close()
    return env


def test_pulir():
    env = base_pulir()
    out = run(env, "pulir"); run(env, "pulir")
    con = db(env)
    lugares = dict(con.execute("SELECT e.slug, p.nombre FROM events e LEFT JOIN places p ON p.id = e.place_id"))
    # por ciudad escrita, por el único lugar del viaje; con varias ciudades o ciudad desconocida, no se adivina
    assert lugares == {"a": "Barcelona", "b": "Madrid", "c": None, "d": None}, (lugares, out)
    v = con.execute("SELECT inicio, fin, nota FROM visits WHERE trip_id = 1").fetchone()
    assert v == ("2020-05-01", "2020-05-03", "Premios"), v       # fechas del viaje y nota al día
    assert con.execute("SELECT notas FROM trips WHERE slug = 'uno'").fetchone()[0] == ""
    assert con.execute("SELECT notas FROM trips WHERE slug = 'fut'").fetchone()[0] == "Próximo viaje"  # aún no ha llegado
    assert "Sitio raro" in out, out                              # avisa de lo que no puede enlazar


def test_lugar_y_pin():
    env = base_pulir()
    run(env, "lugar", "--nombre", "Toledo", "--lat", "39.8628", "--lng", "-4.0273", "--confianza", "alta", "--renombrar", "Toledo centro")
    run(env, "lugar", "--nombre", "Figueres", "--pais", "España", "--lat", "42.2666", "--lng", "2.9638")
    con = db(env)
    assert con.execute("SELECT nombre, lat, coord_confianza FROM places WHERE id = 3").fetchone() == ("Toledo centro", 39.8628, "alta")
    assert con.execute("SELECT lng FROM places WHERE nombre = 'Figueres'").fetchone() == (2.9638,)
    for _ in range(2):
        out = run(env, "pin", "--viaje", "dos", "--titulo", "El Principito", "--ciudad", "Madrid")
    r = con.execute("SELECT o.titulo, p.nombre, t.slug FROM objects o JOIN places p ON p.id = o.place_id "
                    "JOIN trips t ON t.id = o.trip_id WHERE o.tipo = 'pin'").fetchall()
    assert r == [("El Principito", "Madrid", "dos")], (r, out)


def test_nivel_premio():
    import json
    env = base_temporal(); run(env, "init")
    filas = [f"c-{i},{i:03d},certificado,T{i},Org,2025-01,{p}," for i, p in enumerate(
        ["1st Prize", "Winner", "3rd Place Award", "1st Finalist", "Top 10", "Speaker", "Participation Recognition", "Honor Roll"])]
    catalogo(env, filas)
    salida = Path(env["ARCHIVO_DB"]).parent / "web.json"
    run(env, "exportar", salida)
    d = json.loads(salida.read_text(encoding="utf-8"))
    niveles = [o["nivel"] for o in sorted(d["objetos_sueltos"], key=lambda o: int(o["uid"][2:]))]
    assert niveles == ["primer premio", "primer premio", "podio", "finalista", "finalista", "ponente", "participación", "mención"], niveles
    assert d["totales"]["premios"]["primer premio"] == 2, d["totales"]["premios"]


def test_evento_editar_y_fechas_de_visitas():
    env = base_pulir()
    run(env, "pulir")                                            # la visita del viaje 'uno' hereda 2020-05-01..03
    out = run(env, "evento", "--slug", "d", "--ciudad", "Toledo", "--lugar", "Catedral")
    run(env, "pulir")
    con = db(env)
    assert con.execute("SELECT e.lugar, p.nombre FROM events e JOIN places p ON p.id = e.place_id WHERE slug = 'd'").fetchone()         == ("Catedral", "Toledo"), out
    run(env, "viaje", "--slug", "uno", "--inicio", "2020-04", "--fin", "2020-04")
    assert con.execute("SELECT inicio, fin FROM visits WHERE trip_id = 1").fetchone() == ("2020-04", "2020-04")
    assert con.execute("SELECT inicio FROM visits WHERE trip_id = 2 ORDER BY inicio").fetchall() == [("2020-06-01",), ("2020-06-02",)]


def test_categorias():
    env = base_pulir(); t = Path(env["ARCHIVO_DB"]).parent / "cat.csv"
    t.write_text("uid,num_archivo,tipo,titulo,organizador,fecha,rol_premio,categoria_propuesta,evento\n"
                 "c-1,001,certificado,T1,O,2020-01,,robótica,a\nc-2,002,certificado,T2,O,2020-01,,IA/ética,a\n"
                 "c-3,003,certificado,T3,O,2020-01,,neurociencia/divulgación,\nc-4,004,certificado,T4,O,2020-01,,emprendimiento/tecnología,\n"
                 "c-5,005,certificado,T5,O,2020-01,,TIC/mujeres en tecnología,\nc-6,006,certificado,T6,O,2020-01,,,\n", encoding="utf-8")
    run(env, "importar-catalogo", t)
    con = db(env)
    con.execute("UPDATE objects SET categoria = '' WHERE uid = 'c-1'"); con.commit()  # importado antes de existir la columna
    out = run(env, "importar-catalogo", t)                                             # se rellena al repetir
    cat = dict(con.execute("SELECT uid, categoria FROM objects"))
    assert cat == {"c-1": "Ciencia y tecnología", "c-2": "Ciencia y tecnología", "c-3": "Divulgación", "c-4": "Emprendimiento",
                   "c-5": "Impacto social", "c-6": ""}, (cat, out)
    run(env, "pulir")
    assert con.execute("SELECT categoria FROM events WHERE slug = 'a'").fetchone() == ("Ciencia y tecnología",)


def test_pulir_coherencia():
    env = base_pulir(); con = db(env)
    con.execute("UPDATE places SET continente = 'Europa', region = 'Madrid' WHERE nombre = 'Madrid'")
    con.execute("INSERT INTO places (nombre, pais, lat, lng) VALUES ('Getafe', 'España', 40.3, -3.7)"); con.commit()
    run(env, "pulir")
    assert con.execute("SELECT continente FROM places WHERE nombre = 'Getafe'").fetchone() == ("Europa",)
    assert con.execute("SELECT modalidad, pais FROM events WHERE slug = 'a'").fetchone() == ("presencial", "España")
    assert con.execute("SELECT modalidad FROM events WHERE slug = 'd'").fetchone() == ("presencial",)  # regla: un evento es presencial


def test_base_antigua_pide_migrar():
    env = base_temporal(); con = sqlite3.connect(env["ARCHIVO_DB"])
    con.executescript((ROOT / "tests" / "fixtures" / "schema_v1.sql").read_text(encoding="utf-8"))
    con.executescript((ROOT / "herramientas" / "archivo_db" / "migraciones" / "002.sql").read_text(encoding="utf-8")); con.close()
    assert "migrar" in run(env, "viaje", "--nombre", "X", "--km", "10")
    assert "migrar" in run(env, "init")


def test_viaje_nota_de_visita():
    env = base_pulir()
    run(env, "viaje", "--slug", "uno", "--ciudad", "Madrid", "--nota", "Premios nuevos")
    assert db(env).execute("SELECT nota FROM visits WHERE trip_id = 1").fetchall() == [("Premios nuevos",)]


def _exportado_cifras():
    import json
    env, _ = base_con_viajes()
    salida = Path(env["ARCHIVO_DB"]).parent / "web.json"
    run(env, "exportar", salida)
    return json.loads(salida.read_text(encoding="utf-8"))


def test_anual():
    """La suma de km por año cuadra con totales.km; los viajes futuros no suman; España no es «país nuevo»."""
    d = _exportado_cifras()
    assert sum(a["km"] for a in d["anual"].values()) == d["totales"]["km"] > 0, d["anual"]
    assert sum(a["viajes"] for a in d["anual"].values()) == len([v for v in d["viajes"] if v["estado"] != "futuro"])
    p = d["totales"]["km_perspectiva"]
    assert p["vueltas_tierra"] == round(d["totales"]["km"] / 40075, 2) and {"avion", "tren", "coche"} == set(p["por_transporte"])
    assert sum(a["paises_nuevos"] for a in d["anual"].values()) == len({c["pais"] for c in d["totales"]["ciudades"]} - {"España"})


def test_hitos():
    """Los hitos salen ordenados, sin repetir y sin fechas futuras."""
    import datetime
    h = _exportado_cifras()["hitos"]
    assert [x["fecha"] for x in h] == sorted(x["fecha"] for x in h)
    assert len({x["texto"] for x in h}) == len(h)
    assert all(x["fecha"] <= datetime.date.today().isoformat() for x in h)
    assert any(x["tipo"] == "pais" for x in h), h


if __name__ == "__main__":
    tests = [f for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for f in tests:
        f()
        print(f"   {f.__name__}: OK")
