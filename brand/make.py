"""Brand kit for مجمع البكالوريا — Algerian flag palette.
Writes SVGs + HTML compositions; shoot.js renders them to PNG with Playwright."""
import math, os
G1, G2, G3 = '#0C9A58', '#006233', '#003D20'     # flag green, light → deep
RED, WHITE, INK = '#D21034', '#FFFFFF', '#0B1A12'

def star(cx, cy, R, r=None, rot=-90):
    r = r or R * 0.382
    pts = []
    for i in range(10):
        a = math.radians(rot + i * 36); rr = R if i % 2 == 0 else r
        pts.append(f'{cx + rr*math.cos(a):.2f},{cy + rr*math.sin(a):.2f}')
    return 'M' + ' L'.join(pts) + 'Z'

def pattern(id_, color, op, size=72, sw=1.2):
    """8-point star (khatam) lattice, Maghreb zellige style."""
    s = size; c = s / 2; a = s * 0.25
    sq1 = f'M{c-a},{c-a} H{c+a} V{c+a} H{c-a}Z'
    d = a * math.sqrt(2)
    sq2 = f'M{c},{c-d} L{c+d},{c} L{c},{c+d} L{c-d},{c}Z'
    links = f'M0,0 L{c-a},{c-a} M{s},0 L{c+a},{c-a} M0,{s} L{c-a},{c+a} M{s},{s} L{c+a},{c+a} M{c},0 V{c-d} M{c},{s} V{c+d} M0,{c} H{c-d} M{s},{c} H{c+d}'
    return (f'<pattern id="{id_}" width="{s}" height="{s}" patternUnits="userSpaceOnUse">'
            f'<g fill="none" stroke="{color}" stroke-opacity="{op}" stroke-width="{sw}" stroke-linejoin="round">'
            f'<path d="{sq1}"/><path d="{sq2}"/><path d="{links}"/></g></pattern>')

def mark(size=512, rounded=True, bg=True):
    """The logo mark: open book under the red star, on a green squircle."""
    rx = 118 if rounded else 0
    book = ('<path d="M256 352 C214 322 166 312 112 318 V196 C166 190 214 200 256 232 Z" fill="#FFFFFF"/>'
            '<path d="M256 352 C298 322 346 312 400 318 V196 C346 190 298 200 256 232 Z" fill="#E3F4EA"/>'
            '<path d="M112 318 V340 C166 334 214 344 256 374 C298 344 346 334 400 340 V318" fill="none" stroke="#FFFFFF" stroke-width="12" stroke-linejoin="round" stroke-opacity=".55"/>'
            '<path d="M140 232 C172 230 200 236 228 250 M140 262 C172 260 200 266 228 280 M284 250 C312 236 340 230 372 232 M284 280 C312 266 340 260 372 262" fill="none" stroke="'+G2+'" stroke-opacity=".22" stroke-width="7" stroke-linecap="round"/>')
    st = f'<path d="{star(256, 136, 46)}" fill="{RED}"/>'
    defs = (f'<defs><linearGradient id="mg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{G1}"/><stop offset=".55" stop-color="{G2}"/><stop offset="1" stop-color="{G3}"/></linearGradient>'
            f'{pattern("mp", "#FFFFFF", .07, 64, 1.6)}'
            f'<radialGradient id="mh" cx=".3" cy=".2" r=".9"><stop offset="0" stop-color="#fff" stop-opacity=".22"/><stop offset=".6" stop-color="#fff" stop-opacity="0"/></radialGradient></defs>')
    back = (f'<rect width="512" height="512" rx="{rx}" fill="url(#mg)"/><rect width="512" height="512" rx="{rx}" fill="url(#mp)"/>'
            f'<rect width="512" height="512" rx="{rx}" fill="url(#mh)"/>') if bg else ''
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="{size}" height="{size}">{defs}{back}{book}{st}</svg>'

