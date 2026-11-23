#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lanyard Archive v2
Calibración geométrica mediante 4 marcadores ArUco, selección asistida del objeto,
medición en mm y archivo SQLite con originales inmutables.

Uso:
  python lanyard_ingest_v2.py
  python lanyard_ingest_v2.py "C:\\Users\\...\\Pictures\\Lanyards"
  python lanyard_ingest_v2.py --input "fotos.zip" --out "archive"

Requiere opencv-contrib-python (incluye cv2.aruco).
No procesa silenciosamente una imagen sin calibración válida.
"""
from __future__ import annotations
import argparse, csv, datetime as dt, hashlib, json, os, re, shutil, sqlite3, sys, tempfile, zipfile
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np
import pillow_heif
import pymupdf
from PIL import Image, ImageOps

pillow_heif.register_heif_opener()

IMG_EXT = {".heic", ".heif", ".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}
PDF_EXT = {".pdf"}
MM_W, MM_H = 150.0, 210.0
PX_PER_MM = 8
OUT_W, OUT_H = int(MM_W*PX_PER_MM), int(MM_H*PX_PER_MM)
# Marker square size and top-left position in the physical template coordinate system.
MARKER_MM = 18.0
INSET_MM = 5.0
MARKER_LAYOUT = {
    0: (INSET_MM, INSET_MM),  # top-left
    1: (MM_W-INSET_MM-MARKER_MM, INSET_MM),  # top-right
    2: (MM_W-INSET_MM-MARKER_MM, MM_H-INSET_MM-MARKER_MM),  # bottom-right
    3: (INSET_MM, MM_H-INSET_MM-MARKER_MM),  # bottom-left
}
DATE_RE = re.compile(r"^\d{4}(?:-\d{2}(?:-\d{2})?)?$")

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def safe_slug(value: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:60] or "sin-titulo"

def ensure_dirs(out: Path) -> None:
    for name in ("originals", "calibrated", "master", "web", "quarantine"):
        (out/name).mkdir(parents=True, exist_ok=True)

def init_db(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("""
    CREATE TABLE IF NOT EXISTS items (
      uid TEXT PRIMARY KEY,
      pair_id TEXT,
      side TEXT NOT NULL CHECK(side IN ('front','back','single','unknown')),
      event TEXT NOT NULL,
      organizer TEXT DEFAULT '',
      event_date TEXT DEFAULT '',
      venue TEXT DEFAULT '',
      city TEXT DEFAULT '',
      role TEXT DEFAULT '',
      object_type TEXT DEFAULT 'lanyard',
      width_mm REAL,
      height_mm REAL,
      aspect_ratio REAL,
      calibrated INTEGER NOT NULL DEFAULT 0,
      calibration_error_px REAL,
      source_name TEXT NOT NULL,
      source_sha256 TEXT NOT NULL,
      original_path TEXT NOT NULL,
      calibrated_path TEXT NOT NULL,
      master_path TEXT NOT NULL,
      web_path TEXT NOT NULL,
      notes TEXT DEFAULT '',
      created_utc TEXT NOT NULL
    )""")
    con.execute("CREATE INDEX IF NOT EXISTS idx_items_event_date ON items(event_date)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_items_pair ON items(pair_id)")
    con.execute("CREATE TABLE IF NOT EXISTS imports (sha256 TEXT PRIMARY KEY, source_name TEXT, imported_utc TEXT)")
    con.commit()
    return con

def extract_zip(zpath: Path, dest: Path) -> list[Path]:
    root = dest.resolve()
    found=[]
    with zipfile.ZipFile(zpath) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name=info.filename.replace("\\","/")
            if name.startswith("/") or ".." in Path(name).parts or name.startswith("__MACOSX/"):
                continue
            target=(dest/name).resolve()
            if root not in target.parents:
                raise ValueError(f"Ruta insegura dentro del ZIP: {name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, target.open("wb") as dst:
                shutil.copyfileobj(src,dst)
            found.append(target)
    return found

def collect_inputs(source: Path, temp: Path) -> list[Path]:
    if source.is_dir():
        candidates=[p for p in source.rglob("*") if p.is_file()]
    elif source.suffix.lower()==".zip":
        candidates=extract_zip(source,temp)
    else:
        candidates=[source]
    return sorted([p for p in candidates if p.suffix.lower() in IMG_EXT|PDF_EXT],
                  key=lambda p:(p.stat().st_mtime,p.name.lower()))

def load_pages(path: Path, dpi: int=300) -> list[Image.Image]:
    if path.suffix.lower() in PDF_EXT:
        pages=[]
        with pymupdf.open(path) as doc:
            for page in doc:
                pix=page.get_pixmap(dpi=dpi,alpha=False)
                pages.append(Image.frombytes("RGB",(pix.width,pix.height),pix.samples))
        return pages
    with Image.open(path) as im:
        return [ImageOps.exif_transpose(im).convert("RGB")]

def marker_detector():
    if not hasattr(cv2, "aruco"):
        raise RuntimeError("Falta cv2.aruco. Instala opencv-contrib-python, no opencv-python.")
    aruco=cv2.aruco
    dictionary=aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
    params=aruco.DetectorParameters()
    return aruco, dictionary, params

def calibrate_page(rgb: np.ndarray) -> tuple[np.ndarray, float, int]:
    """Rectifica la zona 150x210 mm usando esquinas físicas de los IDs 0..3."""
    aruco,dictionary,params=marker_detector()
    gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
    if hasattr(aruco,"ArucoDetector"):
        corners, ids, _=aruco.ArucoDetector(dictionary,params).detectMarkers(gray)
    else:
        corners, ids, _=aruco.detectMarkers(gray,dictionary,parameters=params)
    if ids is None:
        raise ValueError("No se han detectado marcadores ArUco. Comprueba impresión, enfoque y luz.")
    found={int(mid): c.reshape(4,2) for c,mid in zip(corners,ids.flatten())}
    missing=set(MARKER_LAYOUT)-set(found)
    if missing:
        raise ValueError(f"Faltan marcadores: {sorted(missing)}. Deben verse los cuatro.")
    src=[]; dst=[]
    # ArUco corners are ordered TL, TR, BR, BL in marker coordinates.
    local=np.array([[0,0],[MARKER_MM,0],[MARKER_MM,MARKER_MM],[0,MARKER_MM]],np.float32)
    for mid,(x,y) in MARKER_LAYOUT.items():
        src.extend(found[mid])
        physical=local+np.array([x,y],np.float32)
        dst.extend(physical*np.array([PX_PER_MM,PX_PER_MM],np.float32))
    src=np.asarray(src,np.float32); dst=np.asarray(dst,np.float32)
    Hmat, inliers=cv2.findHomography(src,dst,cv2.RANSAC,3.0)
    if Hmat is None or inliers is None or int(inliers.sum()) < 12:
        raise ValueError("Calibración geométrica inconsistente; no se guardará el recorte.")
    projected=cv2.perspectiveTransform(src.reshape(-1,1,2),Hmat).reshape(-1,2)
    errors=np.linalg.norm(projected-dst,axis=1)
    err=float(np.sqrt(np.mean(errors**2)))
    if err > 3.0:
        raise ValueError(f"Error de calibración alto ({err:.2f}px). Repite la foto más perpendicular.")
    warped=cv2.warpPerspective(rgb,Hmat,(OUT_W,OUT_H),flags=cv2.INTER_CUBIC,
                               borderMode=cv2.BORDER_CONSTANT,borderValue=(255,255,255))
    return warped,err,len(found)

def choose_roi(calibrated: np.ndarray) -> tuple[int,int,int,int]:
    """Selección visual explícita: evita adivinar los límites de tarjetas con formas distintas."""
    preview=calibrated.copy()
    cv2.putText(preview,"Selecciona el objeto completo y pulsa ENTER",(20,35),
                cv2.FONT_HERSHEY_SIMPLEX,0.65,(20,50,100),2,cv2.LINE_AA)
    scale=min(1.0,1000.0/max(preview.shape[:2]))
    shown=cv2.resize(preview,None,fx=scale,fy=scale,interpolation=cv2.INTER_AREA) if scale<1 else preview
    roi=cv2.selectROI("Lanyard Archive - selecciona el objeto",shown,showCrosshair=True,fromCenter=False)
    cv2.destroyAllWindows()
    x,y,w,h=map(int,roi)
    if w<10 or h<10:
        raise ValueError("Selección cancelada o demasiado pequeña.")
    if scale<1:
        x,y,w,h=[int(round(v/scale)) for v in (x,y,w,h)]
    x=max(0,min(x,calibrated.shape[1]-1)); y=max(0,min(y,calibrated.shape[0]-1))
    w=min(w,calibrated.shape[1]-x); h=min(h,calibrated.shape[0]-y)
    if w<20 or h<20:
        raise ValueError("Selección demasiado pequeña.")
    return x,y,w,h

def ask(prompt: str, default: str="") -> str:
    suffix=f" [{default}]" if default else ""
    value=input(f"{prompt}{suffix}: ").strip()
    return value or default

def ask_date(default: str) -> str:
    while True:
        value=ask("Fecha del evento (AAAA-MM-DD o AAAA-MM)",default)
        if not value or DATE_RE.fullmatch(value):
            return value
        print("Formato no válido.")

def atomic_save_jpeg(image: Image.Image, path: Path) -> None:
    tmp=path.with_suffix(path.suffix+".tmp")
    image.save(tmp,format="JPEG",quality=97,subsampling=0,optimize=True)
    os.replace(tmp,path)

def export_csv(con: sqlite3.Connection, path: Path) -> None:
    rows=con.execute("SELECT uid,pair_id,side,event,organizer,event_date,venue,city,role,object_type,"
                     "width_mm,height_mm,aspect_ratio,calibrated,calibration_error_px,source_name,"
                     "original_path,calibrated_path,master_path,web_path,notes FROM items ORDER BY event_date,event,uid").fetchall()
    headers=["uid","pair_id","side","event","organizer","event_date","venue","city","role","object_type",
             "width_mm","height_mm","aspect_ratio","calibrated","calibration_error_px","source_name",
             "original_path","calibrated_path","master_path","web_path","notes"]
    tmp=path.with_suffix(".csv.tmp")
    with tmp.open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.writer(f); writer.writerow(headers); writer.writerows(rows)
    os.replace(tmp,path)

def process_one(path: Path, page_no: int, image: Image.Image, out: Path, con: sqlite3.Connection,
                args, digest: str) -> None:
    rgb=np.asarray(image.convert("RGB"))
    calibrated,err,nmarkers=calibrate_page(rgb)
    # Save a calibrated full-sheet image for audit and future reprocessing.
    stamp=dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    event=ask("Evento")
    if not event:
        raise ValueError("El nombre del evento es obligatorio.")
    event_date=ask_date("")
    organizer=ask("Organizador")
    city=ask("Ciudad")
    venue=ask("Lugar")
    role=ask("Rol / acreditación")
    object_type=ask("Tipo (lanyard/pin/tarjeta/otro)","lanyard").lower()
    side=ask("Cara (front/back/single/unknown)","single").lower()
    if side not in {"front","back","single","unknown"}:
        raise ValueError("Cara no válida.")
    pair_id=ask("ID de pareja (mismo valor para anverso y reverso; vacío si no aplica)")
    notes=ask("Notas")
    x,y,w,h=choose_roi(calibrated)
    crop=calibrated[y:y+h,x:x+w].copy()
    # Physical measurement is derived from the rectified sheet scale, not image EXIF/DPI.
    width_mm=w/PX_PER_MM
    height_mm=h/PX_PER_MM
    uid=f"{safe_slug(event)}-{stamp}"
    original_name=f"{uid}{path.suffix.lower()}"
    original_path=out/"originals"/original_name
    shutil.copy2(path,original_path)
    calibrated_path=out/"calibrated"/f"{uid}_sheet.jpg"
    master_path=out/"master"/f"{uid}_{side}.jpg"
    web_path=out/"web"/f"{uid}_{side}.webp"
    atomic_save_jpeg(Image.fromarray(calibrated),calibrated_path)
    atomic_save_jpeg(Image.fromarray(crop),master_path)
    web=Image.fromarray(crop)
    web.thumbnail((1800,1800),Image.Resampling.LANCZOS)
    tmp=web_path.with_suffix(".webp.tmp")
    web.save(tmp,format="WEBP",quality=88,method=6)
    os.replace(tmp,web_path)
    with con:
        con.execute("""INSERT INTO items VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (uid,pair_id,side,event,organizer,event_date,venue,city,role,object_type,
             round(width_mm,2),round(height_mm,2),round(width_mm/height_mm,5),1,round(err,3),
             path.name,digest,str(original_path.relative_to(out)),str(calibrated_path.relative_to(out)),
             str(master_path.relative_to(out)),str(web_path.relative_to(out)),notes,
             dt.datetime.now(dt.timezone.utc).isoformat()))
        con.execute("INSERT OR IGNORE INTO imports VALUES (?,?,?)",
                    (f"{digest}:{page_no}",path.name,dt.datetime.now(dt.timezone.utc).isoformat()))
    print(f"Guardado: {uid} · {width_mm:.1f} × {height_mm:.1f} mm · calibración {err:.2f}px")

