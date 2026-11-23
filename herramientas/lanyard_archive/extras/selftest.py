# -*- coding: utf-8 -*-
"""
selftest.py - Banco de pruebas con fotos sintéticas de medidas CONOCIDAS.

Genera "fotos" de la plantilla con una acreditación de tamaño exacto (esquinas redondeadas,
cabecera negra, etiqueta blanca casi igual al papel, banda lila, orificio con rotura), les aplica
una cámara real (perspectiva con distancia focal, ruido, desenfoque, JPEG) y luz lateral, y
compara lo que mide lanyard_core con la verdad.

    python selftest.py            # informe completo
    python selftest.py --rapido   # solo los casos principales
"""
from __future__ import annotations

import argparse
import io
import math
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import pymupdf
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import lanyard_core as core

HERE = Path(__file__).parent
PDFS = {"v2": HERE / "plantilla_calibracion_150x210_v2.pdf", "a4": ROOT / "plantilla_calibracion_A4_v3.pdf"}
DPI = 300
PPM_S = DPI / 25.4                          # px/mm de la hoja renderizada
PAGE_MM = (210.0, 297.0)
# centro de colocación del objeto en mm de página (origen arriba-izquierda)
CENTER = {"v2": (30 + 75.0, 43.5 + 95.0), "a4": (105.0, 150.0)}


def render_sheet(layout: str) -> np.ndarray:
    p = pymupdf.open(PDFS[layout])[0]
    pix = p.get_pixmap(dpi=DPI, alpha=False)
    sheet = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3).copy()
    sheet = (sheet.astype(np.float32) * np.array([0.985, 0.985, 0.95], np.float32)).astype(np.uint8)   # papel no 100 % blanco
    return sheet


def make_card(w_mm, h_mm, kind="ifest", hole_mm=6.0, tear=True):
    """RGBA a PPM_S px/mm. 'ifest' imita tu acreditación; 'white' = certificado blanco (caso difícil)."""
    W, H = int(round(w_mm * PPM_S)), int(round(h_mm * PPM_S))
    img = np.zeros((H, W, 4), np.uint8)
    if kind == "ifest":
        img[..., :3] = (246, 246, 250)                                  # etiqueta casi igual al papel
        img[: int(H * 0.30), :, :3] = (18, 18, 20)                      # cabecera negra
        img[int(H * 0.30) + int(H * 0.45): int(H * 0.30) + int(H * 0.52), :, :3] = (14, 14, 16)
        img[int(H * 0.82):, :, :3] = (160, 90, 175)                     # banda lila
        cv2.putText(img, "iFest", (int(W * 0.12), int(H * 0.22)), cv2.FONT_HERSHEY_SIMPLEX, W / 380, (250, 250, 250, 255), 3, cv2.LINE_AA)
        cv2.putText(img, "Projecte", (int(W * 0.1), int(H * 0.55)), cv2.FONT_HERSHEY_SIMPLEX, W / 700, (30, 30, 30, 255), 2, cv2.LINE_AA)
    else:
        img[..., :3] = (250, 250, 250)
        cv2.putText(img, "CERTIFICADO", (int(W * 0.1), int(H * 0.3)), cv2.FONT_HERSHEY_SIMPLEX, W / 450, (40, 40, 40, 255), 2, cv2.LINE_AA)
    img[..., 3] = 255
    r = int(4.0 * PPM_S)                                                # esquinas redondeadas 4 mm
    mask = np.zeros((H, W), np.uint8)
    cv2.rectangle(mask, (r, 0), (W - r, H), 255, -1)
    cv2.rectangle(mask, (0, r), (W, H - r), 255, -1)
    for cx, cy in [(r, r), (W - r, r), (r, H - r), (W - r, H - r)]:
        cv2.circle(mask, (cx, cy), r, 255, -1)
    if hole_mm > 0:
        hc = (W // 2, int(9.0 * PPM_S))
        cv2.circle(mask, hc, int(hole_mm / 2 * PPM_S), 0, -1)
        if tear:
            cv2.rectangle(mask, (hc[0] - int(0.8 * PPM_S), 0), (hc[0] + int(0.8 * PPM_S), hc[1]), 0, -1)
    img[..., 3] = mask
    return img


def paste(sheet, card, center_mm, angle):
    """Pega la tarjeta girada con sombra suave."""
    H, W = card.shape[:2]
    cx, cy = center_mm[0] * PPM_S, center_mm[1] * PPM_S
    M = cv2.getRotationMatrix2D((W / 2, H / 2), angle, 1.0)
    big = int(math.hypot(W, H)) + 8
    M[0, 2] += (big - W) / 2
    M[1, 2] += (big - H) / 2
    rc = cv2.warpAffine(card, M, (big, big), flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0))
    pad = big
    out = np.pad(sheet.astype(np.float32), ((pad, pad), (pad, pad), (0, 0)), mode="edge")
    x0, y0 = int(round(cx - big / 2)) + pad, int(round(cy - big / 2)) + pad
    a = rc[..., 3:4].astype(np.float32) / 255.0
    sh = cv2.GaussianBlur(rc[..., 3].astype(np.float32) / 255.0, (0, 0), 6)[..., None]
    sh = np.roll(np.roll(sh, 5, axis=1), 7, axis=0)
    region = out[y0:y0 + big, x0:x0 + big]
    region *= (1 - 0.22 * sh)                                           # sombra
    region[:] = region * (1 - a) + rc[..., :3].astype(np.float32) * a
    return np.clip(out[pad:-pad, pad:-pad], 0, 255).astype(np.uint8)


