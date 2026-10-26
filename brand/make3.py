"""Brand kit v3 — emblem «النجمة الثمانية»: an eight-point Islamic star (two gold squares)
around a dark medallion carrying «بكالوريا» (Reem Kufi) over the gold rule with the red dot
and «BAC» (Cinzel). Same palette as v2 (make2.py): green, cream, gold, Algerian-flag red.

Run from brand/:  python make3.py && node shoot3.js   -> out3/*.png
Fonts: copy src/assets/fonts/* and brand/fonts/* next to the generated HTML (done below).
"""
import math, os, shutil
from make2 import HEAD, green_bg, lockup, GREEN, DEEP, CREAM, GOLD, RED

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = '<style>@font-face{font-family:CZ;src:url("Cinzel[wght].ttf");font-weight:400 900}</style>'


def _rule(w, h=6, r=13):
    return (f'<div style="display:flex;align-items:center;width:{w}px;direction:ltr">'
            f'<i style="flex:1;height:{h}px;background:{GOLD};border-radius:9px"></i>'
            f'<b style="width:{2*r}px;height:{2*r}px;border-radius:50%;background:{RED};margin:0 -3px"></b>'
            f'<i style="flex:1;height:{h}px;background:{GOLD};border-radius:9px"></i></div>')


def emblem(size, bg=True, words=True, bac_only=False):
    """The emblem drawn on an 800x800 design box, scaled to `size` px.
    bg: square green zellige background (avatar); False = transparent (sits on covers).
    bac_only: favicon variant — just «BAC», large, for 16-48 px."""
    pts = lambda rr, rot: ' '.join(f'{400+rr*math.cos(math.radians(a+rot)):.1f},{400+rr*math.sin(math.radians(a+rot)):.1f}'
                                   for a in (45, 135, 225, 315))
    def star(rr, sw, op=1, fill='none', fo=1):
        return ''.join(f'<polygon points="{pts(rr, rot)}" fill="{fill}" fill-opacity="{fo}" stroke="{GOLD}" stroke-width="{sw}" '
                       f'stroke-opacity="{op}" stroke-linejoin="round" />' for rot in (0, 45))
    svg = (f'<svg style="position:absolute;inset:0" width="800" height="800" viewBox="0 0 800 800">'
           + star(376, 0, 0, DEEP, .55 if bg else .8) + star(376, 8) + star(350, 2.5, .7)
           + f'<circle cx="400" cy="400" r="268" fill="{DEEP}" fill-opacity="{.35 if bg else .6}" stroke="{GOLD}" stroke-width="2" stroke-opacity=".6" /></svg>')
    if bac_only:
        txt = (f'<div style="font:800 190px/1 CZ;color:{CREAM};letter-spacing:.04em;margin-right:-.04em;direction:ltr">BAC</div>'
               f'<div style="margin-top:34px">{_rule(330, 12, 22)}</div>')
    elif words:
        txt = (f'<div style="font:700 140px/1.2 RK;color:{CREAM};margin-top:-8px">بكالوريا</div>'
               f'<div style="margin:12px 0 22px">{_rule(300)}</div>'
               f'<div style="font:700 98px/1 CZ;color:{GOLD};letter-spacing:.22em;margin-right:-.22em;direction:ltr">BAC</div>')
    else:
        txt = ''
    box = ((green_bg() if bg else '') + svg +
           f'<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center">{txt}</div>')
    return (f'<div style="width:{size}px;height:{size}px;position:relative;flex:none">'
            f'<div style="width:800px;height:800px;position:absolute;left:0;top:0;transform:scale({size/800});transform-origin:0 0">{box}</div></div>')


def page(name, w, h, body, bg='transparent'):
    open(os.path.join(OUT, name + '.html'), 'w').write(
        HEAD + FONTS + f'<style>html,body{{width:{w}px;height:{h}px;background:{bg};overflow:hidden}}</style>' + body)


def row(e, fs, gap, tag=True, color=CREAM, sub='rgba(251,248,241,.78)'):
    """Emblem on the right (read first in RTL), wordmark lockup on the left."""
    return f'<div style="display:flex;align-items:center;gap:{gap}px">{e}{lockup(fs, tag, color, sub)}</div>'


CHIPS = ['مواضيع و حلول', 'دروس و ملخصات', 'بكالوريا أجنبية', 'أولمبياد', 'سلاسل فيديو']
SIZES = {}

if __name__ == '__main__':
    OUT = os.path.join(HERE, 'build3'); os.makedirs(OUT, exist_ok=True)
    for d in (os.path.join(HERE, '..', 'src', 'assets', 'fonts'), os.path.join(HERE, 'fonts')):
        for f in os.listdir(d): shutil.copy(os.path.join(d, f), OUT)
    def add(name, w, h, body, bg='transparent', transparent=False):
        page(name, w, h, body, bg); SIZES[name] = [w, h, transparent]
    add('avatar', 800, 800, emblem(800))
    add('logo-icon', 1024, 1024, emblem(1024))
    add('favicon', 512, 512, emblem(512, bac_only=True))
    add('emblem', 800, 800, emblem(800, bg=False), transparent=True)
    add('logo-wordmark', 2000, 900, f'<div style="position:absolute;inset:0;display:grid;place-items:center">{row(emblem(620, bg=False), 140, 70, True, GREEN, "#6B7A70")}</div>', transparent=True)
    add('logo-wordmark-dark', 2000, 900, f'<div style="position:absolute;inset:0;display:grid;place-items:center">{row(emblem(620, bg=False), 140, 70)}</div>', DEEP)
    # YouTube banner 2560x1440 — safe area 1546x423 centred (y 508..931); chips just below it
    add('youtube-banner', 2560, 1440, green_bg() + f'''<div style="position:absolute;left:507px;top:490px;width:1546px;height:450px;display:grid;place-items:center">{row(emblem(450, bg=False), 96, 60)}</div>
<div style="position:absolute;left:0;right:0;top:958px;display:flex;justify-content:center;gap:16px">{''.join(f'<span style="font:700 30px TJ;color:{CREAM};padding:8px 24px;border-radius:99px;border:1.5px solid rgba(201,162,74,.6)">{t}</span>' for t in CHIPS)}</div>''')
    # Facebook cover 1640x624 (the round profile picture covers the lower-left on desktop, so keep it centred)
    add('facebook-cover', 1640, 624, green_bg() + f'<div style="position:absolute;inset:0;display:grid;place-items:center">{row(emblem(440, bg=False), 84, 56)}</div>')
    # Open Graph 1200x630
    add('og-image', 1200, 630, green_bg() + f'''<div style="position:absolute;inset:0;padding:0 70px;display:flex;align-items:center;gap:56px">
<div style="flex:1"><div class="wm" style="font-size:58px">مَجْمَعُ البكالوريا</div>
<div style="font:700 46px/1.4 EM;color:{CREAM};margin-top:26px;white-space:nowrap">كل ما يحتاجه طالب البكالوريا<br>في مكان واحد</div>
<div class="rule" style="width:320px;margin-top:26px"><i></i><b></b><i></i></div></div>{emblem(470, bg=False)}</div>''')
    open(os.path.join(OUT, 'sizes.json'), 'w').write(__import__('json').dumps(SIZES))
    print('pages ->', OUT)
