#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lanyard Archive - versión simple.

Haz las fotos EN ORDEN: anverso, reverso, anverso, reverso...  Cada pareja es un lanyard.
El programa calibra, recorta, te enseña el resultado una vez por lanyard y te pregunta
evento, fecha, lugar... una sola vez por pareja (Enter = repetir lo anterior).

  python lanyard_archive.py                  # elige una carpeta, ZIP o foto
  python lanyard_archive.py --input fotos.zip
  python lanyard_archive.py --pin            # una foto = un pin (pregunta ciudad)
  python lanyard_archive.py --medir-regla 99.6   # una vez: escala real de tu impresora

Salida: carpeta "Lanyards_procesados" junto a tus fotos (se abre sola al terminar):
  web/        WebP con transparencia (para la web)
  master/     PNG con transparencia, máxima calidad
  originals/  copia de las fotos originales
  archive.json / archive.csv   una fila por lanyard
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
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from pathlib import Path

import cv2
import numpy as np
import pillow_heif
import pymupdf
from PIL import Image, ImageOps

import lanyard_core as core

pillow_heif.register_heif_opener()

EXT = {".heic", ".heif", ".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".pdf"}
DATE_RE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
CONFIG = Path(__file__).resolve().parent / "calibracion_impresora.json"
CSV_COLS = ["id", "tipo", "evento", "fecha", "lugar", "ciudad", "organizador", "rol", "forma", "ancho_mm", "alto_mm",
            "agujero_mm", "anclaje_x", "anclaje_y", "front_web", "back_web", "front_png", "back_png",
            "originales", "avisos"]


class Quit(Exception): ...
class Skip(Exception): ...


# --------------------------------------------------------------------------- fotos
class Photo:
    """Una foto (o una página de PDF). Se carga solo cuando hace falta."""

    def __init__(self, path: Path, page: int = 0):
        self.path, self.page = path, page
        self.name = path.name + (f"#p{page + 1}" if path.suffix.lower() == ".pdf" else "")
        self.key = f"{hashlib.sha1(path.read_bytes()).hexdigest()[:16]}:{page}"
        self.taken = _taken(path)

    def load(self) -> np.ndarray:
        if self.path.suffix.lower() == ".pdf":
            with pymupdf.open(self.path) as d:
                pix = d[self.page].get_pixmap(dpi=300, alpha=False)
            return np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3).copy()
        with Image.open(self.path) as im:
            return np.asarray(ImageOps.exif_transpose(im).convert("RGB")).copy()