def main() -> int:
    parser=argparse.ArgumentParser(description="Archivo digital calibrado de acreditaciones y lanyards.")
    parser.add_argument("--input",type=Path,help="Carpeta, ZIP, imagen o PDF de entrada.")
    parser.add_argument("--out",type=Path,default=Path("LanyardArchive"))
    parser.add_argument("--dpi",type=int,default=300)
    args=parser.parse_args()
    source=args.input
    if source is None:
        import tkinter as tk
        from tkinter import filedialog
        root=tk.Tk(); root.withdraw()
        chosen=filedialog.askdirectory(title="Selecciona la carpeta con tus fotos") or filedialog.askopenfilename(
            title="Selecciona un ZIP, imagen o PDF",
            filetypes=[("Archivos compatibles","*.zip *.jpg *.jpeg *.png *.heic *.heif *.webp *.tif *.tiff *.pdf")])
        root.destroy()
        if not chosen:
            print("No se ha seleccionado ninguna entrada."); return 0
        source=Path(chosen)
    if not source.exists():
        print(f"No existe: {source}"); return 2
    out=args.out.resolve(); ensure_dirs(out)
    con=init_db(out/"archive.sqlite3")
    try:
        with tempfile.TemporaryDirectory(prefix="lanyard_") as td:
            files=collect_inputs(source,Path(td))
            if not files:
                print("No se han encontrado imágenes o PDF compatibles."); return 1
            print(f"{len(files)} archivo(s). La calibración requiere los cuatro ArUco visibles.")
            for f in files:
                digest=sha256_file(f)
                try:
                    for page_no,img in enumerate(load_pages(f,args.dpi),1):
                        page_key=f"{digest}:{page_no}"
                        if con.execute("SELECT 1 FROM imports WHERE sha256=?",(page_key,)).fetchone():
                            print(f"Ya importado, omitido: {f.name} (página {page_no})")
                            continue
                        print(f"\nProcesando {f.name} (página {page_no})")
                        process_one(f,page_no,img,out,con,args,digest)
                except KeyboardInterrupt:
                    print("\\nInterrumpido por el usuario."); break
                except Exception as exc:
                    print(f"NO GUARDADO: {f.name}: {exc}")
                    # Keep failed source intact in quarantine for later inspection.
                    target=out/"quarantine"/f.name
                    if f.is_file() and not target.exists() and f.resolve()!=target.resolve():
                        try: shutil.copy2(f,target)
                        except OSError: pass
                export_csv(con,out/"archive.csv")
                (out/"archive.json").write_text(json.dumps(
                    [dict(zip([d[0] for d in con.execute("SELECT * FROM items").description],r))
                     for r in con.execute("SELECT * FROM items").fetchall()],
                    ensure_ascii=False,indent=2,default=str),encoding="utf-8")
            print(f"\\nArchivo: {out}\\nBase de datos: {out/'archive.sqlite3'}")
    finally:
        con.close()
    return 0

if __name__=="__main__":
    raise SystemExit(main())
