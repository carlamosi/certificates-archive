# Prompt de identidad de marca · Certificates Archive

> **Desactualizado (2026-11-23):** la paleta negra y amarilla de abajo ya no vale. La identidad vigente es [IDENTIDAD.md](IDENTIDAD.md): papel `#F7F4EE`, azul matasellos `#2F5BEA`, cristal y sellos. Adapta los prompts a esa paleta antes de usarlos.

> Para generadores de imagen (Midjourney, Ideogram, Imagen, DALL·E, Firefly, etc.). Los prompts están en inglés porque la mayoría de generadores responden mejor así; cada bloque tiene su instrucción en español para entenderlo.
>
> **Regla general:** los generadores escriben mal el texto. Genera siempre **sin texto** y añade el nombre "Certificates Archive" en Figma, Inkscape o similar con la tipografía Open Sauce.

---

## 0. Ficha de marca (contexto para cualquier prompt)

**Qué es:** archivo personal de eventos, premios, lanyards y viajes. Parte museo, parte cuaderno de viajes, parte herramienta de precisión.
**Atributos:** preciso, sobrio, cálido, íntimo, de museo contemporáneo.
**Paleta:** negro casi puro `#0A0A0B`, blanco cálido `#F5F3EE`, amarillo señal `#FFD23F`. Nada de morado, azul eléctrico ni gradientes arcoíris.
**Tipografía:** Open Sauce One.
**Motivo visual central:** el **orificio de la anilla** de un lanyard: un círculo recortado en una etiqueta negra. Es la firma de la marca.

**Lo que NO debe aparecer en ninguna imagen:**
- Logotipos de terceros (Xartec, UPC, Generalitat, IRIS, ni ningún patrocinador de los lanyards reales).
- Personas reconocibles. Si hay personas, que sean siluetas o manos sin rostro.
- Texto legible generado por la IA.
- Morado, rosa o gradientes cónicos de "tecnología".
- Sellos, medallas o iconos de trofeo cliché.

---

## 1. Símbolo (marca)

**Concepto:** una etiqueta rectangular negra con las esquinas redondeadas (proporción 1:1.4, como un lanyard) y un orificio circular en la parte superior. Un único punto amarillo en el centro del orificio, como un foco.

**Prompt (inglés):**
```
Minimal logo mark, flat vector style, a single black rounded rectangle tag with soft corners,
a perfectly circular hole punched near the top center, a small solid yellow dot exactly in the
center of the hole, pure black background, no text, no shadows, no gradients, no 3D, centered
composition, generous negative space, sharp geometric edges, contemporary museum identity,
simple enough to work at 16 pixels, vector-clean --style raw --ar 1:1 --no text, gradient, shadow, 3d, bevel, glow, emoji, badge
```

**Variantes a generar (una a la vez):**
- Símbolo en negro sobre blanco cálido.
- Símbolo en blanco sobre negro.
- Símbolo con el punto amarillo sobre fondo negro (versión principal).

**Criterio para elegir:** que se lea en 16 px, que el orificio sea el elemento más reconocible, y que no parezca un icono de "etiqueta de precio" o de "tarjeta de crédito".

---

## 2. Icono de aplicación / favicon

```
App icon, square, pure black background with a subtle warm radial glow in the upper right corner,
a single black tag shape with a circular hole at the top and a small yellow dot in the hole,
flat vector illustration, no text, minimal, premium, iOS-style rounded square silhouette, crisp
edges, lots of breathing room --ar 1:1 --no text, gradient rainbow, purple, blue, glow overload, 3d, skeuomorphic, emoji
```

---

## 3. Cabecera de redes y portada

```
Editorial museum poster composition, near-black background (#0A0A0B), a single diagonal row of
tags hanging from a thin metal rail, each tag black with a round hole at the top, one tag
slightly lit with a warm yellow accent (#FFD23F), soft directional light from upper left, deep
shadow falling to the right, large empty negative space on the right third for typography, fine
film grain at 3 percent, photographic realism, 35mm lens look, calm and precise, no people, no
text --ar 16:9 --style raw --no text, logos, people, faces, purple, blue, neon, rainbow, glow, clutter, stock photo
```

Después, sobre el espacio vacío, escribe en Open Sauce One Black, mayúsculas de 11 px con tracking 0.14em: **CERTIFICATES ARCHIVE**, y debajo en itálica 300: *lanyards, eventos y viajes*.

---

## 4. Lanyard de producto (mockup)

Imagen fotográfica para la web y para presentaciones. Usar solo como ambientación, no como dato.

```
Photorealistic product photograph of a black woven lanyard tag hanging from a brushed steel
clip, the tag is matte black with a small clean circular hole near the top edge, a single thin
yellow line printed along the lower edge, shot on a warm off-white paper background, soft
window light from the left, gentle shadow on the paper, shallow depth of field, Hasselblad look,
premium editorial still life, no text, no logo, no person --ar 4:5 --style raw --no text, logo, brand names, people, hands, purple, neon, cartoon
```

---

## 5. Textura de pared de museo

Fondo para la web (muy sutil, con opacidad baja en la UI).

```
Seamless texture of a warm off-white museum wall with an almost imperceptible plaster
variation, very low contrast, soft even light, no objects, no shadows, flat frontal view,
tileable --ar 1:1 --tile --style raw --no shadow, object, text, color cast, pattern, grunge
```

---

## 6. Ilustración de viaje (mapa, sin marcas)

Para la capa de viajes del mapa, que sea abstracta y no copie el estilo de ninguna app.

```
Abstract minimal map motif, black background, a few thin white arcs curving between small
yellow dots like flight paths, no country outlines, no labels, no text, precise linework, 1px
strokes, airy composition, editorial --ar 16:9 --no text, labels, countries, logos, gradients,
rainbow, 3d --style raw
```

---

## 7. Papelería: tarjeta de visita o etiqueta de cartela (plantilla)

```
Flat top-down mockup of a black matte business card with a single circular hole cut into the
top edge, a small yellow dot visible through the hole, on a warm off-white linen surface, soft
natural light, no text, no logo, no person --ar 3:2 --style raw --no text, logo, gradient, hand, face
```

---

## 8. Consistencia entre imágenes

- Fija una **semilla** (`--seed`) y usa siempre la misma **imagen de estilo** como referencia (`--sref` o similar) con el símbolo de la sección 1.
- Mantén la misma **paleta**: si la imagen sale con un tono morado o azulado, regenera; no lo corrijas en Photoshop solo con tono.
- Mantén siempre el **ángulo de luz desde arriba-izquierda**.
- Un solo amarillo por imagen.

---

## 9. Revisión antes de usar una imagen

- [ ] Sin texto ilegible ni letras inventadas.
- [ ] Sin logotipos de terceros ni personas identificables.
- [ ] Paleta dentro de `#0A0A0B`, `#F5F3EE`, `#FFD23F`.
- [ ] El símbolo funciona en 16 px en negro y en blanco.
- [ ] Coherente con la luz de la sección 8.
- [ ] Se puede escribir sobre ella sin pelearse con el fondo.
