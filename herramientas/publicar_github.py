"""Publica el código del archivo en GitHub sin datos de otras personas.

Uso:  python herramientas/publicar_github.py            (publica la rama actual)
      python herramientas/publicar_github.py --prueba   (prepara la copia y la revisa, sin subir)

- Copia lo que hay en git (HEAD) a una carpeta espejo fuera del proyecto
  (`../certificates-archive-publico`), con su propio historial público.
- Cambia los nombres reales por alias según `datos/anonimizar.txt`
  (una línea por persona: `Nombre Real = Persona A`). Ese fichero no va a git.
- Se niega a subir si queda algún nombre de `web/data/archivo.json` (personas)
  o de `datos/anonimizar.txt` en los ficheros de texto.
"""
import io, os, subprocess, sys, tarfile, json, datetime, shutil, unicodedata

RAIZ = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True, check=True).stdout.strip()
REMOTO = 'https://github.com/carlamosi/certificates-archive.git'
PRINCIPAL = os.path.normpath(RAIZ.replace('\\', '/').split('/.claude/worktrees/')[0])   # en un worktree, la carpeta principal
ESPEJO = os.path.join(os.path.dirname(PRINCIPAL), 'certificates-archive-publico')
BINARIOS = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.pdf', '.xlsx', '.sqlite', '.woff2', '.ico', '.heif', '.heic', '.zip')


def git(*args, cwd):
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


def alias():
    p = os.path.join(PRINCIPAL, 'datos', 'anonimizar.txt')   # privado: vive solo en la carpeta principal
    pares = []
    for linea in open(p, encoding='utf-8'):
        if '=' in linea and not linea.strip().startswith('#'):
            real, falso = (x.strip() for x in linea.split('=', 1))
            pares.append((real, falso))
            # también la clave normalizada de la base («persona d») y su versión pegada («personad»)
            pares.append((norma(real), norma(falso)))
            pares.append((norma(real).replace(' ', ''), norma(falso).replace(' ', '')))
    return pares


def norma(t):
    return unicodedata.normalize('NFD', t).encode('ascii', 'ignore').decode().lower()


def personas_de_la_base():
    """Nombres, claves normalizadas e Instagram de las personas de la base: nada de esto puede salir."""
    for base in (RAIZ, PRINCIPAL):
        p = os.path.join(base, 'web', 'data', 'archivo.json')
        if os.path.exists(p):
            gente = json.load(open(p, encoding='utf-8')).get('personas', [])
            vetos = [x.get('nombre', '') for x in gente] + [norma(x.get('nombre', '')) for x in gente] + [x.get('instagram') or '' for x in gente]
            return [v for v in vetos if len(v) > 4]
    return []


def main():
    prueba = '--prueba' in sys.argv
    pares = alias()
    if not os.path.isdir(os.path.join(ESPEJO, '.git')):
        os.makedirs(ESPEJO, exist_ok=True)
        git('init', '-b', 'main', cwd=ESPEJO)
        git('remote', 'add', 'origin', REMOTO, cwd=ESPEJO)
    # vacía el espejo (menos .git) y vuelca HEAD
    for nombre in os.listdir(ESPEJO):
        if nombre != '.git':
            ruta = os.path.join(ESPEJO, nombre)
            shutil.rmtree(ruta) if os.path.isdir(ruta) else os.remove(ruta)
    tar = subprocess.run(['git', 'archive', 'HEAD'], cwd=RAIZ, capture_output=True, check=True).stdout
    tarfile.open(fileobj=io.BytesIO(tar)).extractall(ESPEJO, filter='data')
    # anonimiza y revisa
    vetados = sorted({r for r, _ in pares} | set(personas_de_la_base()), key=len, reverse=True)
    restos = []
    for carpeta, dirs, ficheros in os.walk(ESPEJO):
        dirs[:] = [d for d in dirs if d != '.git']
        for f in ficheros:
            ruta = os.path.join(carpeta, f)
            if f.lower().endswith(BINARIOS):
                continue
            try:
                texto = open(ruta, encoding='utf-8').read()
            except UnicodeDecodeError:
                continue
            nuevo = texto
            for real, falso in pares:
                nuevo = nuevo.replace(real, falso)
            if nuevo != texto:
                open(ruta, 'w', encoding='utf-8', newline='').write(nuevo)
            restos += [(os.path.relpath(ruta, ESPEJO), n) for n in vetados if n in nuevo]
    if restos:
        print('NO SE PUBLICA: quedan nombres de personas:')
        for ruta, n in restos:
            print(f'  {ruta}: {n}')
        print('Añádelos a datos/anonimizar.txt y vuelve a ejecutar.')
        sys.exit(1)
    git('add', '-A', cwd=ESPEJO)
    if not git('status', '--porcelain', cwd=ESPEJO).strip():
        print('Nada nuevo que publicar.')
        return
    if prueba:
        print(f'Prueba correcta: copia lista en {ESPEJO}, sin nombres. No se ha subido nada.')
        return
    origen = git('log', '-1', '--format=%h %s', cwd=RAIZ).strip()
    git('commit', '-m', f'Publicación {datetime.date.today():%Y-%m-%d} (desde {origen})', cwd=ESPEJO)
    subprocess.run(['git', 'push', '-u', 'origin', 'main'], cwd=ESPEJO, check=True)
    print('Publicado en', REMOTO.removesuffix('.git'))


if __name__ == '__main__':
    main()
