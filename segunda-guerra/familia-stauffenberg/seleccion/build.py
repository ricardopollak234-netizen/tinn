import json, sys, csv, io, collections
sys.path.insert(0, sys.argv[1])
from assets import A
from mapping import MAP
S = sys.argv[1]; OUT = sys.argv[2]
scenes = json.load(open(f'{S}/scenes.json', encoding='utf-8'))
assert len(scenes) == len(MAP), (len(scenes), len(MAP))

STYLE = ('1940s World War II historical documentary look, muted desaturated colors with cold blue-gray '
         'and faded sepia tones, deep shadows, high contrast, archival film grain, subtle vignette, '
         'shallow depth of field, 16:9, no text, no watermark, no swastikas or Nazi insignia')
LIGHT = {
 'past':   'soft warm window light, nostalgic',
 'night':  'night, harsh vehicle headlights and long shadows',
 'prison': 'cold harsh overhead light, claustrophobic',
 'end':    'gray spring light, smoke and dust of a collapsing country',
 'post':   'pale clean daylight, quiet and reflective',
}
FICHA = [
 ('NINA (pregnant)', 'a German woman in her early thirties with dark brown hair pinned back in a 1940s style, dark intelligent eyes and an oval face, visibly pregnant'),
 ('NINA (pale and ill)', 'a pale exhausted German woman in her early thirties with dark brown hair loose on the pillow, dark intelligent eyes and an oval face'),
 ('NINA (1950s)', 'a German woman in her forties with dark hair streaked with gray pinned back, dark intelligent eyes, an oval face and a plain dark 1950s wool dress'),
 ('NINA (old)', 'an elderly German woman'),
 ('NINA', 'a German woman in her twenties to early thirties with dark brown hair pinned back in a 1930s-1940s style, dark intelligent eyes, an oval face and a simple dark dress'),
 ('CLAUS (1943-1944)', 'a German officer in his mid-thirties with dark wavy hair, a black eye patch over his left eye and an empty right sleeve folded at the wrist, plain field-gray uniform without insignia'),
 ('CLAUS (1940)', 'a tall slim German officer in his early thirties with dark wavy hair combed back, a strong straight nose and dark eyes, plain field-gray uniform without insignia'),
 ('CLAUS (1942)', 'a tall slim German officer in his mid-thirties with dark wavy hair combed back, a strong straight nose and dark eyes, plain field-gray uniform without insignia'),
 ('CLAUS', 'a tall slim German officer in his twenties with dark wavy hair combed back, a strong straight nose and dark eyes'),
 ('BERTHOLD', 'a ten-year-old German boy with short light-brown hair parted to the side in a knitted 1940s sweater and short trousers'),
 ('HEIMERAN', 'an eight-year-old German boy with tousled dark-blond hair in a 1940s shirt'),
 ('FRANZ LUDWIG', 'a six-year-old German boy with straight brown hair and a round face'),
 ('VALERIE', 'a three-year-old German girl with light-brown hair in a short bob and a small smock dress'),
 ('KONSTANZE', 'a tiny newborn baby girl wrapped in a white wool blanket'),
 ('MELITTA', 'a German woman in her early forties with short dark hair and a determined face in a 1940s leather flying jacket'),
 ('DR SCHRANK', 'a German doctor in his fifties with gray hair and round glasses in a white coat'),
]
def expand(p):
    for k, v in FICHA:
        p = p.replace(k, v)
    return p

LIC = {
 'NARA': 'Dominio público (obra del gobierno de EE. UU.: Signal Corps, Fuerza Aérea, películas oficiales). Revisar que el catálogo diga "Unrestricted"; NO usar si dice "courtesy of" o cita a un tercero.',
 'BA':   'Bundesarchiv en Commons: CC BY-SA 3.0 DE. Poner en la descripción: "Bundesarchiv, Bild [número] / [autor] / CC-BY-SA 3.0".',
 'COM':  'Wikimedia Commons: revisar la página del archivo. CC0/PD: libre. CC BY o CC BY-SA: autor + licencia en la descripción del video.',
 'STK':  'Pexels/Pixabay/Unsplash: uso comercial gratis sin atribución (no es dominio público). Personas solo de espaldas, en silueta o no identificables.',
 'MAPA': 'Natural Earth: dominio público. OpenStreetMap: "© colaboradores de OpenStreetMap".',
 'GRAF': 'Gráfico propio, sin licencia de terceros (si incluye fotos, usar las de Bundesarchiv/Commons con su crédito).',
 'GLABS':'Generada con G-Labs (último recurso). No hay material libre de esta escena.',
}
BLOCKS = [(1,'hook'),(25,'familia'),(62,'transformación'),(91,'20 de julio'),(123,'sippenhaft'),
          (151,'nina prisionera'),(198,'niños meister'),(232,'rehenes'),(266,'reencuentro'),
          (276,'posguerra'),(311,'cinco destinos'),(343,'final')]
