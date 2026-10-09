#!/usr/bin/env python3
"""Gráficos y mapas propios del video "¿Adónde fueron las Waffen-SS después de 1945?" (sin IA).

Uso: python3 graficos_waffenss.py CARPETA_NATURAL_EARTH CARPETA_MEDIOS
Reutiliza el estilo y los mapas de graficos_stauffenberg.py (Natural Earth, dominio público).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import graficos_stauffenberg as g
from PIL import ImageDraw

F, W, H, INK, DIM, RED = g.F, g.W, g.H, g.INK, g.DIM, g.RED
center, wrap_center, save, paper = g.center, g.wrap_center, g.save, g.paper

def card(n, big, small=None, big_size=92, small_col=DIM, y=330, line=True):
    im = paper(int(n)); d = ImageDraw.Draw(im)
    yy = wrap_center(d, y, big, F(big_size, True), 1600)
    if small: yy = wrap_center(d, yy + 40, small, F(46), 1500, small_col)
    if line: d.line((W / 2 - 260, yy + 30, W / 2 + 260, yy + 30), fill=RED, width=3)
    save(im, n)

def stat(n, number, label, sub=None):
    im = paper(int(n)); d = ImageDraw.Draw(im)
    center(d, 290, number, F(190, True), INK)
    center(d, 540, label, F(60), DIM)
    if sub: center(d, 640, sub, F(38), (120, 110, 96))
    save(im, n)

def half(n):
    im = paper(int(n)); d = ImageDraw.Draw(im)
    center(d, 150, 'Waffen-SS en 1945', F(64, True))
    x0, x1, y0, y1 = 260, W - 260, 420, 560
    mid = (x0 + x1) / 2
    d.rectangle((x0, y0, mid, y1), fill=(150, 138, 118)); d.rectangle((mid, y0, x1, y1), fill=RED)
    d.text((x0, y1 + 30), 'Alemanes del Reich', font=F(46), fill=INK)
    t = 'Extranjeros y alemanes étnicos'; d.text((x1 - d.textlength(t, font=F(46)), y1 + 30), t, font=F(46), fill=INK)
    center(d, 780, 'Cerca de la mitad, según muchos historiadores', F(40), DIM)
    save(im, n)

def subscribe(n, text):
    im = paper(int(n)); d = ImageDraw.Draw(im)
    center(d, 380, text, F(58), INK)
    bx, by = W / 2 - 230, 520
    d.rounded_rectangle((bx, by, bx + 460, by + 110), 16, fill=RED)
    center(d, by + 26, 'SUSCRÍBETE', F(56, True), (245, 238, 225))
    save(im, n)

def end_card(n):
    im = paper(int(n)); d = ImageDraw.Draw(im)
    center(d, 160, 'Nos vemos en el siguiente video', F(64, True))
    for x in (W / 2 - 700, W / 2 + 60):
        d.rectangle((x, 380, x + 640, 740), outline=DIM, width=3)
    center(d, 800, 'Música: Kevin MacLeod (incompetech.com) · CC BY 4.0', F(30), DIM)
    save(im, n)

def map_degrelle(n):
    im, P = g.map_base((-12.0, 41.0, 16.0, 62.5), int(n)); d = ImageDraw.Draw(im)
    pts = [(10.75, 59.91), (4.5, 55.0), (-4.0, 47.5), (-1.99, 43.32)]
    g.dashed(d, [P(*p) for p in pts], RED, 7)
    g.pin(d, P, 10.75, 59.91, 'Oslo', INK, big=True)
    g.pin(d, P, -1.99, 43.32, 'San Sebastián', RED, dx=-330, dy=10, big=True)
    g.pin(d, P, 4.35, 50.85, 'Bruselas', DIM)
    d.text(P(-11.0, 45.6), 'Golfo de Vizcaya', font=F(36), fill=DIM)
    g.title(d, '8 de mayo de 1945: la huida de Léon Degrelle'); save(im, n)

def map_ratlines(n, mengele=False):
    im, P = g.map_base((2.0, 40.0, 20.0, 50.5), int(n)); d = ImageDraw.Draw(im)
    if mengele:
        pts = [(10.27, 48.45), (11.4, 47.27), (11.35, 46.5), (8.93, 44.41)]
        g.dashed(d, [P(*p) for p in pts], RED, 7)
        g.arrow(d, P(8.93, 44.41), P(3.0, 41.0))
        g.pin(d, P, 10.27, 48.45, 'Baviera', INK, big=True)
        g.pin(d, P, 8.93, 44.41, 'Génova', RED, dx=-180, dy=10, big=True)
        d.text((P(3.0, 41.0)[0] + 10, P(3.0, 41.0)[1] - 70), 'a Buenos Aires', font=F(40, True), fill=RED, stroke_width=4, stroke_fill=(15, 13, 11))
        g.title(d, '1949: la ruta de Josef Mengele')
    else:
        for path in ([(11.58, 48.14), (13.05, 47.8), (12.9, 46.6), (12.33, 45.44)], [(12.33, 45.44), (12.48, 41.9)], [(12.33, 45.44), (8.93, 44.41)]):
            g.dashed(d, [P(*p) for p in path], RED, 6)
        g.arrow(d, P(8.93, 44.41), P(3.0, 41.0)); g.arrow(d, P(12.48, 41.9), P(5.0, 40.3))
        g.pin(d, P, 11.58, 48.14, 'Múnich'); g.pin(d, P, 13.05, 47.8, 'Salzburgo')
        g.pin(d, P, 12.48, 41.9, 'Roma', RED, big=True); g.pin(d, P, 8.93, 44.41, 'Génova', RED, dx=-180, dy=10, big=True)
        d.text((P(3.0, 41.0)[0] + 10, P(3.0, 41.0)[1] - 70), 'a Argentina', font=F(40, True), fill=RED, stroke_width=4, stroke_fill=(15, 13, 11))
        g.title(d, 'Las rutas de las ratas')
    save(im, n)

def map_volunteers(n):
    im, P = g.map_base((-6.0, 43.0, 32.0, 64.0), int(n)); d = ImageDraw.Draw(im)
    for lon, lat, nm, dx, dy in [(10.75, 59.91, 'Noruega', 18, -30), (12.57, 55.68, 'Dinamarca', 18, -30), (4.9, 52.37, 'Holanda', -180, -30),
                                 (4.35, 50.85, 'Bélgica', -170, 0), (2.35, 48.86, 'Francia', -150, 10), (24.1, 56.95, 'Letonia', 18, -30),
                                 (24.75, 59.44, 'Estonia', 18, -30), (24.03, 49.84, 'Galitzia (Ucrania)', 18, -10)]:
        g.pin(d, P, lon, lat, nm, RED, dx, dy, big=True)
    g.title(d, 'Los voluntarios extranjeros: ¿y después?'); save(im, n)

if __name__ == '__main__':
    card('024', 'CASI UN MILLÓN DE HOMBRES.', 'Un uniforme declarado criminal. Y miles de caminos para escapar de él.')
    subscribe('025', 'Lo que pasó cuando terminó la guerra y empezó el olvido')
    stat('037', '≈ 900.000', 'hombres pasaron por las Waffen-SS', 'según la mayoría de los historiadores')
    stat('038', '38', 'divisiones', 'muchas solo existieron en el papel')
    half('042')
    card('106', '«organización criminal»', 'Tribunal Militar Internacional · Núremberg, 1 de octubre de 1946', big_size=100)
    card('109', 'LA EXCEPCIÓN', 'Los reclutados por el Estado sin posibilidad de elegir, que no hubieran cometido crímenes.', big_size=96)
    card('149', '«Soldados como los demás»', 'Paul Hausser · Soldaten wie andere auch, 1966', big_size=100)
    map_degrelle('206')
    map_ratlines('225')
    map_ratlines('230', mengele=True)
    map_volunteers('245')
    card('334', '¿ADÓNDE FUERON?', None, big_size=130, y=400)
    card('349', 'El tatuaje se podía quemar.', 'La cicatriz se quedaba.', big_size=92, small_col=INK)
    card('350', 'La guerra terminó en 1945.', 'El uniforme no se quitó tan fácilmente.', big_size=92, small_col=INK)
    card('351', '¿Deben ser juzgados igual los reclutados a la fuerza y los voluntarios?', 'Te leo en los comentarios', big_size=76)
    subscribe('352', 'Si esta historia te pareció importante…')
    end_card('353')
    print('ok')
