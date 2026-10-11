#!/usr/bin/env python3
"""Arma guion.txt y las partes para Voizum (narracion/teil_NN.txt) a partir de escenas_de.csv.

Uso: python3 guion_aleman.py CARPETA_ES CARPETA_DE
Los párrafos son los mismos que los del guion en español. Correrlo de nuevo después de corregir
la traducción en escenas_de.csv (columna texto_de).
"""
import csv, os, re, sys

ES, DE = sys.argv[1], sys.argv[2]
MAX = 4800  # caracteres por parte de Voizum
rows = list(csv.reader(open(os.path.join(DE, 'escenas_de.csv'), encoding='utf-8-sig'), delimiter=';'))[1:]
norm = lambda s: re.sub(r'\s+', ' ', s).strip()
# qué escenas cierran párrafo en el guion original
pars = [norm(p) for p in open(os.path.join(ES, 'guion.txt'), encoding='utf-8').read().split('\n\n') if p.strip()]
fin_par = set(); i = 0
for p in pars:
    acc = ''
    while norm(acc) != p:
        acc += ' ' + rows[i][1]; i += 1
        assert len(norm(acc)) <= len(p), f'escenas_de.csv no coincide con el guion en español cerca de la escena {rows[i - 1][0]}'
    fin_par.add(rows[i - 1][0])
assert i == len(rows)
out, cur = [], []
for r in rows:
    cur.append(r[2])
    if r[0] in fin_par: out.append(' '.join(cur)); cur = []
txt = '\n\n'.join(out) + '\n'
open(os.path.join(DE, 'guion.txt'), 'w', encoding='utf-8').write(txt)
partes, cur = [], ''
for p in out:
    if cur and len(cur) + 2 + len(p) > MAX: partes.append(cur); cur = p
    else: cur = f'{cur}\n\n{p}' if cur else p
partes.append(cur)
if len(partes) > 1 and len(partes[-1]) < 1000: ultima = partes.pop(); partes[-1] += '\n\n' + ultima
narr = os.path.join(DE, 'narracion'); os.makedirs(narr, exist_ok=True)
for f in os.listdir(narr):
    if f.startswith('teil_') and f.endswith('.txt'): os.remove(os.path.join(narr, f))
for k, p in enumerate(partes, 1):
    open(os.path.join(narr, f'teil_{k:02d}.txt'), 'w', encoding='utf-8').write(p + '\n')
print(f'{len(out)} párrafos, {len(txt.split())} palabras, partes: {[len(p) for p in partes]}')
