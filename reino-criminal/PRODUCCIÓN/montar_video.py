"""Monta el video final de Reino Criminal a partir de escenas.txt, la narración y la carpeta de medios.

Cada escena NNN busca en la carpeta de medios un archivo NNN.jpg / .png / .webp (imagen)
o NNN.mp4 / .mov / .webm (clip). Las imágenes llevan un zoom lento (Ken Burns), los clips se
recortan a la duración de la escena (sin su audio) y, si falta un archivo, se pone una
tarjeta provisional con el número de escena para poder previsualizar igual.

La duración de cada escena se reparte en proporción a sus palabras sobre la duración real
de la narración, así que el corte cae aproximadamente donde cambia la frase.

Uso (desde la carpeta PRODUCCIÓN):
    python montar_video.py --audio "narracion\\narracion.mp3"
    python montar_video.py --audio "narracion\\narracion.mp3" --desde 1 --hasta 30   (prueba corta)

Necesita ffmpeg: usa el del sistema o, si no está, el que trae moviepy (imageio-ffmpeg).
"""
import argparse, re, shutil, subprocess, sys, tempfile
from pathlib import Path

IMG = ('.jpg', '.jpeg', '.png', '.webp')
VID = ('.mp4', '.mov', '.webm', '.mkv', '.m4v')
W, H, FPS = 1920, 1080, 30
GRADO = "eq=contrast=1.08:saturation=1.12,colorbalance=rs=0.06:gs=0.02:bs=-0.07:rm=0.04:bm=-0.04,vignette=PI/5"


def ffmpeg_bin():
    exe = shutil.which('ffmpeg')
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit('No se encontró ffmpeg. Instalá moviepy (trae imageio-ffmpeg) o ffmpeg.')


def duracion(ff, ruta):
    out = subprocess.run([ff, '-i', str(ruta)], capture_output=True, text=True, errors='ignore').stderr
    m = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', out)
    if not m:
        sys.exit(f'No se pudo leer la duración de {ruta}')
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def leer_escenas(ruta):
    escenas = []
    for linea in Path(ruta).read_text(encoding='utf-8').splitlines():
        m = re.match(r'^(\d{3}) \| ~\d+ s \| NARRACIÓN: (.*)$', linea)
        if m:
            escenas.append({'n': int(m.group(1)), 'texto': m.group(2), 'palabras': len(m.group(2).split())})
    if not escenas:
        sys.exit(f'No se encontraron escenas en {ruta}')
    return escenas


def buscar_medio(carpeta, n):
    for ext in IMG + VID:
        for nombre in (f'{n:03d}{ext}', f'{n:03d}{ext.upper()}'):
            p = carpeta / nombre
            if p.exists():
                return p
    return None


