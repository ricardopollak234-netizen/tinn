"""Agrega música de fondo a un video ya montado, sin volver a renderizar la imagen.

- Cada tema suena en su tramo (los cortes se pasan en segundos) y se encadena con un
  fundido cruzado de 4 s. Si un tema es más corto que su tramo, se repite.
- La música se nivela a un volumen bajo y además se "agacha" sola cuando habla la voz
  (sidechain), para que la narración siempre se entienda.
- El audio final queda en -14 LUFS, el nivel que usa YouTube.

Uso:
    python musica_fondo.py --video video.mp4 --narracion narracion/narracion.mp3 \
        --musica "musica/Tema 1.mp3" "musica/Tema 2.mp3" --cortes 300 --salida video_con_musica.mp4

Sin --cortes, los temas se reparten en partes iguales.
"""
import argparse, re, shutil, subprocess, sys

def ffmpeg_bin():
    exe = shutil.which('ffmpeg')
    if exe: return exe
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit('No se encontró ffmpeg. Instalá moviepy (trae imageio-ffmpeg) o ffmpeg.')

def duracion(ff, ruta):
    out = subprocess.run([ff, '-i', ruta], capture_output=True, text=True, errors='ignore').stderr
    h, m, s = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', out).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--video', required=True)
    ap.add_argument('--narracion', required=True)
    ap.add_argument('--musica', nargs='+', required=True, help='temas en orden')
    ap.add_argument('--cortes', nargs='*', type=float, default=None, help='segundos donde cambia de tema')
    ap.add_argument('--nivel', type=float, default=-27.0, help='volumen de la música en LUFS (más negativo = más bajo)')
    ap.add_argument('--salida', default='video_con_musica.mp4')
    a = ap.parse_args()

    ff = ffmpeg_bin()
    total = duracion(ff, a.narracion)
    n = len(a.musica)
    cortes = a.cortes if a.cortes else [total * i / n for i in range(1, n)]
    if len(cortes) != n - 1:
        sys.exit(f'Con {n} temas hacen falta {n - 1} cortes.')
    limites = [0.0] + list(cortes) + [total]
    XF = 4.0

    cmd = [ff, '-y', '-v', 'error', '-i', a.video, '-i', a.narracion]
    for m in a.musica:
        cmd += ['-stream_loop', '-1', '-i', m]
    f = []
    for i in range(n):
        d = limites[i + 1] - limites[i] + (XF if i < n - 1 else 0)
        f.append(f"[{i + 2}:a]atrim=0:{d:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo,"
                 f"loudnorm=I={a.nivel}:TP=-8:LRA=11[m{i}]")
    prev = 'm0'
    for i in range(1, n):
        f.append(f"[{prev}][m{i}]acrossfade=d={XF}:c1=tri:c2=tri[x{i}]"); prev = f'x{i}'
    f.append(f"[{prev}]afade=t=in:d=3,afade=t=out:st={total - 6:.3f}:d=6[cama]")
    f.append("[1:a]aformat=sample_rates=48000:channel_layouts=stereo,loudnorm=I=-16:TP=-2:LRA=11,asplit=2[voz][voz_sc]")
    f.append("[cama][voz_sc]sidechaincompress=threshold=0.03:ratio=4:attack=80:release=900:makeup=1[cama_d]")
    f.append("[voz][cama_d]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[aud]")
    cmd += ['-filter_complex', ';'.join(f), '-map', '0:v', '-map', '[aud]', '-c:v', 'copy',
            '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', a.salida]
    subprocess.run(cmd, check=True)
    print(f'Listo: {a.salida}')

if __name__ == '__main__':
    main()
