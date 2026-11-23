#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
archivo.py - Base de datos del Certificates Archive (SQLite).

Comandos:
  init                         crea datos/archivo.sqlite con el esquema (v2)
  migrar                       pasa la base a la última versión (v4) (copia previa)
  copia                        copia de seguridad en datos/copias/
  importar-viajes XLSX         viajes, visitas, lugares, aeropuertos y pines desde mis_viajes.xlsx
  viaje ...                    crea un viaje o cambia uno existente (--slug)
  sello ...                    añade un sello LEGO del pasaporte
  pin ...                      añade un pin a un viaje
  lugar ...                    crea un lugar o corrige sus coordenadas
  pulir                        arreglos automáticos: lugar de eventos, fechas de visitas, notas caducadas
  importar-objetos FICHERO     lanyards/pines desde archive.json (lo genera Lanyard Archive)
  importar-catalogo CSV        certificados desde certificates_archive_v1.csv
  importar-fotos FICHERO [--zip gente.zip]   fotos con personas (formato abajo); extrae las imágenes del zip
  foto --archivo F --nota T        pie de foto (F: nombre del fichero o una parte que no se repita)
  persona --nombre N --instagram U   guarda el Instagram de una persona (usuario o URL)
  fotos-web                    WebP (1600 px) y miniatura de cada foto, en web/img/fotos/ (HEIF incluido)
  importar-charlas FICHERO     grabaciones (vídeos del móvil, por ruta local)
  evento ...                   crea o muestra un evento
  charla ...                   añade una grabación (keynote, mesa redonda, pitch)
  resumen                      recuento y avisos de calidad
  exportar SALIDA.json         datos para la web

Formato de fotos (un bloque por evento, viaje o fotos sueltas):
  #evento Nombre del evento | Organizador | Lugar | Ciudad | AAAA-MM-DD
  #viaje Nombre o slug del viaje          (fotos de un viaje sin evento, p. ej. familiar)
  #sin-evento                             (fotos sueltas: solo fecha y personas)
  2025/09/09 - Persona A | Persona B | Persona C | Persona D
  2025/09/09 - Carla Monté | Persona A => IMG_0412.heic
  - La parte "=> archivo" es opcional; sin ella se usa un identificador de la línea.
  - Cada línea de foto se importa una sola vez aunque repitas el fichero.