def mark_mono(color='#FFFFFF', star_color=RED):
    """Mark without the tile, for placing on green backgrounds."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="80 80 352 320">'
            f'<path d="M256 352 C214 322 166 312 112 318 V196 C166 190 214 200 256 232 Z" fill="{color}"/>'
            f'<path d="M256 352 C298 322 346 312 400 318 V196 C346 190 298 200 256 232 Z" fill="{color}" fill-opacity=".86"/>'
            f'<path d="M112 318 V340 C166 334 214 344 256 374 C298 344 346 334 400 340 V318" fill="none" stroke="{color}" stroke-width="12" stroke-opacity=".5"/>'
            f'<path d="M140 232 C172 230 200 236 228 250 M140 262 C172 260 200 266 228 280 M284 250 C312 236 340 230 372 232 M284 280 C312 266 340 260 372 262" fill="none" stroke="{G2}" stroke-opacity=".25" stroke-width="7" stroke-linecap="round"/>'
            f'<path d="{star(256, 136, 46)}" fill="{star_color}"/></svg>')

FONTS = '''<style>
@font-face{font-family:Readex;src:url(readex-pro-var.woff);font-weight:500 700}
@font-face{font-family:Plex;src:url(plex-arabic-Regular.woff);font-weight:400}
@font-face{font-family:Plex;src:url(plex-arabic-SemiBold.woff);font-weight:600}
*{margin:0;box-sizing:border-box}body{direction:rtl;font-family:Plex;-webkit-font-smoothing:antialiased}
.t{font-family:Readex;font-weight:700}
</style>'''
PAT_BG = f'<svg width="0" height="0" style="position:absolute"><defs>{pattern("zp", "#FFFFFF", .07, 96, 1.4)}{pattern("zl", G2, .07, 96, 1.4)}</defs></svg>'

def page(name, w, h, body, bg='transparent'):
    html = f'<!doctype html><meta charset="utf-8">{FONTS}<style>html,body{{width:{w}px;height:{h}px;background:{bg};overflow:hidden}}</style>{PAT_BG}{body}'
    open(f'{name}.html', 'w', encoding='utf-8').write(html)

GREEN_BG = f'''<div style="position:absolute;inset:0;background:radial-gradient(70% 90% at 85% 10%, {G1} 0%, {G2} 45%, {G3} 100%)"></div>
<svg style="position:absolute;inset:0;width:100%;height:100%"><rect width="100%" height="100%" fill="url(#zp)"/></svg>
<div style="position:absolute;inset:0;background:radial-gradient(40% 60% at 12% 100%, rgba(210,16,52,.28), transparent 70%)"></div>'''

def wordmark(fs, color='#fff', sub=True, subcolor='rgba(255,255,255,.75)'):
    s = f'<div class="t" style="font-size:{fs}px;line-height:1.15;color:{color}">مَجْمَعُ البكالوريا</div>'
    if sub: s += f'<div style="font-size:{fs*0.34}px;color:{subcolor};margin-top:{fs*0.12}px;font-weight:600">مواضيع و حلول البكالوريا الجزائرية منذ 2013</div>'
    return s

if __name__ == '__main__':
    open('logo-mark.svg', 'w').write(mark())
    open('logo-mark-white.svg', 'w').write(mark_mono())
    open('logo-mark-green.svg', 'w').write(mark_mono(G2))
    # 1. square marks (avatar = mark at full bleed, rounded corners irrelevant since platforms crop to a circle)
    page('logo-mark', 1024, 1024, mark(1024))
    page('avatar', 800, 800, f'<div style="position:absolute;inset:0">{GREEN_BG}</div><div style="position:absolute;left:150px;top:140px;width:500px;height:460px">{mark_mono()}</div>'.replace('<svg xmlns','<svg width="500" height="460" xmlns'))
    # 2. horizontal lockups
    lock = lambda col, sub: f'<div style="display:flex;align-items:center;gap:56px;padding:60px 80px">{mark(300)}<div>{wordmark(150, col, True, sub)}</div></div>'
    page('logo-horizontal', 1800, 420, lock(INK, '#5B6B62'))
    page('logo-horizontal-dark', 1800, 420, lock('#fff', 'rgba(255,255,255,.7)'), '#0A1510')
    # 3. YouTube banner 2560x1440, safe area 1546x423 centred
    yt = f'''{GREEN_BG}
<div style="position:absolute;left:507px;top:508px;width:1546px;height:423px;display:flex;align-items:center;gap:70px;justify-content:center;transform:scale(1.18)">
  <div style="width:250px;height:230px;flex:none">{mark_mono().replace('<svg xmlns','<svg width="250" height="230" xmlns')}</div>
  <div>{wordmark(118)}
    <div style="display:flex;gap:14px;margin-top:26px">{''.join(f'<span style="font:600 30px Plex;color:#fff;padding:8px 22px;border-radius:99px;background:rgba(255,255,255,.12);border:1.5px solid rgba(255,255,255,.25)">{t}</span>' for t in ['حلول مفصلة','رياضيات','فيزياء','آلة حاسبة'])}</div>
  </div>
</div>
<div style="position:absolute;left:0;right:0;bottom:420px;text-align:center;font:600 30px Plex;color:rgba(255,255,255,.8);direction:ltr">bacalauria.github.io/majmaa</div>'''
    page('youtube-banner', 2560, 1440, yt)
    # 4. Facebook cover 1640x624 (keep text inside the central ~1200x360 for mobile crop)
    fb = f'''{GREEN_BG}
<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;gap:56px;padding-top:10px">
  <div style="width:230px;height:212px">{mark_mono().replace('<svg xmlns','<svg width="230" height="212" xmlns')}</div>
  <div>{wordmark(112)}
  <div style="margin-top:22px;font:600 30px Plex;color:#fff;direction:ltr;text-align:right;opacity:.9">bacalauria.github.io/majmaa</div></div>
</div>'''
    page('facebook-cover', 1640, 624, fb)
    # 5. Open-Graph image for links shared from the site
    og = f'''{GREEN_BG}
<div style="position:absolute;inset:0;padding:70px 80px;display:flex;flex-direction:column;justify-content:space-between">
  <div style="display:flex;align-items:center;gap:22px"><div style="width:110px;height:101px">{mark_mono().replace('<svg xmlns','<svg width="110" height="101" xmlns')}</div><div class="t" style="font-size:52px;color:#fff">مَجْمَعُ البكالوريا</div></div>
  <div><div class="t" style="font-size:60px;line-height:1.3;color:#fff">كل مواضيع البكالوريا الجزائرية<br>و حلولها، من 1995 إلى اليوم</div>
  <div style="display:flex;gap:12px;margin-top:28px">{''.join(f'<span style="font:600 26px Plex;color:#fff;padding:6px 20px;border-radius:99px;background:{c}">{t}</span>' for t,c in [('PDF','rgba(255,255,255,.14)'),('Word','rgba(255,255,255,.14)'),('فيديو الحل','#D21034')])}</div></div>
</div>'''
    page('og-image', 1200, 630, og)