def tarjeta(n, texto, destino):
    """Tarjeta provisional para escenas sin medio todavía."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None
    im = Image.new('RGB', (W, H), (14, 10, 6))
    d = ImageDraw.Draw(im)
    try:
        f1 = ImageFont.truetype('arial.ttf', 90); f2 = ImageFont.truetype('arial.ttf', 40)
    except OSError:
        try:
            f1 = ImageFont.truetype('DejaVuSans-Bold.ttf', 90); f2 = ImageFont.truetype('DejaVuSans.ttf', 40)
        except OSError:
            f1 = f2 = ImageFont.load_default()
    d.text((120, 380), f'ESCENA {n:03d} — FALTA EL MEDIO', fill=(255, 178, 56), font=f1)
    palabras, lineas, actual = texto.split(), [], ''
    for p in palabras:
        if len(actual) + len(p) > 70:
            lineas.append(actual); actual = ''
        actual += p + ' '
    lineas.append(actual)
    for i, l in enumerate(lineas[:4]):
        d.text((120, 540 + i * 60), l, fill=(243, 226, 195), font=f2)
    im.save(destino)
    return destino


def render_escena(ff, medio, segundos, salida, indice, grado):
    frames = max(1, round(segundos * FPS))
    filtro_grado = (',' + GRADO) if grado else ''
    if medio.suffix.lower() in VID:
        cmd = [ff, '-y', '-v', 'error', '-stream_loop', '-1', '-i', str(medio), '-t', f'{frames / FPS:.3f}', '-an',
               '-vf', f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1{filtro_grado}',
               '-frames:v', str(frames)]
    else:
        zmax = 1.10
        paso = (zmax - 1) / frames
        if indice % 2 == 0:   # acercar
            z = f"min(1+{paso:.6f}*on,{zmax})"
        else:                 # alejar
            z = f"max({zmax}-{paso:.6f}*on,1)"
        x = "iw/2-(iw/zoom/2)" if indice % 3 else "(iw-iw/zoom)*on/" + str(frames)
        cmd = [ff, '-y', '-v', 'error', '-loop', '1', '-i', str(medio),
               '-vf', f'scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase,crop={W * 2}:{H * 2},'
                      f"zoompan=z='{z}':x='{x}':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},setsar=1{filtro_grado}",
               '-frames:v', str(frames)]
    cmd += ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', str(salida)]
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--escenas', default='escenas.txt')
    ap.add_argument('--audio', required=True, help='narración (mp3/wav)')
    ap.add_argument('--medios', default='medios', help='carpeta con 001.jpg, 002.mp4, …')
    ap.add_argument('--salida', default='video_final.mp4')
    ap.add_argument('--desde', type=int, default=1)
    ap.add_argument('--hasta', type=int, default=9999)
    ap.add_argument('--sin-grado', action='store_true', help='no aplicar la corrección de color neo-noir')
    a = ap.parse_args()

    ff = ffmpeg_bin()
    escenas = leer_escenas(a.escenas)
    total_palabras = sum(e['palabras'] for e in escenas)
    dur_audio = duracion(ff, a.audio)
    carpeta = Path(a.medios)

    # tiempos de cada escena (proporcionales a las palabras, redondeados a fotogramas sin acumular error)
    acum = 0
    for e in escenas:
        ini = round(acum / total_palabras * dur_audio * FPS)
        acum += e['palabras']
        fin = round(acum / total_palabras * dur_audio * FPS)
        e['ini'], e['seg'] = ini / FPS, (fin - ini) / FPS
    sel = [e for e in escenas if a.desde <= e['n'] <= a.hasta]

    faltan = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        lista = []
        for i, e in enumerate(sel):
            medio = buscar_medio(carpeta, e['n'])
            if medio is None:
                faltan.append(e['n'])
                medio = tarjeta(e['n'], e['texto'], tmp / f"tarjeta_{e['n']:03d}.png")
                if medio is None:
                    sys.exit('Falta Pillow para crear las tarjetas provisionales (pip install pillow).')
            seg = tmp / f"seg_{e['n']:03d}.mp4"
            print(f"[{i + 1}/{len(sel)}] escena {e['n']:03d}  {e['seg']:.2f} s  ← {Path(medio).name}", flush=True)
            render_escena(ff, Path(medio), e['seg'], seg, e['n'], not a.sin_grado)
            lista.append(seg)
        (tmp / 'lista.txt').write_text(''.join(f"file '{p.as_posix()}'\n" for p in lista), encoding='utf-8')
        video = tmp / 'video.mp4'
        subprocess.run([ff, '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', str(tmp / 'lista.txt'), '-c', 'copy', str(video)], check=True)
        ini, fin = sel[0]['ini'], sel[-1]['ini'] + sel[-1]['seg']
        subprocess.run([ff, '-y', '-v', 'error', '-i', str(video), '-ss', f'{ini:.3f}', '-to', f'{fin:.3f}', '-i', a.audio,
                        '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', a.salida], check=True)

    print(f'\nListo: {a.salida}  ({len(sel)} escenas, {fin - ini:.1f} s)')
    if faltan:
        Path('faltan_medios.txt').write_text('\n'.join(f'{n:03d}' for n in faltan) + '\n', encoding='utf-8')
        print(f'Faltan {len(faltan)} medios (tarjeta provisional). Lista en faltan_medios.txt')


if __name__ == '__main__':
    main()