def _taken(p: Path) -> dt.datetime:
    try:
        if p.suffix.lower() != ".pdf":
            with Image.open(p) as im:
                ex = im.getexif()
                v = ex.get_ifd(0x8769).get(36867) or ex.get(306)
            if v:
                return dt.datetime.strptime(str(v).strip()[:19], "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return dt.datetime.fromtimestamp(p.stat().st_mtime)


def collect(src: Path, tmp: Path) -> list[Photo]:
    if src.is_dir():
        files = [p for p in src.rglob("*") if p.is_file()]
    elif src.suffix.lower() == ".zip":
        with zipfile.ZipFile(src) as z:
            z.extractall(tmp)                      # extractall ya rechaza rutas peligrosas
        files = [p for p in tmp.rglob("*") if p.is_file()]
    else:
        files = [src]
    files = [p for p in files if p.suffix.lower() in EXT and not p.name.startswith((".", "_"))
             and "Lanyards_procesados" not in p.parts]
    photos: list[Photo] = []
    for p in files:
        n = 1
        if p.suffix.lower() == ".pdf":
            with pymupdf.open(p) as d:
                n = len(d)
        photos += [Photo(p, i) for i in range(n)]
    return sorted(photos, key=lambda x: (x.taken, x.name.lower()))


# --------------------------------------------------------------------------- pantalla
def screen_size() -> tuple[int, int]:
    try:
        import tkinter as tk
        r = tk.Tk(); r.withdraw()
        w, h = r.winfo_screenwidth(), r.winfo_screenheight()
        r.destroy()
        return w, h
    except Exception:
        return 1280, 720


def has_gui() -> bool:
    try:
        cv2.namedWindow("_t"); cv2.destroyWindow("_t")
        return True
    except cv2.error:
        return False


def fit(img: np.ndarray, max_w: int, max_h: int) -> np.ndarray:
    s = min(max_w / img.shape[1], max_h / img.shape[0], 1.0)
    return cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else img


def review(analyses: list, title: str) -> str:
    """Una ventana con todas las caras, ajustada a tu pantalla. Devuelve ok / skip / quit / '1' / '2'."""
    sw, sh = screen_size()
    faces = [a.debug for a in analyses]
    h = min(f.shape[0] for f in faces)
    row = np.hstack([cv2.resize(f, (int(f.shape[1] * h / f.shape[0]), h)) for f in faces])
    row = fit(row, int(sw * 0.92), int(sh * 0.78))
    bar = np.full((46, row.shape[1], 3), 35, np.uint8)
    cv2.putText(bar, "ENTER = vale   1 / 2 = marcar esa cara a mano   S = saltar   Q = salir", (12, 31),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.imshow(title, np.vstack([row, bar]))
    while True:
        k = cv2.waitKey(80) & 0xFF
        if cv2.getWindowProperty(title, cv2.WND_PROP_VISIBLE) < 1:
            return "skip"
        if k in (13, 32): out = "ok"
        elif k in (ord("s"), ord("S"), 27): out = "skip"
        elif k in (ord("q"), ord("Q")): out = "quit"
        elif k in (ord("1"), ord("2")) and int(chr(k)) <= len(analyses): out = chr(k)
        else: continue
        cv2.destroyAllWindows()
        return out


def pick_roi(plane: np.ndarray) -> tuple:
    sw, sh = screen_size()
    s = min((sh * 0.8) / plane.shape[0], (sw * 0.8) / plane.shape[1], 1.0)
    small = cv2.cvtColor(cv2.resize(plane, None, fx=s, fy=s, interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2BGR)
    x, y, w, h = cv2.selectROI("Rodea el objeto y pulsa ENTER", small, showCrosshair=False)
    cv2.destroyAllWindows()
    if w < 10 or h < 10:
        raise Skip
    return tuple(int(v / s) for v in (x, y, w, h))


# --------------------------------------------------------------------------- análisis
def analyze(photo: Photo, args, scale: float, roi=None) -> core.Analysis:
    rgb = photo.load()
    try:
        return core.analyze(rgb, args.plantilla, roi=roi, print_scale=scale)
    except ValueError as e:
        if isinstance(e, core.CalibrationError) or args.sin_gui or not has_gui():
            raise
        print(f"   No distingo el objeto solo en {photo.name}. Rodéalo a mano.")
        cal = core.calibrate(rgb, args.plantilla)
        return core.analyze(rgb, args.plantilla, roi=pick_roi(cal.plane), print_scale=scale)


# --------------------------------------------------------------------------- preguntas
def ask(q: str, default: str = "") -> str:
    try:
        v = input(f"   {q}" + (f" [{default}]" if default else "") + ": ").strip()
    except EOFError:
        raise Quit
    if v.lower() == "q":
        raise Quit
    return v or default


def ask_date(default: str) -> str:
    while True:
        v = ask("Fecha (AAAA-MM-DD o AAAA-MM)", default)
        if DATE_RE.fullmatch(v):
            return v
        print("   Formato no válido.")


def ask_meta(pin: bool, prev: dict, taken: dt.datetime) -> dict:
    if pin:
        city = ask("Ciudad del pin")
        while not city:
            city = ask("La ciudad es obligatoria")
        return {"tipo": "pin", "evento": f"Pin {city}", "fecha": ask_date(prev.get("fecha") or taken.strftime("%Y-%m-%d")),
                "lugar": "", "ciudad": city, "organizador": "", "rol": ""}
    event = ask("Evento", prev.get("evento", ""))
    while not event:
        event = ask("El evento es obligatorio")
    same = event == prev.get("evento")
    keep = lambda k: prev.get(k, "") if same else ""
    return {"tipo": "lanyard", "evento": event,
            "fecha": ask_date(prev.get("fecha", "") if same else taken.strftime("%Y-%m-%d")),
            "lugar": ask("Lugar", keep("lugar")), "ciudad": ask("Ciudad", keep("ciudad")),
            "organizador": ask("Organizador (opcional)", keep("organizador")), "rol": ask("Rol (opcional)")}


# --------------------------------------------------------------------------- guardado
def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:48] or "sin-nombre"


def write_atomic(path: Path, write) -> None:
    tmp = path.with_name(path.name + ".tmp")
    write(tmp)
    os.replace(tmp, path)


def save_item(out: Path, records: list, meta: dict, group: list, analyses: list) -> dict:
    base = f"{meta['fecha']}_{slug(meta['evento'])}"
    uid, n = base, 2
    while any(r["id"] == uid for r in records):
        uid, n = f"{base}-{n}", n + 1
    files: dict = {}
    for side, ph, an in zip(["front", "back"], group, analyses):
        rgba = np.dstack([an.crop, an.alpha])
        png, web = out / "master" / f"{uid}_{side}.png", out / "web" / f"{uid}_{side}.webp"
        write_atomic(png, lambda t, rgba=rgba: Image.fromarray(rgba, "RGBA").save(t, "PNG", optimize=True))

        def w(t, rgba=rgba):
            im = Image.fromarray(rgba, "RGBA"); im.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
            im.save(t, "WEBP", quality=88, method=6)
        write_atomic(web, w)
        shutil.copy2(ph.path, out / "originals" / f"{uid}_{side}{ph.path.suffix.lower()}")
        files[side] = (png, web)

    a0 = analyses[0]
    all_rect = all(an.seg.mode == "rect" for an in analyses)
    dims = [sorted([an.width_mm, an.height_mm]) for an in analyses]
    warns = [w for an in analyses for w in an.warnings]
    if all_rect and len(dims) == 2:
        if max(abs(dims[0][0] - dims[1][0]), abs(dims[0][1] - dims[1][1])) > 1.5:
            warns.append("anverso y reverso no miden igual (>1,5 mm): revisa alguna foto")
        w_mm, h_mm = (float(np.mean([d[i] for d in dims])) for i in (0, 1))   # misma tarjeta = misma medida
    else:
        w_mm, h_mm = a0.width_mm, a0.height_mm                                # forma libre: medida del anverso
    top = min(a0.holes, key=lambda h: h["cy"]) if a0.holes else None
    ch, cw = a0.crop.shape[:2]
    rel = lambda p: str(p.relative_to(out)).replace("\\", "/")
    return {"id": uid, **meta,
            "forma": "rectangular" if all_rect else "libre", "ancho_mm": round(w_mm, 1), "alto_mm": round(h_mm, 1),
            "agujero_mm": ";".join(f"{h['d_mm']:.1f}" for h in a0.holes),
            "anclaje_x": round(top["cx"] / cw, 4) if top else "", "anclaje_y": round(top["cy"] / ch, 4) if top else "",
            "front_web": rel(files["front"][1]), "back_web": rel(files["back"][1]) if "back" in files else "",
            "front_png": rel(files["front"][0]), "back_png": rel(files["back"][0]) if "back" in files else "",
            "originales": " | ".join(p.name for p in group), "avisos": " | ".join(dict.fromkeys(warns)),
            "_keys": [p.key for p in group]}


def write_index(out: Path, records: list) -> None:
    records.sort(key=lambda r: (r["fecha"], r["id"]))
    write_atomic(out / "archive.json", lambda t: t.write_text(json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8"))

    def w(t):
        with t.open("w", encoding="utf-8-sig", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=CSV_COLS, extrasaction="ignore"); wr.writeheader(); wr.writerows(records)
    write_atomic(out / "archive.csv", w)


def open_folder(p: Path) -> None:
    try:
        if sys.platform.startswith("win"): os.startfile(p)               # noqa
        elif sys.platform == "darwin": subprocess.Popen(["open", str(p)])
        else: subprocess.Popen(["xdg-open", str(p)])
    except Exception:
        pass


# --------------------------------------------------------------------------- principal
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", type=Path, help="carpeta, ZIP o foto")
    ap.add_argument("--out", type=Path, help="carpeta de salida (por defecto: junto a tus fotos)")
    ap.add_argument("--pin", action="store_true", help="una foto = un pin")
    ap.add_argument("--plantilla", choices=["auto", *core.LAYOUTS], default="auto")
    ap.add_argument("--rapido", action="store_true", help="no abrir la ventana de revisión si no hay avisos")
    ap.add_argument("--sin-gui", action="store_true", help="sin ventanas")
    ap.add_argument("--medir-regla", type=float, metavar="MM", help="medida real (mm) de la regla de 100 mm impresa")
    args = ap.parse_args()

    if args.medir_regla:
        if not 90 <= args.medir_regla <= 110:
            print("La regla debería medir cerca de 100 mm."); return 2
        CONFIG.write_text(json.dumps({"print_scale": round(args.medir_regla / 100, 5)}))
        print(f"Escala de impresora guardada: {args.medir_regla / 100:.4f}"); return 0
    scale = json.loads(CONFIG.read_text())["print_scale"] if CONFIG.exists() else 1.0
    if not CONFIG.exists():
        print("NOTA: asumo que imprimiste al 100 %. Mide la regla de 100 mm con una regla y ejecuta --medir-regla <mm>.\n")

    src = args.input
    if src is None:
        import tkinter as tk
        from tkinter import filedialog
        r = tk.Tk(); r.withdraw()
        pick = filedialog.askdirectory(title="Carpeta con tus fotos") or filedialog.askopenfilename(title="ZIP o foto")
        r.destroy()
        if not pick:
            return 0
        src = Path(pick)
    if not src.exists():
        print(f"No existe: {src}"); return 2
    out = (args.out or (src if src.is_dir() else src.parent) / "Lanyards_procesados").resolve()
    for d in ("web", "master", "originals"):
        (out / d).mkdir(parents=True, exist_ok=True)

    idx = out / "archive.json"
    records = json.loads(idx.read_text(encoding="utf-8")) if idx.exists() else []
    done = {k for r in records for k in r.get("_keys", [])}
    per = 1 if args.pin else 2
    use_gui = not args.sin_gui and has_gui()
    saved, failed, prev = [], [], {}

    try:
        with tempfile.TemporaryDirectory() as tmp:
            photos = [p for p in collect(src, Path(tmp)) if p.key not in done]
            if not photos:
                print("No hay fotos nuevas."); return 0
            groups = [photos[i:i + per] for i in range(0, len(photos), per)]
            print(f"{len(photos)} foto(s) -> {len(groups)} {'pin(es)' if args.pin else 'lanyard(s)'}. "
                  f"Salida: {out}\nEscribe q en cualquier pregunta para guardar y salir.\n")
            for n, g in enumerate(groups, 1):
                label = " + ".join(p.name for p in g)
                print(f"[{n}/{len(groups)}] {label}")
                if len(g) < per:
                    print("   Falta la foto del reverso: se salta.\n"); failed.append(label); continue
                try:
                    ans = [analyze(p, args, scale) for p in g]
                    for p, a in zip(g, ans):
                        print(f"   {p.name}: {a.width_mm:.1f} x {a.height_mm:.1f} mm"
                              + (f" · agujero ø{a.holes[0]['d_mm']:.1f}" if a.holes else ""))
                        for w in a.warnings:
                            print(f"      AVISO: {w}")
                    if use_gui and not (args.rapido and not any(a.warnings for a in ans)):
                        while True:
                            act = review(ans, label)
                            if act == "ok": break
                            if act == "skip": raise Skip
                            if act == "quit": raise Quit
                            i = int(act) - 1
                            ans[i] = analyze(g[i], args, scale, roi=pick_roi(core.calibrate(g[i].load(), args.plantilla).plane))
                    meta = ask_meta(args.pin, prev, g[0].taken)
                    rec = save_item(out, records, meta, g, ans)
                    records.append(rec); saved.append(rec); prev = meta
                    write_index(out, records)                     # se guarda tras cada lanyard
                    print(f"   Guardado: {rec['id']}\n")
                except Skip:
                    print("   Saltado (se volverá a ofrecer).\n")
                except (core.CalibrationError, ValueError) as e:
                    print(f"   NO PROCESADO: {e}\n"); failed.append(label)
    except (Quit, KeyboardInterrupt):
        print("\nSaliendo; lo ya guardado está a salvo.")
    finally:
        if records:
            write_index(out, records)

    print("=" * 60)
    for r in saved:
        print(f"  {r['id']:<45} {r['ancho_mm']} x {r['alto_mm']} mm")
    if failed:
        print("\nNo procesados. Repite la foto mala y mete esas dos fotos (anverso y reverso) en una carpeta NUEVA:\n  "
              + "\n  ".join(failed))
    print(f"\nCarpeta: {out}")
    open_folder(out)
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
