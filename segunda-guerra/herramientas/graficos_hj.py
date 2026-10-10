#!/usr/bin/env python3
"""Gráficos y mapas propios del video "¿Qué pasó con las Juventudes Hitlerianas después de la guerra?".

Uso: python3 graficos_hj.py CARPETA_NATURAL_EARTH CARPETA_MEDIOS
Reutiliza el estilo de graficos_stauffenberg.py y las tarjetas de graficos_waffenss.py.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import graficos_stauffenberg as g
import graficos_waffenss as wss
from PIL import ImageDraw

F, W, H, INK, DIM, RED = g.F, g.W, g.H, g.INK, g.DIM, g.RED
center, paper, save = g.center, g.paper, g.save
card, stat, subscribe, end_card = wss.card, wss.stat, wss.subscribe, wss.end_card

def estructura(n):
    im = paper(int(n)); d = ImageDraw.Draw(im)
    center(d, 110, 'Las Juventudes Hitlerianas', F(64, True))
    cols = [('Niños', [('10–14 años', 'Deutsches Jungvolk'), ('14–18 años', 'Hitlerjugend')]),
            ('Niñas', [('10–14 años', 'Jungmädel'), ('14–18 años', 'Liga de Muchachas Alemanas (BDM)')])]
    for i, (tit, filas) in enumerate(cols):
        x = 220 + i * 780
        d.text((x, 260), tit, font=F(54, True), fill=RED)
        for j, (edad, nombre) in enumerate(filas):
            y = 380 + j * 220
            d.rectangle((x, y, x + 700, y + 170), outline=DIM, width=3)
            d.text((x + 30, y + 22), edad, font=F(44, True), fill=INK)
            d.text((x + 30, y + 92), nombre, font=F(38), fill=DIM)
    center(d, 900, 'Obligatoria para todos desde marzo de 1939', F(40), INK)
    save(im, n)

def map_havel(n):
    im, P = g.map_base((12.6, 52.25, 13.75, 52.70), int(n)); d = ImageDraw.Draw(im)
    g.pin(d, P, 13.405, 52.52, 'Cancillería del Reich', RED, dx=18, dy=-40, big=True)
    g.pin(d, P, 13.19, 52.515, 'Puentes de Pichelsdorf (río Havel)', INK, dx=-300, dy=30, big=True)
    g.pin(d, P, 13.20, 52.535, 'Spandau', DIM, dx=-150, dy=-40)
    g.arrow(d, P(13.9, 52.62), P(13.55, 52.55))
    d.text((P(13.45, 52.60)[0], P(13.45, 52.60)[1]), 'Ejército Rojo', font=F(40, True), fill=RED, stroke_width=4, stroke_fill=(15, 13, 11))
    g.title(d, 'Abril de 1945: los muchachos de los puentes'); save(im, n)

def map_wolfskinder(n):
    im, P = g.map_base((19.0, 53.6, 26.5, 56.6), int(n)); d = ImageDraw.Draw(im)
    g.pin(d, P, 20.51, 54.71, 'Königsberg', INK, big=True)
    g.pin(d, P, 23.90, 54.90, 'Kaunas', DIM)
    g.pin(d, P, 25.28, 54.69, 'Vilna', DIM)
    for a, b in (((21.4, 54.9), (23.2, 55.2)), ((21.9, 54.6), (23.5, 54.7))):
        g.dashed(d, [P(*a), P(*b)], RED, 7)
    d.text((P(21.0, 55.75)[0], P(21.0, 55.75)[1]), 'Prusia Oriental', font=F(42, True), fill=INK, stroke_width=4, stroke_fill=(15, 13, 11))
    d.text((P(23.6, 55.6)[0], P(23.6, 55.6)[1]), 'Lituania', font=F(42, True), fill=INK, stroke_width=4, stroke_fill=(15, 13, 11))
    g.title(d, '1945–1948: los niños lobo cruzan el río Niemen'); save(im, n)

if __name__ == '__main__':
    subscribe('025', 'Lo que pasó con los niños de Hitler cuando el uniforme se cayó a pedazos')
    estructura('043')
    stat('056', '≈ 8.000.000', 'miembros hacia 1940', 'prácticamente toda una generación')
    map_havel('089')
    map_wolfskinder('131')
    card('334', '¿QUÉ PASÓ CON ELLOS?', None, big_size=120, y=400)
    card('335', 'Desaparecieron como organización en unos meses.', 'Sus miembros vivieron el resto del siglo con ella dentro.', big_size=70, small_col=INK)
    card('348', 'Los regímenes que quieren perdurar', 'no empiezan por los ejércitos. Empiezan por los niños.', big_size=84, small_col=INK)
    card('349', 'El nazismo duró doce años.', 'Su huella en aquella generación duró toda una vida.', big_size=92, small_col=INK)
    card('350', '¿Se puede culpar a un niño de catorce años por lo que le enseñaron a creer?', 'Te leo en los comentarios', big_size=72)
    subscribe('351', 'Si esta historia te pareció importante…')
    end_card('352')
    print('ok')
