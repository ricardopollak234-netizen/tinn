#!/usr/bin/env python3
"""Monta el video final a partir de las escenas, la voz y la música.

Entradas (todas dentro de la carpeta del video, p. ej. familia-stauffenberg/):
  tiempos_escenas.csv   escena;inicio_s;fin_s;duracion_s;narracion  (sale de align)
  medios/               001.jpg / 001.png / 001.mp4 … (una por escena; si falta, se usa
                        el medio de una escena anterior indicada en reutilizar.csv, y si
                        tampoco hay, una tarjeta de "FALTA IMAGEN" para el borrador)
  narracion/narracion_completa.mp3
  musica.csv            inicio_s;archivo;  (pistas de fondo por bloque, en orden)

Uso:
  python3 generar_video.py CARPETA_VIDEO [--borrador] [--desde N --hasta M]

--borrador renderiza a 960x540 y más rápido, para revisar el montaje.
Requiere ffmpeg y Pillow.
"""
import argparse, csv, os, subprocess, sys, math, random, shutil, textwrap
from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageEnhance

FPS = 30
IMG_EXT = ('.jpg', '.jpeg', '.png', '.webp', '.tif', '.tiff')
VID_EXT = ('.mp4', '.mov', '.webm', '.mkv', '.m4v')

# Tono del canal: casi blanco y negro, sepia suave, contraste, viñeta y grano.
def grade(w):
    return (f"eq=saturation=0.30:contrast=1.10:brightness=-0.02,"
            f"colorchannelmixer=rr=1.05:gg=0.98:bb=0.86,"
            f"vignette=PI/4.5,noise=alls={6 if w < 1900 else 9}:allf=t,format=yuv420p")

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-3000:]); raise SystemExit(f'ffmpeg falló: {" ".join(cmd[:6])}…')

