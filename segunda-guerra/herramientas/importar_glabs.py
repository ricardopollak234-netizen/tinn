#!/usr/bin/env python3
"""Copia las imágenes generadas con G-Labs a medios/NNN.png según el orden de
prompts_glabs_orden.txt.

Uso: python3 importar_glabs.py CARPETA_VIDEO CARPETA_DESCARGAS

Las imágenes de CARPETA_DESCARGAS se toman en el orden en que se descargaron
(fecha de modificación). Si un archivo ya se llama como la escena (p. ej. 045.png
o escena_045.jpg), se usa ese número y no el orden.
"""
import os, re, sys
from PIL import Image

base, desc = sys.argv[1], sys.argv[2]
orden = re.findall(r'escena (\d{3})', open(os.path.join(base, 'prompts_glabs_orden.txt'), encoding='utf-8').read())
fotos = [os.path.join(desc, f) for f in os.listdir(desc) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
fotos.sort(key=os.path.getmtime)
por_nombre, sueltas = {}, []
for f in fotos:
    m = re.search(r'(\d{3})', os.path.basename(f))
    if m and m.group(1) in orden: por_nombre[m.group(1)] = f
    else: sueltas.append(f)
pendientes = [n for n in orden if n not in por_nombre]
for n, f in zip(pendientes, sueltas): por_nombre[n] = f
os.makedirs(os.path.join(base, 'medios'), exist_ok=True)
for n in orden:
    if n in por_nombre:
        Image.open(por_nombre[n]).convert('RGB').save(os.path.join(base, 'medios', f'{n}.png'))
        print(f'{n} ← {os.path.basename(por_nombre[n])}')
faltan = [n for n in orden if n not in por_nombre]
print(f'\n{len(orden) - len(faltan)} de {len(orden)} importadas.' + (f' Faltan: {" ".join(faltan)}' if faltan else ''))
