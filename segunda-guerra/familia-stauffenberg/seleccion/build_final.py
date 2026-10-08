"""Escribe escenas.txt, fuentes_visuales.csv, prompts_glabs.txt creditos_descripcion.txt y creditos_completos.txt
a partir del plan final (una foto/clip distinto por escena).
Uso: python3 build_final.py CARPETA_SELECCION CARPETA_VIDEO
"""
import csv, io, json, os, re, sys
SEL, V = sys.argv[1], sys.argv[2]
sys.path.insert(0, SEL)
from assets import A
from mapping import MAP

# Estilo fijo y ficha de personajes: los mismos de build.py
src = open(os.path.join(SEL, 'build.py'), encoding='utf-8').read()
ns = {}
exec(src[src.index('STYLE ='):src.index('LIC =')], ns)
STYLE, LIGHT, expand = ns['STYLE'], ns['LIGHT'], ns['expand']

cands = json.load(open(os.path.join(SEL, 'cands.json'), encoding='utf-8'))
plan = json.load(open(os.path.join(SEL, 'plan_final.json'), encoding='utf-8'))
clips = json.load(open(os.path.join(SEL, 'clips.json'), encoding='utf-8'))
lic = json.load(open(os.path.join(SEL, 'licencias.json'), encoding='utf-8'))
rows = list(csv.reader(open(os.path.join(V, 'tiempos_escenas.csv'), encoding='utf-8-sig'), delimiter=';'))[1:]

CLIP_SRC = {
    '111-m-1012-r8.mp4': ('"Tunisian Victory" (1944), rollo 8 — US Army Signal Corps / British Ministry of Information',
                         'https://archive.org/details/111-m-1012-r8', 'Dominio público (película del gobierno de EE. UU., NARA 111-M-1012)'),
}
def clip_src(f):
    if f in CLIP_SRC: return CLIP_SRC[f]
    t = f.rsplit('.', 1)[0].replace('_', ' ')
    return (f'Universal Newsreel: {t}', 'https://archive.org/details/universal_newsreels',
            'Dominio público (Universal Newsreels, donados al dominio público vía NARA)')

def mmss(s):
    s = float(s); return f'{int(s // 60):02d}:{s % 60:04.1f}'

def lic_text(name):
    i = lic.get(name, {})
    l = ', '.join(i.get('lic') or []) or 'ver página'
    aut = re.sub(r'(\.mw-parser-output[^{]*\{[^}]*\}\s*)+', '', i.get('autor') or '')
    for corte in (' Alternative names', ' Description', ' Date of birth', ' Born ', ' Work location', ' Authority', ' (', ' creator QS'):
        if corte in aut: aut = aut[:aut.index(corte)]
    who = i.get('attr') or aut
    for corte in (' You are free', ' Attribution', ' The copyright holder', ' Author', ' Unknown author'):
        if corte in who: who = who[:who.index(corte)]
    who = who.strip(' .,;:-')
    if len(who) > 70: who = who[:70].rsplit(' ', 1)[0] + '…'
    return l, who, i.get('url', '')

esc, csvrows, gl = [], [], []
fotos_credito = {}
for r, m in zip(rows, MAP):
    n, t0, t1, dur, texto = r[0], r[1], r[2], float(r[3]), r[4]
    key = m.split('|')[0]
    kind, val = plan[n]
    head = f'{n} | {mmss(t0)}–{mmss(t1)} ({dur:.1f} s) | {texto}'
    if kind == 'clip':
        f, start, crop, _ = clips[n]
        titulo, url, lc = clip_src(f)
        desc = f'CLIP: {titulo}, desde {start} s'
        csvrows.append([n, t0, t1, 'CLIP', f'{n}.mp4', f'{titulo} (desde {start} s)', url, lc, ''])
    elif kind == 'commons':
        k, i = val.rsplit('__', 1); name = cands[k][int(i)]
        l, who, url = lic_text(name)
        tipo = 'BA' if name.startswith('Bundesarchiv') else 'COM'
        desc = f'FOTO [{tipo}]: {name} ({l})'
        csvrows.append([n, t0, t1, tipo, f'{n}.jpg', name, url, l, who])
        fotos_credito[name] = (l, who)
    elif kind == 'graf':
        tipo = A[key][0]
        desc = f'{tipo}: gráfico propio ({n}.png, herramientas/graficos_stauffenberg.py)'
        csvrows.append([n, t0, t1, tipo, f'{n}.png', 'gráfico propio' + (' (Natural Earth, dominio público)' if tipo == 'MAPA' else ''), '', 'propio', ''])
    else:
        tipo, clip, buscar, donde, prompt, light = A[key]
        full = f'{expand(prompt)}, {LIGHT[light]}, {STYLE}'
        desc = f'G-LABS (guardar como medios/{n}.png): {full}'
        gl.append(f'{n} | {mmss(t0)} | {dur:.1f} s | {texto}\n      PROMPT: {full}')
        csvrows.append([n, t0, t1, 'GLABS', f'{n}.png', buscar, '', 'Generada con G-Labs', ''])
    esc.append(head + '\n      ' + desc)

