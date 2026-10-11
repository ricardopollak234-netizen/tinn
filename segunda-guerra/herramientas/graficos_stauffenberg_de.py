#!/usr/bin/env python3
"""Versión en alemán de graficos_stauffenberg.py: mismos gráficos y mapas, textos en alemán.

Uso: python3 graficos_stauffenberg_de.py CARPETA_NATURAL_EARTH CARPETA_MEDIOS [FOTO_HOFACKER FOTO_GOERDELER FOTO_TRESCKOW]
Sin las tres fotos no se genera el collage 207 (armar_video_aleman.py usa entonces la escena del video
en español con el título tapado).
CARPETA_NATURAL_EARTH contiene ne_50m_land/, ne_50m_rivers_lake_centerlines/ y ne_50m_lakes/
(naturalearthdata.com, dominio público). Requiere Pillow y pyshp.
"""
import math, os, random, sys
import shapefile
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
NE, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
SERIF = '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
SERIF_B = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
for cand in ('/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf',):
    if os.path.exists(cand): SERIF = cand
for cand in ('/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf',):
    if os.path.exists(cand): SERIF_B = cand
def F(size, bold=False): return ImageFont.truetype(SERIF_B if bold else SERIF, size)

PAPER = (34, 30, 25); INK = (226, 214, 190); DIM = (150, 138, 118); RED = (176, 52, 40)

