"""Genera los iconos de la PWA y las imágenes de arranque de iOS en web/img/app/.
Dibuja el sello de web/img/logo.svg con Pillow (no hace falta rasterizador SVG).
Uso: python herramientas/generar_iconos_pwa.py   (si cambia el logo, hay que retocar sello() a la par)"""
import os
from PIL import Image, ImageDraw, ImageFont

SALIDA = os.path.join(os.path.dirname(__file__), '..', 'web', 'img', 'app')
PAPEL, OSCURO = '#F7F4EE', '#121316'   # tokens --paper de web/style.css (claro y oscuro)
TINTA, TINTA_OSCURO = (27, 26, 23), (242, 239, 232)
S = 16  # aumento al dibujar el sello (64 unidades -> 1024 px)


def sello():
    """El sello del logo a 64*S px, con los orificios transparentes."""
    n = 64 * S
    degradado = Image.new('RGBA', (n, n))
    d = ImageDraw.Draw(degradado)
    for y in range(4 * S, 60 * S):
        t = (y - 4 * S) / (56 * S)
        d.line([(4 * S, y), (60 * S, y)], fill=tuple(round(a + (b - a) * t) for a, b in zip((0x4A, 0x72, 0xF2), (0x2F, 0x5B, 0xEA))) + (255,))
    # el degradado solo en el cuadrado 4..60
    capa = Image.new('RGBA', (n, n))
    capa.alpha_composite(degradado)
    trazos = Image.new('RGBA', (n, n))
    t = ImageDraw.Draw(trazos)
    t.rounded_rectangle([11 * S, 11 * S, 53 * S, 53 * S], radius=4 * S, outline=(255, 255, 255, 153), width=2 * S)
    capa.alpha_composite(trazos)
    # onda: dos curvas cúbicas de logo.svg (M18 44 c4-4 8-4 12 0 s8 4 12 0)
    onda = Image.new('L', (n, n))   # trazo opaco en una máscara; la transparencia se aplica después
    o = ImageDraw.Draw(onda)
    pts = []
    for p0, p1, p2, p3 in [((18, 44), (22, 40), (26, 40), (30, 44)), ((30, 44), (34, 48), (38, 48), (42, 44))]:
        for i in range(61):
            u = i / 60
            pts.append(tuple(((1 - u) ** 3 * a + 3 * (1 - u) ** 2 * u * b + 3 * (1 - u) * u ** 2 * c + u ** 3 * e) * S for a, b, c, e in zip(p0, p1, p2, p3)))
    o.line(pts, fill=255, width=round(2.4 * S), joint='curve')
    for x, y in (pts[0], pts[-1]):
        o.ellipse([x - 1.2 * S, y - 1.2 * S, x + 1.2 * S, y + 1.2 * S], fill=255)
    capa.alpha_composite(Image.merge('RGBA', (*(Image.new('L', (n, n), 255),) * 3, onda.point(lambda v: v * 217 // 255))))
    # orificios: perímetro cada 7 unidades y el del cordón
    mascara = Image.new('L', (n, n), 255)
    m = ImageDraw.Draw(mascara)
    for k in range(4, 61, 7):
        for x, y in ((k, 4), (k, 60), (4, k), (60, k)):
            m.ellipse([(x - 2.4) * S, (y - 2.4) * S, (x + 2.4) * S, (y + 2.4) * S], fill=0)
    m.ellipse([(32 - 4.5) * S, (19 - 4.5) * S, (32 + 4.5) * S, (19 + 4.5) * S], fill=0)
    capa.putalpha(Image.composite(capa.getchannel('A'), Image.new('L', (n, n), 0), mascara))
    return capa


def lienzo(lado, fondo, fraccion, alto=None, desplazar=0):
    """Imagen lado×alto con el sello centrado (ocupa `fraccion` del lado menor)."""
    alto = alto or lado
    img = Image.new('RGBA', (lado, alto), fondo) if fondo else Image.new('RGBA', (lado, alto), (0, 0, 0, 0))
    t = round(min(lado, alto) * fraccion)
    s = SELLO.resize((t, t), Image.LANCZOS)
    img.alpha_composite(s, ((lado - t) // 2, (alto - t) // 2 + desplazar))
    return img


def fuente(px, negrita=False):
    for f in ('segoeuib.ttf' if negrita else 'segoeui.ttf', 'arial.ttf', 'DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(f, px)
        except OSError:
            pass
    return ImageFont.load_default(px)


def arranque(fondo, tinta):
    """Imagen de arranque iPhone 12 mini (375×812 @3x = 1125×2436): sello y nombre."""
    w, h = 1125, 2436
    img = lienzo(w, fondo, 0.34, h, desplazar=-80)
    d = ImageDraw.Draw(img)
    texto = 'Certificates Archive'
    f = fuente(66)
    ancho = d.textlength(texto, font=f)
    d.text(((w - ancho) / 2, h // 2 + 330), texto, font=f, fill=tinta)
    return img.convert('RGB')


if __name__ == '__main__':
    os.makedirs(SALIDA, exist_ok=True)
    SELLO = sello()
    guardar = lambda im, nombre: im.save(os.path.join(SALIDA, nombre), optimize=True)
    guardar(lienzo(32, None, 1), 'favicon-32.png')
    for lado, nombre in ((180, 'apple-touch-icon.png'), (192, 'icon-192.png'), (512, 'icon-512.png')):
        guardar(lienzo(lado, PAPEL, 0.62).convert('RGB'), nombre)   # sin transparencia
    guardar(lienzo(512, PAPEL, 0.5).convert('RGB'), 'icon-512-maskable.png')   # el sello cabe en la zona segura (80 %)
    guardar(arranque(PAPEL, TINTA), 'arranque-claro.png')
    guardar(arranque(OSCURO, TINTA_OSCURO), 'arranque-oscuro.png')
    print('Iconos en', os.path.normpath(SALIDA), '->', ', '.join(sorted(os.listdir(SALIDA))))
