"""Escribe escenas.txt, fuentes_visuales.csv, prompts_ia.txt y los créditos del video de las Juventudes Hitlerianas.
Uso: python3 build_docs.py CARPETA_SELECCION CARPETA_VIDEO"""
import csv, io, json, os, re, sys
SEL, V = sys.argv[1], sys.argv[2]
L = lambda f: json.load(open(os.path.join(SEL, f), encoding='utf-8'))
cands, plan, clips, lic = L('cands.json'), L('plan.json'), L('clips.json'), L('licencias.json')
prompts = L('ia_prompts.json')
STY = '1940s black and white archival documentary photograph, film grain, realistic, '
rows = list(csv.reader(open(os.path.join(V, 'tiempos_escenas.csv'), encoding='utf-8-sig'), delimiter=';'))[1:]
def name(tag): k, i = tag.rsplit('__', 1); return cands[k][int(i)]
def mmss(s): s = float(s); return f'{int(s // 60):02d}:{s % 60:04.1f}'
def who_of(nm):
    i = lic.get(nm, {}); aut = re.sub(r'(\.mw-parser-output[^{]*\{[^}]*\}\s*)+', '', i.get('autor') or '')
    for c in (' Alternative names', ' Description', ' Date of birth', ' Born ', ' Work location', ' Authority', ' (', ' creator QS'):
        if c in aut: aut = aut[:aut.index(c)]
    w = i.get('attr') or aut
    if len(nm) > 90: pass
    for c in (' You are free', ' Attribution', ' The copyright holder', ' Author', ' Unknown author'):
        if c in w: w = w[:w.index(c)]
    w = w.strip(' .,;:-'); return w[:70].rsplit(' ', 1)[0] + '…' if len(w) > 70 else w
esc, out, ia, need = [], [], [], set()
LIBRE = {'public domain', 'pdm', 'cc0', 'no restrictions', 'pd-1923'}
for r in rows:
    n, t0, t1, dur, txt = r[0], r[1], r[2], float(r[3]), r[4]
    kind, val = plan[n]
    if kind == 'clip':
        f, st = clips[n][0], clips[n][1]
        if f.startswith('111-OF-8'):
            titulo, enlace = 'Your Job in Germany (Ejército de EE. UU., 1945, 111-OF-8)', 'https://archive.org/details/111-OF-8'
        else:
            titulo, enlace = 'Universal Newsreel: ' + f.rsplit('.', 1)[0].replace('_', ' '), 'https://archive.org/details/universal_newsreels'
        desc = f'CLIP: {titulo}, desde {st} s'
        out.append([n, t0, t1, 'CLIP', f'{n}.mp4', f'{titulo} (desde {st} s)', enlace, 'Dominio público', ''])
    elif kind == 'commons':
        nm = name(val); l = ', '.join(lic.get(nm, {}).get('lic') or ['ver página']); who = who_of(nm)
        tipo = 'BA' if nm.startswith('Bundesarchiv') else 'COM'
        desc = f'FOTO [{tipo}]: {nm} ({l})'
        out.append([n, t0, t1, tipo, f'{n}.jpg', nm, lic.get(nm, {}).get('url', ''), l, who])
        partes = {x.strip().lower() for x in l.split(',')}
        if nm.startswith('Bundesarchiv') or not (partes & LIBRE):
            if nm.startswith('Bundesarchiv'):
                num = nm.split(',')[0].replace('Bundesarchiv ', '')
                need.add(f'Bundesarchiv, {num}{" / " + who if who and "Bundesarchiv" not in who else ""} / CC-BY-SA 3.0')
            else:
                t = nm.rsplit(".", 1)[0]; t = t if len(t) <= 80 else t[:77].rsplit(' ', 1)[0] + '…'
                need.add(f'"{t}" — {who or "autor en Wikimedia Commons"} — {l}')
    elif kind == 'graf':
        desc = f'GRÁFICO propio ({n}.png, herramientas/graficos_hj.py)'
        out.append([n, t0, t1, 'GRAF', f'{n}.png', 'gráfico propio (mapas: Natural Earth, dominio público)', '', 'propio', ''])
    else:
        p = STY + prompts[n]; desc = f'IMAGEN IA (medios/{n}.png, SD-Turbo; se puede reemplazar por G-Labs): {p}'
        ia.append(f'{n} | {mmss(t0)} | {dur:.1f} s | {txt}\n      PROMPT: {p}')
        out.append([n, t0, t1, 'IA', f'{n}.png', prompts[n], '', 'Generada con IA (SD-Turbo, Stability AI Community License)', ''])
    esc.append(f'{n} | {mmss(t0)}–{mmss(t1)} ({dur:.1f} s) | {txt}\n      {desc}')
