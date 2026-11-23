#!/usr/bin/env python3
"""
sync.py - Copia lo generado por Lanyard Archive a la web.

    python sync.py "ruta/a/Lanyards_procesados"

Copia archive.json a data/ y las imágenes WebP a img/web/, reescribiendo las rutas.
Puedes ejecutarlo cada vez que proceses lanyards nuevos: la web se actualiza sola.
"""
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__); return 2
    src = Path(sys.argv[1]).expanduser().resolve()
    index = src / "archive.json"
    if not index.exists():
        print(f"No encuentro {index}"); return 1

    records = json.loads(index.read_text(encoding="utf-8"))
    dst_img = HERE / "img" / "web"
    dst_img.mkdir(parents=True, exist_ok=True)
    for old in dst_img.glob("*.webp"):             # imágenes de la sincronización anterior
        old.unlink()
    (HERE / "data").mkdir(exist_ok=True)

    copied = 0
    for r in records:
        for key in ("front_web", "back_web"):
            rel = r.get(key) or ""
            if not rel:
                continue
            name = Path(rel).name
            shutil.copy2(src / rel, dst_img / name)
            r[key] = f"img/web/{name}"
            copied += 1
        for key in ("front_png", "back_png", "_keys"):
            r.pop(key, None)                       # la web solo necesita las WebP
    (HERE / "data" / "archive.json").write_text(json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(records)} objeto(s) · {copied} imagen(es) → {HERE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