def photograph(sheet, ppm_photo=11.5, tilt=(3.0, -2.0), roll=4.0, light=0.12, light_dir=0.0, blur=0.8,
               noise=2.0, canvas=(3024, 4032), seed=0):
    """Proyección con cámara pinhole (f=3100 px) del plano de la hoja + luz lateral + ruido + JPEG."""
    rng = np.random.default_rng(seed)
    f = 3100.0
    cw, ch = canvas
    d = f / ppm_photo
    rx, ry, rz = [math.radians(v) for v in (tilt[0], tilt[1], roll)]
    Rx = np.array([[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]])
    Ry = np.array([[math.cos(ry), 0, math.sin(ry)], [0, 1, 0], [-math.sin(ry), 0, math.cos(ry)]])
    Rz = np.array([[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]])
    R = Rz @ Ry @ Rx
    sh_, sw_ = sheet.shape[:2]
    src = np.float32([[0, 0], [sw_, 0], [sw_, sh_], [0, sh_]])
    dst = []
    for u, v in src:
        P = R @ np.array([u / PPM_S - PAGE_MM[0] / 2, v / PPM_S - PAGE_MM[1] / 2, 0.0]) + np.array([0, 0, d])
        dst.append([f * P[0] / P[2] + cw / 2, f * P[1] / P[2] + ch / 2])
    Hs = cv2.getPerspectiveTransform(src, np.float32(dst))
    desk = np.full((ch, cw, 3), (92, 74, 58), np.float32) + rng.normal(0, 6, (ch, cw, 1)).astype(np.float32)
    desk = cv2.GaussianBlur(desk, (0, 0), 2)
    warped = cv2.warpPerspective(sheet, Hs, (cw, ch), flags=cv2.INTER_AREA)
    m = cv2.warpPerspective(np.full(sheet.shape[:2], 255, np.uint8), Hs, (cw, ch), flags=cv2.INTER_LINEAR)
    m = cv2.GaussianBlur(m, (0, 0), 1.0)[..., None].astype(np.float32) / 255.0
    img = warped.astype(np.float32) * m + desk * (1 - m)
    xs = np.linspace(-1, 1, cw, dtype=np.float32)[None, :]
    ys = np.linspace(-1, 1, ch, dtype=np.float32)[:, None]
    gx, gy = math.cos(light_dir), math.sin(light_dir)
    img *= (1 - light * (0.5 + 0.5 * (gx * xs + gy * ys)))[..., None]          # lámpara lateral
    img *= (1 - 0.08 * (xs ** 2 + ys ** 2))[..., None]                          # viñeteo
    if blur > 0:
        img = cv2.GaussianBlur(img, (0, 0), blur)
    img += rng.normal(0, noise, img.shape).astype(np.float32)
    jpg = io.BytesIO()
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(jpg, "JPEG", quality=88)
    return np.asarray(Image.open(io.BytesIO(jpg.getvalue())).convert("RGB")).copy()


