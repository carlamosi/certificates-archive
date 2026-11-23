#!/usr/bin/env python3
"""
make_template.py — Plantilla de calibración A4 para fotografiar lanyards, pines y certificados.

Geometría (en mm, nominal):
  - Rectángulo de referencia de 150 x 210 mm, centrado en A4 (210 x 297).
  - Cruces de registro "+" en las cuatro esquinas de ese rectángulo (brazo 8 mm, grosor 0,5 mm).
  - Regla de 100 mm en el borde inferior, marcas cada 10 mm (largas cada 50 mm).
  - Cuadrado de referencia de 50 x 50 mm junto a la regla.
  - Cuadrícula de 10 mm en el interior (ayuda visual a la inclinación; no interfiere con la detección).

Salida:
  - template_calibracion_A4.pdf   (imprimir a 100 % / tamaño real, sin "ajustar a página")
  - calib_meta.json               (geometría nominal que usará el script de recorte)
"""
import json
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

PAGE_W, PAGE_H = A4                       # 595.27 x 841.89 pt  (210 x 297 mm)
REF_W, REF_H = 150 * mm, 210 * mm         # rectángulo de referencia nominal
MARGIN_X = (PAGE_W - REF_W) / 2           # 30 mm a cada lado
MARGIN_Y = (PAGE_H - REF_H) / 2           # 43.5 mm arriba y abajo
ARM = 8 * mm
LINE = 0.5
GRID = 10 * mm

x0, y0 = MARGIN_X, MARGIN_Y               # esquina inferior izquierda del rectángulo
x1, y1 = x0 + REF_W, y0 + REF_H

OUT_PDF = "template_calibracion_A4.pdf"
OUT_META = "calib_meta.json"


def cross(c, x, y):
    c.setLineWidth(LINE)
    c.line(x - ARM / 2, y, x + ARM / 2, y)
    c.line(x, y - ARM / 2, x, y + ARM / 2)


def draw():
    c = canvas.Canvas(OUT_PDF, pagesize=A4)
    c.setTitle("Plantilla de calibración 150x210 mm")
    c.setAuthor("lanyard_ingest")

    # Cuadrícula de 10 mm dentro del rectángulo de referencia (muy tenue)
    c.setStrokeColorRGB(0.85, 0.85, 0.85)
    c.setLineWidth(0.25)
    n_x, n_y = int(REF_W / GRID), int(REF_H / GRID)
    for i in range(1, n_x):
        c.line(x0 + i * GRID, y0, x0 + i * GRID, y1)
    for j in range(1, n_y):
        c.line(x0, y0 + j * GRID, x1, y0 + j * GRID)

    # Borde del rectángulo de referencia
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(LINE)
    c.rect(x0, y0, REF_W, REF_H, stroke=1, fill=0)

    # Cuatro cruces de registro en las esquinas exactas
    for (x, y) in [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]:
        cross(c, x, y)

    # Etiquetas de esquina (ayuda al operador, el script no las usa)
    c.setFont("Helvetica", 6)
    c.drawString(x0 + 2 * mm, y1 - 4 * mm, "ARRIBA-IZQ")
    c.drawRightString(x1 - 2 * mm, y1 - 4 * mm, "ARRIBA-DCHA")
    c.drawString(x0 + 2 * mm, y0 + 2 * mm, "ABAJO-IZQ")
    c.drawRightString(x1 - 2 * mm, y0 + 2 * mm, "ABAJO-DCHA")

    # Título y texto de instrucciones, fuera del área de trabajo
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 16 * mm, "Plantilla de calibración 150 x 210 mm")
    c.setFont("Helvetica", 8)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 21 * mm,
                        "Imprimir al 100 % (sin ajustar a página). Colocar el objeto dentro del rectángulo, sin tapar las cruces.")

    # Regla de 100 mm en el borde inferior, fuera del rectángulo
    ruler_y = 14 * mm
    ruler_x = x0
    c.setLineWidth(LINE)
    c.line(ruler_x, ruler_y, ruler_x + 100 * mm, ruler_y)
    for i in range(0, 101):
        xt = ruler_x + i * mm
        if i % 10 == 0:
            length = 3.5 * mm if i % 50 else 5 * mm
            c.line(xt, ruler_y, xt, ruler_y + length)
            if i % 10 == 0:
                c.setFont("Helvetica", 6)
                c.drawCentredString(xt, ruler_y - 3 * mm, str(i))
        else:
            c.line(xt, ruler_y, xt, ruler_y + 1.5 * mm)
    c.setFont("Helvetica", 7)
    c.drawString(ruler_x + 102 * mm, ruler_y, "regla 100 mm (mm)")

    # Cuadrado de referencia 50 x 50 mm, a la derecha de la regla
    sq_x = ruler_x + 115 * mm
    sq_y = ruler_y - 2 * mm
    c.rect(sq_x, sq_y, 50 * mm, 50 * mm, stroke=1, fill=0)
    c.setFont("Helvetica", 7)
    c.drawString(sq_x, sq_y + 52 * mm, "cuadrado 50 x 50 mm")

    c.showPage()
    c.save()


def write_meta():
    meta = {
        "version": 1,
        "page": "A4",
        "page_mm": [210, 297],
        "ref_rect_mm": [150, 210],
        "ref_rect_origin_mm": [round(MARGIN_X / mm, 3), round(MARGIN_Y / mm, 3)],
        "registration_crosses_mm": [[0, 0], [150, 0], [0, 210], [150, 210]],
        "ruler_mm": 100,
        "square_mm": 50,
        "print_instruction": "Imprimir a 100 % (sin ajustar a página). El script calibra la escala con las cruces.",
    }
    with open(OUT_META, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    draw()
    write_meta()
    print("OK:", OUT_PDF, OUT_META)
