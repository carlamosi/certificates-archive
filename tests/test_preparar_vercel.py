"""El nombre del vídeo para la web debe coincidir con el que busca web/intervenciones.js (srcDe)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'herramientas'))
from preparar_vercel import videos_locales

datos = {'eventos': [{'charlas': [
    {'archivo_local': r'C:\ruta\IMG_0532.MOV', 'url': ''},          # Windows, mayúsculas
    {'archivo_local': '/ruta/charla.final.mov', 'url': ''},           # varios puntos
    {'archivo_local': r'C:\ruta\otra.mp4', 'url': 'https://youtu.be/abcdefghijk'},   # con URL: no se convierte
    {'archivo_local': '', 'url': ''},
]}]}
assert list(videos_locales(datos)) == [(r'C:\ruta\IMG_0532.MOV', 'IMG_0532.mp4'), ('/ruta/charla.final.mov', 'charla.final.mp4')]
print('   test_preparar_vercel: OK')
