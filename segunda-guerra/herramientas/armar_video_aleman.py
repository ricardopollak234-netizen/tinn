#!/usr/bin/env python3
"""Arma la versión en alemán de un video ya terminado en español.

No hacen falta los medios originales: cada escena se toma del video final en español y se
acelera o se frena hasta durar lo mismo que su frase en alemán. Las escenas con texto en
pantalla (gráficos, mapas, tarjetas) se reemplazan por su versión alemana de graficos/.

Entradas en CARPETA_DE (p. ej. familia-stauffenberg-de/):
  escenas_de.csv        escena;texto_es;texto_de  (una fila por escena del video en español)
  narracion/            la voz en alemán: teil_01.mp3 … teil_NN.mp3 (una por cada teil_NN.txt,
                        es lo más preciso) o un solo narracion_completa.mp3
  graficos/NNN.png      gráficos con texto en alemán (herramientas/graficos_stauffenberg_de.py)
Entradas en CARPETA_ES (p. ej. familia-stauffenberg/):
  tiempos_escenas.csv, video_final.mp4, musica.csv y musica/

Uso:
  python3 armar_video_aleman.py CARPETA_ES CARPETA_DE [--solo-tiempos] [--borrador] [--hasta N] [--hilos 4]

Primero escribe CARPETA_DE/tiempos_escenas.csv (dónde empieza cada escena en la voz alemana,
buscando las pausas de la narración) y después el video CARPETA_DE/video_final.mp4.
Si tiempos_escenas.csv ya existe, lo usa tal cual: así se puede corregir a mano y volver a
correr. Para recalcularlo, borrarlo. Requiere ffmpeg y Pillow.
"""
import argparse, csv, glob, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generar_video import FPS, CRF, PRESET, MOVES, grade, run, canvas_16x9, seg_image, build_music

# Imágenes que ya vienen con el tono del canal (sacadas del video en español): no se gradúan dos veces.
PREGRADUADAS = {'207'}


def leer_csv(p):
    return [r for r in csv.reader(open(p, encoding='utf-8-sig'), delimiter=';')][1:]


def duracion(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def pausas(audio, ruido='-38dB', minimo=0.10):
    """Silencios de la narración como (inicio, fin)."""
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', audio, '-af',
                        f'silencedetect=noise={ruido}:d={minimo}', '-f', 'null', '-'],
                       capture_output=True, text=True)
    ini = [float(x) for x in re.findall(r'silence_start: (-?[\d.]+)', r.stderr)]
    fin = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', r.stderr)]
    return list(zip(ini, fin))


def peso(texto):
    """Duración relativa de una frase: letras más un poco por cada pausa de puntuación."""
    # los números se leen mucho más largos de lo que se escriben («1944» = neunzehnhundertvierundvierzig)
    largo = len(re.sub(r'\d+', '', texto))
    for num in re.findall(r'\d+', texto):
        largo += 26 if len(num) == 4 and num[:2] in ('18', '19', '20') else 7 * len(num) + 3
    return largo + 14 * len(re.findall(r'[.!?…](?=\s|$|[«»"“”])', texto)) + 5 * len(re.findall(r'[,;:—]', texto))


def cierre(texto):
    t = texto.rstrip(' «»"“”')
    return 1.0 if t[-1:] in '.!?…' else (0.5 if t[-1:] in ',;:—' else 0.0)