open(os.path.join(V, 'escenas.txt'), 'w', encoding='utf-8').write(
    'ESCENAS DEL VIDEO — una imagen o clip distinto por escena (sin repeticiones)\n'
    'Formato: escena | tiempo en la narración | texto\n\n' + '\n\n'.join(esc) + '\n')
buf = io.StringIO(); w = csv.writer(buf, delimiter=';')
w.writerow(['escena', 'inicio_s', 'fin_s', 'tipo', 'archivo en medios/', 'fuente', 'enlace', 'licencia', 'autor / atribución'])
w.writerows(csvrows)
open(os.path.join(V, 'fuentes_visuales.csv'), 'w', encoding='utf-8-sig', newline='').write(buf.getvalue())
open(os.path.join(V, 'prompts_glabs.txt'), 'w', encoding='utf-8').write(
    f'IMÁGENES G-LABS — {len(gl)} escenas sin material libre (todas distintas, ninguna se repite)\n'
    'Generar cada una en 16:9 y guardarla como medios/NNN.png (NNN = número de escena).\n'
    'Después volver a correr: python3 herramientas/generar_video.py familia-stauffenberg\n\n'
    + '\n\n'.join(gl) + '\n')

# Créditos para la descripción de YouTube (incluye las fotos del collage de la escena 207)
for name in ('Bundesarchiv Bild 146-1993-069-06, Carl Friedrich Goerdeler.jpg', 'Bundesarchiv Bild 146-1976-130-53, Henning v. Tresckow.jpg'):
    fotos_credito[name] = lic_text(name)[:2]
need = []
for name, (l, who) in sorted(fotos_credito.items()):
    libres = {'public domain', 'pdm', 'cc0', 'no restrictions', 'pd-1923'}
    partes = {x.strip().lower() for x in l.split(',')}
    if name.startswith('Bundesarchiv') or not (partes & libres):
        if name.startswith('Bundesarchiv'):
            num = name.split(',')[0].replace('Bundesarchiv ', '')
            need.append(f'Bundesarchiv, {num}{" / " + who if who and "Bundesarchiv" not in who else ""} / CC-BY-SA 3.0')
        else:
            need.append(f'"{name.rsplit(".", 1)[0]}" — {who or "autor en Wikimedia Commons"} — {l}')
musica = sorted({os.path.basename(r[1]).rsplit('.', 1)[0].replace('_', ' ') for r in
                 csv.reader(open(os.path.join(V, 'musica.csv'), encoding='utf-8-sig'), delimiter=';') if r and r[0][:1].isdigit()})
corto = ['Música: Kevin MacLeod (incompetech.com) — ' + ', '.join(f'"{t}"' for t in musica) + '.',
         'Licencia: Creative Commons By Attribution 4.0 — http://creativecommons.org/licenses/by/4.0/', '',
         'Archivo fílmico: Universal Newsreels y "Tunisian Victory" (1944), dominio público (National Archives / archive.org).',
         'Fotografías: Bundesarchiv (CC-BY-SA 3.0 DE) y Wikimedia Commons (licencias CC BY / CC BY-SA y dominio público).',
         'Mapas: Natural Earth (dominio público). Narración: voz generada con Voizum.',
         'Lista completa de autores y licencias de cada imagen: [PEGAR AQUÍ EL ENLACE A creditos_completos.txt]']
open(os.path.join(V, 'creditos_descripcion.txt'), 'w', encoding='utf-8').write(
    'CRÉDITOS CORTOS — pegar en la descripción de YouTube (entra en el límite de 5000 caracteres)\n\n' + '\n'.join(corto) + '\n')
txt = ['CRÉDITOS COMPLETOS DE IMÁGENES — "¿Qué pasó con la familia de Stauffenberg?"',
       'Publicar este texto (comentario fijado, web o documento público) y enlazarlo desde la descripción.', ''] + corto[:-1] + [
       '', 'Imágenes que requieren atribución (el resto son de dominio público o CC0):'] + sorted(set(need)) + ['']
open(os.path.join(V, 'creditos_completos.txt'), 'w', encoding='utf-8').write('\n'.join(txt))
from collections import Counter
print(Counter(r[3] for r in csvrows), 'G-Labs:', len(gl), 'créditos:', len(set(need)), 'chars corto:', len('\n'.join(corto)))
