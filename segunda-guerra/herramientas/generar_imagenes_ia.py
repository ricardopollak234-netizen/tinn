"""Genera las imágenes de las escenas sin material libre con SD-Turbo (gratis, en CPU).
Alternativa a G-Labs: 1 paso por imagen, ~10 s cada una en 4 núcleos.
Uso: python3 generar_imagenes_ia.py CARPETA_VIDEO CARPETA_SALIDA [escenas,separadas,por,coma]
Requiere: pip install torch --index-url https://download.pytorch.org/whl/cpu; pip install diffusers transformers accelerate
Licencia del modelo: Stability AI Community License (uso comercial gratis con menos de US$1M de ingresos;
registrarse en https://stability.ai/community-license).
"""
import sys, os, re, time, torch
from diffusers import AutoPipelineForText2Image
V, OUT = sys.argv[1], sys.argv[2]
solo = sys.argv[3].split(',') if len(sys.argv) > 3 else None
orden = re.findall(r'escena (\d{3})', open(os.path.join(V, 'prompts_glabs_orden.txt'), encoding='utf-8').read())
lote = open(os.path.join(V, 'prompts_glabs_lote.txt'), encoding='utf-8').read().strip().split('\n')
torch.set_num_threads(4)
pipe = AutoPipelineForText2Image.from_pretrained('stabilityai/sd-turbo', torch_dtype=torch.float32)
pipe.set_progress_bar_config(disable=True)
STY = '1940s black and white archival documentary photograph, film grain, realistic, '
for n, p in zip(orden, lote):
    if solo and n not in solo: continue
    out = os.path.join(OUT, f'{n}.png')
    if os.path.exists(out): continue
    desc = p.split(', 1940s World War II historical documentary look')[0]
    desc = desc.replace('Cinematic ', '').replace('cinematic ', '')
    t = time.time()
    g = torch.Generator().manual_seed(int(n))
    im = pipe(prompt=STY + desc, num_inference_steps=1, guidance_scale=0.0, width=768, height=432, generator=g).images[0]
    im.save(out); print(n, f'{time.time() - t:.1f}s', flush=True)
print('SDDONE', flush=True)