def alinear(textos, t0, t1, sil):
    """Ubica los cortes entre escenas de un tramo de voz [t0, t1] en las pausas.

    Cada escena debería durar según su largo de texto y tener dentro tantas pausas largas
    (de fin de oración) como puntos internos; entre todas las combinaciones de pausas (en
    orden) se elige la que mejor cumple ambas cosas, y las escenas que terminan en punto
    prefieren cortar en una pausa larga.
    """
    n = len(textos)
    if n == 1: return [t0]
    sil = [(a, b) for a, b in sil if a > t0 + 0.3 and b < t1 - 0.3]
    cand = [((a + b) / 2, b - a) for a, b in sil]
    pesos = [peso(t) for t in textos]
    # pausas largas = finales de oración: tantas como puntos haya en el tramo
    puntos = [len(re.findall(r'[.!?…][«»"“”]?(?=\s)', t.rstrip())) for t in textos]
    n_largas = sum(puntos) + sum(1 for t in textos[:-1] if cierre(t) == 1.0)
    largos = sorted((b - a for a, b in sil), reverse=True)
    umbral = 0.8 * largos[min(n_largas, len(largos)) - 1] if largos and n_largas else 99
    larga = [1 if b - a >= umbral else 0 for a, b in sil]
    acum = [0]
    for x in larga: acum.append(acum[-1] + x)
    ritmo = (t1 - t0) / sum(pesos)
    m, k = len(cand), n - 1
    if m < k:  # casi sin pausas: reparto proporcional
        acc, out = 0, [t0]
        for p in pesos[:-1]: acc += p; out.append(t0 + acc * ritmo)
        return out
    INF = float('inf')

    def tramo(j, a, b, i_a, i_b):
        """Costo de que la escena j vaya de a a b; i_a..i_b son las pausas que quedan adentro."""
        esp = ritmo * pesos[j]
        largas = acum[i_b] - acum[i_a]
        return ((b - a - esp) / (0.25 * esp + 0.4)) ** 2 + 4.0 * (largas - puntos[j]) ** 2

    def bonus(j, i):  # una frase que termina en punto debería cortar en una pausa larga
        c = cierre(textos[j])
        return 4.0 * (larga[i] if c == 1.0 else 0) + 1.0 * c * min(cand[i][1], 0.8)
    # costo[j][i]: mejor forma de poner el corte j (final de la escena j) en la pausa i
    costo = [[INF] * m for _ in range(k)]; de = [[None] * m for _ in range(k)]
    for i in range(m - k + 1):
        costo[0][i] = tramo(0, t0, cand[i][0], 0, i) - bonus(0, i)
    for j in range(1, k):
        lim = 4 * puntos[j] + 12
        for i in range(j, m - (k - 1 - j)):
            mejor, arg = INF, None
            for i2 in range(max(j - 1, i - 1 - lim), i):
                c = costo[j - 1][i2]
                if c == INF: continue
                c += tramo(j, cand[i2][0], cand[i][0], i2 + 1, i)
                if c < mejor: mejor, arg = c, i2
            if arg is not None: costo[j][i] = mejor - bonus(j, i); de[j][i] = arg
    # la última escena va del último corte hasta t1
    fin = [costo[k - 1][i] + tramo(k, cand[i][0], t1, i + 1, m) if costo[k - 1][i] < INF else INF for i in range(m)]
    i = min(range(m), key=lambda x: fin[x]); cortes = []
    for j in range(k - 1, -1, -1):
        cortes.append(i); i = de[j][i]
    cortes.reverse()
    # cada escena empieza a mitad de la pausa que la precede
    return [t0] + [cand[i][0] for i in cortes]


def alinear_escenas(textos, t0, t1, sil):
    """Como alinear(), pero las escenas cortadas a mitad de frase (sin puntuación al final,
    donde la voz no hace pausa) se alinean juntas y después se reparten según su largo."""
    grupos = [[0]]
    for j in range(1, len(textos)):
        if cierre(textos[j - 1]) == 0: grupos[-1].append(j)
        else: grupos.append([j])
    ini_g = alinear([' '.join(textos[j] for j in g) for g in grupos], t0, t1, sil)
    out = []
    for gi, g in enumerate(grupos):
        a = ini_g[gi]; b = ini_g[gi + 1] if gi + 1 < len(grupos) else t1
        pesos = [peso(textos[j]) for j in g]; acc = 0
        for p in pesos:
            out.append(a + (b - a) * acc / sum(pesos)); acc += p
    return out


