import sys, os, json, time, torch
from diffusers import AutoPipelineForText2Image
P = json.load(open(sys.argv[1])); OUT = sys.argv[2]
torch.set_num_threads(4)
pipe = AutoPipelineForText2Image.from_pretrained('stabilityai/sd-turbo', torch_dtype=torch.float32)
pipe.set_progress_bar_config(disable=True)
STY = '1940s black and white archival documentary photograph, film grain, realistic, '
for n, p in P.items():
    out = os.path.join(OUT, f'{n}.png')
    if os.path.exists(out): continue
    t = time.time(); g = torch.Generator().manual_seed(int(n) + 31)
    pipe(prompt=STY + p, num_inference_steps=2, guidance_scale=0.0, width=640, height=360, generator=g).images[0].save(out)
    print(n, f'{time.time()-t:.1f}s', flush=True)
print('SDDONE', flush=True)
