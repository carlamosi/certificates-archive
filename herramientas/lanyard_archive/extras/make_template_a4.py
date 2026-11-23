# -*- coding: utf-8 -*-
"""
make_template_a4.py - Genera plantilla_calibracion_A4_v3.pdf

Hoja A4 completa con 4 marcadores ArUco (DICT_4X4_50, IDs 0-3) de 20 mm a 10 mm de los bordes
(las impresoras no imprimen en los ~4 mm exteriores). Todo el dibujo es vectorial: cada celda del
marcador es un rectángulo exacto, sin interpolación de imagen.

Zona útil entre marcadores: 150 x 210 mm (cabe un A5/A6 completo).
Controles visuales independientes de la calibración: regla horizontal y vertical de 100 mm.
La geometría debe coincidir con LAYOUTS["a4"] en lanyard_core.py.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import cv2
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from lanyard_core import LAYOUTS

LAYOUT = LAYOUTS["a4"]
OUT = "plantilla_calibracion_A4_v3.pdf"
PAGE_H_MM = 297.0


def y_rl(y_mm: float) -> float:
    """mm medidos desde arriba -> puntos de reportlab (origen abajo)."""
    return (PAGE_H_MM - y_mm) * mm


def draw_marker(c, marker_id: int, x_mm: float, y_mm: float, size_mm: float):
    ar = cv2.aruco
    cells = ar.generateImageMarker(ar.getPredefinedDictionary(ar.DICT_4X4_50), marker_id, 6)   # 6x6 con borde
    cell = size_mm / 6.0
    c.setFillColorRGB(0, 0, 0)
    c.setStrokeColorRGB(0, 0, 0)
    for r in range(6):
        for k in range(6):
            if cells[r, k] == 0:                                   # celda negra
                c.rect((x_mm + k * cell) * mm, y_rl(y_mm + (r + 1) * cell), cell * mm, cell * mm,
                       stroke=0, fill=1)


def ruler_h(c, x_mm, y_mm, length=100):
    c.setLineWidth(0.3)
    c.line(x_mm * mm, y_rl(y_mm), (x_mm + length) * mm, y_rl(y_mm))
    for i in range(length + 1):
        h = 4.0 if i % 10 == 0 else (2.5 if i % 5 == 0 else 1.4)
        c.line((x_mm + i) * mm, y_rl(y_mm), (x_mm + i) * mm, y_rl(y_mm) - h * mm)
        if i % 10 == 0:
            c.setFont("Helvetica", 5.5)
            c.drawCentredString((x_mm + i) * mm, y_rl(y_mm) - 7.2 * mm, str(i))


def ruler_v(c, x_mm, y_mm, length=100):
    c.setLineWidth(0.3)
    c.line(x_mm * mm, y_rl(y_mm), x_mm * mm, y_rl(y_mm + length))
    for i in range(length + 1):
        w = 4.0 if i % 10 == 0 else (2.5 if i % 5 == 0 else 1.4)
        c.line(x_mm * mm, y_rl(y_mm + i), (x_mm + w) * mm, y_rl(y_mm + i))
        if i % 10 == 0:
            c.setFont("Helvetica", 5.5)
            c.drawString((x_mm + 5.0) * mm, y_rl(y_mm + i) - 1.8, str(i))


def main():
    c = canvas.Canvas(OUT, pagesize=A4)
    c.setTitle("Lanyard Archive - plantilla de calibración A4 v3")
    c.setAuthor("Lanyard Archive")
    for mid, (x, y) in LAYOUT.markers.items():
        draw_marker(c, mid, x, y, LAYOUT.marker_mm)

    c.setFillColorRGB(0.1, 0.12, 0.2)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(105 * mm, y_rl(17), "LANYARD ARCHIVE / CALIBRACIÓN A4")
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0.35, 0.38, 0.5)
    c.drawCentredString(105 * mm, y_rl(22), "Imprimir al 100 % · Desactivar «ajustar a página» · No plastificar")
    c.drawCentredString(105 * mm, y_rl(26), "Fotografía toda la hoja desde arriba, con los 4 marcadores nítidos")

    x, y, w, h = LAYOUT.zone_mm
    c.setStrokeColorRGB(0.6, 0.65, 0.75)
    c.setLineWidth(0.4)
    c.setDash(2, 2)
    c.rect(x * mm, y_rl(y + h), w * mm, h * mm, stroke=1, fill=0)
    c.setDash()
    c.setFont("Helvetica", 7)
    c.drawCentredString(105 * mm, y_rl(y - 2.5), "Zona de colocación: hasta 150 × 210 mm (A5 vertical)")

    c.setStrokeColorRGB(0, 0, 0)
    c.setFillColorRGB(0, 0, 0)
    ruler_h(c, 55, 275)                 # entre los marcadores inferiores
    c.setFont("Helvetica", 6)
    c.drawString(158 * mm, y_rl(275) - 0.8 * mm, "mm")
    ruler_v(c, 12, 85)                  # entre los marcadores laterales
    c.setFont("Helvetica", 6)
    c.drawString(12 * mm, y_rl(85) + 2.5 * mm, "mm")

    c.setFont("Helvetica", 5.5)
    c.setFillColorRGB(0.45, 0.48, 0.6)
    c.drawCentredString(105 * mm, y_rl(291), "ArUco DICT_4X4_50 · IDs 0-3 · marcador 20 mm · regla de 100 mm = control visual independiente")
    c.showPage()
    c.save()
    print("OK:", OUT)


if __name__ == "__main__":
    main()