def tiempos_alemanes(de, escenas):
    """Devuelve [(escena, inicio, fin, texto)] y la ruta de la narración completa."""
    narr = os.path.join(de, 'narracion')
    partes = sorted(glob.glob(os.path.join(narr, 'teil_*.mp3')))
    completa = os.path.join(narr, 'narracion_completa.mp3')
    norm = lambda s: re.sub(r'\s+', ' ', s).strip()
    tramos = []  # (archivo, escenas del tramo)
    if partes:
        idx = 0
        for p in partes:
            txt = norm(open(p[:-4] + '.txt', encoding='utf-8').read())
            grupo, acc = [], ''
            while idx < len(escenas) and len(norm(acc)) < len(txt):
                acc += ' ' + escenas[idx][2]; grupo.append(escenas[idx]); idx += 1
            if norm(acc) != txt:
                raise SystemExit(f'{os.path.basename(p)}: el texto no coincide con escenas_de.csv')
            tramos.append((p, grupo))
        if idx != len(escenas):
            raise SystemExit(f'Faltan partes: las {len(partes)} partes cubren {idx} de {len(escenas)} escenas')
        # unir las partes en un solo archivo para el montaje
        lista = os.path.join(narr, '_partes.txt')
        with open(lista, 'w') as f:
            for p in partes: f.write(f"file '{os.path.abspath(p)}'\n")
        run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lista,
             '-c:a', 'libmp3lame', '-b:a', '192k', completa])
        os.remove(lista)
    elif os.path.exists(completa):
        tramos = [(completa, escenas)]
    else:
        raise SystemExit('No hay narración: poner narracion/teil_01.mp3 … o narracion/narracion_completa.mp3')
    filas, base = [], 0.0
    for p, grupo in tramos:
        dur = duracion(p); sil = pausas(p)
        # la voz real del tramo: sin el silencio del principio y del final
        v0 = sil[0][1] if sil and sil[0][0] <= 0.05 else 0.0
        v1 = sil[-1][0] if sil and sil[-1][1] >= dur - 0.05 else dur
        ini = alinear_escenas([g[2] for g in grupo], v0, v1, sil)
        ini[0] = 0.0
        for j, g in enumerate(grupo):
            fin = ini[j + 1] if j + 1 < len(grupo) else dur
            filas.append((g[0], base + ini[j], base + fin, g[2]))
        base += dur
    if partes:  # ajustar a la duración real del archivo unido
        filas[-1] = filas[-1][:2] + (duracion(completa),) + filas[-1][3:]
    return filas, completa


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('es'); ap.add_argument('de')
    ap.add_argument('--solo-tiempos', action='store_true', help='calcular tiempos_escenas.csv y salir')
    ap.add_argument('--borrador', action='store_true', help='960x540, para revisar')
    ap.add_argument('--hilos', type=int, default=os.cpu_count() or 2)
    ap.add_argument('--hasta', help='armar solo hasta esta escena (para revisar)')
    ap.add_argument('--salida')
    a = ap.parse_args()
    es, de = os.path.abspath(a.es), os.path.abspath(a.de)
    W, H = (960, 540) if a.borrador else (1920, 1080)

    esp = leer_csv(os.path.join(es, 'tiempos_escenas.csv'))
    escenas = leer_csv(os.path.join(de, 'escenas_de.csv'))
    assert [r[0] for r in esp] == [r[0] for r in escenas], 'escenas_de.csv no coincide con las escenas en español'

    tp = os.path.join(de, 'tiempos_escenas.csv')
    if os.path.exists(tp):
        filas = [(r[0], float(r[1]), float(r[2]), r[4]) for r in leer_csv(tp)]
        voz = os.path.join(de, 'narracion', 'narracion_completa.mp3')
        print(f'Usando {tp} (borrarlo para recalcular)')
    else:
        filas, voz = tiempos_alemanes(de, escenas)
        with open(tp, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f, delimiter=';'); w.writerow(['escena', 'inicio_s', 'fin_s', 'duracion_s', 'narracion'])
            for n, t0, t1, txt in filas: w.writerow([n, f'{t0:.2f}', f'{t1:.2f}', f'{t1 - t0:.2f}', txt])
        print(f'Tiempos escritos en {tp}')
    if a.solo_tiempos: return
    if a.hasta: filas = [f for f in filas if f[0] <= a.hasta.zfill(3)]

    # dónde está cada escena dentro del video en español (se armó concatenando escenas de N cuadros)
    pos, cuadro = {}, 0
    for r in esp:
        fr = max(2, round((float(r[2]) - float(r[1])) * FPS))
        pos[r[0]] = (cuadro / FPS, fr / FPS); cuadro += fr
    video_es = os.path.join(es, 'video_final.mp4')
    graf = os.path.join(de, 'graficos')
    tmp = os.path.join(de, f'_tmp_segmentos_{W}'); os.makedirs(tmp, exist_ok=True)

    def hacer(t):
        i, (n, t0, t1, _) = t
        dur = t1 - t0; frames = max(2, round(dur * FPS))
        seg = os.path.join(tmp, f'{n}.mp4'); png = os.path.join(graf, f'{n}.png')
        fuente = png if os.path.exists(png) else video_es
        firma = f'{fuente}|{os.path.getmtime(fuente)}|{frames}|{W}|{CRF}'
        if os.path.exists(seg + '.ok') and open(seg + '.ok').read() == firma:
            return f'{n} (ya estaba)'
        part = seg[:-4] + '.part.mp4'
        if fuente == png:
            img = os.path.join(tmp, f'{n}_canvas.jpg'); canvas_16x9(png, W, H, img)
            if n in PREGRADUADAS:  # acercamiento suave, solo con el grano
                vf = (f"zoompan=z='1+0.06*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},"
                      f"noise=alls={4 if W < 1900 else 5}:allf=t,format=yuv420p")
                run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-i', img, '-vf', vf, '-frames:v', str(frames),
                     '-c:v', 'libx264', '-preset', PRESET, '-crf', CRF, '-r', str(FPS), '-an', part])
            else:
                seg_image(img, frames / FPS, W, H, MOVES[i % len(MOVES)], part)
            como = 'gráfico alemán'
        else:
            s0, ds = pos[n]
            f = (frames / FPS) / ds  # >1 frena, <1 acelera
            vf = (f'setpts={f:.5f}*(PTS-STARTPTS),' + (f'framerate=fps={FPS}' if f > 1.02 else f'fps={FPS}')
                  + ',tpad=stop_mode=clone:stop=6')  # sin asomar un cuadro de la escena siguiente
            if W != 1920: vf += f',scale={W}:{H}'
            run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{s0:.3f}', '-t', f'{ds:.3f}', '-i', video_es, '-an',
                 '-vf', vf + ',format=yuv420p', '-frames:v', str(frames), '-c:v', 'libx264', '-preset', PRESET,
                 '-crf', CRF, '-r', str(FPS), part])
            como = f'video ES x{1 / f:.2f}'
        os.replace(part, seg); open(seg + '.ok', 'w').write(firma)
        return f'{n} ({dur:.1f} s) {como}'

    with ThreadPoolExecutor(a.hilos) as ex:
        for msg in ex.map(hacer, list(enumerate(filas))): print(msg, flush=True)
    lista = os.path.join(tmp, 'lista.txt')
    with open(lista, 'w') as f:
        for n, *_ in filas: f.write(f"file '{os.path.join(tmp, n + '.mp4')}'\n")
    mudo = os.path.join(tmp, 'video_mudo.mp4')
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lista, '-c', 'copy', mudo])

    # música: cada bloque arranca en la misma escena que en español
    inicio = {n: t0 for n, t0, *_ in filas}
    plan = []
    for r in csv.reader(open(os.path.join(es, 'musica.csv'), encoding='utf-8-sig'), delimiter=';'):
        if r and r[0][:1].isdigit():
            m = re.search(r'\((\d{3})\)', r[2])
            if m.group(1) in inicio: plan.append((inicio[m.group(1)], os.path.join(es, r[1])))
    total = filas[-1][2]
    musica = os.path.join(tmp, 'musica.wav')
    build_music(de, plan, total, musica)
    salida = a.salida or os.path.join(de, 'video_borrador.mp4' if a.borrador else 'video_final.mp4')
    # misma mezcla que generar_video.py: voz al frente, música 18 dB abajo y que baja cuando habla
    fc = (f"[1:a]loudnorm=I=-16:TP=-1.5,aresample=44100,asplit=2[v][vsc];"
          f"[2:a]aresample=44100,volume=-18dB[mus];[mus][vsc]sidechaincompress=threshold=0.03:ratio=4:attack=30:release=600[md];"
          f"[v][md]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]")
    run(['ffmpeg', '-v', 'error', '-y', '-i', mudo, '-i', voz, '-i', musica, '-filter_complex', fc,
         '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', salida])
    cp = os.path.join(de, 'capitulos.csv')
    if os.path.exists(cp):  # capítulos para la descripción de YouTube, con los minutos de la voz alemana
        lin = [f'{int(inicio[r[0]] // 60)}:{int(inicio[r[0]] % 60):02d} {r[1]}' for r in leer_csv(cp) if r[0] in inicio]
        open(os.path.join(de, 'capitulos.txt'), 'w', encoding='utf-8').write('\n'.join(lin) + '\n')
        print('\n'.join(lin))
    print(f'\nLISTO: {salida} ({total / 60:.1f} min)')


if __name__ == '__main__':
    main()
