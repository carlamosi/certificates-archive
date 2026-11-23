# -*- coding: utf-8 -*-
"""
lanyard_core.py - Núcleo de visión de Lanyard Archive v3 (sin entrada/salida de usuario).

Cadena completa:
  foto -> 4 marcadores ArUco -> homografía a mm reales -> plano rectificado (10 px/mm)
       -> modelo de la superficie del papel (ajuste polinómico robusto, absorbe la luz lateral)
       -> segmentación del objeto -> contorno convexo refinado a resolución completa
       -> orificios (máscara alfa) -> enderezado -> medidas en mm + controles de calidad.

Todo es determinista y se puede probar sin pantalla (ver selftest.py).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import cv2
import numpy as np

PX_MM = 10            # resolución del plano rectificado (px por mm)
SHARP_WARN_PX = 2.2   # sigma de borde (px) a partir de la cual se avisa de desenfoque
SMALL = 0.2           # factor de la imagen de trabajo para el ajuste del papel (-> 2 px/mm)


# --------------------------------------------------------------------------- plantillas
@dataclass(frozen=True)
class Layout:
    name: str
    title: str
    plane_mm: tuple          # (ancho, alto) del plano rectificado
    marker_mm: float         # lado del marcador ArUco
    markers: dict            # id -> (x, y) esquina superior izquierda, en mm
    zone_mm: tuple           # (x, y, ancho, alto) de la zona de colocación recomendada
    border_mm: float = 2.0   # franja exterior que se ignora


LAYOUTS = {
    "v2": Layout("v2", "Plantilla v2 (marco 150x210, ArUco 18 mm)", (150.0, 210.0), 18.0,
                 {0: (5.0, 5.0), 1: (127.0, 5.0), 2: (127.0, 187.0), 3: (5.0, 187.0)},
                 (25.0, 25.0, 100.0, 120.0), 2.0),
    "a4": Layout("a4", "Plantilla A4 v3 (hoja completa, ArUco 20 mm)", (210.0, 297.0), 20.0,
                 {0: (10.0, 10.0), 1: (180.0, 10.0), 2: (180.0, 267.0), 3: (10.0, 267.0)},
                 (30.0, 40.0, 150.0, 210.0), 6.0),
}


class CalibrationError(Exception):
    """La foto no permite una calibración fiable; no se debe guardar nada."""


# --------------------------------------------------------------------------- 1. calibración
def _detect_markers(gray: np.ndarray) -> dict:
    ar = cv2.aruco
    dictionary = ar.getPredefinedDictionary(ar.DICT_4X4_50)
    found: dict = {}
    for profile in range(3):
        p = ar.DetectorParameters()
        p.cornerRefinementMethod = ar.CORNER_REFINE_SUBPIX
        if profile >= 1:                                   # perfil más tolerante
            p.adaptiveThreshWinSizeMin, p.adaptiveThreshWinSizeMax, p.adaptiveThreshWinSizeStep = 5, 83, 10
            p.minMarkerPerimeterRate, p.polygonalApproxAccuracyRate = 0.01, 0.05
        g = gray if profile < 2 else cv2.createCLAHE(2.0, (8, 8)).apply(gray)
        corners, ids, _ = ar.ArucoDetector(dictionary, p).detectMarkers(g)
        if ids is None:
            continue
        for c, i in zip(corners, ids.flatten()):
            if int(i) in range(4) and int(i) not in found:
                found[int(i)] = c.reshape(4, 2).astype(np.float64)
        if len(found) == 4:
            break
    return found


def _fit(found: dict, layout: Layout):
    local = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], np.float64) * layout.marker_mm
    src = np.vstack([found[i] for i in layout.markers])
    dst = np.vstack([local + np.array(layout.markers[i]) for i in layout.markers])
    H, _ = cv2.findHomography(src, dst, 0)
    if H is None:
        return None, 1e9, 1e9
    proj = cv2.perspectiveTransform(src.reshape(-1, 1, 2), H).reshape(-1, 2)
    err = np.linalg.norm(proj - dst, axis=1)
    return H, float(np.sqrt((err ** 2).mean())), float(err.max())


def _marker_sharpness(gray: np.ndarray, found: dict) -> float:
    """Anchura típica del borde (sigma, px) medida en los marcadores, que tienen contraste máximo conocido.
    Para un escalón difuminado con sigma s, la pendiente máxima es contraste/(s*sqrt(2*pi)) -> s = 0,4*contraste/pendiente.
    Cuanto MENOR, más nítida (nítida ~0,6-1,2 px; desenfocada >2 px)."""
    vals = []
    for c in found.values():
        x0, y0 = np.floor(c.min(0)).astype(int)
        x1, y1 = np.ceil(c.max(0)).astype(int)
        crop = gray[max(0, y0):y1, max(0, x0):x1].astype(np.float32)
        if crop.size < 400:
            continue
        lo, hi = np.percentile(crop, [2, 98])
        contrast = max(float(hi - lo), 1.0)
        gx = cv2.Sobel(crop, cv2.CV_32F, 1, 0, ksize=3, scale=1 / 8.0)
        gy = cv2.Sobel(crop, cv2.CV_32F, 0, 1, ksize=3, scale=1 / 8.0)
        slope = float(np.percentile(np.hypot(gx, gy), 97))
        vals.append(0.4 * contrast / max(slope, 1e-3))
    return float(np.median(vals)) if vals else 99.0


@dataclass
class Calibration:
    layout: Layout
    plane: np.ndarray              # RGB rectificado, PX_MM px/mm
    rms_mm: float
    max_mm: float
    photo_px_per_mm: float
    tilt_pct: float
    sharp: float
    layout_margin: float           # rms(2.ª mejor plantilla) / rms(elegida): >2 = elección clara
    warnings: list = field(default_factory=list)


def calibrate(rgb: np.ndarray, layout: str = "auto") -> Calibration:
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    found = _detect_markers(gray)
    if len(found) < 4:
        missing = sorted(set(range(4)) - set(found))
        raise CalibrationError(f"Solo veo {len(found)} de 4 marcadores (faltan IDs {missing}). "
                               "Encuadra la hoja completa, sin tapar ni doblar ningún marcador.")
    cands = LAYOUTS if layout == "auto" else {layout: LAYOUTS[layout]}
    fits = {n: _fit(found, l) for n, l in cands.items()}
    name = min(fits, key=lambda n: fits[n][1])
    H, rms, mx = fits[name]
    if rms > 0.6:
        raise CalibrationError(f"Calibración inconsistente (error {rms:.2f} mm). Repite la foto: "
                               "hoja plana, móvil paralelo y marcadores nítidos.")
    others = [v[1] for n, v in fits.items() if n != name]
    margin = (min(others) / max(rms, 1e-6)) if others else 99.0
    lay = LAYOUTS[name]
    W, Hh = (int(round(v * PX_MM)) for v in lay.plane_mm)
    M = np.diag([PX_MM, PX_MM, 1.0]) @ H
    plane = cv2.warpPerspective(rgb, M, (W, Hh), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    side = np.mean([np.linalg.norm(found[i][(k + 1) % 4] - found[i][k]) for i in found for k in range(4)])
    ppm = float(side / lay.marker_mm)
    c = {i: found[i].mean(0) for i in found}
    d = lambda a, b: float(np.linalg.norm(c[a] - c[b]))
    tilt = max(abs(d(0, 1) - d(3, 2)) / max(d(0, 1), d(3, 2)),
               abs(d(0, 3) - d(1, 2)) / max(d(0, 3), d(1, 2))) * 100
    sharp = _marker_sharpness(gray, found)

    w = []
    if layout == "auto" and margin < 1.6:
        w.append("no distingo con claridad qué plantilla has usado; indica --plantilla v2 o a4")
    if ppm < 6:
        w.append(f"resolución baja ({ppm:.1f} px/mm en la foto): acércate o usa la cámara 1x")
    if tilt > 20:
        w.append(f"móvil muy inclinado ({tilt:.0f} %): se corrige, pero pierdes nitidez en el lado lejano")
    return Calibration(lay, plane, rms, mx, ppm, tilt, sharp, margin, w)


# --------------------------------------------------------------------------- 2. segmentación
def keepout_mask(layout: Layout, scale: float) -> np.ndarray:
    """1 = zona que nunca puede contener objeto (marcadores + margen, borde de la hoja)."""
    W, H = (int(round(v * scale)) for v in layout.plane_mm)
    ko = np.zeros((H, W), np.uint8)
    m = 3.0
    for (x, y) in layout.markers.values():
        x0, y0 = int((x - m) * scale), int((y - m) * scale)
        x1, y1 = int(math.ceil((x + layout.marker_mm + m) * scale)), int(math.ceil((y + layout.marker_mm + m) * scale))
        ko[max(0, y0):y1, max(0, x0):x1] = 1
    b = max(1, int(layout.border_mm * scale))
    ko[:b], ko[-b:], ko[:, :b], ko[:, -b:] = 1, 1, 1, 1
    return ko


def _design(xn, yn):
    return np.stack([np.ones_like(xn), xn, yn, xn * xn, xn * yn, yn * yn], axis=-1)


def fit_paper(lab: np.ndarray, valid: np.ndarray):
    """Superficie de papel = polinomio de grado 2 por canal, ajustado de forma iterativa y robusta.
    Absorbe degradados de luz (lámpara lateral); lo que se aleja de la superficie es 'objeto'."""
    h, w, _ = lab.shape
    yy, xx = np.mgrid[0:h, 0:w]
    A = _design((xx / (w - 1)) * 2 - 1, (yy / (h - 1)) * 2 - 1).reshape(-1, 6).astype(np.float64)
    X = lab.reshape(-1, 3).astype(np.float64)
    v = valid.ravel()
    inl = v & (X[:, 0] >= np.percentile(X[v, 0], 40))           # semilla: el 60 % más claro
    wts = np.array([1.0, 0.8, 0.8])
    coef, res = None, None
    rng = np.random.default_rng(0)
    for T in (26, 20, 15, 12, 10):
        idx = np.flatnonzero(inl)
        if idx.size < 200:
            break
        if idx.size > 40000:
            idx = rng.choice(idx, 40000, replace=False)
        coef = np.linalg.lstsq(A[idx], X[idx], rcond=None)[0]
        res = np.linalg.norm((A @ coef - X) * wts, axis=1)
        inl = v & (res < T)
    if coef is None:
        raise ValueError("no encuentro papel suficiente alrededor del objeto")
    sigma = 1.4826 * np.median(np.abs(res[inl] - np.median(res[inl]))) if inl.any() else 3.0
    surf = (A @ coef).reshape(h, w, 3)
    return coef, surf.astype(np.float32), res.reshape(h, w), float(sigma), float((surf[..., 0].max() - surf[..., 0].min()))


def _largest(mask: np.ndarray):
    n, lab, st, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if n <= 1:
        return None
    i = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    return (lab == i).astype(np.uint8) * 255


def _significant(mask: np.ndarray, min_area_px: int):
    """Une todos los trozos relevantes (p. ej. cabecera y banda de una tarjeta con etiqueta blanca,
    casi igual al papel). Devuelve la máscara unión o None."""
    n, lab, st, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    keep = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= min_area_px]
    if not keep:
        return None
    return (np.isin(lab, keep)).astype(np.uint8) * 255


@dataclass
class Segment:
    hull: np.ndarray               # polígono convexo (px del plano a resolución completa)
    alpha_plane: np.ndarray        # máscara 0/255 a resolución completa (con orificios)
    holes: list                    # [{cx, cy, d_mm, area_mm2, notch}]
    width_mm: float
    height_mm: float
    angle_deg: float
    rectangularity: float
    light_var_pct: float
    flags: list = field(default_factory=list)
    resf_thr: float = 0.0
    mode: str = "rect"                       # "rect" (rectangular) | "forma" (silueta libre, p. ej. una medalla)
    outline: list = field(default_factory=list)   # polígonos para dibujar el contorno


def segment_object(plane: np.ndarray, layout: Layout, roi=None, find_holes: bool = True) -> Segment:
    H, W = plane.shape[:2]
    sw, sh = int(W * SMALL), int(H * SMALL)
    small = cv2.resize(plane, (sw, sh), interpolation=cv2.INTER_AREA)
    lab_s = cv2.cvtColor(cv2.GaussianBlur(small, (3, 3), 0).astype(np.float32) / 255.0, cv2.COLOR_RGB2LAB)
    valid = keepout_mask(layout, PX_MM * SMALL) == 0
    if roi is not None:
        rm = np.zeros_like(valid)
        x, y, w, h = [int(v * SMALL) for v in roi]
        rm[y:y + h, x:x + w] = True
        valid &= rm
    coef, surf_s, res_s, sigma, lvar = fit_paper(lab_s, valid)
    thr = float(max(9.0, 4.0 * sigma))
    sensitive = False

    def _mask(t):
        m = ((res_s > t) & valid).astype(np.uint8) * 255
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
        return _significant(m, int(150 * (PX_MM * SMALL) ** 2))

    comp = _mask(thr)
    if comp is None:                                   # objeto claro: reintento con mayor sensibilidad
        thr, sensitive = float(max(4.0, 3.0 * sigma)), True
        comp = _mask(thr)
    if comp is None:
        raise ValueError("no distingo el objeto del papel (¿blanco sobre blanco?). Pon una cartulina oscura mate debajo del objeto y repite la foto")
    cnts, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    hull_s = cv2.convexHull(np.vstack(cnts))

    # --- refinado a resolución completa dentro de una banda alrededor del casco
    band_s = np.zeros((sh, sw), np.uint8)
    cv2.fillPoly(band_s, [hull_s], 255)
    band_s = cv2.dilate(band_s, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
    band = cv2.resize(band_s, (W, H), interpolation=cv2.INTER_NEAREST)
    surf = cv2.resize(surf_s, (W, H), interpolation=cv2.INTER_CUBIC)
    lab_f = cv2.cvtColor(cv2.GaussianBlur(plane, (0, 0), 1.2).astype(np.float32) / 255.0, cv2.COLOR_RGB2LAB)
    resf = np.linalg.norm((lab_f - surf) * np.array([1.0, 0.8, 0.8], np.float32), axis=2)
    maskf = ((resf > thr) & (band > 0)).astype(np.uint8) * 255
    maskf = cv2.morphologyEx(maskf, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    compf = _significant(maskf, int(150 * PX_MM ** 2))
    if compf is None:
        raise ValueError("no distingo el objeto del papel (¿blanco sobre blanco?). Pon una cartulina oscura mate debajo del objeto y repite la foto")
    # Borde al 50 % del contraste de cada trozo: invariante al desenfoque y a sombras suaves.
    n_c, lab_c0, st_c, _ = cv2.connectedComponentsWithStats(compf, connectivity=8)
    half = np.zeros_like(compf)
    k_dil = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * int(3 * PX_MM) + 1,) * 2)
    for i in range(1, n_c):
        comp_i = (lab_c0 == i).astype(np.uint8)
        core_i = cv2.erode(comp_i, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * int(2 * PX_MM) + 1,) * 2))
        if core_i.sum() < 500:
            core_i = comp_i
        contrast = float(np.median(resf[core_i > 0]))
        near = cv2.dilate(comp_i, k_dil)
        half |= ((resf > max(thr, 0.5 * contrast)) & (near > 0)).astype(np.uint8) * 255
    half = cv2.morphologyEx(half, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    compf = _significant(half, int(150 * PX_MM ** 2)) if half.any() else compf
    cf, _ = cv2.findContours(compf, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    hull = cv2.convexHull(np.vstack(cf))
    inside = np.zeros((H, W), np.uint8)
    cv2.fillPoly(inside, [hull], 255)

    rect = cv2.minAreaRect(hull)
    rectangularity = float(cv2.contourArea(hull) / max(rect[1][0] * rect[1][1], 1.0))
    is_rect = rectangularity >= 0.92

    flags = []
    if sensitive:
        flags.append("objeto muy claro: contorno de baja confianza; coloca una cartulina oscura debajo y repite")
    if (inside & (cv2.resize(keepout_mask(layout, PX_MM), (W, H)) * 255)).any():
        flags.append("el objeto toca un marcador o el borde de la hoja: apártalo")

    frame_M = np.float64([[1, 0, 0], [0, 1, 0]])
    if is_rect:
        # Rectángulo robusto: se ignoran el 3 % de puntos más extremos de cada lado (protuberancias, flecos).
        ang = ((rect[2] + 45) % 90) - 45
        Mr = cv2.getRotationMatrix2D(rect[0], ang, 1.0)
        pts_c = np.vstack([c_.reshape(-1, 2) for c_ in cf]).astype(np.float32)   # contorno real, no la envolvente
        p = pts_c @ Mr[:, :2].T + Mr[:, 2]
        x0, x1 = np.percentile(p[:, 0], [3, 97])
        y0, y1 = np.percentile(p[:, 1], [3, 97])
        corners = np.float32([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])
        hull = (corners - Mr[:, 2]) @ np.linalg.inv(Mr[:, :2]).T
        clip = np.zeros((H, W), np.uint8)
        cv2.fillPoly(clip, [np.round(hull).astype(np.int32)], 255)
        inside = cv2.bitwise_and(inside, clip)                  # conserva las esquinas redondeadas, recorta bultos
        outline = [hull]
        frame_M = Mr
        fx0, fx1, fy0, fy1 = float(x0), float(x1), float(y0), float(y1)
    else:
        # Forma libre: silueta real (no la envolvente convexa).
        sil = cv2.morphologyEx(compf, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)))
        sc, _ = cv2.findContours(sil, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        inside = np.zeros((H, W), np.uint8)
        cv2.drawContours(inside, sc, -1, 255, -1)
        outline = [c_.reshape(-1, 2) for c_ in sc]
        ysb, xsb = np.where(inside > 0)
        fx0, fx1, fy0, fy1 = float(xsb.min()), float(xsb.max()), float(ysb.min()), float(ysb.max())
        if rectangularity < 0.5:
            flags.append("forma muy irregular: revisa el contorno en la ventana")

    # --- orificios: arriba, redondos (o una rotura abierta al borde superior), como mucho 2
    holes, alpha = [], inside.copy()
    if find_holes:
        top_limit = fy0 + min(30.0 * PX_MM, 0.25 * (fy1 - fy0))
        contrast = float(np.median(resf[compf > 0]))
        thr_hole = min(max(thr, 0.5 * contrast), 30.0)      # media-altura: la sombra dentro del hueco no lo encoge
        paperlike = ((resf <= thr_hole) & (inside > 0)).astype(np.uint8)
        dist_edge = cv2.distanceTransform(inside, cv2.DIST_L2, 5) / PX_MM
        n, lab_c, st, cen = cv2.connectedComponentsWithStats(paperlike, connectivity=8)
        cands = []
        for i in range(1, n):
            area_mm2 = st[i, cv2.CC_STAT_AREA] / PX_MM ** 2
            cx, cy = cen[i]
            fx, fy = frame_M[:, :2] @ np.array([cx, cy]) + frame_M[:, 2]      # coordenadas en el marco del objeto
            if not (3.0 <= area_mm2 <= 160.0) or fy > top_limit:
                continue                                            # solo arriba y de tamaño de orificio
            x, y, w_, h_ = st[i, 0:4]
            sub = (lab_c[y:y + h_, x:x + w_] == i).astype(np.uint8)
            cc, _ = cv2.findContours(sub, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            per = cv2.arcLength(max(cc, key=cv2.contourArea), True)
            circ = 4 * math.pi * area_mm2 * PX_MM ** 2 / max(per * per, 1.0)
            thick = cv2.distanceTransform(sub, cv2.DIST_L2, 3).max() / PX_MM
            dmin = float(dist_edge[y:y + h_, x:x + w_][sub > 0].min())
            interior_x = fx0 + 8 * PX_MM < fx < fx1 - 8 * PX_MM
            notch = dmin < 1.5 and thick >= 1.2 and interior_x and fy < fy0 + 15 * PX_MM
            roundhole = circ > 0.6 and thick >= 1.0
            if notch or roundhole:
                cands.append((area_mm2, i, cx, cy, notch))
        for area_mm2, i, cx, cy, notch in sorted(cands, reverse=True)[:2]:
            alpha[lab_c == i] = 0
            holes.append({"cx": float(cx), "cy": float(cy), "d_mm": float(2 * math.sqrt(area_mm2 / math.pi)),
                          "area_mm2": float(area_mm2), "notch": bool(notch)})
    return Segment(hull.reshape(-1, 2).astype(np.float32), alpha, holes, 0.0, 0.0,
                   float(rect[2]), rectangularity, float(lvar), flags, thr,
                   "rect" if is_rect else "forma", outline)


# --------------------------------------------------------------------------- 3. enderezado y recorte
def deskew_crop(plane: np.ndarray, seg: Segment, pad_px: int = 3):
    """Gira el plano para alinear los bordes del objeto con los ejes; devuelve recorte RGB + alfa y medidas."""
    if seg.mode == "forma":
        ang, (cx, cy) = 0.0, (0.0, 0.0)             # sin girar: anverso y reverso son espejo uno del otro
    else:
        rect = cv2.minAreaRect(seg.hull)
        ang = ((rect[2] + 45) % 90) - 45            # corrección en [-45, 45]
        (cx, cy) = rect[0]
    M = cv2.getRotationMatrix2D((cx, cy), ang, 1.0)
    H, W = plane.shape[:2]
    rot = cv2.warpAffine(plane, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    arot = cv2.warpAffine(seg.alpha_plane, M, (W, H), flags=cv2.INTER_LINEAR)
    pts = (seg.hull @ M[:, :2].T) + M[:, 2]
    width_mm = float(pts[:, 0].max() - pts[:, 0].min()) / PX_MM
    height_mm = float(pts[:, 1].max() - pts[:, 1].min()) / PX_MM
    x0, y0 = np.floor(pts.min(0)).astype(int)
    x1, y1 = np.ceil(pts.max(0)).astype(int)
    x0, y0, x1, y1 = max(0, x0 - pad_px), max(0, y0 - pad_px), min(W, x1 + pad_px), min(H, y1 + pad_px)
    crop = rot[y0:y1, x0:x1].copy()
    a = arot[y0:y1, x0:x1]
    a = cv2.erode((a > 127).astype(np.uint8) * 255, np.ones((3, 3), np.uint8))   # quita el halo de papel
    a = cv2.GaussianBlur(a, (0, 0), 1.0)
    holes = []
    for h in seg.holes:
        p = M[:, :2] @ np.array([h["cx"], h["cy"]]) + M[:, 2]
        holes.append({**h, "cx": float(p[0] - x0), "cy": float(p[1] - y0)})
    return crop, a, width_mm, height_mm, float(ang), holes


# --------------------------------------------------------------------------- 4. calidad
def quality_checks(cal: Calibration, seg: Segment, crop: np.ndarray, alpha: np.ndarray) -> tuple[dict, list]:
    obj = alpha > 127
    sat = float(((crop >= 253).all(axis=2) & obj).sum() / max(obj.sum(), 1) * 100)
    q = {"sharpness": round(cal.sharp, 2), "clipped_pct": round(sat, 2), "light_var": round(seg.light_var_pct, 1),
         "tilt_pct": round(cal.tilt_pct, 1), "photo_px_per_mm": round(cal.photo_px_per_mm, 1)}
    w = list(cal.warnings) + list(seg.flags)
    if cal.sharp > SHARP_WARN_PX:
        w.append(f"foto desenfocada (borde {cal.sharp:.1f} px): toca la pantalla sobre el objeto antes de disparar y apoya el móvil")
    if sat > 4.0:
        w.append(f"{sat:.1f} % del objeto está quemado (blanco puro): reflejo o exceso de luz; usa luz difusa")
    if seg.light_var_pct > 18:
        w.append("luz muy desigual en la hoja: colócate de frente a la ventana o difumina la lámpara")
    return q, w


# --------------------------------------------------------------------------- 5. todo en uno
@dataclass
class Analysis:
    cal: Calibration
    seg: Segment
    crop: np.ndarray
    alpha: np.ndarray
    width_mm: float
    height_mm: float
    angle_deg: float
    holes: list
    quality: dict
    warnings: list
    debug: np.ndarray


def analyze(rgb: np.ndarray, layout: str = "auto", roi=None, print_scale: float = 1.0,
            find_holes: bool = True) -> Analysis:
    cal = calibrate(rgb, layout)
    seg = segment_object(cal.plane, cal.layout, roi=roi, find_holes=find_holes)
    crop, alpha, wmm, hmm, ang, holes = deskew_crop(cal.plane, seg)
    q, warns = quality_checks(cal, seg, crop, alpha)
    wmm, hmm = wmm * print_scale, hmm * print_scale
    holes = [{**h, "d_mm": h["d_mm"] * print_scale} for h in holes]
    dbg = draw_debug(cal, seg, wmm, hmm, seg.holes)
    return Analysis(cal, seg, crop, alpha, wmm, hmm, ang, holes, q, warns, dbg)


def draw_debug(cal: Calibration, seg: Segment, wmm: float, hmm: float, holes: list, max_side: int = 900,
               margin_mm: float = 12.0):
    """Imagen de revisión: solo el objeto + un margen, con el contorno y los orificios dibujados."""
    img = cv2.cvtColor(cal.plane, cv2.COLOR_RGB2BGR).copy()
    H, W = img.shape[:2]
    hull = seg.hull.astype(np.int32)
    for poly in (seg.outline or [hull]):
        cv2.polylines(img, [np.round(poly).astype(np.int32)], True, (255, 90, 0), 5, cv2.LINE_AA)
    for h in holes:                                   # solo los orificios aceptados
        cv2.circle(img, (int(h["cx"]), int(h["cy"])), max(int(h["d_mm"] / 2 * PX_MM), 8) + 6, (0, 230, 255), 5, cv2.LINE_AA)
    m = int(margin_mm * PX_MM)
    x0, y0 = hull.min(0)
    x1, y1 = hull.max(0)
    img = img[max(0, y0 - m):min(H, y1 + m), max(0, x0 - m):min(W, x1 + m)]
    cv2.putText(img, f"{wmm:.1f} x {hmm:.1f} mm", (24, 80), cv2.FONT_HERSHEY_SIMPLEX, 2.4, (255, 90, 0), 6, cv2.LINE_AA)
    s = min(1.0, max_side / max(img.shape[:2]))
    return cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else img