def run_case(name, layout, w_mm, h_mm, expect_hole=True, kind="ifest", angle=7.0, verbose=True, **cam):
    sheet = render_sheet(layout)
    card = make_card(w_mm, h_mm, kind=kind, hole_mm=6.0 if expect_hole else 0.0, tear=expect_hole)
    sheet = paste(sheet, card, CENTER[layout], angle)
    photo = photograph(sheet, **cam)
    t = time.time()
    try:
        a = core.analyze(photo, layout="auto")
    except (core.CalibrationError, ValueError) as e:
        return {"name": name, "error": str(e)}
    dt = time.time() - t
    got = sorted([a.width_mm, a.height_mm])
    want = sorted([w_mm, h_mm])
    err = [got[0] - want[0], got[1] - want[1]]
    hole_d = max((h["d_mm"] for h in a.holes if not h["notch"]), default=None)
    n_notch = sum(h["notch"] for h in a.holes)
    return {"name": name, "layout": a.cal.layout.name, "w": a.width_mm, "h": a.height_mm, "err": err,
            "rms": a.cal.rms_mm, "holes": len(a.holes), "hole_d": hole_d, "notch": n_notch,
            "warn": a.warnings, "q": a.quality, "t": dt, "analysis": a}


def fmt(r):
    if "error" in r:
        return f"  {r['name']:<34} -> RECHAZADA: {r['error']}"
    e = r["err"]
    ok = "OK " if max(abs(e[0]), abs(e[1])) <= 0.6 else "REVISAR"
    hole = f"{r['holes']} hueco(s)" + (f" ø{r['hole_d']:.1f}" if r["hole_d"] else "") + (f" +rotura" if r["notch"] else "")
    return (f"  {r['name']:<34} {ok:<7} err ancho/alto = {e[0]:+.2f} / {e[1]:+.2f} mm | calib {r['rms']:.3f} mm | "
            f"{hole} | borde {r['q']['sharpness']:.2f}px | {r['t']:.1f}s" + (f"\n      avisos: {' | '.join(r['warn'])}" if r["warn"] else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--guardar", type=Path, help="carpeta donde guardar imágenes de depuración")
    a = ap.parse_args()

    print("=" * 100)
    print("AUTOTEST con medidas conocidas (acreditación A6-like con orificio roto; etiqueta blanca ~ papel)")
    print("=" * 100)
    cases = [
        ("v2 · 90x130 base", "v2", 90, 130, True, "ifest", 7.0, {}),
        ("a4 · A6 105x148 base", "a4", 105, 148, True, "ifest", -6.0, {}),
        ("a4 · luz lateral fuerte (35 %)", "a4", 105, 148, True, "ifest", 4.0, dict(light=0.35, light_dir=0.3)),
        ("a4 · móvil inclinado 10°", "a4", 105, 148, True, "ifest", 4.0, dict(tilt=(9.0, -7.0))),
        ("a4 · baja resolución (7 px/mm)", "a4", 105, 148, True, "ifest", 4.0, dict(ppm_photo=7.0)),
        ("a4 · desenfoque ligero", "a4", 105, 148, True, "ifest", 4.0, dict(blur=1.6)),
        ("a4 · desenfoque fuerte", "a4", 105, 148, True, "ifest", 4.0, dict(blur=4.5)),
        ("a4 · tarjeta pequeña 54x86", "a4", 54, 86, False, "ifest", 12.0, {}),
        ("a4 · certificado blanco (difícil)", "a4", 90, 120, False, "white", 3.0, {}),
    ]
    if a.rapido:
        cases = cases[:4]
    results = []
    for name, lay, w, h, hole, kind, ang, cam in cases:
        r = run_case(name, lay, w, h, hole, kind, ang, **cam)
        results.append(r)
        print(fmt(r))
        if a.guardar and "analysis" in r:
            a.guardar.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(a.guardar / f"{name.replace(' ', '_').replace('·', '')}.jpg"), r["analysis"].debug)

    if not a.rapido:
        print("\nLOTE ALEATORIO (40 fotos: plantilla, tamaño, giro, inclinación, luz, ruido al azar)")
        rng = np.random.default_rng(7)
        errs, fails, hole_miss = [], 0, 0
        for i in range(40):
            lay = "v2" if rng.random() < 0.4 else "a4"
            w = float(rng.uniform(60, 90 if lay == "v2" else 105))
            h = float(rng.uniform(85, 130 if lay == "v2" else 148))
            cam = dict(ppm_photo=float(rng.uniform(8, 13)), tilt=(float(rng.uniform(-6, 6)), float(rng.uniform(-6, 6))),
                       roll=float(rng.uniform(-8, 8)), light=float(rng.uniform(0.05, 0.3)),
                       light_dir=float(rng.uniform(0, 2 * math.pi)), blur=float(rng.uniform(0.5, 1.3)),
                       noise=float(rng.uniform(1.5, 3.5)), seed=i)
            r = run_case(f"rand{i}", lay, w, h, True, "ifest", float(rng.uniform(-20, 20)), **cam)
            if "error" in r:
                fails += 1
                print(f"  rand{i}: {r['error']}")
                continue
            errs.extend(r["err"])
            hole_miss += int(r["holes"] == 0)
        e = np.abs(np.array(errs))
        print(f"  válidas: {40 - fails}/40 | error medio {e.mean():.3f} mm | mediana {np.median(e):.3f} mm | "
              f"p95 {np.percentile(e, 95):.3f} mm | máximo {e.max():.3f} mm | sin detectar orificio: {hole_miss}")

        print("\nCASOS QUE DEBEN FALLAR (el programa debe negarse a guardar, no inventar medidas)")
        sheet = render_sheet("a4")
        sheet = paste(sheet, make_card(105, 148), CENTER["a4"], 5.0)
        x, y = core.LAYOUTS["a4"].markers[1]
        occl = sheet.copy()
        cv2.rectangle(occl, (int(x * PPM_S), int(y * PPM_S)), (int((x + 20) * PPM_S), int((y + 20) * PPM_S)), (230, 230, 230), -1)
        try:
            core.analyze(photograph(occl))
            print("  marcador tapado          -> ERROR: aceptó una foto con un marcador tapado")
        except core.CalibrationError as e:
            print(f"  marcador tapado          -> rechazada correctamente: {e}")
        near = paste(render_sheet("a4"), make_card(105, 148), (105.0, 40.0), 0.0)     # objeto encima del marcador superior
        try:
            r = core.analyze(photograph(near))
            print(f"  objeto sobre marcadores  -> avisos: {r.warnings}")
        except (core.CalibrationError, ValueError) as e:
            print(f"  objeto sobre marcadores  -> rechazada: {e}")

    bad = [r for r in results if "err" in r and isinstance(r["err"], list) and max(abs(r["err"][0]), abs(r["err"][1])) > 0.6]
    print("\nRESUMEN: " + ("todos los casos principales dentro de ±0,6 mm" if not bad else f"{len(bad)} caso(s) fuera de ±0,6 mm"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