def canvas_16x9(src, W, H, out):
    """Encaja la imagen en 16:9: si casi lo es, recorta; si no, fondo desenfocado."""
    im = Image.open(src).convert('RGB')
    cw, ch = W * 2, H * 2  # margen para el movimiento
    r = im.width / im.height
    if abs(r - 16 / 9) < 0.25:
        s = max(cw / im.width, ch / im.height)
        im2 = im.resize((max(cw, round(im.width * s)), max(ch, round(im.height * s))), Image.LANCZOS)
        x = (im2.width - cw) // 2; y = (im2.height - ch) // 2
        im2.crop((x, y, x + cw, y + ch)).save(out, quality=92)
        return
    s = max(cw / im.width, ch / im.height)
    bg = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x = (bg.width - cw) // 2; y = (bg.height - ch) // 2
    bg = bg.crop((x, y, x + cw, y + ch)).filter(ImageFilter.GaussianBlur(40))
    bg = ImageEnhance.Brightness(bg).enhance(0.45)
    s2 = min(cw * 0.92 / im.width, ch * 0.92 / im.height)
    fg = im.resize((round(im.width * s2), round(im.height * s2)), Image.LANCZOS)
    bg.paste(fg, ((cw - fg.width) // 2, (ch - fg.height) // 2))
    bg.save(out, quality=92)

def placeholder(n, texto, W, H, out):
    im = Image.new('RGB', (W * 2, H * 2), (18, 16, 14))
    d = ImageDraw.Draw(im)
    try:
        f1 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', W // 18)
        f2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', W // 40)
    except OSError:
        f1 = f2 = ImageFont.load_default()
    d.text((W // 6, H // 2), f'ESCENA {n} — FALTA IMAGEN', fill=(200, 60, 50), font=f1)
    y = H // 2 + W // 12
    for line in textwrap.wrap(texto, 70)[:6]:
        d.text((W // 6, y), line, fill=(190, 180, 160), font=f2); y += W // 30
    im.save(out, quality=90)

MOVES = ['in', 'out', 'right', 'left', 'in_top', 'out']

def seg_image(img, dur, W, H, move, out):
    frames = max(2, round(dur * FPS))
    z0, z1 = (1.0, 1.12)
    if move == 'out': z0, z1 = 1.12, 1.0
    zexpr = f"{z0}+({z1}-{z0})*on/{frames}"
    if move in ('in', 'out'):
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif move == 'in_top':
        x, y = "iw/2-(iw/zoom/2)", "ih/4-(ih/zoom/4)"
    elif move == 'right':
        zexpr = "1.10"; x, y = f"(iw-iw/zoom)*on/{frames}", "ih/2-(ih/zoom/2)"
    else:
        zexpr = "1.10"; x, y = f"(iw-iw/zoom)*(1-on/{frames})", "ih/2-(ih/zoom/2)"
    vf = (f"zoompan=z='{zexpr}':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS},"
          f"{grade(W)}")
    run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-i', img, '-vf', vf, '-frames:v', str(frames),
         '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-r', str(FPS), '-an', out])

def seg_video(src, dur, W, H, out):
    frames = max(2, round(dur * FPS))
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},{grade(W)}")
    run(['ffmpeg', '-v', 'error', '-y', '-stream_loop', '-1', '-i', src, '-vf', vf,
         '-frames:v', str(frames), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-an', out])

def find_media(d, n):
    for e in IMG_EXT + VID_EXT:
        p = os.path.join(d, f'{n}{e}')
        if os.path.exists(p): return p
    return None

def build_music(base, plan, total, out):
    """Une las pistas por bloque (en bucle si hace falta) con fundidos de 3 s."""
    parts = []
    tmp = os.path.join(base, '_tmp_musica'); os.makedirs(tmp, exist_ok=True)
    for i, (start, f) in enumerate(plan):
        end = plan[i + 1][0] if i + 1 < len(plan) else total
        dur = end - start + (3 if i + 1 < len(plan) else 0)
        p = os.path.join(tmp, f'm{i:02d}.wav')
        run(['ffmpeg', '-v', 'error', '-y', '-stream_loop', '-1', '-i', f, '-t', f'{dur:.2f}',
             '-af', f'loudnorm=I=-16:TP=-2,afade=t=in:d=2,afade=t=out:st={max(0, dur - 3):.2f}:d=3',
             '-ar', '44100', '-ac', '2', p])
        parts.append(p)
    # superponer cada bloque en su minuto
    inputs = []; filt = []
    for i, p in enumerate(parts):
        inputs += ['-i', p]
        filt.append(f'[{i}]adelay={int(plan[i][0] * 1000)}|{int(plan[i][0] * 1000)}[a{i}]')
    filt.append(''.join(f'[a{i}]' for i in range(len(parts))) + f'amix=inputs={len(parts)}:normalize=0,atrim=0:{total:.2f}[m]')
    run(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(filt), '-map', '[m]', out])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('carpeta'); ap.add_argument('--borrador', action='store_true')
    ap.add_argument('--desde', type=int, default=1); ap.add_argument('--hasta', type=int, default=10**6)
    ap.add_argument('--salida')
    a = ap.parse_args()
    base = os.path.abspath(a.carpeta)
    W, H = (960, 540) if a.borrador else (1920, 1080)
    rows = list(csv.reader(open(os.path.join(base, 'tiempos_escenas.csv'), encoding='utf-8-sig'), delimiter=';'))[1:]
    rows = [r for r in rows if a.desde <= int(r[0]) <= a.hasta]
    reuse = {}
    rp = os.path.join(base, 'reutilizar.csv')
    if os.path.exists(rp):
        for r in csv.reader(open(rp, encoding='utf-8-sig'), delimiter=';'):
            if r and r[0].isdigit(): reuse[r[0].zfill(3)] = r[1].zfill(3)
    medios = os.path.join(base, 'medios')
    tmp = os.path.join(base, '_tmp_segmentos'); os.makedirs(tmp, exist_ok=True)
    lista = []; faltan = []
    random.seed(7)
    for i, r in enumerate(rows):
        n, t0, t1 = r[0], float(r[1]), float(r[2])
        dur = t1 - t0
        src = find_media(medios, n) or (find_media(medios, reuse[n]) if n in reuse else None)
        seg = os.path.join(tmp, f'{n}.mp4')
        if src and src.lower().endswith(VID_EXT):
            seg_video(src, dur, W, H, seg)
        else:
            img = os.path.join(tmp, f'{n}_canvas.jpg')
            if src: canvas_16x9(src, W, H, img)
            else: placeholder(n, r[4], W, H, img); faltan.append(n)
            seg_image(img, dur, W, H, MOVES[i % len(MOVES)] if src else 'in', seg)
        lista.append(seg)
        print(f'{n} ({dur:.1f} s) {"FALTA" if not src else os.path.basename(src)}', flush=True)
    with open(os.path.join(tmp, 'lista.txt'), 'w') as f:
        for s in lista: f.write(f"file '{s}'\n")
    video = os.path.join(tmp, 'video_mudo.mp4')
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', os.path.join(tmp, 'lista.txt'), '-c', 'copy', video])
    t_ini = float(rows[0][1]); total = float(rows[-1][2]) - t_ini
    voz = os.path.join(base, 'narracion', 'narracion_completa.mp3')
    plan = []
    mp = os.path.join(base, 'musica.csv')
    for r in csv.reader(open(mp, encoding='utf-8-sig'), delimiter=';'):
        if r and r[0][:1].isdigit():
            s = float(r[0]) - t_ini
            plan.append((max(0.0, s), os.path.join(base, r[1])))
    # quedarse con el bloque vigente al inicio del tramo y los que empiezan dentro de él
    plan = [p for j, p in enumerate(plan) if p[0] < total and (j + 1 == len(plan) or plan[j + 1][0] > 0)]
    musica = os.path.join(tmp, 'musica.wav')
    build_music(base, plan, total, musica)
    salida = a.salida or os.path.join(base, 'video_borrador.mp4' if a.borrador else 'video_final.mp4')
    # Voz al frente; música 18 dB por debajo y que además baja cuando habla el narrador.
    fc = (f"[1:a]atrim={t_ini:.2f}:{t_ini + total:.2f},asetpts=PTS-STARTPTS,loudnorm=I=-16:TP=-1.5,asplit=2[v][vsc];"
          f"[2:a]volume=-18dB[mus];[mus][vsc]sidechaincompress=threshold=0.03:ratio=4:attack=30:release=600[md];"
          f"[v][md]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    run(['ffmpeg', '-v', 'error', '-y', '-i', video, '-i', voz, '-i', musica, '-filter_complex', fc,
         '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', salida])
    print(f'\nLISTO: {salida}')
    print(f'Escenas sin imagen ({len(faltan)}): {" ".join(faltan) if faltan else "ninguna"}')

if __name__ == '__main__':
    main()
