#!/usr/bin/env python3
"""
lanyard_ingest.py — Digitaliza lanyards, pins, certificados y fotos.

Entrada : un .zip, una carpeta o un fichero suelto (HEIC/HEIF, JPG, PNG, WebP, TIFF, PDF).
Proceso : extrae -> ordena cronológicamente (EXIF / metadatos PDF) -> detecta y recorta
          cada pieza (con corrección de perspectiva) -> te pregunta evento y fecha
          -> guarda imágenes y una fila por objeto en items_nuevos.csv.
Salida  : <out>/master/*.jpg   (alta calidad, archivo permanente)
          <out>/web/*.webp     (ligeras, para la web)
          <out>/items_nuevos.csv (ordenado por fecha del evento)
          <out>/.ingest_state.json (permite reanudar sin repetir ficheros)

Uso rápido:
    python lanyard_ingest.py fotos.zip
    python lanyard_ingest.py fotos.zip --tipo pin --ciudades ciudades_geo.csv
    python lanyard_ingest.py fotos.zip --dry-run        # solo prueba el recorte

En cada pregunta: Enter acepta el valor [entre corchetes]; "s" salta el fichero;
"q" guarda y sale.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import pillow_heif
import pymupdf
from PIL import Image, ImageOps

pillow_heif.register_heif_opener()

IMG_EXT = {".heic", ".heif", ".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}
PDF_EXT = {".pdf"}
TIPOS = ("lanyard", "pin", "certificado", "foto")
CSV_COLS = [
    "uid", "tipo", "titulo", "organizador", "fecha", "rol", "lugar",
    "ciudad", "pin_id", "notas", "imagen_front", "imagen_back", "imagenes_extra", "origen",
]
DATE_RE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")  # AAAA, AAAA-MM o AAAA-MM-DD


class Quit(Exception):
    """El usuario pide guardar y salir."""


# --------------------------------------------------------------------------- utilidades
def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s.lower()).strip()


def slug(s: str, maxlen: int = 48) -> str:
    return re.sub(r"[^a-z0-9]+", "-", norm(s)).strip("-")[:maxlen] or "sin-nombre"


def sha1(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------- entrada
def extract_zip(zpath: Path, dest: Path) -> None:
    """Extrae el zip evitando rutas maliciosas (zip-slip) y basura de macOS."""
    root = dest.resolve()
    with zipfile.ZipFile(zpath) as zf:
        for info in zf.infolist():
            name = info.filename
            if info.is_dir() or name.startswith("__MACOSX") or Path(name).name.startswith("."):
                continue
            target = (dest / name).resolve()
            if root not in target.parents:
                raise ValueError(f"Ruta sospechosa en el zip: {name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out)
            ts = dt.datetime(*info.date_time).timestamp()
            os.utime(target, (ts, ts))


def collect_inputs(src: Path, workdir: Path) -> list[Path]:
    if src.is_dir():
        files = [p for p in src.rglob("*") if p.is_file()]
    elif src.suffix.lower() == ".zip":
        extract_zip(src, workdir)
        files = [p for p in workdir.rglob("*") if p.is_file()]
    else:
        files = [src]
    ok = {*IMG_EXT, *PDF_EXT}
    return [p for p in files if p.suffix.lower() in ok and not p.name.startswith(".")]


def shot_datetime(path: Path) -> dt.datetime:
    """Fecha de captura: EXIF (imágenes) o metadatos (PDF); si no hay, mtime."""
    try:
        if path.suffix.lower() in PDF_EXT:
            with pymupdf.open(path) as doc:
                raw = (doc.metadata or {}).get("creationDate", "")
            m = re.match(r"D:(\d{4})(\d{2})(\d{2})(\d{2})?(\d{2})?(\d{2})?", raw or "")
            if m:
                parts = [int(x) if x else 0 for x in m.groups()]
                return dt.datetime(*parts)
        else:
            with Image.open(path) as im:
                exif = im.getexif()
                val = exif.get_ifd(0x8769).get(36867) or exif.get(306)  # DateTimeOriginal | DateTime
            if val:
                return dt.datetime.strptime(str(val).strip()[:19], "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return dt.datetime.fromtimestamp(path.stat().st_mtime)


def load_pages(path: Path, dpi: int) -> list[Image.Image]:
    """Devuelve una imagen RGB por foto / por página de PDF."""
    if path.suffix.lower() in PDF_EXT:
        pages = []
        with pymupdf.open(path) as doc:
            for page in doc:
                pix = page.get_pixmap(dpi=dpi, alpha=False)
                pages.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
        return pages
    with Image.open(path) as im:
        return [ImageOps.exif_transpose(im).convert("RGB")]  # respeta la orientación del iPhone


# --------------------------------------------------------------------------- recorte
def order_points(pts: np.ndarray) -> np.ndarray:
    s, d = pts.sum(axis=1), np.diff(pts, axis=1).ravel()
    return np.array([pts[np.argmin(s)], pts[np.argmin(d)], pts[np.argmax(s)], pts[np.argmax(d)]], np.float32)


def detect_objects(rgb: np.ndarray, min_area: float = 0.02, thr: float = 22.0) -> list[np.ndarray]:
    """Detecta piezas sobre un fondo liso. Devuelve cajas (tl,tr,br,bl) en píxeles originales."""
    h, w = rgb.shape[:2]
    scale = min(1.0, 1400 / max(h, w))
    small = cv2.resize(rgb, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1 else rgb
    lab = cv2.cvtColor(cv2.GaussianBlur(small, (5, 5), 0), cv2.COLOR_RGB2LAB).astype(np.float32)
    sh, sw = lab.shape[:2]
    b = max(4, int(0.02 * min(sh, sw)))
    border = np.concatenate([lab[:b].reshape(-1, 3), lab[-b:].reshape(-1, 3),
                             lab[:, :b].reshape(-1, 3), lab[:, -b:].reshape(-1, 3)])
    bg = np.median(border, axis=0)                          # color del fondo = mediana del borde
    mask = (np.linalg.norm(lab - bg, axis=2) > thr).astype(np.uint8) * 255
    k = max(5, int(0.012 * min(sh, sw))) | 1
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    total = sh * sw
    boxes = []
    for c in cnts:
        area = cv2.contourArea(c)
        if area < min_area * total:
            continue
        if area > 0.92 * total:                             # el "objeto" es toda la foto: fondo no uniforme
            return []
        boxes.append(order_points(cv2.boxPoints(cv2.minAreaRect(c)) / scale))
    if not boxes:
        return []
    cx = [b_[:, 0].mean() for b_ in boxes]
    cy = [b_[:, 1].mean() for b_ in boxes]
    key = (lambda i: cx[i]) if np.ptp(cx) >= np.ptp(cy) else (lambda i: cy[i])
    return [boxes[i] for i in sorted(range(len(boxes)), key=key)]


def warp(rgb: np.ndarray, box: np.ndarray, inset: int = 4) -> np.ndarray:
    tl, tr, br, bl = box
    W = int(round(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl))))
    H = int(round(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl))))
    dst = np.array([[0, 0], [W - 1, 0], [W - 1, H - 1], [0, H - 1]], np.float32)
    out = cv2.warpPerspective(rgb, cv2.getPerspectiveTransform(box, dst), (W, H),
                              flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return out[inset:-inset, inset:-inset] if inset and min(H, W) > 4 * inset else out


def crop_pieces(img: Image.Image, args) -> tuple[list[Image.Image], bool]:
    rgb = np.asarray(img)
    boxes = detect_objects(rgb, args.min_area, args.threshold)
    if not boxes:
        return [img], False                                 # sin detección: imagen completa
    crops = [Image.fromarray(warp(rgb, b, args.inset)) for b in boxes]
    if args.portrait:
        crops = [c.rotate(-90, expand=True) if c.width > c.height else c for c in crops]
    return crops, True


# --------------------------------------------------------------------------- guardado
def save_piece(img: Image.Image, stem: str, out: Path, web_max: int, keep_master: bool) -> str:
    if keep_master:
        img.save(out / "master" / f"{stem}.jpg", quality=95, subsampling=0, optimize=True)
    web = img.copy()
    web.thumbnail((web_max, web_max), Image.LANCZOS)
    web.save(out / "web" / f"{stem}.webp", quality=85, method=6)
    return f"web/{stem}.webp"


# --------------------------------------------------------------------------- ciudades / pines
def load_cities(path: Path | None) -> dict[str, dict]:
    if not path or not path.exists():
        return {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        return {norm(r["ciudad"]): r for r in csv.DictReader(f)}


def pick_city(cities: dict[str, dict]) -> dict:
    """Pregunta una ciudad con autocompletado sobre ciudades_geo.csv."""
    while True:
        q = ask("Ciudad del pin")
        if not cities:
            return {"ciudad": q}
        n = norm(q)
        if n in cities:
            return cities[n]
        hits = [r for k, r in cities.items() if n and n in k]
        if len(hits) == 1:
            return hits[0]
        if hits:
            print("   ¿Cuál? " + " | ".join(f"{i+1}) {r['ciudad']}" for i, r in enumerate(hits)))
            sel = ask("Número (Enter = ninguna de ellas, usar texto libre)", "")
            if sel.isdigit() and 1 <= int(sel) <= len(hits):
                return hits[int(sel) - 1]
        print("   (ciudad no encontrada en tu lista de viajes; se guarda como texto libre)")
        return {"ciudad": q.strip()}


# --------------------------------------------------------------------------- interacción
def ask(prompt: str, default: str | None = None, validate=None) -> str:
    while True:
        try:
            raw = input(f"   {prompt}" + (f" [{default}]" if default else "") + ": ").strip()
        except EOFError:
            raise Quit
        if raw.lower() == "q":
            raise Quit
        val = raw or (default or "")
        if validate and val and not validate(val):
            print("   Formato no válido.")
            continue
        return val


def ask_date(default: str) -> str:
    return ask("Fecha del evento (AAAA-MM-DD, o AAAA-MM)", default, lambda v: bool(DATE_RE.match(v)))


@dataclass
class Item:
    uid: str; tipo: str; titulo: str; organizador: str; fecha: str; rol: str; lugar: str
    ciudad: str; pin_id: str; notas: str; imagen_front: str; imagen_back: str
    imagenes_extra: str; origen: str


def load_items(csv_path: Path) -> list[dict]:
    if not csv_path.exists():
        return []
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_items(csv_path: Path, rows: list[dict]) -> None:
    rows = sorted(rows, key=lambda r: (r["fecha"], r["uid"]))    # orden cronológico por fecha del evento
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLS)
        w.writeheader()
        w.writerows(rows)


def unique_uid(base: str, taken: set[str]) -> str:
    uid, n = base, 2
    while uid in taken:
        uid, n = f"{base}-{n}", n + 1
    taken.add(uid)
    return uid


# --------------------------------------------------------------------------- principal
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entrada", type=Path, help=".zip, carpeta o fichero")
    ap.add_argument("--out", type=Path, default=Path("archive_out"))
    ap.add_argument("--tipo", choices=TIPOS, default="lanyard", help="tipo por defecto (se puede cambiar por foto)")
    ap.add_argument("--ciudades", type=Path, default=Path("ciudades_geo.csv"))
    ap.add_argument("--dpi", type=int, default=220, help="resolución al rasterizar PDFs")
    ap.add_argument("--min-area", type=float, default=0.02, help="área mínima de una pieza (fracción de la foto)")
    ap.add_argument("--threshold", type=float, default=22.0, help="sensibilidad fondo/objeto (Lab). Baja si recorta de menos")
    ap.add_argument("--inset", type=int, default=4, help="píxeles recortados del borde para quitar restos de fondo")
    ap.add_argument("--portrait", action="store_true", help="gira las piezas horizontales a vertical")
    ap.add_argument("--swap", action="store_true", help="intercambia anverso/reverso (por defecto: izquierda = anverso)")
    ap.add_argument("--web-max", type=int, default=2000)
    ap.add_argument("--no-master", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="solo detecta piezas; no guarda ni pregunta")
    args = ap.parse_args()

    out = args.out
    for sub in ("master", "web"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    csv_path, state_path = out / "items_nuevos.csv", out / ".ingest_state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    rows = load_items(csv_path)
    taken = {r["uid"] for r in rows}
    cities = load_cities(args.ciudades)
    prev: dict[str, str] = {}

    with tempfile.TemporaryDirectory() as tmp:
        files = collect_inputs(args.entrada, Path(tmp))
        if not files:
            print("No encuentro imágenes ni PDFs en la entrada.")
            return 1
        files.sort(key=lambda p: (shot_datetime(p), p.name))      # cronológico
        print(f"{len(files)} fichero(s), ordenados por fecha de captura. Escribe 'q' para guardar y salir, 's' para saltar.\n")
        try:
            for i, path in enumerate(files, 1):
                digest = sha1(path)
                if digest in state and not args.dry_run:
                    print(f"[{i}/{len(files)}] {path.name}: ya procesado, lo salto.")
                    continue
                taken_at = shot_datetime(path)
                skipped = False
                for page_no, img in enumerate(load_pages(path, args.dpi), 1):
                    label = path.name + (f" (pág. {page_no})" if path.suffix.lower() in PDF_EXT else "")
                    crops, detected = crop_pieces(img, args)
                    print(f"[{i}/{len(files)}] {label}  captura: {taken_at:%Y-%m-%d %H:%M}  "
                          f"-> {len(crops)} pieza(s){'' if detected else '  (sin detección: imagen completa)'}")
                    if args.dry_run:
                        for n, c in enumerate(crops, 1):
                            print(f"      pieza {n}: {c.width}x{c.height}px")
                        continue

                    tipo = ask(f"Tipo {'/'.join(TIPOS)} (s = saltar)", args.tipo, lambda v: v in TIPOS or v == "s")
                    if tipo == "s":
                        skipped = True
                        print("   Saltado (se volverá a ofrecer en la próxima ejecución).\n")
                        continue
                    if tipo == "pin":
                        row = pick_city(cities)
                        ciudad = row.get("ciudad", "")
                        pin_id = ask("ID del pin", row.get("pin_id", "") if row.get("pin") == "sí" else "")
                        titulo = f"Pin {ciudad}"
                        organizador = rol = lugar = ""
                        fecha = ask_date(row.get("primera_fecha") or f"{taken_at:%Y-%m-%d}")
                    else:
                        ciudad = pin_id = ""
                        titulo = ask("Nombre del evento", prev.get("titulo", ""))
                        if not titulo:
                            print("   Sin nombre: salto esta foto.\n")
                            skipped = True
                            continue
                        fecha = ask_date(f"{taken_at:%Y-%m-%d}")
                        same = prev.get("fecha") == fecha and prev.get("titulo") == titulo
                        organizador = ask("Organizador (opcional)", prev.get("organizador", "") if same else "")
                        lugar = ask("Lugar (opcional)", prev.get("lugar", "") if same else "")
                        rol = ask("Rol / premio (opcional)", "")
                    notas = ask("Notas (opcional)", "")

                    uid = unique_uid(f"{fecha}-{slug(titulo)}-{tipo}", taken)
                    names = ["front", "back"] if len(crops) == 2 else (["front"] if len(crops) == 1 else
                            [f"pieza{n}" for n in range(1, len(crops) + 1)])
                    if len(crops) == 2 and args.swap:
                        names.reverse()
                    saved = {nm: save_piece(c, f"{uid}_{nm}", out, args.web_max, not args.no_master)
                             for nm, c in zip(names, crops)}
                    extra = [v for k, v in saved.items() if k not in ("front", "back")]
                    rows.append(vars(Item(uid, tipo, titulo, organizador, fecha, rol, lugar, ciudad, pin_id,
                                          notas, saved.get("front", ""), saved.get("back", ""),
                                          " | ".join(extra), path.name)))
                    prev = dict(titulo=titulo, fecha=fecha, organizador=organizador, lugar=lugar)
                    print(f"   OK -> {uid}\n")
                if not skipped:
                    state[digest] = path.name
        except Quit:
            print("\nGuardando y saliendo...")
        finally:
            if not args.dry_run:
                write_items(csv_path, rows)
                state_path.write_text(json.dumps(state, ensure_ascii=False, indent=1))
                print(f"{len(rows)} fila(s) en {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
