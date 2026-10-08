"""Une parte_1.mp4 … parte_5.mp4 en un solo archivo, sin recomprimir (calidad intacta).

Uso (desde esta carpeta):  python unir_video.py
Resultado: reino_criminal_mayito_flaco.mp4 (listo para subir a YouTube)
"""
import shutil, subprocess, sys
from pathlib import Path

aqui = Path(__file__).parent
ff = shutil.which('ffmpeg')
if not ff:
    try:
        import imageio_ffmpeg; ff = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit('No se encontró ffmpeg. Instalá moviepy (trae imageio-ffmpeg) o ffmpeg.')
partes = sorted(aqui.glob('parte_*.mp4'), key=lambda p: int(p.stem.split('_')[1]))
lista = aqui / '_lista.txt'
lista.write_text(''.join(f"file '{p.name}'\n" for p in partes), encoding='utf-8')
salida = aqui / 'reino_criminal_mayito_flaco.mp4'
subprocess.run([ff, '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', str(lista), '-c', 'copy', '-movflags', '+faststart', str(salida)], check=True)
lista.unlink()
print(f'Listo: {salida}')
