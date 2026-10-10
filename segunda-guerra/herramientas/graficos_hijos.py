#!/usr/bin/env python3
"""Gráficos y mapas propios del video "Los hijos de los generales de Hitler que entraron al nuevo ejército alemán".

Uso: python3 graficos_hijos.py CARPETA_NATURAL_EARTH CARPETA_MEDIOS
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
SHADOW = dict(stroke_width=4, stroke_fill=(15, 13, 11))

def map_rin(n):
    im, P = g.map_base((5.6, 49.6, 8.4, 51.1), int(n)); d = ImageDraw.Draw(im)
    g.pin(d, P, 7.10, 50.73, 'Bonn', INK, dx=18, dy=-40, big=True)
    g.pin(d, P, 7.40, 50.43, 'Andernach', RED, dx=18, dy=-10, big=True)
    g.pin(d, P, 6.76, 50.01, 'Abadía de Himmerod', RED, dx=-120, dy=24, big=True)
    d.text(P(7.62, 50.58), 'Río Rin', font=F(36, True), fill=DIM, **SHADOW)
    g.title(d, '1950–1956: donde nació el nuevo ejército'); save(im, n)

def map_mogilev(n):
    im, P = g.map_base((25.5, 52.6, 32.5, 55.4), int(n)); d = ImageDraw.Draw(im)
    g.pin(d, P, 30.33, 53.90, 'Moguilov (fortaleza, junio de 1944)', RED, dx=-300, dy=-70, big=True)
    g.pin(d, P, 27.56, 53.90, 'Minsk (ahorcamiento, 30/01/1946)', INK, dx=-200, dy=40, big=True)
    g.title(d, 'Bielorrusia, 1944–1946'); save(im, n)

def oath(n, year, text, col):
    im = paper(int(n)); d = ImageDraw.Draw(im)
    center(d, 260, year, F(76, True), col)
    g.wrap_center(d, 430, text, F(64), 1500, INK)
    save(im, n)

if __name__ == '__main__':
    subscribe('023', 'Las historias que quedaron a la sombra de la guerra')
    map_rin('044')
    stat('087', '553', 'oficiales superiores examinados', '470 aceptados · 51 rechazados')
    map_mogilev('129')
    stat('281', '+ 12.000', 'oficiales de carrera venían de la Wehrmacht', 'a finales de los años cincuenta')
    oath('289', 'Juramento de 1934', '«Juro por Dios… obediencia incondicional al Führer del Reich y del pueblo alemán, Adolf Hitler…»', RED)
    oath('290', 'Bundeswehr, desde 1956', '«…servir lealmente a la República Federal de Alemania y defender con valentía el derecho y la libertad del pueblo alemán.»', INK)
    card('299', 'Un régimen injusto como el Tercer Reich', 'no puede fundar una tradición. (Decreto de tradición, 1982)', big_size=78, small_col=INK)
    card('335', '¿QUÉ FUE DE LOS HIJOS?', None, big_size=110, y=400)
    card('350', '¿Habrías seguido el camino de tu padre?', 'Te leo en los comentarios', big_size=80)
    subscribe('352', 'Si esta historia te pareció interesante…')
    end_card('354')
    print('ok')
