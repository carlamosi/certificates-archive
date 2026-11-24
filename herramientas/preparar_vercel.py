"""Prepara la web completa (con datos, fotos y vídeos) y la sube al repositorio privado que publica Vercel.

Uso:  python herramientas/preparar_vercel.py            (prepara y sube: Vercel la publica sola)
      python herramientas/preparar_vercel.py --prueba   (solo prepara la carpeta, sin subir)

- Copia `web/` a `../certificates-archive-vercel/` (fuera del repositorio: lleva datos personales).
- Añade los vídeos de las charlas que estén en el ordenador (`archivo_local` de la base) a `video/`.
- Comprueba que existen todas las imágenes y vídeos que cita `data/archivo.json`.
- Se niega a subir un fichero de más de 95 MB (GitHub no acepta más de 100 MB por fichero).
- Sube la carpeta a github.com/carlamosi/certificates-archive-web (PRIVADO). Vercel está enlazado a ese
  repositorio y publica cada subida.
"""
import datetime, json, os, shutil, subprocess, sys

RAIZ = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True, check=True).stdout.strip()
PRINCIPAL = os.path.normpath(RAIZ.replace('\\', '/').split('/.claude/worktrees/')[0])   # en un worktree, la carpeta principal
WEB = os.path.join(PRINCIPAL, 'web')   # los datos, fotos y vídeos solo están en la carpeta principal
DESTINO = os.path.join(os.path.dirname(PRINCIPAL), 'certificates-archive-vercel')
REMOTO = 'https://github.com/carlamosi/certificates-archive-web.git'
MAX_FICHERO_MB = 95
NO_SUBIR = shutil.ignore_patterns('__pycache__', '*.pyc', 'sync.py', 'README.md')
VERCEL_JSON = {
    # el enlace es solo para Carla: que los buscadores no la indexen
    'headers': [{'source': '/(.*)', 'headers': [{'key': 'X-Robots-Tag', 'value': 'noindex, nofollow'}]}],
}


def rutas_citadas(nodo):
    """Rutas relativas a ficheros (img/…, video/…) que aparecen en archivo.json."""
    if isinstance(nodo, dict):
        for v in nodo.values():
            yield from rutas_citadas(v)
    elif isinstance(nodo, list):
        for v in nodo:
            yield from rutas_citadas(v)
    elif isinstance(nodo, str) and nodo.startswith(('img/', 'video/')):
        yield nodo


def videos_locales(datos):
    """(ruta en el ordenador, nombre) de los vídeos de charlas que no tienen URL."""
    for e in datos.get('eventos', []):
        for c in e.get('charlas', []):
            p = c.get('archivo_local') or ''
            if p and not c.get('url'):
                yield p, os.path.basename(p.replace('\\', '/'))


def ficheros(carpeta):
    for d, subs, fs in os.walk(carpeta):
        subs[:] = [s for s in subs if s not in ('.git', '.vercel')]
        for f in fs:
            yield os.path.join(d, f)


def git(*args):
    return subprocess.run(['git', *args], cwd=DESTINO, capture_output=True, text=True, check=True).stdout


def vaciar_sin_git():
    """Borra la copia anterior pero conserva su historial (.git) y el enlace con Vercel (.vercel)."""
    for n in os.listdir(DESTINO):
        if n not in ('.git', '.vercel'):
            p = os.path.join(DESTINO, n)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)


def main():
    prueba = '--prueba' in sys.argv
    datos_json = os.path.join(WEB, 'data', 'archivo.json')
    if not os.path.exists(datos_json):
        sys.exit('Falta web/data/archivo.json. Ejecuta antes: python herramientas/archivo_db/archivo.py exportar web/data/archivo.json')
    datos = json.load(open(datos_json, encoding='utf-8'))

    os.makedirs(DESTINO, exist_ok=True)
    vaciar_sin_git()
    shutil.copytree(WEB, DESTINO, ignore=NO_SUBIR, dirs_exist_ok=True)
    json.dump(VERCEL_JSON, open(os.path.join(DESTINO, 'vercel.json'), 'w', encoding='utf-8'), indent=2)
    open(os.path.join(DESTINO, '.gitignore'), 'w').write('.vercel\n.env*\n')   # el enlace y el token de Vercel no se suben

    avisos = []
    os.makedirs(os.path.join(DESTINO, 'video'), exist_ok=True)
    for origen, nombre in videos_locales(datos):
        final = os.path.join(DESTINO, 'video', nombre)
        if os.path.exists(final):
            continue
        if os.path.exists(origen):
            shutil.copy2(origen, final)
        else:
            avisos.append(f'vídeo no encontrado en el ordenador: {origen}')
    avisos += [f'falta {r}' for r in sorted({r for r in rutas_citadas(datos) if not os.path.exists(os.path.join(DESTINO, r))})]

    todos = list(ficheros(DESTINO))
    mb = sum(os.path.getsize(f) for f in todos) / 1e6
    print(f'Carpeta lista: {DESTINO}  ({len(todos)} ficheros, {mb:.1f} MB)')
    for a in avisos:
        print('  AVISO:', a)
    grandes = [(os.path.getsize(f) / 1e6, os.path.relpath(f, DESTINO)) for f in todos if os.path.getsize(f) > MAX_FICHERO_MB * 1e6]
    if grandes:
        print('  Demasiado grandes para GitHub: ' + ', '.join(f'{n} ({t:.0f} MB)' for t, n in grandes))
        sys.exit('Sube esos vídeos a YouTube como «no listado» y pon su enlace en la charla (campo url): la web ya los incrusta.')
    if prueba:
        return

    if not os.path.isdir(os.path.join(DESTINO, '.git')):
        git('init', '-b', 'main')
        git('remote', 'add', 'origin', REMOTO)
    git('add', '-A')
    if not git('status', '--porcelain').strip():
        print('Sin cambios: la web publicada ya está al día.')
        return
    git('commit', '-m', f'Web {datetime.date.today().isoformat()}')
    git('push', '-u', 'origin', 'main')
    print('Subida. Vercel la publicará en un minuto.')


if __name__ == '__main__':
    main()
