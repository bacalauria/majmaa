"""Brand kit v2 — logo 4 «الاسم وحده»: Reem Kufi wordmark, gold rule, red dot.
Deep green #0B4D2E, cream #FBF8F1, gold #C9A24A, flag red #D21034."""
import math
GREEN, DEEP, CREAM, GOLD, RED = '#0B4D2E', '#073821', '#FBF8F1', '#C9A24A', '#D21034'
S, cx, cy, D = open('mim-path.txt').read().split('|', 3); S, cx, cy = float(S), float(cx), float(cy)

def mim(size, fill=CREAM, bg=GREEN, rx=112, dot=True):
    rect = f'<rect width="512" height="512" rx="{rx}" fill="{bg}"/>' if bg else ''
    extra = (f'<path d="M176 420H336" stroke="{GOLD}" stroke-width="8" stroke-linecap="round"/>'
             f'<circle cx="256" cy="420" r="16" fill="{RED}"/>') if dot else ''
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="{size}" height="{size}">{rect}'
            f'<g transform="translate(256 236) scale({S:.4f} {-S:.4f}) translate({-cx:.1f} {-cy:.1f})"><path d="{D}" fill="{fill}"/></g>{extra}</svg>')

def zellige(color, op, s=96):
    c = s/2; a = s*.25; d = a*math.sqrt(2)
    return (f'<pattern id="z" width="{s}" height="{s}" patternUnits="userSpaceOnUse"><g fill="none" stroke="{color}" stroke-opacity="{op}" stroke-width="1.3">'
            f'<path d="M{c-a},{c-a}H{c+a}V{c+a}H{c-a}Z"/><path d="M{c},{c-d}L{c+d},{c}L{c},{c+d}L{c-d},{c}Z"/>'
            f'<path d="M0,0L{c-a},{c-a}M{s},0L{c+a},{c-a}M0,{s}L{c-a},{c+a}M{s},{s}L{c+a},{c+a}M{c},0V{c-d}M{c},{s}V{c+d}M0,{c}H{c-d}M{s},{c}H{c+d}"/></g></pattern>')

HEAD = '''<!doctype html><meta charset="utf-8"><style>
@font-face{font-family:RK;src:url(reem-kufi-var.woff);font-weight:400 700}
@font-face{font-family:EM;src:url(el-messiri-var.woff);font-weight:400 700}
@font-face{font-family:TJ;src:url(tajawal-Regular.woff);font-weight:400}
@font-face{font-family:TJ;src:url(tajawal-Bold.woff);font-weight:700}
*{margin:0;box-sizing:border-box}body{direction:rtl;font-family:TJ;-webkit-font-smoothing:antialiased;position:relative}
.wm{font-family:RK;font-weight:700;line-height:1.05;color:%s}
.rule{display:flex;align-items:center;gap:0}.rule i{height:3px;background:%s;flex:1}.rule b{width:14px;height:14px;border-radius:50%%;background:%s;margin:0 -2px}
</style>''' % (CREAM, GOLD, RED)

def green_bg():
    return (f'<svg style="position:absolute;inset:0;width:100%;height:100%"><defs>{zellige("#FFFFFF", .06)}'
            f'<radialGradient id="g" cx=".75" cy=".15" r="1"><stop offset="0" stop-color="#11683F"/><stop offset=".55" stop-color="{GREEN}"/><stop offset="1" stop-color="{DEEP}"/></radialGradient></defs>'
            f'<rect width="100%" height="100%" fill="url(#g)"/><rect width="100%" height="100%" fill="url(#z)"/></svg>')

def lockup(fs, tag=True, color=CREAM, sub='rgba(251,248,241,.78)'):
    """Two-line wordmark: مَجْمَعُ / البكالوريا, gold rule with the red dot, then the archive span."""
    t = (f'<div style="text-align:center"><div class="wm" style="font-size:{fs*1.25}px;color:{color}">مَجْمَعُ</div>'
         f'<div class="wm" style="font-size:{fs*.86}px;color:{color};margin-top:{fs*.02}px">البكالوريا</div>'
         f'<div class="rule" style="width:{fs*3}px;margin:{fs*.3}px auto {fs*.22}px"><i></i><b style="width:{fs*.16}px;height:{fs*.16}px"></b><i></i></div>')
    if tag: t += f'<div style="font:400 {fs*.3}px TJ;letter-spacing:.06em;color:{sub}">كل ما يحتاجه طالب البكالوريا، في مكان واحد</div>'
    return t + '</div>'

def page(name, w, h, body, bg='transparent'):
    open(name + '.html', 'w').write(HEAD + f'<style>html,body{{width:{w}px;height:{h}px;background:{bg};overflow:hidden}}</style>' + body)

if __name__ == '__main__':
    open('logo-icon.svg', 'w').write(mim(512))
    page('logo-icon', 1024, 1024, mim(1024, rx=0) .replace('rx="0"', 'rx="0"'))
    page('avatar', 800, 800, mim(800, rx=0))
    # wordmark on light and on dark
    page('logo-wordmark', 1400, 900, f'<div style="position:absolute;inset:0;display:grid;place-items:center">{lockup(150, True, GREEN, "#6B7A70")}</div>')
    page('logo-wordmark-dark', 1400, 900, f'<div style="position:absolute;inset:0;display:grid;place-items:center">{lockup(150)}</div>', DEEP)
    # YouTube banner 2560x1440 — safe area 1546x423 centred (y 508..931)
    page('youtube-banner', 2560, 1440, green_bg() + f'''<div style="position:absolute;left:507px;top:508px;width:1546px;height:423px;display:grid;place-items:center">{lockup(104)}</div>
    <div style="position:absolute;left:0;right:0;top:948px;display:flex;justify-content:center;gap:16px">{''.join(f'<span style="font:700 30px TJ;color:{CREAM};padding:8px 24px;border-radius:99px;border:1.5px solid rgba(201,162,74,.6)">{t}</span>' for t in ['مواضيع و حلول','دروس و ملخصات','بكالوريا أجنبية','أولمبياد','سلاسل فيديو'])}</div>''')
    # Facebook cover 1640x624
    page('facebook-cover', 1640, 624, green_bg() + f'<div style="position:absolute;inset:0;display:grid;place-items:center">{lockup(92)}</div>')
    # Open Graph 1200x630
    page('og-image', 1200, 630, green_bg() + f'''<div style="position:absolute;inset:0;padding:64px 76px;display:flex;flex-direction:column;justify-content:space-between">
    <div class="wm" style="font-size:60px">مَجْمَعُ البكالوريا</div>
    <div><div style="font:700 62px/1.3 EM;color:{CREAM}">كل ما يحتاجه طالب البكالوريا<br>في مكان واحد</div>
    <div class="rule" style="width:340px;margin-top:26px"><i></i><b></b><i></i></div></div></div>''')
