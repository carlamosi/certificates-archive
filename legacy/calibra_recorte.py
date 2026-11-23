#!/usr/bin/env python3
"""
calibra_recorte.py (v2) - Recorte métrico con plantilla de calibración A4.

Qué hace con cada foto:
  1. Abre HEIC/JPG/PNG respetando la orientación EXIF del iPhone.
  2. Localiza las 4 cruces "+" de la plantilla (correlación multiescala y multiángulo).
  3. Corrige la perspectiva a un plano métrico de 16 px/mm (rectángulo 150 x 210 mm).
  4. Separa el objeto del papel por color, quitando cuadrícula y motas.
  5. Mide ancho y alto reales, localiza los orificios y genera un PNG con canal alfa
     (el orificio queda transparente: esa es la máscara que usará la web).
  6. Evalúa la calidad de la toma y avisa de lo que empeora el resultado.
  7. Guarda master (PNG), web (WebP), depuración (JPG con el análisis dibujado) y medidas.csv.

Uso:
  python calibra_recorte.py foto1.heic foto2.jpg --out salida
  python calibra_recorte.py --calibrar-regla 99.4   # la regla de 100 mm impresa, medida con regla metálica
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import cv2
import numpy as np
import pillow_heif
from PIL import Image, ImageOps

pillow_heif.register_heif_opener()

PX_MM = 16                     # resolución del plano métrico (px por mm nominal)
REF_W, REF_H = 150.0, 210.0    # rectángulo de referencia nominal (mm)
MARGIN_MM = 5.0                # zona de seguridad: descarta cruces y bordes del plano
SHARP_MIN = 60.0               # varianza del laplaciano mínima (tunable)
CALIB = Path("calib.json")
CSV_COLS = ["archivo", "ancho_mm", "alto_mm", "orificios_mm", "ppm_foto", "nitidez",
            "reflejo_pct", "desequilibrio_luz", "no_paralelo_pct", "avisos"]


def dist(a, b) -> float:
    return float(math.hypot(a[0] - b[0], a[1] - b[1]))


def load_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as im:
        return np.asarray(ImageOps.exif_transpose(im).convert("RGB")).copy()


def load_factor() -> float:
    return float(json.loads(CALIB.read_text())["factor"]) if CALIB.exists() else 1.0


# ----------------------------------------------------------------- 1. cruces
def cross_kernel(arm: int, thick: int, angle: float) -> np.ndarray:
    size = 2 * arm + 2 * thick + 4
    c = size // 2
    k = np.zeros((size, size), np.float32)
    cv2.line(k, (c - arm, c), (c + arm, c), 1.0, thick)
    cv2.line(k, (c, c - arm), (c, c + arm), 1.0, thick)
    if angle:
        M = cv2.getRotationMatrix2D((c, c), angle, 1.0)
        k = cv2.warpAffine(k, M, (size, size))
    return k - k.mean()


def find_crosses(rgb: np.ndarray, max_side: int = 1400):
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape
    s = min(1.0, max_side / max(h, w))
    small = cv2.resize(gray, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else gray
    dark = cv2.GaussianBlur(255.0 - small.astype(np.float32), (3, 3), 0)
    m = max(small.shape)
    cands = []
    for arm in range(max(6, int(0.012 * m)), int(0.07 * m), 3):
        for ang in range(-12, 13, 4):
            k = cross_kernel(arm, 2, ang)
            res = cv2.matchTemplate(dark, k, cv2.TM_CCOEFF_NORMED)
            peak = cv2.dilate(res, np.ones((arm, arm), np.uint8))
            ys, xs = np.where((res >= peak) & (res > 0.35))
            half = k.shape[0] // 2
            for y, x in zip(ys, xs):
                cands.append((float(res[y, x]), (x + half) / s, (y + half) / s, arm / s))
    cands.sort(reverse=True)
    kept = []
    for c in cands:
        if all(dist(c[1:3], kc[1:3]) > 0.6 * c[3] for kc in kept):
            kept.append(c)
        if len(kept) >= 60:
            break
    return kept


def refine_corners(rgb, quad, arm_px):
    """Afina cada esquina a resolución completa: máximo de correlación con la cruz en una ventana local."""
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    dark = 255.0 - gray.astype(np.float32)
    out = []
    for p in quad:
        R = int(arm_px * 2.6)
        x, y = int(round(p[0])), int(round(p[1]))
        x0, y0 = max(0, x - R), max(0, y - R)
        win = dark[y0:y + R, x0:x + R]
        k = cross_kernel(int(arm_px), 2, 0)
        if win.shape[0] <= k.shape[0] or win.shape[1] <= k.shape[1]:
            out.append(p)
            continue
        res = cv2.matchTemplate(win, k, cv2.TM_CCOEFF_NORMED)
        half = k.shape[0] // 2
        _, _, _, mx = cv2.minMaxLoc(res)
        out.append((mx[0] + half + x0, mx[1] + half + y0))
    return np.float32(out)


def pick_corners(kept, n_top: int = 30):
    """Elige 4 cruces que formen un rectángulo convexo ~150x210 con ángulos rectos,
    maximizando la suma de correlaciones. Evita falsos positivos del borde y del objeto."""
    if len(kept) < 4:
        return None
    top = kept[:n_top]
    pts = [(c[1], c[2]) for c in top]
    sc = [c[0] for c in top]
    target = REF_W / REF_H
    best, best_q = -1e9, None
    n = len(top)
    for a in range(n):
        for b in range(a + 1, n):
            for c_ in range(b + 1, n):
                for d in range(c_ + 1, n):
                    idx = (a, b, c_, d)
                    qpts = [pts[i] for i in idx]
                    # orden angular para formar un cuadrilátero
                    cx = sum(p[0] for p in qpts) / 4
                    cy = sum(p[1] for p in qpts) / 4
                    order = sorted(range(4), key=lambda i: math.atan2(qpts[i][1] - cy, qpts[i][0] - cx))
                    q = np.float32([qpts[i] for i in order])
                    # TL, TR, BR, BL: el más arriba-izq. primero (min x+y) y sentido horario
                    s = q.sum(1)
                    k0 = int(s.argmin())
                    q = np.roll(q, -k0, axis=0)
                    if dist(q[0], q[1]) < dist(q[0], q[3]) * 0.5 and False:
                        continue
                    sides = [dist(q[i], q[(i + 1) % 4]) for i in range(4)]
                    if min(sides) < 0.3 * max(sides):
                        continue
                    ang_ok = True
                    for i in range(4):
                        v1 = q[(i - 1) % 4] - q[i]
                        v2 = q[(i + 1) % 4] - q[i]
                        cosang = float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9))
                        if abs(math.degrees(math.acos(max(-1, min(1, cosang)))) - 90) > 12:
                            ang_ok = False
                            break
                    if not ang_ok:
                        continue
                    ratio = min(sides[0], sides[1]) / max(sides[0], sides[1])
                    if abs(ratio - target) > 0.12 and abs(1 / ratio - target) > 0.12:
                        pass  # la proporción se valida aparte (permite plantilla girada)
                    # paralelogramo: en un rectángulo TL+BR ~ TR+BL (tolerante a perspectiva leve)
                    para = np.linalg.norm((q[0] + q[2]) - (q[1] + q[3])) / (sum(sides) + 1e-9)
                    pr = min(sides[0] + sides[2], sides[1] + sides[3]) / max(sides[0] + sides[2], sides[1] + sides[3])
                    ratio_wh = min(sides[0], sides[1]) / max(sides[0], sides[1])
                    score = (sum(sc[i] for i in idx) - 4.0 * para - 1.5 * abs(ratio_wh - target)
                             - 1.0 * (1 - pr))
                    if score > best:
                        best, best_q = score, q
    return best_q


def quad_checks(q):
    tl, tr, br, bl = q
    top, bot = dist(tl, tr), dist(bl, br)
    lef, rig = dist(tl, bl), dist(tr, br)
    par = max(abs(top - bot) / max(top, bot), abs(lef - rig) / max(lef, rig)) * 100
    ratio = min(top, lef) / max(top, lef)          # nominal 150/210 = 0,714
    return par, ratio


# ----------------------------------------------------------------- 2. plano métrico
def to_plane(rgb, quad):
    tl, tr, br, bl = quad
    landscape = dist(tl, tr) > dist(tl, bl)        # plantilla girada en la foto
    w_mm, h_mm = (REF_H, REF_W) if landscape else (REF_W, REF_H)
    W, H = int(w_mm * PX_MM), int(h_mm * PX_MM)
    dst = np.float32([[0, 0], [W - 1, 0], [W - 1, H - 1], [0, H - 1]])
    M = cv2.getPerspectiveTransform(quad, dst)
    plane = cv2.warpPerspective(rgb, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return plane


# ----------------------------------------------------------------- 3. segmentación
def segment(plane):
    """Fondo local (cierre morfológico a escala reducida) -> absorbe el degradado de luz.
    Objetos más estrechos que el kernel (~100 mm) desaparecen del fondo y se detectan como diferencia."""
    m = int(MARGIN_MM * PX_MM)
    H, W = plane.shape[:2]
    roi = plane[m:H - m, m:W - m]
    lab = cv2.cvtColor(cv2.GaussianBlur(roi, (5, 5), 0), cv2.COLOR_RGB2LAB).astype(np.float32)
    f = 8
    small = cv2.resize(lab, (lab.shape[1] // f, lab.shape[0] // f), interpolation=cv2.INTER_AREA)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (201, 201))
    bg_small = np.dstack([cv2.morphologyEx(small[..., c], cv2.MORPH_CLOSE, k) for c in range(3)])
    bg_small = cv2.GaussianBlur(bg_small, (0, 0), 6)
    bg = cv2.resize(bg_small, (lab.shape[1], lab.shape[0]), interpolation=cv2.INTER_LINEAR)
    diff = np.sqrt((lab[..., 0] - bg[..., 0]) ** 2 * 1.0 + (lab[..., 1] - bg[..., 1]) ** 2 * 0.5
                   + (lab[..., 2] - bg[..., 2]) ** 2 * 0.5)
    mask = (diff > 22).astype(np.uint8) * 255
    k2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k2)     # quita cuadrícula y motas
    return roi, lab, mask


def find_object(mask):
    cnts, hier = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    cnts = list(cnts)
    if not cnts:
        return None
    hier = hier[0]
    outers = [i for i in range(len(cnts)) if hier[i][3] == -1]
    if not outers:
        return None
    main = max(outers, key=lambda i: cv2.contourArea(cnts[i]))
    if cv2.contourArea(cnts[main]) < 0.01 * mask.size:
        return None
    holes = [i for i in range(len(cnts)) if hier[i][3] == main]
    return cnts, main, holes


def hole_list(cnts, hole_idx, obj_area):
    out = []
    for i in hole_idx:
        a = cv2.contourArea(cnts[i])
        p = cv2.arcLength(cnts[i], True)
        if p == 0 or not (0.0005 * obj_area < a < 0.05 * obj_area):
            continue
        circ = 4 * math.pi * a / (p * p)
        if circ > 0.6:
            (x, y), r = cv2.minEnclosingCircle(cnts[i])
            out.append({"idx": i, "x": x, "y": y, "d": 2 * r})
    return out


# ----------------------------------------------------------------- 4. recorte alineado
def rotated_crop(img, alpha, contour, holes):
    rect = cv2.minAreaRect(contour)
    box = cv2.boxPoints(rect)
    cx, cy = rect[0]

    def try_sign(sgn):
        M = cv2.getRotationMatrix2D((cx, cy), sgn * _edge_angle(box, cx, cy), 1.0)
        pb = box @ M[:, :2].T + M[:, 2]
        e = [pb[(i + 1) % 4] - pb[i] for i in range(4)]
        le = max(e, key=lambda v: np.hypot(*v))
        return abs(le[1]) / np.hypot(*le), M, pb

    d1, M1, pb1 = try_sign(1)
    d2, M2, pb2 = try_sign(-1)
    M, pb = (M1, pb1) if d1 <= d2 else (M2, pb2)
    H, W = img.shape[:2]
    rot = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    ral = cv2.warpAffine(alpha, M, (W, H), flags=cv2.INTER_NEAREST)
    x0, y0 = np.floor(pb.min(0)).astype(int) - 4
    x1, y1 = np.ceil(pb.max(0)).astype(int) + 4
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    out = np.dstack([rot[y0:y1, x0:x1], ral[y0:y1, x0:x1]])
    hs = []
    for h in holes:
        p = M[:, :2] @ np.array([h["x"], h["y"]]) + M[:, 2]
        hs.append({"x": p[0] - x0, "y": p[1] - y0, "d": h["d"]})
    return out, hs, (x1 - x0, y1 - y0)


def _edge_angle(box, cx, cy):
    e = [box[(i + 1) % 4] - box[i] for i in range(4)]
    le = max(e, key=lambda v: np.hypot(*v))
    return math.degrees(math.atan2(le[1], le[0]))


# ----------------------------------------------------------------- 5. calidad
def quality(roi, lab, mask_obj, mask_all, ppm_foto, par, ratio, holes, obj_bbox_touch):
    avisos = []
    g = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
    lap = cv2.Laplacian(g, cv2.CV_64F)
    sharp = float(lap[mask_obj > 0].var()) if (mask_obj > 0).any() else 0.0

    hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)
    glare = ((hsv[..., 2] > 240) & (hsv[..., 1] < 40) & (mask_obj > 0)).sum()
    glare_pct = 100.0 * glare / max(1, (mask_obj > 0).sum())

    paper = (mask_all == 0)
    w = roi.shape[1]
    Lp = lab[..., 0]
    left = Lp[:, : w // 3][paper[:, : w // 3]].mean()
    right = Lp[:, 2 * w // 3:][paper[:, 2 * w // 3:]].mean()
    luz = float(abs(left - right) * 100 / 255)

    if ppm_foto < 8:
        avisos.append(f"resolución baja ({ppm_foto:.1f} px/mm en la foto): acércate o usa 1x")
    if sharp < SHARP_MIN:
        avisos.append("posible desenfoque: toca la pantalla sobre el objeto antes de disparar")
    if glare_pct > 0.5:
        avisos.append(f"reflejo ({glare_pct:.1f} % del objeto): luz más difusa o cambia el ángulo")
    if luz > 12:
        avisos.append("luz lateral desigual: ponte de frente a la ventana o usa papel difusor")
    if par > 3:
        avisos.append(f"móvil no paralelo a la plantilla ({par:.1f} %): cámara en horizontal sobre la mesa")
    if abs(ratio - REF_W / REF_H) > 0.06:
        avisos.append("la proporción de la plantilla no es 150x210: revisa impresión o encuadre")
    if not holes:
        avisos.append("no veo orificio cerrado: si lo tiene, el fondo bajo el hueco debe ser claro")
    if obj_bbox_touch:
        avisos.append("el objeto toca la zona de seguridad: aléjalo de las cruces")
    return sharp, glare_pct, luz, avisos


# ----------------------------------------------------------------- proceso
def process(path: Path, out: Path, factor: float, manual=None):
    rgb = load_rgb(path)
    if manual is not None:
        quad = np.float32(manual)
    else:
        kept = find_crosses(rgb)
        quad = pick_corners(kept)
        if quad is None:
            return None, (f"no encuentro las 4 cruces ({len(kept)} candidatas). Abre la foto, "
                          "anota las 4 esquinas (TL, TR, BR, BL) y repite con --esquinas")
    par, ratio = quad_checks(quad)
    ppm_foto = math.sqrt(cv2.contourArea(quad.astype(np.float32)) / (REF_W * REF_H))

    plane = to_plane(rgb, quad)
    roi, lab, mask = segment(plane)
    found = find_object(mask)
    if found is None:
        return None, "no detecto el objeto sobre el papel (¿objeto claro sobre papel claro? usa fondo oscuro)"
    cnts, main, hole_idx = found
    obj_area = cv2.contourArea(cnts[main])
    holes = hole_list(cnts, hole_idx, obj_area)

    # Envolvente convexa: recupera zonas claras del objeto (p. ej. etiqueta blanca) que el fondo absorbe.
    hull = cv2.convexHull(cnts[main])
    alpha = np.zeros(mask.shape, np.uint8)
    cv2.drawContours(alpha, [hull], -1, 255, -1)
    for h in holes:
        cv2.drawContours(alpha, [cnts[h["idx"]]], -1, 0, -1)
    cnts[main] = hull

    x, y, bw, bh = cv2.boundingRect(cnts[main])
    touch = x <= 2 or y <= 2 or x + bw >= roi.shape[1] - 2 or y + bh >= roi.shape[0] - 2

    crop, hs, _ = rotated_crop(roi, alpha, cnts[main], holes)
    sharp, glare_pct, luz, avisos = quality(roi, lab, mask, mask, ppm_foto, par, ratio, holes, touch)

    dims = sorted([cv2.minAreaRect(cnts[main])[1][0] / PX_MM * factor,
                   cv2.minAreaRect(cnts[main])[1][1] / PX_MM * factor], reverse=True)
    stem = path.stem
    (out / "master").mkdir(parents=True, exist_ok=True)
    (out / "web").mkdir(parents=True, exist_ok=True)
    (out / "debug").mkdir(parents=True, exist_ok=True)

    Image.fromarray(crop, "RGBA").save(out / "master" / f"{stem}_recorte.png")
    web = Image.fromarray(crop, "RGBA")
    web.thumbnail((1200, 1200), Image.LANCZOS)
    web.save(out / "web" / f"{stem}_recorte.webp", quality=88, method=6)

    dbg = cv2.cvtColor(roi, cv2.COLOR_RGB2BGR)
    cv2.drawContours(dbg, [cnts[main]], -1, (255, 120, 0), 2)
    for h in holes:
        cv2.circle(dbg, (int(h["x"]), int(h["y"])), int(h["d"] / 2), (0, 255, 255), 2)
    cv2.imwrite(str(out / "debug" / f"{stem}_debug.jpg"), dbg, [cv2.IMWRITE_JPEG_QUALITY, 90])

    orif = ";".join(f"{h['d'] / PX_MM * factor:.1f}" for h in holes)
    row = {"archivo": path.name,
           "ancho_mm": f"{dims[0]:.2f}", "alto_mm": f"{dims[1]:.2f}",
           "orificios_mm": orif, "ppm_foto": f"{ppm_foto:.1f}", "nitidez": f"{sharp:.0f}",
           "reflejo_pct": f"{glare_pct:.2f}", "desequilibrio_luz": f"{luz:.1f}",
           "no_paralelo_pct": f"{par:.2f}", "avisos": " | ".join(avisos)}
    return row, None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("fotos", nargs="*", type=Path)
    ap.add_argument("--out", type=Path, default=Path("salida_recortes"))
    ap.add_argument("--calibrar-regla", type=float,
                    help="medida real en mm de la regla de 100 mm impresa (con regla metálica)")
    ap.add_argument("--esquinas", type=str, default=None,
                    help="esquinas manuales TL,TR,BR,BL como x1,y1,x2,y2,x3,y3,x4,y4 (píxeles de la foto original)")
    a = ap.parse_args()
    manual = None
    if a.esquinas:
        v = [float(t) for t in a.esquinas.split(",")]
        manual = [(v[0], v[1]), (v[2], v[3]), (v[4], v[5]), (v[6], v[7])]

    if a.calibrar_regla:
        factor = a.calibrar_regla / 100.0
        CALIB.write_text(json.dumps({"factor": round(factor, 5),
                                     "regla_medida_mm": a.calibrar_regla}, indent=2))
        print(f"factor de impresora = {factor:.5f} guardado en {CALIB}")
        return 0
    if not a.fotos:
        ap.error("indica al menos una foto o usa --calibrar-regla")

    factor = load_factor()
    print(f"factor de impresora: {factor:.5f}")
    a.out.mkdir(parents=True, exist_ok=True)
    csv_path = a.out / "medidas.csv"
    new = not csv_path.exists()
    with open(csv_path, "a", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLS)
        if new:
            w.writeheader()
        for p in a.fotos:
            row, err = process(p, a.out, factor, manual)
            if err:
                print(f"[ERROR] {p.name}: {err}")
                continue
            w.writerow(row)
            print(f"[OK] {p.name}: {row['ancho_mm']} x {row['alto_mm']} mm | "
                  f"orificios {row['orificios_mm'] or '-'} | nitidez {row['nitidez']} | "
                  f"avisos: {row['avisos'] or 'ninguno'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