def paper(seed=1):
    random.seed(seed)
    im = Image.new('RGB', (W, H), PAPER)
    px = im.load()
    noise = Image.effect_noise((W // 4, H // 4), 22).resize((W, H)).filter(ImageFilter.GaussianBlur(2))
    im = Image.blend(im, Image.merge('RGB', [noise] * 3).point(lambda v: v * 0.25), 0.18)
    # viñeta
    v = Image.new('L', (W, H), 0); d = ImageDraw.Draw(v)
    d.ellipse((-W * 0.15, -H * 0.25, W * 1.15, H * 1.25), fill=255)
    v = v.filter(ImageFilter.GaussianBlur(220))
    return Image.composite(im, Image.new('RGB', (W, H), (8, 7, 6)), v)

def center(d, y, text, font, fill=INK):
    w = d.textlength(text, font=font); d.text(((W - w) / 2, y), text, font=font, fill=fill)

def wrap_center(d, y, text, font, maxw, fill=INK, lh=1.25):
    words = text.split(); lines = []; cur = ''
    for w_ in words:
        t = (cur + ' ' + w_).strip()
        if d.textlength(t, font=font) > maxw and cur: lines.append(cur); cur = w_
        else: cur = t
    lines.append(cur)
    for i, l in enumerate(lines): center(d, y + i * font.size * lh, l, font, fill)
    return y + len(lines) * font.size * lh

def save(im, n): im.save(os.path.join(OUT, f'{n}.png'))

# ---------- tarjetas de texto ----------
def title_card():
    im = paper(23); d = ImageDraw.Draw(im)
    center(d, 330, 'FÜNF KINDER.', F(96, True)); center(d, 460, 'EINE WITWE.', F(96, True))
    center(d, 590, 'EIN NAME, DEN DAS REICH AUSLÖSCHEN WOLLTE.', F(64), DIM)
    d.line((W / 2 - 260, 720, W / 2 + 260, 720), fill=RED, width=3)
    save(im, '023')

def quote(n, variant):
    im = paper(int(n)); d = ImageDraw.Draw(im)
    if variant == 1:
        f = F(70, True)
        y = wrap_center(d, 330, '„Die Familie Graf Stauffenberg wird ausgelöscht werden bis ins letzte Glied.“', f, 1500)
        center(d, y + 50, 'Heinrich Himmler', F(44), DIM)
    else:
        center(d, 250, 'Posen, 3. August 1944', F(48), RED)
        y = wrap_center(d, 380, '„…bis ins letzte Glied.“', F(110, True), 1600)
        center(d, y + 40, 'Himmlers Rede vor den Gauleitern der NSDAP', F(40), DIM)
    save(im, n)

def subscribe(n, variant):
    im = paper(int(n)); d = ImageDraw.Draw(im)
    if variant == 1:
        center(d, 380, 'Geschichten, die beginnen, wo die Bücher enden', F(58), INK)
    else:
        center(d, 380, 'Wenn diese Geschichte es wert war, erzählt zu werden…', F(62), INK)
    bx, by = W / 2 - 230, 520
    d.rounded_rectangle((bx, by, bx + 460, by + 110), 16, fill=RED)
    center(d, by + 26, 'ABONNIEREN', F(56, True), (245, 238, 225))
    save(im, n)

def question(n, variant):
    im = paper(int(n)); d = ImageDraw.Draw(im)
    if variant == 1:
        wrap_center(d, 320, 'Müssen Kinder tragen, was ihre Eltern getan haben, im Guten wie im Schlechten?', F(76, True), 1500)
    else:
        center(d, 380, 'Schreib es in die Kommentare', F(80, True))
        center(d, 520, 'Geerbte Schuld… oder ein Name, aus dem jeder selbst etwas macht?', F(46), DIM)
    save(im, n)

def end_card():
    im = paper(369); d = ImageDraw.Draw(im)
    center(d, 160, 'Wir sehen uns im nächsten Video', F(64, True))
    for x in (W / 2 - 700, W / 2 + 60):
        d.rectangle((x, 380, x + 640, 740), outline=DIM, width=3)
    center(d, 800, 'Musik: Kevin MacLeod (incompetech.com) · CC BY 4.0', F(30), DIM)
    save(im, '369')

def poll(n, step):
    im = paper(int(n)); d = ImageDraw.Draw(im)
    center(d, 120, 'Allensbach-Umfrage, 1951', F(64, True))
    center(d, 210, 'Was halten Sie vom Attentat des 20. Juli 1944?', F(44), DIM)
    data = [('Dafür', 40, (196, 176, 130)), ('Dagegen', 30, RED), ('Keine Meinung / weiß nicht', 30, (110, 102, 92))]
    for i, (lab, pct, col) in enumerate(data):
        y = 360 + i * 200
        on = i < step
        d.text((260, y + 20), lab, font=F(48), fill=INK if on else (80, 74, 66))
        d.rectangle((900, y, 900 + 800, y + 110), outline=(70, 64, 56), width=2)
        if on:
            d.rectangle((900, y, 900 + int(800 * pct / 40 * 0.95), y + 110), fill=col)
            d.text((900 + int(800 * pct / 40 * 0.95) + 24, y + 22), f'{pct} %', font=F(56, True), fill=INK)
    save(im, n)

TREE = {
 'top': [('Claus', 'erschossen 1944'), ('Nina', '1913–2006')],
 'kids': ['Berthold', 'Heimeran', 'Franz Ludwig', 'Valerie', 'Konstanze'],
 'side': [('Berthold (Bruder)', 'gehängt 1944'), ('Alexander', 'Geisel der SS'), ('Melitta', 'abgeschossen 1945'),
          ('Anna (Ninas Mutter)', 'in Haft gest. 1945'), ('Nikolaus von Üxküll', 'gehängt 1944'),
          ('Peter Yorck', 'hingerichtet 1944'), ('Caesar von Hofacker', 'hingerichtet 1944')],
}
def tree(n, mode):
    im = paper(int(n)); d = ImageDraw.Draw(im)
    center(d, 70, 'DIE FAMILIE STAUFFENBERG', F(54, True))
    def box(x, y, name, sub, hl=False, crossed=False, dim=False):
        col = RED if hl else (DIM if not dim else (70, 64, 56))
        d.rectangle((x - 150, y - 45, x + 150, y + 55), outline=col, width=3 if hl else 2)
        fs = 34
        while fs > 22 and d.textlength(name, font=F(fs, True)) > 280: fs -= 1  # que el nombre entre en el recuadro
        tw = d.textlength(name, font=F(fs, True)); d.text((x - tw / 2, y - 32 + (34 - fs) // 2), name, font=F(fs, True), fill=INK if not dim else (90, 84, 74))
        if sub:
            tw = d.textlength(sub, font=F(24)); d.text((x - tw / 2, y + 12), sub, font=F(24), fill=DIM if not dim else (80, 74, 66))
        if crossed: d.line((x - 150, y + 5, x + 150, y + 5), fill=RED, width=5)
    show_side = mode in ('ramas', 'muertos', 'completo')
    focus_kids = mode in ('meister', 'cinco', 'completo', 'sangre')
    box(W / 2 - 220, 230, 'Claus', 'erschossen 1944', crossed=(mode == 'muertos'), dim=(mode == 'ramas'))
    box(W / 2 + 220, 230, 'Nina', '1913–2006', dim=(mode == 'ramas'))
    d.line((W / 2 - 70, 235, W / 2 + 70, 235), fill=DIM, width=2)
    d.line((W / 2, 235, W / 2, 380), fill=DIM, width=2)
    xs = [W / 2 + (i - 2) * 340 for i in range(5)]
    d.line((xs[0], 380, xs[-1], 380), fill=DIM, width=2)
    for i, k in enumerate(TREE['kids']):
        d.line((xs[i], 380, xs[i], 430), fill=DIM, width=2)
        sub = 'Meister' if mode == 'meister' and i < 4 else ('geb. 1945' if i == 4 else '')
        if mode == 'sangre': sub = 'schuldig?'
        box(xs[i], 480, k, sub, hl=focus_kids, dim=(mode in ('ramas', 'muertos')))
    if show_side:
        for i, (nm, sub) in enumerate(TREE['side']):
            x = W / 2 + ((i % 4) - 1.5) * 440; y = 760 + (i // 4) * 170
            dead = 'Alexander' not in nm
            box(x, y, nm, sub, hl=(mode == 'ramas'), crossed=(mode == 'muertos' and dead), dim=False)
    if mode == 'sangre':
        center(d, 780, 'Sippenhaft: Schuld wird mit dem Blut „vererbt“', F(46), RED)
    save(im, n)

# ---------- mapas ----------
def load_shapes():
    land = shapefile.Reader(os.path.join(NE, 'ne_50m_land', 'ne_50m_land')).shapes()
    rivers = shapefile.Reader(os.path.join(NE, 'ne_50m_rivers_lake_centerlines', 'ne_50m_rivers_lake_centerlines')).shapes()
    lakes = shapefile.Reader(os.path.join(NE, 'ne_50m_lakes', 'ne_50m_lakes')).shapes()
    return land, rivers, lakes
LAND, RIVERS, LAKES = load_shapes()

def map_base(bbox, seed):
    lon0, lat0, lon1, lat1 = bbox
    k = math.cos(math.radians((lat0 + lat1) / 2))
    sx = W / ((lon1 - lon0) * k); sy = H / (lat1 - lat0); s = min(sx, sy)
    ox = (W - (lon1 - lon0) * k * s) / 2; oy = (H - (lat1 - lat0) * s) / 2
    P = lambda lon, lat: (ox + (lon - lon0) * k * s, oy + (lat1 - lat) * s)
    im = Image.new('RGB', (W, H), (14, 19, 24)); d = ImageDraw.Draw(im)
    def polys(shapes, fill, outline=None, width=1, line=False):
        for sh in shapes:
            pts = sh.points; parts = list(sh.parts) + [len(pts)]
            for a, b in zip(parts[:-1], parts[1:]):
                seg = [P(*p) for p in pts[a:b]]
                if len(seg) < 2: continue
                if line: d.line(seg, fill=fill, width=width)
                else: d.polygon(seg, fill=fill, outline=outline)
    polys(LAND, (96, 86, 70), (140, 128, 106))
    polys(LAKES, (14, 19, 24))
    polys(RIVERS, (70, 100, 118), line=True, width=3)
    tex = paper(seed)
    im = Image.blend(im, tex, 0.15)
    return im, P

def pin(d, P, lon, lat, label, col=INK, dx=18, dy=-30, big=False):
    x, y = P(lon, lat); r = 12 if big else 9
    d.ellipse((x - r, y - r, x + r, y + r), fill=col, outline=(20, 18, 15), width=2)
    d.text((x + dx, y + dy), label, font=F(40 if big else 34, big), fill=col, stroke_width=4, stroke_fill=(15, 13, 11))

def dashed(d, pts, col=RED, w=6, dash=22):
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0); n = max(1, int(L / dash))
        for i in range(0, n, 2):
            a, b = i / n, min(1, (i + 1) / n)
            d.line((x0 + (x1 - x0) * a, y0 + (y1 - y0) * a, x0 + (x1 - x0) * b, y0 + (y1 - y0) * b), fill=col, width=w)

def arrow(d, a, b, col=RED, w=8):
    d.line((a, b), fill=col, width=w)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for s_ in (-1, 1):
        d.line((b, (b[0] - 34 * math.cos(ang + s_ * 0.45), b[1] - 34 * math.sin(ang + s_ * 0.45))), fill=col, width=w)

def title(d, text):
    d.rectangle((0, 0, W, 110), fill=(15, 13, 11)); d.text((60, 28), text, font=F(50, True), fill=INK)

def map_arrests():
    im, P = map_base((4, 36.0, 28, 58.0), 149); d = ImageDraw.Draw(im)
    src = P(8.98, 48.22)
    for lon, lat in [(13.40, 52.52), (13.17, 53.19), (23.73, 37.98), (18.65, 54.35), (8.62, 48.17)]:
        d.line((src, P(lon, lat)), fill=RED, width=4)
    pin(d, P, 8.98, 48.22, 'Lautlingen', RED, dx=-240, dy=-52, big=True)
    pin(d, P, 8.62, 48.17, 'Rottweil', dx=-150, dy=22)
    pin(d, P, 13.40, 52.52, 'Berlin'); pin(d, P, 13.17, 53.19, 'Ravensbrück', dy=-44)
    pin(d, P, 23.73, 37.98, 'Athen (Alexander)'); pin(d, P, 18.65, 54.35, 'Danzig')
    pin(d, P, 10.89, 49.89, 'Bamberg', DIM)
    title(d, 'Sommer 1944: das Netz der Verhaftungen'); save(im, '149')

def map_oder(n, route):
    im, P = map_base((10.5, 49.8, 23.5, 55.8), int(n)); d = ImageDraw.Draw(im)
    if not route:
        for lat in (51.2, 52.3, 53.3):
            arrow(d, P(21.0, lat), P(15.4, lat + 0.05))
        dashed(d, [P(14.6, 53.6), P(14.6, 52.6), P(14.7, 51.6), P(15.0, 51.0)], RED, 8)
        title(d, 'Januar 1945: Die Rote Armee erreicht die Oder')
    else:
        dashed(d, [P(14.55, 52.35), P(13.75, 52.45), P(13.06, 52.40)], (210, 190, 140), 7)
        title(d, 'Februar 1945: von Frankfurt (Oder) nach Potsdam')
    pin(d, P, 14.55, 52.35, 'Frankfurt (Oder)', RED, big=True)
    pin(d, P, 13.40, 52.52, 'Berlin', dy=-44); pin(d, P, 13.06, 52.40, 'Potsdam', dx=-170, dy=10)
    save(im, n)

def map_nina():
    im, P = map_base((9.0, 47.6, 16.0, 53.3), 189); d = ImageDraw.Draw(im)
    dashed(d, [P(13.06, 52.40), P(12.4, 51.3), P(11.95, 50.31)], RED, 7)
    dashed(d, [P(11.95, 50.31), P(13.35, 48.84)], (110, 102, 92), 5)
    pin(d, P, 13.06, 52.40, 'Potsdam', big=True)
    pin(d, P, 11.95, 50.31, 'Trogen (bei Hof)', RED, big=True)
    pin(d, P, 13.35, 48.84, 'Schönberg (geplantes Ziel)', DIM)
    title(d, 'April 1945: Ninas und Konstanzes Verlegung'); save(im, '189')

def map_hostages():
    im, P = map_base((8.5, 45.6, 16.0, 52.4), 235); d = ImageDraw.Draw(im)
    pts = [(11.25, 51.02), (12.10, 49.01), (13.35, 48.84), (11.43, 48.26), (11.40, 47.27), (12.17, 46.73)]
    dashed(d, [P(*p) for p in pts], RED, 7)
    names = ['Buchenwald', 'Regensburg', 'Schönberg', 'Dachau', 'Innsbruck', 'Niederdorf']
    offs = [(18, -30), (-210, -20), (18, -34), (-170, -10), (-190, -20), (18, 4)]
    for (lon, lat), nm, (dx, dy) in zip(pts, names, offs):
        pin(d, P, lon, lat, nm, RED if nm in ('Buchenwald', 'Niederdorf') else INK, dx, dy, big=nm in ('Buchenwald', 'Niederdorf'))
    title(d, 'April 1945: der Geiselkonvoi der SS'); save(im, '235')

def map_danzig():
    im, P = map_base((14.0, 52.2, 23.5, 56.2), 264); d = ImageDraw.Draw(im)
    pin(d, P, 18.63, 54.31, 'Matzkau bei Danzig', RED, big=True)
    d.text((P(16.0, 53.0)[0], P(16.0, 53.0)[1]), 'Oder ein sowjetisches Lager?', font=F(44), fill=DIM)
    title(d, '1945: Wo starb Anna von Lerchenfeld?'); save(im, '264')

def collage_conspirators(photos):
    im = paper(207); d = ImageDraw.Draw(im)
    center(d, 70, 'Die Kinder der Verschwörer', F(56, True))
    ok = [p for p in photos if p and os.path.exists(p)]
    for i, p in enumerate(ok[:3]):
        ph = Image.open(p).convert('L').convert('RGB')
        ph.thumbnail((520, 640)); x = 160 + i * 560 + (520 - ph.width) // 2
        im.paste(ph, (int(x), 220)); d.rectangle((x - 6, 214, x + ph.width + 6, 220 + ph.height + 6), outline=DIM, width=3)
    names = ['Hofacker', 'Goerdeler', 'Tresckow']
    for i, nm in enumerate(names):
        tw = d.textlength(nm, font=F(44, True)); d.text((160 + i * 560 + 260 - tw / 2, 900), nm, font=F(44, True), fill=INK)
    save(im, '207')

if __name__ == '__main__':
    title_card(); quote('013', 1); quote('128', 2)
    subscribe('024', 1); subscribe('368', 2); question('366', 1); question('367', 2); end_card()
    poll('282', 1); poll('283', 2); poll('284', 3)
    tree('131', 'sangre'); tree('137', 'ramas'); tree('274', 'meister'); tree('278', 'muertos'); tree('311', 'cinco'); tree('364', 'completo')
    map_arrests(); map_oder('169', False); map_oder('172', True); map_nina(); map_hostages(); map_danzig()
    if len(sys.argv) > 5: collage_conspirators(sys.argv[3:6])
    print('ok')