def block(n):
    b = BLOCKS[0][1]
    for s, name in BLOCKS:
        if n >= s: b = name
    return b

first_glabs = {}
esc, rows, gl_main, gl_back = [], [], [], []
cnt = collections.Counter(); unique = collections.defaultdict(set)
prev = None
for s, m in zip(scenes, MAP):
    key, _, note = m.partition('|')
    assert key in A, key
    assert key != prev or A[key][0] == 'GRAF', f'escena {s["n"]} repite {key}'
    prev = key
    tipo, clip, buscar, donde, prompt, light = A[key]
    n = s['n']; secs = round(s['w'] / 2.87)
    full = f'{expand(prompt)}, {LIGHT[light]}, {STYLE}'
    tag = tipo + (' + CLIP' if clip else '')
    nota = f' [{note}]' if note else ''
    lines = [f'{n:03d} | ~{secs} s | NARRACIÓN: {s["t"]}']
    if tipo == 'GLABS':
        if key in first_glabs:
            ref = first_glabs[key]
            lines.append(f'FUENTE [G-LABS]: reutilizar la imagen de la escena {ref:03d} (sin generar otra){nota}')
            gl_main.append(f'{n:03d} | = escena {ref:03d} (reutilizar, no generar)')
        else:
            first_glabs[key] = n
            lines.append(f'FUENTE [G-LABS]: {buscar}{nota}')
            lines.append(f'IMAGEN G-LABS: {full}')
            gl_main.append(f'{n:03d} | {full}')
            unique['GLABS'].add(key)
    else:
        lines.append(f'FUENTE [{tag}]: {buscar}{nota} → {donde}')
        if tipo in ('MAPA', 'GRAF'):
            lines.append('SIN G-LABS: hacer en el editor (no usar IA para mapas ni textos)')
        else:
            lines.append(f'RESPALDO G-LABS (solo si no se consigue la fuente libre): {full}')
            gl_back.append(f'{n:03d} | {full}')
        unique[tipo].add(key)
    cnt[tipo] += 1
    esc.append('\n'.join(lines))
    rows.append([f'{n:03d}', secs, block(n), tipo, 'sí' if clip else '', buscar + nota, donde, LIC[tipo], '', ''])

open(f'{OUT}/escenas.txt', 'w', encoding='utf-8').write('\n\n'.join(esc) + '\n')
buf = io.StringIO()
w = csv.writer(buf, delimiter=';')
w.writerow(['escena','seg','bloque','tipo','clip posible','qué buscar','dónde','licencia / crédito','archivo usado (URL)','crédito a poner'])
w.writerows(rows)
open(f'{OUT}/fuentes_visuales.csv', 'w', encoding='utf-8-sig', newline='').write(buf.getvalue())
open(f'{OUT}/prompts_glabs.txt', 'w', encoding='utf-8').write(
  'PROMPTS G-LABS — SOLO LAS ESCENAS SIN MATERIAL LIBRE (último recurso)\n'
  'Las líneas "= escena N" reutilizan una imagen ya generada: no generar de nuevo.\n\n' + '\n'.join(gl_main) + '\n')
open(f'{OUT}/prompts_glabs_respaldo.txt', 'w', encoding='utf-8').write(
  'PROMPTS G-LABS DE RESPALDO — usar SOLO si no se encuentra la foto o el clip libre de esa escena\n\n' + '\n'.join(gl_back) + '\n')
fl = ['FICHA DE PERSONAJES — descripción fija usada en todos los prompts de G-Labs (no usar nombres reales en G-Labs)', '']
for k, v in FICHA: fl += [f'{k}:', f'  {v}', '']
open(f'{OUT}/ficha_personajes.txt', 'w', encoding='utf-8').write('\n'.join(fl))
tot = sum(round(s['w']/2.87) for s in scenes)
print('escenas', len(scenes), 'dur', tot//60, 'min', tot%60, 's; media', round(tot/len(scenes),1), 's')
print('por tipo (escenas):', dict(cnt))
print('recursos distintos:', {k: len(v) for k, v in unique.items()})
print('imágenes G-Labs a generar:', len(first_glabs))