open(os.path.join(V, 'escenas.txt'), 'w', encoding='utf-8').write('ESCENAS DEL VIDEO — una imagen o clip distinto por escena (sin repeticiones)\n\n' + '\n\n'.join(esc) + '\n')
buf = io.StringIO(); w = csv.writer(buf, delimiter=';')
w.writerow(['escena', 'inicio_s', 'fin_s', 'tipo', 'archivo en medios/', 'fuente', 'enlace', 'licencia', 'autor / atribución']); w.writerows(out)
open(os.path.join(V, 'fuentes_visuales.csv'), 'w', encoding='utf-8-sig', newline='').write(buf.getvalue())
open(os.path.join(V, 'prompts_ia.txt'), 'w', encoding='utf-8').write(
    f'IMÁGENES GENERADAS CON IA — {len(ia)} escenas sin material libre (todas distintas)\n'
    'Se generaron con SD-Turbo. Si querés mejorarlas con G-Labs, usá el mismo prompt y guardá la imagen como medios/NNN.png.\n\n' + '\n\n'.join(ia) + '\n')
musica = sorted({os.path.basename(r[1]).rsplit('.', 1)[0].replace('_', ' ') for r in csv.reader(open(os.path.join(V, 'musica.csv'), encoding='utf-8-sig'), delimiter=';') if r and r[0][:1].isdigit()})
corto = ['Música: Kevin MacLeod (incompetech.com) — ' + ', '.join(f'"{t}"' for t in musica) + '.',
         'Licencia: Creative Commons By Attribution 4.0 — http://creativecommons.org/licenses/by/4.0/', '',
         'Archivo fílmico: Universal Newsreels y "Your Job in Germany" (Ejército de EE. UU., 1945), dominio público (National Archives / archive.org).',
         'Fotografías: Bundesarchiv (CC-BY-SA 3.0 DE), Wikimedia Commons (CC BY / CC BY-SA, Licence Ouverte y dominio público).',
         'Mapas: Natural Earth (dominio público). Narración: voz generada con Voizum.',
         'Cuatro ilustraciones fueron generadas con IA (Stability AI SD-Turbo) y no son fotografías de época.',
         'Lista completa de autores y licencias de cada imagen: [PEGAR AQUÍ EL ENLACE A creditos_completos.txt]']
open(os.path.join(V, 'creditos_descripcion.txt'), 'w', encoding='utf-8').write('CRÉDITOS CORTOS — pegar en la descripción de YouTube\n\n' + '\n'.join(corto) + '\n')
open(os.path.join(V, 'creditos_completos.txt'), 'w', encoding='utf-8').write('\n'.join(
    ['CRÉDITOS COMPLETOS DE IMÁGENES — "¿Qué pasó con las Juventudes Hitlerianas después de la guerra?"',
     'Publicar este texto (comentario fijado, web o documento público) y enlazarlo desde la descripción.', ''] + corto[:-1] +
    ['', 'Imágenes que requieren atribución (el resto son de dominio público o CC0):'] + sorted(need) + ['']))
from collections import Counter
print(Counter(x[3] for x in out), 'IA:', len(ia), 'créditos:', len(need))