"""
from __future__ import annotations

import argparse
import csv
import os
import datetime as dt
import difflib
import hashlib
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DB = Path(os.environ.get("ARCHIVO_DB", ROOT / "datos" / "archivo.sqlite"))
SCHEMA = HERE / "schema.sql"
DATE_RE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
PHOTO_RE = re.compile(r"^(\d{4})[/-](\d{2})[/-](\d{2})\s*-\s*(.+?)(?:\s*=>\s*(\S.*))?$")


# --------------------------------------------------------------------------- utilidades
def norm(s: str) -> str:
    """Clave de comparación: sin acentos, minúsculas, espacios colapsados."""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9' -]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def slug(s: str, n: int = 60) -> str:
    return re.sub(r"[^a-z0-9]+", "-", norm(s)).strip("-")[:n] or "sin-nombre"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def iso_date(v: str) -> str:
    v = (v or "").strip().replace("/", "-")
    if not DATE_RE.fullmatch(v):
        raise ValueError(f"fecha no válida: '{v}' (usa AAAA, AAAA-MM o AAAA-MM-DD)")
    return v


def connect(path: Path | None = None) -> sqlite3.Connection:
    path = path or DB
    if not path.exists():
        raise SystemExit(f"No existe {path}. Ejecuta primero: python archivo.py init")
    con = sqlite3.connect(path)
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    return con


SIN_EVENTO = object()  # bloque #viaje o #sin-evento: la foto no crea evento
FOTOS_DIR = Path(os.environ.get("ARCHIVO_FOTOS", ROOT / "datos" / "fotos_originales"))
FOTOS_WEB = Path(os.environ.get("ARCHIVO_FOTOS_WEB", ROOT / "web" / "img" / "fotos"))  # fuera de git


def foto_web_nombre(archivo: str) -> str:
    """Nombre del WebP: un hash del original, para que la ruta no lleve nombres de personas."""
    return hashlib.sha1(archivo.encode("utf-8")).hexdigest()[:12]


def exif_date(data: bytes) -> str | None:
    """Fecha de captura (AAAA-MM-DD) desde los bytes de una foto, JPG o HEIC. None si no hay."""
    try:
        from PIL import Image
        try:
            import pillow_heif; pillow_heif.register_heif_opener()
        except ImportError:
            pass
        import io
        with Image.open(io.BytesIO(data)) as im:
            ex = im.getexif()
            v = ex.get_ifd(0x8769).get(36867) or ex.get(306)
        return str(v)[:10].replace(":", "-") if v else None
    except Exception:
        return None


def extraer_zip(zip_path: Path, nombres: set[str]) -> dict[str, bytes]:
    """Lee del zip solo los ficheros pedidos (sin extraer rutas peligrosas) y los guarda en FOTOS_DIR."""
    import zipfile
    found = {}
    FOTOS_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        index = {Path(i.filename).name: i for i in z.infolist() if not i.is_dir()}
        for n in sorted(nombres):
            info = index.get(n)
            if not info:
                continue
            data = z.read(info)
            (FOTOS_DIR / n).write_bytes(data)
            found[n] = data
    return found


# --------------------------------------------------------------------------- entidades
def get_or_create_event(con, nombre, fecha, organizador="", lugar="", ciudad="", pais="",
                        modalidad="", categoria="") -> int:
    fecha = iso_date(fecha)
    s = f"{fecha}_{slug(nombre)}"
    row = con.execute("SELECT id FROM events WHERE slug = ?", (s,)).fetchone()
    if row:
        return row["id"]
    cur = con.execute(
        "INSERT INTO events (slug, nombre, fecha, organizador, lugar, ciudad, pais, modalidad, categoria) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (s, nombre.strip(), fecha, organizador, lugar, ciudad, pais, modalidad, categoria))
    return cur.lastrowid


def get_or_create_person(con, nombre: str) -> int:
    nombre = re.sub(r"\s+", " ", nombre).strip()
    k = norm(nombre)
    row = con.execute("SELECT id FROM people WHERE clave = ?", (k,)).fetchone()
    if row:
        return row["id"]
    return con.execute("INSERT INTO people (nombre, clave) VALUES (?,?)", (nombre, k)).lastrowid


def lugar_por_nombre(con, ciudad: str, pais: str = "") -> int:
    """Lugar por nombre (y país si se da). Si no existe se crea; si hay varios con ese nombre, pide el país."""
    filas = con.execute("SELECT id FROM places WHERE nombre = ?" + (" AND pais = ?" if pais else ""),
                        (ciudad, pais) if pais else (ciudad,)).fetchall()
    if len(filas) > 1:
        raise SystemExit(f"Hay varios lugares llamados '{ciudad}': indica el país con --pais")
    if filas:
        return filas[0]["id"]
    return con.execute("INSERT INTO places (nombre, pais) VALUES (?,?)", (ciudad, pais)).lastrowid


def near_duplicate_people(con, umbral: float = 0.88):
    """Personas con nombres casi iguales (posible error de escritura). No fusiona nada: solo avisa."""
    rows = con.execute("SELECT id, nombre, clave FROM people ORDER BY clave").fetchall()
    out = []
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            r = difflib.SequenceMatcher(None, a["clave"], b["clave"]).ratio()
            if r >= umbral:
                out.append((a["nombre"], b["nombre"], round(r, 2)))
    return out


def hacer_copia(motivo: str = "") -> Path:
    """Copia consistente de la base (API de backup de SQLite) en datos/copias/."""
    destino = DB.parent / "copias" / f"archivo_{dt.datetime.now():%Y%m%d-%H%M%S}{'_' + motivo if motivo else ''}.sqlite"
    destino.parent.mkdir(parents=True, exist_ok=True)
    src = connect(); dst = sqlite3.connect(destino)
    with dst:
        src.backup(dst)
    src.close(); dst.close()
    return destino


def version(con) -> int:
    return con.execute("PRAGMA user_version").fetchone()[0]


ULTIMA = 4  # versión de schema.sql; migraciones/00N.sql lleva de N-1 a N


def km_entre(a, b) -> float:
    """Distancia de círculo máximo (haversine) en km entre dos puntos (lat, lng)."""
    import math
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def ruta_viaje(con, trip) -> tuple[float, list[dict]]:
    """Km calculados (ida y vuelta) y tramos de vuelo. Ida: Barcelona -> salida -> escala -> llegada -> ciudades
    por fecha; vuelta: última ciudad -> los mismos aeropuertos al revés -> Barcelona. Se saltan puntos sin coordenadas."""
    casa = con.execute("SELECT lat, lng FROM places WHERE nombre = 'Barcelona' AND lat IS NOT NULL").fetchone()
    aeros = [con.execute("SELECT iata, lat, lng FROM airports WHERE iata = ? AND lat IS NOT NULL", (c,)).fetchone()
             for c in (trip["salida"], trip["escala"], trip["llegada"]) if c]
    aeros = [a for a in aeros if a]
    ciudades = con.execute("SELECT p.lat, p.lng FROM visits v JOIN places p ON p.id = v.place_id WHERE v.trip_id = ? "
                           "AND p.lat IS NOT NULL ORDER BY v.inicio IS NULL, v.inicio, v.id", (trip["id"],)).fetchall()
    inicio = ([tuple(casa)] if casa else []) + [(a["lat"], a["lng"]) for a in aeros]
    ruta = inicio + [tuple(c) for c in ciudades] + inicio[::-1]  # vuelta por el mismo camino
    km = sum(km_entre(a, b) for a, b in zip(ruta, ruta[1:]))
    punto = lambda a: {"iata": a["iata"], "lat": a["lat"], "lng": a["lng"]}
    vuelos = [{"origen": punto(a), "destino": punto(b)} for a, b in zip(aeros, aeros[1:])]
    return km, vuelos


def nivel_premio(premio: str) -> str:
    """Nivel común para premios escritos de mil formas ("1st Prize", "Winner", "Finalista nacional"...)."""
    p = norm(premio)
    if not p:
        return ""
    if re.search(r"1st (prize|place)|winner|primer premio|ganador", p):
        return "primer premio"
    if re.search(r"2nd|3rd|segundo|tercer", p):
        return "podio"
    if "final" in p or re.search(r"\btop \d", p):
        return "finalista"
    if re.search(r"speaker|ponente", p):
        return "ponente"
    if "particip" in p:
        return "participación"
    return "mención"  # honor roll, distinction, merit, ambassador...


def exigir_v2(con):
    if version(con) < 2:
        raise SystemExit("La base está en v1. Ejecuta: python archivo.py migrar")


# --------------------------------------------------------------------------- importadores
def cmd_migrar(_):
    con = connect()
    v = version(con)
    if v >= ULTIMA:
        print(f"La base ya está en v{ULTIMA}: no hay nada que migrar."); return
    copia = hacer_copia(f"antes-v{ULTIMA}")
    con.isolation_level = None  # transacción manual: el script entero se confirma o se deshace
    con.execute("PRAGMA foreign_keys = OFF")
    try:
        con.execute("BEGIN")
        for n in range(v + 1, ULTIMA + 1):
            for stmt in (HERE / "migraciones" / f"{n:03d}.sql").read_text(encoding="utf-8").split(";\n"):
                if stmt.strip() and not all(l.strip().startswith("--") or not l.strip() for l in stmt.splitlines()):
                    con.execute(stmt)
        fk = con.execute("PRAGMA foreign_key_check").fetchall()
        if fk:
            raise sqlite3.IntegrityError(f"{len(fk)} claves foráneas rotas")
        con.execute("COMMIT")
    except sqlite3.Error as e:
        con.execute("ROLLBACK")
        raise SystemExit(f"La migración ha fallado y no se ha cambiado nada ({e}). Copia previa: {copia}")
    con.execute("PRAGMA foreign_keys = ON")
    print(f"Base migrada a v{ULTIMA}. Copia previa: {copia}")


def _hoja(wb, nombre: str, requeridas: list[str]):
    """Filas (n.º de fila, dict) de una hoja del Excel; la cabecera se busca por nombre de columna, no por posición."""
    rows = list(wb[nombre].iter_rows(values_only=True))
    for i, r in enumerate(rows[:10]):
        cab = ["" if c is None else str(c).strip() for c in r]
        if all(c in cab for c in requeridas):
            for n, fila in enumerate(rows[i + 1:], i + 2):
                d = dict(zip(cab, fila))
                if d.get(requeridas[0]) not in (None, ""):
                    yield n, d
            return
    raise SystemExit(f"hoja '{nombre}': no encuentro las columnas {requeridas}")


def _fecha(v) -> str | None:
    if v in (None, ""):
        return None
    return v.date().isoformat() if hasattr(v, "date") else iso_date(str(v))


def _texto(v) -> str:
    return "" if v is None else str(v).strip()


def cmd_importar_viajes(a):
    import openpyxl
    con = connect(); exigir_v2(con)
    wb = openpyxl.load_workbook(a.fichero, data_only=True)
    leer = lambda p: list(csv.DictReader(open(p, encoding="utf-8-sig"))) if Path(p).exists() else []
    geo = {(r["ciudad"], r["pais"]): r for r in leer(a.geo)}
    aero_geo = {r["iata"]: r for r in leer(a.aeropuertos)}
    continentes = {_texto(d["País"]): _texto(d["Continente"]) for _, d in _hoja(wb, "Países", ["País", "Continente"])}
    num = lambda v: float(v) if v not in (None, "") else None
    n = dict(viajes=0, visitas=0, lugares=0, aeropuertos=0, pines=0)

    def lugar(nombre, pais, region="", continente="") -> int:
        row = con.execute("SELECT id FROM places WHERE nombre = ? AND pais = ?", (nombre, pais)).fetchone()
        if row:
            return row["id"]
        g = geo.get((nombre, pais), {})
        if not g:
            print(f"  AVISO: '{nombre}' ({pais}) no tiene coordenadas en {Path(a.geo).name}")
        n["lugares"] += 1
        return con.execute(
            "INSERT INTO places (nombre, region, pais, continente, lat, lng, coord_confianza) VALUES (?,?,?,?,?,?,?)",
            (nombre, region, pais, continente or continentes.get(pais, ""), num(g.get("lat")), num(g.get("lng")),
             g.get("coord_confianza", ""))).lastrowid

    with con:
        for _, d in _hoja(wb, "Aeropuertos", ["IATA", "Aeropuerto", "Ciudad", "País"]):
            iata = _texto(d["IATA"]).upper()
            if con.execute("SELECT 1 FROM airports WHERE iata = ?", (iata,)).fetchone():
                continue
            g = aero_geo.get(iata, {})
            con.execute("INSERT INTO airports (iata, nombre, place_id, lat, lng) VALUES (?,?,?,?,?)",
                        (iata, _texto(d["Aeropuerto"]), lugar(_texto(d["Ciudad"]), _texto(d["País"])),
                         num(g.get("lat")), num(g.get("lng"))))
            n["aeropuertos"] += 1

        viajes = {}
        for fila, d in _hoja(wb, "Viajes", ["Viaje", "Fecha inicio", "Fecha fin"]):
            nombre = _texto(d["Viaje"])
            row = con.execute("SELECT id FROM trips WHERE slug = ?", (slug(nombre),)).fetchone()
            if row:
                viajes[nombre] = row["id"]; continue
            codigos = []
            for col in ("Salida", "Llegada", "Escala"):
                c = _texto(d.get(col)).upper() or None
                if c and not con.execute("SELECT 1 FROM airports WHERE iata = ?", (c,)).fetchone():
                    print(f"  AVISO fila {fila} de Viajes: el aeropuerto '{c}' no está en la hoja Aeropuertos; se deja vacío")
                    c = None
                codigos.append(c)
            viajes[nombre] = con.execute(
                "INSERT INTO trips (slug, nombre, inicio, fin, transporte, salida, llegada, escala, motivo, notas) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (slug(nombre), nombre, _fecha(d["Fecha inicio"]), _fecha(d["Fecha fin"]), _texto(d.get("Transporte")),
                 *codigos, _texto(d.get("Motivo / Descripción")), _texto(d.get("Notas")))).lastrowid
            n["viajes"] += 1

        for fila, d in _hoja(wb, "Ciudades", ["Ciudad", "País", "Viaje"]):
            ciudad, viaje = _texto(d["Ciudad"]), _texto(d["Viaje"])
            trip = viajes.get(viaje) if viaje else None
            if viaje and trip is None:
                print(f"  AVISO fila {fila} de Ciudades: el viaje '{viaje}' no está en la hoja Viajes; la visita queda sin viaje")
            pid = lugar(ciudad, _texto(d["País"]), _texto(d.get("Región")), _texto(d.get("Continente")))
            inicio = _fecha(d.get("Fecha inicio"))
            # sin UNIQUE útil cuando faltan fechas (NULL <> NULL en SQLite): se busca con IS
            if not con.execute("SELECT 1 FROM visits WHERE place_id = ? AND trip_id IS ? AND inicio IS ?",
                               (pid, trip, inicio)).fetchone():
                con.execute("INSERT INTO visits (place_id, trip_id, inicio, fin, nota) VALUES (?,?,?,?,?)",
                            (pid, trip, inicio, _fecha(d.get("Fecha fin")), _texto(d.get("Nota"))))
                n["visitas"] += 1
            if _texto(d.get("Pin")) == "☑":
                pin_id = _texto(d.get("ID pin"))
                cur = con.execute("INSERT OR IGNORE INTO objects (uid, tipo, place_id, trip_id, pin_id, created_utc) "
                                  "VALUES (?,?,?,?,?,?)", (f"pin-{slug(f'{ciudad} {pin_id}')}", "pin", pid, trip, pin_id, now()))
                n["pines"] += cur.rowcount
    print(f"viajes: {n['viajes']} nuevos · visitas: {n['visitas']} · lugares: {n['lugares']} · "
          f"aeropuertos: {n['aeropuertos']} · pines: {n['pines']}")


def cmd_sello(a):
    con = connect(); exigir_v2(con)
    fecha = iso_date(a.fecha)
    uid = f"sello-{fecha}-{slug(a.sitio)}"
    with con:
        if con.execute("SELECT 1 FROM objects WHERE uid = ?", (uid,)).fetchone():
            print(f"sello {uid}: ya existía"); return
        trip = None
        if a.viaje:
            row = con.execute("SELECT id FROM trips WHERE slug = ?", (a.viaje,)).fetchone()
            if not row:
                raise SystemExit(f"no existe el viaje '{a.viaje}' (mira los slugs con: archivo.py resumen)")
            trip = row["id"]
        con.execute("INSERT INTO objects (uid, tipo, fecha, sitio, place_id, trip_id, front_web, created_utc) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (uid, "sello", fecha, a.sitio.strip(), lugar_por_nombre(con, a.ciudad.strip(), a.pais.strip()),
                     trip, a.imagen, now()))
    print(f"sello {uid}: añadido")


def cmd_viaje(a):
    """Crea un viaje o, si el slug ya existe, cambia solo los campos que se pasan."""
    con = connect(); exigir_v2(con)
    clave = a.slug or slug(a.nombre or "")
    if not clave:
        raise SystemExit("indica --nombre (viaje nuevo) o --slug (viaje existente)")
    campos = {k: getattr(a, k) for k in ("nombre", "inicio", "fin", "transporte", "salida", "escala", "llegada",
                                          "motivo", "notas", "km_manual") if getattr(a, k) is not None}
    for k in ("inicio", "fin"):
        if campos.get(k):
            campos[k] = iso_date(campos[k])
    for k in ("salida", "escala", "llegada"):
        if campos.get(k):
            campos[k] = campos[k].upper()
            if not con.execute("SELECT 1 FROM airports WHERE iata = ?", (campos[k],)).fetchone():
                raise SystemExit(f"no existe el aeropuerto '{campos[k]}' (no se ha cambiado nada)")
    with con:
        t = con.execute("SELECT id FROM trips WHERE slug = ?", (clave,)).fetchone()
        if t:
            if campos:
                con.execute(f"UPDATE trips SET {', '.join(k + ' = ?' for k in campos)} WHERE id = ?", (*campos.values(), t["id"]))
            tid, accion = t["id"], "actualizado"
        else:
            if not a.nombre:
                raise SystemExit(f"no existe el viaje '{clave}': para crearlo indica --nombre")
            campos["slug"] = clave
            tid = con.execute(f"INSERT INTO trips ({', '.join(campos)}) VALUES ({', '.join('?' * len(campos))})",
                              tuple(campos.values())).lastrowid
            accion = "añadido"
        if a.ciudad:
            v = con.execute("SELECT inicio, fin FROM trips WHERE id = ?", (tid,)).fetchone()
            pid = lugar_por_nombre(con, a.ciudad.strip(), a.pais.strip())
            if not con.execute("SELECT 1 FROM visits WHERE place_id = ? AND trip_id = ? AND inicio IS ?", (pid, tid, v["inicio"])).fetchone():
                con.execute("INSERT INTO visits (place_id, trip_id, inicio, fin) VALUES (?,?,?,?)", (pid, tid, v["inicio"], v["fin"]))
    print(f"viaje {clave}: {accion}")


def cmd_lugar(a):
    """Crea un lugar o corrige sus coordenadas (y su nombre con --renombrar)."""
    con = connect(); exigir_v2(con)
    with con:
        pid = lugar_por_nombre(con, a.nombre.strip(), a.pais.strip())
        con.execute("UPDATE places SET lat = ?, lng = ?, coord_confianza = ? WHERE id = ?", (a.lat, a.lng, a.confianza, pid))
        if a.renombrar:
            con.execute("UPDATE places SET nombre = ? WHERE id = ?", (a.renombrar.strip(), pid))
    print(f"lugar {a.renombrar or a.nombre}: {a.lat}, {a.lng} ({a.confianza})")


def cmd_pin(a):
    con = connect(); exigir_v2(con)
    t = con.execute("SELECT id, slug FROM trips WHERE slug = ?", (a.viaje,)).fetchone()
    if not t:
        raise SystemExit(f"no existe el viaje '{a.viaje}' (mira los slugs con: archivo.py resumen)")
    uid = f"pin-{slug(f'{a.titulo} {t[1]}')}"
    with con:
        if con.execute("SELECT 1 FROM objects WHERE uid = ?", (uid,)).fetchone():
            print(f"pin {uid}: ya existía"); return
        con.execute("INSERT INTO objects (uid, tipo, titulo, place_id, trip_id, created_utc) VALUES (?,?,?,?,?,?)",
                    (uid, "pin", a.titulo.strip(), lugar_por_nombre(con, a.ciudad.strip(), a.pais.strip()), t[0], now()))
    print(f"pin {uid}: añadido")


def cmd_pulir(_):
    """Arreglos automáticos y repetibles: lugar de los eventos, fechas de visitas y notas de 'Próximo viaje' caducadas."""
    con = connect(); exigir_v2(con)
    n = dict(eventos=0, visitas=0, notas=0)
    with con:
        for e in con.execute("SELECT id, slug, ciudad, trip_id FROM events WHERE place_id IS NULL").fetchall():
            por_ciudad = con.execute("SELECT id FROM places WHERE nombre = ? AND lat IS NOT NULL", (e["ciudad"],)).fetchall()
            del_viaje = con.execute("SELECT DISTINCT place_id FROM visits WHERE trip_id = ?", (e["trip_id"],)).fetchall()
            pid = por_ciudad[0][0] if len(por_ciudad) == 1 else del_viaje[0][0] if not e["ciudad"] and len(del_viaje) == 1 else None
            if pid:
                con.execute("UPDATE events SET place_id = ? WHERE id = ?", (pid, e["id"])); n["eventos"] += 1
            elif e["ciudad"]:
                print(f"  AVISO evento {e['slug']}: no encuentro el lugar '{e['ciudad']}' con coordenadas (usa: archivo.py lugar)")
        n["visitas"] = con.execute("UPDATE visits SET inicio = (SELECT inicio FROM trips t WHERE t.id = visits.trip_id), "
                                   "fin = (SELECT fin FROM trips t WHERE t.id = visits.trip_id) WHERE inicio IS NULL AND "
                                   "(SELECT inicio FROM trips t WHERE t.id = visits.trip_id) IS NOT NULL").rowcount
        pasados = "(SELECT id FROM v_viajes WHERE estado = 'pasado')"
        n["notas"] = con.execute(f"UPDATE trips SET notas = '' WHERE notas = 'Próximo viaje' AND id IN {pasados}").rowcount
        n["notas"] += con.execute(f"UPDATE visits SET nota = trim(substr(nota, length('Próximo viaje:') + 1)) "
                                  f"WHERE nota LIKE 'Próximo viaje:%' AND trip_id IN {pasados}").rowcount
    print(f"eventos con lugar: {n['eventos']} · visitas con fecha: {n['visitas']} · notas caducadas: {n['notas']}")


def cmd_copia(_):
    print(f"copia creada: {hacer_copia()}")


def cmd_init(_):
    if DB.exists():
        v = version(sqlite3.connect(DB))
        if v < 2:
            raise SystemExit(f"La base ya existe en v{v}: usa python archivo.py migrar (init no la toca)")
        print(f"La base ya existe (v{v}): no hay nada que crear."); return
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA.read_text(encoding="utf-8"))
    con.commit(); con.close()
    print(f"Base de datos creada: {DB}")


def cmd_importar_objetos(a):
    con = connect()
    records = json.loads(Path(a.fichero).read_text(encoding="utf-8"))
    nuevos = repetidos = 0
    with con:
        for r in records:
            if con.execute("SELECT 1 FROM objects WHERE uid = ?", (r["id"],)).fetchone():
                repetidos += 1; continue
            ev = get_or_create_event(con, r.get("evento", "Sin título"), r.get("fecha", ""),
                                     r.get("organizador", ""), r.get("lugar", ""), r.get("ciudad", ""))
            tipo = "lanyard" if r.get("tipo", "lanyard") != "pin" else "pin"
            con.execute(
                "INSERT INTO objects (uid, event_id, tipo, rol, premio, place_id, pin_id, ancho_mm, alto_mm, forma, "
                "agujero_mm, anclaje_x, anclaje_y, front_web, back_web, avisos, created_utc) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (r["id"], ev, tipo, r.get("rol", ""), "",
                 lugar_por_nombre(con, r["ciudad"]) if tipo == "pin" and r.get("ciudad") else None,
                 r.get("pin_id", ""), r.get("ancho_mm"), r.get("alto_mm"), r.get("forma", ""),
                 r.get("agujero_mm", ""), r.get("anclaje_x") or None, r.get("anclaje_y") or None,
                 r.get("front_web", ""), r.get("back_web", ""), r.get("avisos", ""), now()))
            nuevos += 1
    print(f"objetos: {nuevos} nuevos · {repetidos} ya existían")


def imagen_web(origen: Path, carpeta: Path, uid: str, ancho: int = 1400) -> str:
    """Primera página de un PDF (o una imagen) a JPG para la web. Devuelve la ruta relativa a web/."""
    import pymupdf
    pagina = pymupdf.open(origen)[0]
    zoom = ancho / pagina.rect.width
    carpeta.mkdir(parents=True, exist_ok=True)
    pagina.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).save(carpeta / f"{uid}.jpg", jpg_quality=85)
    return f"img/certificados/{uid}.jpg"


def cmd_importar_catalogo(a):
    con = connect()
    nuevos = repetidos = imagenes = 0
    with open(a.fichero, encoding="utf-8-sig", newline="") as f, con:
        lector = csv.DictReader(f)
        con_columna_evento = "evento" in (lector.fieldnames or [])
        def imagen(fila, uid, archivo):
            origen = Path(a.originales) / archivo
            if origen.exists():
                return imagen_web(origen, Path(a.imagenes), uid)
            print(f"  AVISO fila {fila}: no encuentro '{archivo}' en {a.originales}; se importa sin imagen")
            return ""

        for fila, r in enumerate(lector, 2):
            uid = (r.get("uid") or "").strip()
            archivo = (r.get("archivo") or "").strip()
            existe = con.execute("SELECT front_web FROM objects WHERE uid = ?", (uid,)).fetchone() if uid else None
            if not uid or existe:
                repetidos += 1
                if existe and archivo and not existe["front_web"]:  # certificado escaneado después de importarlo
                    img = imagen(fila, uid, archivo)
                    if img:
                        con.execute("UPDATE objects SET front_web = ? WHERE uid = ?", (img, uid)); imagenes += 1
                continue
            if not con_columna_evento:  # catálogo antiguo: un evento por certificado
                ev = get_or_create_event(con, r["titulo"], r["fecha"], r.get("organizador", ""), r.get("lugar", ""))
            elif (r.get("evento") or "").strip():
                row = con.execute("SELECT id FROM events WHERE slug = ?", (r["evento"].strip(),)).fetchone()
                if not row:
                    raise SystemExit(f"fila {fila}: no existe el evento '{r['evento'].strip()}' (no se ha importado nada)")
                ev = row["id"]
            else:
                ev = None  # certificado suelto (curso online...)
            tipo = {"certificado": "certificado", "lanyard": "lanyard", "foto": "foto", "pin": "pin"}.get(
                (r.get("tipo") or "certificado").strip(), "otro")
            img = imagen(fila, uid, archivo) if archivo else ""
            con.execute(
                "INSERT INTO objects (uid, event_id, tipo, titulo, organizador, fecha, premio, num_archivo, front_web, created_utc) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (uid, ev, tipo, r.get("titulo", "").strip(), r.get("organizador", "").strip(),
                 iso_date(r["fecha"]) if r.get("fecha") else "", r.get("rol_premio", ""), r.get("num_archivo", ""),
                 img, now()))
            nuevos += 1
    print(f"catálogo: {nuevos} nuevos · {repetidos} ya existían o sin uid" + (f" · imágenes añadidas: {imagenes}" if imagenes else ""))


def cmd_importar_fotos(a):
    con = connect()
    lines = Path(a.fichero).read_text(encoding="utf-8").splitlines()
    # ficheros referenciados con "=>" en el texto; si hay zip, se extraen y se comprueban
    refs = set()
    for raw in lines:
        m = PHOTO_RE.match(raw.strip())
        if m and m.group(5):
            refs.add(m.group(5).strip())
    en_zip = extraer_zip(Path(a.zip), refs) if a.zip else {}
    if a.zip:
        for falta in sorted(refs - set(en_zip)):
            print(f"  AVISO: '{falta}' no está en {Path(a.zip).name}")
    exif_cache = {}
    evento = viaje = None
    vistas = {}
    creadas = repetidas = avisos = 0
    with con:
        for n, raw in enumerate(lines, 1):
            line = raw.strip()
            if not line or line.startswith("//"):
                continue
            if line.startswith("#evento"):
                parts = [p.strip() for p in line[len("#evento"):].split("|")]
                if len(parts) < 4:
                    raise SystemExit(f"línea {n}: #evento necesita Nombre | Organizador | Lugar | Ciudad | fecha")
                nombre, org, lugar, ciudad = parts[:4]
                fecha = parts[4] if len(parts) > 4 else ""
                evento = {"nombre": nombre, "organizador": org, "lugar": lugar, "ciudad": ciudad, "fecha": fecha}
                viaje = None
                continue
            if line.startswith("#viaje"):
                exigir_v2(con)
                v = line[len("#viaje"):].strip()
                row = con.execute("SELECT id FROM trips WHERE slug = ? OR slug = ?", (v, slug(v))).fetchone()
                if not row:
                    raise SystemExit(f"línea {n}: no existe el viaje '{v}' (no se ha importado nada)")
                evento, viaje = SIN_EVENTO, row["id"]
                continue
            if line.startswith("#sin-evento"):
                evento, viaje = SIN_EVENTO, None
                continue
            m = PHOTO_RE.match(line)
            if not m:
                raise SystemExit(f"línea {n} no válida: {raw}\n  formato: AAAA/MM/DD - Nombre | Nombre")
            y, mo, d, people_s, archivo = m.groups()
            fecha = f"{y}-{mo}-{d}"
            if evento is None:
                raise SystemExit(f"línea {n}: falta un bloque #evento, #viaje o #sin-evento antes de la foto")
            ev = None
            if evento is not SIN_EVENTO:
                if evento["fecha"] and evento["fecha"][:10] != fecha:
                    print(f"  AVISO línea {n}: la foto es del {fecha} y el evento del {evento['fecha']}")
                    avisos += 1
                ev = get_or_create_event(con, evento["nombre"], evento["fecha"] or fecha,
                                         evento["organizador"], evento["lugar"], evento["ciudad"])
            key = archivo.strip() if archivo else "linea:" + hashlib.sha1(line.encode()).hexdigest()[:16]
            if key in vistas:  # dos fotos con el mismo fichero: la segunda pisaría las personas de la primera
                raise SystemExit(f"línea {n}: '{key}' está repetido en el texto (línea {vistas[key]}). No se ha importado nada.")
            vistas[key] = n
            if archivo and archivo.strip() in en_zip:
                cap = exif_date(en_zip[archivo.strip()])
                exif_cache[archivo.strip()] = cap
                if cap and cap != fecha:
                    print(f"  AVISO línea {n}: la foto dice {cap} en EXIF y el texto {fecha}")
                    avisos += 1
            row = con.execute("SELECT id FROM photos WHERE archivo = ?", (key,)).fetchone()
            if row:
                # reimportar actualiza las personas de la foto (para poder corregir nombres)
                pid = row["id"]; repetidas += 1
                con.execute("DELETE FROM photo_people WHERE photo_id = ?", (pid,))
            else:
                cols, vals = ["event_id", "fecha", "archivo", "fuente"], [ev, fecha, key, "drive"]
                if viaje is not None:
                    cols.append("trip_id"); vals.append(viaje)
                pid = con.execute(f"INSERT INTO photos ({', '.join(cols)}) VALUES ({','.join('?' * len(vals))})",
                                  vals).lastrowid
                creadas += 1
            names = [p.strip() for p in people_s.split("|") if p.strip()]
            for nm in names:
                if len(nm.split()) < 2:
                    print(f"  AVISO línea {n}: '{nm}' parece un nombre incompleto")
                    avisos += 1
                con.execute("INSERT OR IGNORE INTO photo_people (photo_id, person_id) VALUES (?,?)",
                            (pid, get_or_create_person(con, nm)))
    print(f"fotos: {creadas} nuevas · {repetidas} ya importadas · avisos: {avisos}")
    dups = near_duplicate_people(connect())
    for x, y, r in dups:
        print(f"  REVISAR: '{x}' y '{y}' se parecen ({r}). ¿Es la misma persona? Si lo es, corrige la línea y reimporta (solo funciona en líneas con '=> archivo').")


def cmd_evento(a):
    con = connect()
    with con:
        eid = get_or_create_event(con, a.nombre, a.fecha, a.organizador, a.lugar, a.ciudad, a.pais,
                                  a.modalidad, a.categoria)
        if a.viaje:
            exigir_v2(con)
            t = con.execute("SELECT id FROM trips WHERE slug = ?", (a.viaje,)).fetchone()
            if not t:
                raise SystemExit(f"no existe el viaje '{a.viaje}'")
            con.execute("UPDATE events SET trip_id = ? WHERE id = ?", (t["id"], eid))
        s = con.execute("SELECT slug FROM events WHERE id = ?", (eid,)).fetchone()["slug"]
    print(f"evento: {s}")


def cmd_charla(a):
    con = connect()
    ev = con.execute("SELECT id, slug FROM events WHERE slug = ?", (a.slug,)).fetchone()
    if not ev:
        raise SystemExit(f"no existe el evento '{a.slug}'. Créalo antes con: archivo.py evento ...")
    if a.duracion is not None and a.duracion < 0:
        raise SystemExit("la duración no puede ser negativa")
    dup = con.execute("SELECT id FROM talks WHERE event_id=? AND tipo=? AND titulo=? AND url=? AND archivo_local=?",
                      (ev["id"], a.tipo, a.titulo, a.url, a.archivo or "")).fetchone()
    if dup:
        print(f"charla ya existente (#{dup['id']}) en {ev['slug']}: no se duplica"); return
    with con:
        cur = con.execute(
            "INSERT INTO talks (event_id, tipo, titulo, fecha, duracion_s, idioma, url, archivo_local, notas) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (ev["id"], a.tipo, a.titulo, iso_date(a.fecha) if a.fecha else "", a.duracion, a.idioma,
             a.url, a.archivo or "", a.notas))
        tid = cur.lastrowid
        for nm in [p.strip() for p in (a.personas or "").split("|") if p.strip()]:
            con.execute("INSERT OR IGNORE INTO talk_people (talk_id, person_id, papel) VALUES (?,?,?)",
                        (tid, get_or_create_person(con, nm), a.papel))
    print(f"charla #{tid} añadida a {ev['slug']}")


def cmd_importar_charlas(a):
    """Formato por línea:  slug | tipo | título | fecha | duración_s | idioma | archivo | personas (Nombre | Nombre)"""
    lines = Path(a.fichero).read_text(encoding="utf-8").splitlines()
    ns = 0
    for n, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        p = [x.strip() for x in line.split("|")]
        if len(p) < 7:
            raise SystemExit(f"línea {n}: faltan campos (slug | tipo | título | fecha | duración | idioma | archivo | personas)")
        slug_, tipo, titulo, fecha, dur, idioma, archivo = p[:7]
        personas = " | ".join(p[7:]) if len(p) > 7 else ""
        ns_args = argparse.Namespace(slug=slug_, tipo=tipo, titulo=titulo, fecha=fecha,
                                     duracion=int(dur) if dur else None, idioma=idioma, url="",
                                     archivo=archivo, personas=personas, papel="panelista", notas="")
        cmd_charla(ns_args)
        ns += 1
    print(f"charlas procesadas: {ns} (las repetidas se omiten)")


def cmd_resumen(_):
    con = connect()
    q = lambda s: con.execute(s).fetchone()[0]
    print(f"eventos: {q('SELECT COUNT(*) FROM events')} · objetos: {q('SELECT COUNT(*) FROM objects')} · "
          f"personas: {q('SELECT COUNT(*) FROM people')} · fotos: {q('SELECT COUNT(*) FROM photos')} · "
          f"charlas: {q('SELECT COUNT(*) FROM talks')}")
    print("objetos por tipo:", dict(con.execute("SELECT tipo, COUNT(*) FROM objects GROUP BY tipo").fetchall()))
    if version(con) >= 2:
        tipo = lambda t: q(f"SELECT COUNT(*) FROM objects WHERE tipo = '{t}'")
        futuros = q("SELECT COUNT(*) FROM v_viajes WHERE estado = 'futuro'")
        print(f"viajes: {q('SELECT COUNT(*) FROM trips')} (futuros: {futuros}) · "
              f"ciudades: {q('SELECT COUNT(*) FROM v_ciudades')} · países: {q('SELECT COUNT(*) FROM v_paises')} · "
              f"continentes: {q('SELECT COUNT(*) FROM v_continentes')} · pines: {tipo('pin')} · sellos: {tipo('sello')}")
    sin_obj = con.execute("SELECT slug FROM events e WHERE NOT EXISTS (SELECT 1 FROM objects o WHERE o.event_id=e.id) "
                          "AND NOT EXISTS (SELECT 1 FROM photos p WHERE p.event_id=e.id) "
                          "AND NOT EXISTS (SELECT 1 FROM talks t WHERE t.event_id=e.id)").fetchall()
    if sin_obj:
        print(f"eventos sin ningún objeto, foto ni charla ({len(sin_obj)}): {[r[0] for r in sin_obj[:5]]}...")
    for x, y, r in near_duplicate_people(con):
        print(f"REVISAR personas: '{x}' ~ '{y}' ({r})")
    fk = con.execute("PRAGMA foreign_key_check").fetchall()
    print("integridad referencial:", "OK" if not fk else f"{len(fk)} problemas")


def cmd_foto(a):
    con = connect()
    pat = f"%{a.archivo.strip()}%"
    filas = con.execute("SELECT id, archivo FROM photos WHERE archivo LIKE ? COLLATE NOCASE", (pat,)).fetchall()
    if not filas:
        raise SystemExit(f"ninguna foto coincide con '{a.archivo}'")
    if len(filas) > 1:
        raise SystemExit(f"varias fotos coinciden con '{a.archivo}' ({len(filas)}); escribe más del nombre: " + ", ".join(r[1] for r in filas[:4]))
    with con:
        con.execute("UPDATE photos SET notas = ? WHERE id = ?", (a.nota.strip(), filas[0][0]))
    print(f"{filas[0][1]}: nota guardada")


def cmd_persona(a):
    con = connect()
    m = re.fullmatch(r"(?:https?://(?:www\.)?instagram\.com/)?@?([A-Za-z0-9._]{1,30})/?(?:\?.*)?", a.instagram.strip())
    if not m:
        raise SystemExit(f"'{a.instagram}' no vale: usa el usuario (personaf) o https://www.instagram.com/personaf/")
    with con:
        n = con.execute("UPDATE people SET instagram = ? WHERE clave = ?", (m.group(1), norm(a.nombre))).rowcount
    if not n:
        raise SystemExit(f"no existe ninguna persona llamada '{a.nombre}'")
    print(f"{a.nombre}: instagram.com/{m.group(1)}")


def cmd_fotos_web(_):
    from PIL import Image, ImageOps
    try:
        import pillow_heif; pillow_heif.register_heif_opener()
    except ImportError:
        print("AVISO: sin pillow-heif no se leen los HEIF (pip install pillow-heif)")
    con = connect()
    FOTOS_WEB.mkdir(parents=True, exist_ok=True)
    nuevas = repetidas = 0
    for (archivo,) in con.execute("SELECT archivo FROM photos WHERE archivo NOT LIKE 'linea:%' ORDER BY archivo"):
        h = foto_web_nombre(archivo)
        if (FOTOS_WEB / f"{h}.webp").exists() and (FOTOS_WEB / f"{h}_m.webp").exists():
            repetidas += 1; continue
        origen = FOTOS_DIR / archivo
        if not origen.exists():
            print(f"  AVISO: falta {archivo} en {FOTOS_DIR}"); continue
        try:
            with Image.open(origen) as im:
                im = ImageOps.exif_transpose(im).convert("RGB")   # respeta la orientación del móvil
                for sufijo, lado, calidad in (("", 1600, 82), ("_m", 480, 78)):
                    c = im.copy(); c.thumbnail((lado, lado), Image.LANCZOS)
                    c.save(FOTOS_WEB / f"{h}{sufijo}.webp", "WEBP", quality=calidad, method=6)
            nuevas += 1
        except Exception as e:
            print(f"  AVISO: no se pudo leer {archivo}: {e}")
    print(f"fotos web: {nuevas} nuevas · {repetidas} ya hechas · en {FOTOS_WEB}")


def cmd_exportar(a):
    con = connect()
    objetos = lambda filas: [{**dict(o), "nivel": nivel_premio(o["premio"])} for o in filas]

    def foto_json(p):
        personas = [r[0] for r in con.execute(
            "SELECT pe.nombre FROM photo_people pp JOIN people pe ON pe.id=pp.person_id "
            "WHERE pp.photo_id=? ORDER BY pe.nombre", (p["id"],))]
        # las fotos sin "=> archivo" tienen una clave interna "linea:...", que no es un fichero
        archivo = None if p["archivo"].startswith("linea:") else p["archivo"]
        h = foto_web_nombre(archivo) if archivo else None
        web, mini = (f"img/fotos/{h}{s}.webp" if h and (FOTOS_WEB / f"{h}{s}.webp").exists() else None for s in ("", "_m"))
        return {"archivo": archivo, "fecha": p["fecha"], "personas": personas, "nota": p["notas"], "web": web, "mini": mini}

    events = []
    for e in con.execute("SELECT * FROM events ORDER BY fecha, nombre"):
        d = dict(e)
        # coordenadas del lugar del evento (para el mapa); None si el evento no tiene lugar
        lugar = con.execute("SELECT lat, lng FROM places WHERE id=?", (e["place_id"],)).fetchone() if version(con) >= 2 and e["place_id"] else None
        d["lat"], d["lng"] = (lugar["lat"], lugar["lng"]) if lugar else (None, None)
        d["objetos"] = objetos(con.execute("SELECT * FROM objects WHERE event_id=? ORDER BY uid", (e["id"],)))
        d["charlas"] = [dict(t) for t in con.execute("SELECT * FROM talks WHERE event_id=? ORDER BY fecha", (e["id"],))]
        d["fotos"] = []
        for p in con.execute("SELECT * FROM photos WHERE event_id=? ORDER BY fecha, archivo", (e["id"],)):
            d["fotos"].append(foto_json(p))
        events.append(d)
    people = [{"nombre": r["nombre"], "instagram": r["instagram"],
               "fotos": con.execute("SELECT COUNT(*) FROM photo_people WHERE person_id=?", (r["id"],)).fetchone()[0],
               "charlas": con.execute("SELECT COUNT(*) FROM talk_people WHERE person_id=?", (r["id"],)).fetchone()[0]}
              for r in con.execute("SELECT * FROM people ORDER BY nombre")]
    out = {"generado": now(), "eventos": events, "personas": people}
    if version(con) >= 2:
        filas = lambda sql, *args: [dict(r) for r in con.execute(sql, args)]
        if version(con) < ULTIMA:
            raise SystemExit(f"La base está en v{version(con)}. Ejecuta: python archivo.py migrar")
        out["viajes"] = []
        km_total = 0
        for v in filas("SELECT * FROM v_viajes ORDER BY inicio IS NULL, inicio, nombre"):
            t = con.execute("SELECT * FROM trips WHERE id = ?", (v["id"],)).fetchone()
            km, v["vuelos"] = ruta_viaje(con, t)
            v["km"] = round(t["km_manual"] if t["km_manual"] is not None else km)
            if v["estado"] != "futuro":  # lo futuro no cuenta hasta que llega
                km_total += v["km"]
            v["visitas"] = filas("SELECT p.nombre AS ciudad, p.pais, p.lat, p.lng, vi.inicio, vi.fin, vi.nota FROM visits vi "
                                 "JOIN places p ON p.id = vi.place_id WHERE vi.trip_id = ? ORDER BY vi.inicio, p.nombre", v["id"])
            v["eventos"] = [r["slug"] for r in filas("SELECT slug FROM events WHERE trip_id = ? ORDER BY fecha", v["id"])]
            v["objetos"] = objetos(con.execute("SELECT * FROM objects WHERE trip_id = ? ORDER BY tipo, uid", (v["id"],)))
            v["fotos"] = [foto_json(p) for p in con.execute("SELECT * FROM photos WHERE trip_id = ? ORDER BY fecha", (v["id"],))]
            out["viajes"].append(v)
        out["totales"] = {n: filas(f"SELECT * FROM v_{n} ORDER BY 1") for n in ("paises", "ciudades", "continentes", "aeropuertos")}
        out["totales"]["km"] = km_total
        niveles = [nivel_premio(r[0]) for r in con.execute("SELECT premio FROM objects WHERE premio <> ''")]
        out["totales"]["premios"] = {k: niveles.count(k) for k in dict.fromkeys(sorted(niveles))}
        out["objetos_sueltos"] = objetos(con.execute("SELECT * FROM objects WHERE event_id IS NULL AND trip_id IS NULL ORDER BY tipo, uid"))
        out["fotos_sueltas"] = [foto_json(p) for p in con.execute(
            "SELECT * FROM photos WHERE event_id IS NULL AND trip_id IS NULL ORDER BY fecha, archivo")]
    Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
    Path(a.salida).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"exportado: {a.salida} ({len(events)} eventos, {len(people)} personas)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init").set_defaults(f=cmd_init)
    sub.add_parser("copia").set_defaults(f=cmd_copia)
    sub.add_parser("migrar").set_defaults(f=cmd_migrar)
    p = sub.add_parser("sello", help="sello LEGO del pasaporte")
    p.add_argument("--fecha", required=True); p.add_argument("--sitio", required=True, help='"LEGO Store Tivoli"')
    p.add_argument("--ciudad", required=True); p.add_argument("--pais", default="")
    p.add_argument("--viaje", default="", help="slug del viaje"); p.add_argument("--imagen", default="", help="foto o escaneo del sello")
    p.set_defaults(f=cmd_sello)
    p = sub.add_parser("importar-viajes"); p.add_argument("fichero")
    p.add_argument("--geo", default=str(ROOT / "datos" / "ciudades_geo.csv"))
    p.add_argument("--aeropuertos", default=str(ROOT / "datos" / "aeropuertos_geo.csv")); p.set_defaults(f=cmd_importar_viajes)
    p = sub.add_parser("importar-objetos"); p.add_argument("fichero"); p.set_defaults(f=cmd_importar_objetos)
    p = sub.add_parser("importar-catalogo"); p.add_argument("fichero")
    p.add_argument("--originales", default=str(ROOT / "datos" / "certificados_originales"), help="PDF/imágenes de la columna archivo")
    p.add_argument("--imagenes", default=str(ROOT / "web" / "img" / "certificados"), help="dónde dejar el JPG para la web")
    p.set_defaults(f=cmd_importar_catalogo)
    p = sub.add_parser("importar-fotos"); p.add_argument("fichero")
    p.add_argument("--zip", help="zip con las imágenes (p. ej. datos/entrada/gente.zip)"); p.set_defaults(f=cmd_importar_fotos)
    p = sub.add_parser("foto", help="guarda el pie de una foto")
    p.add_argument("--archivo", required=True); p.add_argument("--nota", required=True); p.set_defaults(f=cmd_foto)
    p = sub.add_parser("persona", help="guarda el Instagram de una persona")
    p.add_argument("--nombre", required=True); p.add_argument("--instagram", required=True); p.set_defaults(f=cmd_persona)
    sub.add_parser("fotos-web", help="WebP y miniatura de las fotos para la web").set_defaults(f=cmd_fotos_web)
    p = sub.add_parser("importar-charlas"); p.add_argument("fichero"); p.set_defaults(f=cmd_importar_charlas)
    p = sub.add_parser("viaje", help="crea un viaje o cambia uno existente (--slug)")
    for k in ("slug", "nombre", "inicio", "fin", "transporte", "salida", "escala", "llegada", "motivo", "notas"):
        p.add_argument(f"--{k}")
    p.add_argument("--km", dest="km_manual", type=float, help="km reales; sustituyen al cálculo")
    p.add_argument("--ciudad", default="", help="añade la visita a esta ciudad con las fechas del viaje")
    p.add_argument("--pais", default=""); p.set_defaults(f=cmd_viaje)
    p = sub.add_parser("lugar", help="crea un lugar o corrige sus coordenadas")
    p.add_argument("--nombre", required=True); p.add_argument("--pais", default="")
    p.add_argument("--lat", type=float, required=True); p.add_argument("--lng", type=float, required=True)
    p.add_argument("--confianza", default="alta"); p.add_argument("--renombrar", default=""); p.set_defaults(f=cmd_lugar)
    p = sub.add_parser("pin", help="añade un pin a un viaje")
    p.add_argument("--viaje", required=True, help="slug del viaje"); p.add_argument("--titulo", required=True)
    p.add_argument("--ciudad", required=True); p.add_argument("--pais", default=""); p.set_defaults(f=cmd_pin)
    sub.add_parser("pulir", help="arreglos automáticos repetibles").set_defaults(f=cmd_pulir)
    p = sub.add_parser("evento")
    p.add_argument("--nombre", required=True); p.add_argument("--fecha", required=True)
    p.add_argument("--organizador", default=""); p.add_argument("--lugar", default=""); p.add_argument("--ciudad", default="")
    p.add_argument("--pais", default=""); p.add_argument("--modalidad", default="", choices=["", "presencial", "virtual"])
    p.add_argument("--categoria", default=""); p.add_argument("--viaje", default="", help="slug del viaje")
    p.set_defaults(f=cmd_evento)
    p = sub.add_parser("charla")
    p.add_argument("--slug", required=True); p.add_argument("--tipo", required=True,
                                                            choices=["keynote", "mesa_redonda", "pitch", "otro"])
    p.add_argument("--titulo", default=""); p.add_argument("--fecha", default="")
    p.add_argument("--duracion", type=int, help="segundos"); p.add_argument("--idioma", default="")
    p.add_argument("--url", default=""); p.add_argument("--archivo", default="")
    p.add_argument("--personas", default="", help="Nombre | Nombre"); p.add_argument("--papel", default="panelista")
    p.add_argument("--notas", default=""); p.set_defaults(f=cmd_charla)
    sub.add_parser("resumen").set_defaults(f=cmd_resumen)
    p = sub.add_parser("exportar"); p.add_argument("salida"); p.set_defaults(f=cmd_exportar)
    a = ap.parse_args()
    # la consola de Windows usa cp1252: sin esto los acentos salen rotos o el programa falla al imprimir
    sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
    try:
        a.f(a)
    except ValueError as e:
        print(f"Error: {e}"); return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
