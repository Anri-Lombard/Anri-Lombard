"""Builds the profile SVGs into assets/.

    python art/build.py          # everything (needs GH_TOKEN or a logged-in `gh`)
    python art/build.py daily    # just the data-driven pieces (what the daily Action runs)

Every piece comes in a light (Hulk, daytime) and dark (Loki, night) variant.
"""
import json
import math
import os
import random
import subprocess
import sys
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets"
USER = "Anri-Lombard"

THEMES = {
    "light": dict(bg="#ffffff", ink="#1f2328", muted="#656d76", accent="#1a7f37", signal="#2da44e",
                  term_bg="#f6f8fa", border="#d0d7de", err="#cf222e", ok="#1a7f37", flash="#ffffff", sheen="#ffffff",
                  cells=["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]),
    "dark": dict(bg="#0d1117", ink="#e6edf3", muted="#8b949e", accent="#e3b341", signal="#e3b341",
                 term_bg="#161b22", border="#30363d", err="#f85149", ok="#3fb950", flash="#fff4c2", sheen="#fffbe6",
                 cells=["#161b22", "#2d2145", "#4b2d7f", "#8250df", "#e3b341"]),
}
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
# Reduced motion: stop everything and hide what only makes sense mid-animation.
STILL = "@media (prefers-reduced-motion: reduce) { * { animation: none !important; } .moving { display: none; } }"

BUG = """<g id="bug" transform="scale(.75)">
  <path d="M20 30 L10 24 M20 36 L8 36 M20 42 L10 50 M44 30 L54 24 M44 36 L56 36 M44 42 L54 50 M27 14 L22 6 M37 14 L42 6" stroke="#3b2a4d" stroke-width="3" stroke-linecap="round" fill="none"/>
  <ellipse cx="32" cy="38" rx="14" ry="17" fill="#6d3fa0"/><path d="M32 22 V55" stroke="#3b2a4d" stroke-width="2"/>
  <circle cx="32" cy="19" r="8" fill="#3b2a4d"/><circle cx="29" cy="18" r="2.2" fill="#f5c542"/><circle cx="35" cy="18" r="2.2" fill="#f5c542"/>
  <circle cx="26" cy="34" r="2.5" fill="#f5c542"/><circle cx="38" cy="42" r="2.5" fill="#f5c542"/><circle cx="27" cy="46" r="2" fill="#f5c542"/>
</g>"""

# Fist in local coords: knuckles span x 4..60, bottom at y 60, torn purple cuff above y 0.
FIST = """<rect x="10" y="-36" width="44" height="34" rx="4" fill="#6d3fa0"/>
<path d="M10 -4 l6 6 l6 -6 l6 6 l6 -6 l6 6 l6 -6 l8 6 v-4 h-44 z" fill="#4a2a70"/>
<rect x="4" y="4" width="56" height="56" rx="14" fill="#5a9e3a"/>
<path d="M18 12 v18 M32 12 v18 M46 12 v18" stroke="#3f7a26" stroke-width="3" stroke-linecap="round"/>
<rect x="4" y="34" width="22" height="18" rx="8" fill="#6bb347"/>"""


def svg(w, h, css, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">\n'
            f"<style>\n{css}\n{STILL}\n</style>\n<defs>{defs}</defs>\n{body}\n</svg>\n")


def pct(s, T):
    return round(s / T * 100, 2)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------- signature
# Monoline letters on a 60-tall grid: (path, advance width).
GLYPHS = {
    "A": ("M0 60 L20 0 L40 60 M8 38 H32", 40),
    "N": ("M0 60 V0 L40 60 V0", 40),
    "R": ("M0 60 V0 H24 A15 15 0 0 1 24 30 H0 M20 30 L40 60", 40),
    "I": ("M4 0 H28 M16 0 V60 M4 60 H28", 32),
    "L": ("M0 0 V60 H36", 36),
    "O": ("M20 0 A20 30 0 0 1 20 60 A20 30 0 0 1 20 0", 40),
    "M": ("M0 60 V0 L20 36 L40 0 V60", 40),
    "B": ("M0 60 V0 H22 A14 14 0 0 1 22 28 H0 M22 28 A16 16 0 0 1 22 60 H0", 40),
    "D": ("M0 0 V60 H14 A26 30 0 0 0 14 0 Z", 40),
    " ": ("", 20),
}


def signature(t, theme):
    name, gap, W = "ANRI LOMBARD", 16, 760
    width = sum(GLYPHS[c][1] for c in name) + gap * (len(name) - 1)
    x, paths, masks, n = (W - width) / 2, [], [], 0
    for c in name:
        d, adv = GLYPHS[c]
        if d:
            paths.append(f'<path d="{d}" pathLength="1" transform="translate({x:.1f},24)" style="animation-delay:{n * .13:.2f}s"/>')
            masks.append(f'<path d="{d}" transform="translate({x:.1f},24)"/>')
            n += 1
        x += adv + gap
    neon = theme == "dark"
    css = f"""
.s path {{ fill: none; stroke: {t['accent']}; stroke-width: 4.5; stroke-linecap: round; stroke-linejoin: round;
  stroke-dasharray: 1; animation: draw 1s cubic-bezier(.6,0,.3,1) both; }}
@keyframes draw {{ from {{ stroke-dashoffset: 1; }} to {{ stroke-dashoffset: 0; }} }}
.tag {{ font: 500 17px {MONO}; fill: {t['muted']}; animation: rise 1s 2.1s both; }}
@keyframes rise {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: none; }} }}
.sheen {{ transform: translateX(-260px); animation: sheen 8s 2.6s cubic-bezier(.45,0,.2,1) infinite; }}
@keyframes sheen {{ 0% {{ transform: translateX(-260px); }} 22%,100% {{ transform: translateX({W + 60}px); }} }}
.flicker {{ animation: flicker 9s 3.5s infinite; }}
@keyframes flicker {{ 0%,6%,100% {{ opacity: 1; }} 1% {{ opacity: .35; }} 2% {{ opacity: 1; }} 3.5% {{ opacity: .55; }} 4.5% {{ opacity: 1; }} }}"""
    defs = (f'<linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="{t["sheen"]}" stop-opacity="0"/>'
            f'<stop offset=".5" stop-color="{t["sheen"]}" stop-opacity=".9"/><stop offset="1" stop-color="{t["sheen"]}" stop-opacity="0"/></linearGradient>'
            f'<mask id="m" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="100"><g fill="none" stroke="#fff" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round">{"".join(masks)}</g></mask>')
    if neon:
        defs += ('<filter id="glow" x="-10%" y="-60%" width="120%" height="220%"><feGaussianBlur stdDeviation="3.2" result="b"/>'
                 '<feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    attrs = ' class="s flicker" filter="url(#glow)"' if neon else ' class="s"'
    body = (f'<g{attrs}>{"".join(paths)}</g>\n'
            f'<g mask="url(#m)"><rect class="sheen moving" x="0" y="0" width="200" height="100" fill="url(#g)" transform="skewX(-20)"/></g>\n'
            f'<text class="tag" x="{W / 2}" y="132" text-anchor="middle">I do to bugs what Hulk does to Loki.</text>')
    return svg(W, 150, css, body, defs)


# ---------------------------------------------------------------- terminal
TERM_LINES = [  # (start seconds, typing seconds (0 = printed instantly), class, text)
    (0.5, .7, "cmd", "$ whoami"),
    (1.5, 0, "out", "Anri Lombard - engineer and researcher in AI and software development"),
    (2.6, .6, "cmd", "$ pytest"),
    (3.4, 0, "err", "✗ 3 failed"),
    (6.0, .6, "cmd", "$ pytest"),
    (6.8, 0, "ok", "✓ 128 passed in 0.42s"),
    (7.9, 1.0, "cmd", "$ cat links.txt"),
    (8.9, 0, "out", "linkedin.com/in/anri-lombard-ab37ab201"),
    (9.1, 0, "out", "anri-lombard.vercel.app"),
    (9.9, 0, "cmd", "$"),
]
TERM_T, CHAR_W = 16, 8.6


def typing_keyframes(i, text, start, dur, T):
    """Cover slides off one character at a time with human, uneven gaps."""
    rng = random.Random(i)
    gaps = [rng.uniform(.5, 1.7) for _ in text]
    scale = dur / sum(gaps)
    stops, s = [f"0%,{pct(start, T)}% {{ transform: translateX(0); }}"], start
    for k, g in enumerate(gaps, 1):
        s += g * scale
        stops.append(f"{pct(s, T)}% {{ transform: translateX({k * CHAR_W:.1f}px); }}")
    stops.append(f"100% {{ transform: translateX({len(text) * CHAR_W:.1f}px); }}")
    return f"@keyframes c{i} {{ {' '.join(stops)} }} .c{i} {{ animation: c{i} {T}s step-end infinite; }}"


def terminal(t, theme):
    W, T, top, lh = 760, TERM_T, 66, 25
    H = top + lh * len(TERM_LINES) - 4
    css = [f"""
.cmd {{ fill: {t['ink']}; }} .out {{ fill: {t['muted']}; }} .err {{ fill: {t['err']}; }} .ok {{ fill: {t['ok']}; }}
text {{ font: 14px {MONO}; white-space: pre; }}
.title {{ font: 12px {SANS}; fill: {t['muted']}; }}
.wig {{ transform-box: fill-box; transform-origin: center; animation: wig .9s ease-in-out infinite; }}
@keyframes wig {{ 0%,100% {{ transform: rotate(-12deg); }} 50% {{ transform: rotate(12deg) translateY(-1px); }} }}
.blink {{ animation: blink 1s steps(1) infinite; }} @keyframes blink {{ 50% {{ opacity: 0; }} }}"""]
    body = [f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="10" fill="{t["term_bg"]}" stroke="{t["border"]}"/>',
            f'<path d="M1 36 H{W - 1}" stroke="{t["border"]}"/>',
            '<circle cx="22" cy="18" r="6" fill="#ff5f57"/><circle cx="42" cy="18" r="6" fill="#febc2e"/><circle cx="62" cy="18" r="6" fill="#28c840"/>',
            f'<text class="title" x="{W / 2}" y="22" text-anchor="middle">anri@hulk: ~</text>']
    for i, (s, typing, cls, text) in enumerate(TERM_LINES):
        y, on = top + i * lh, pct(s, T)
        css.append(f"@keyframes o{i} {{ 0%,{on}% {{ opacity: 0; }} {on + .1}%,96% {{ opacity: 1; }} 99%,100% {{ opacity: 0; }} }} .o{i} {{ animation: o{i} {T}s linear infinite; }}")
        line = f'<g class="o{i}"><text class="{cls}" x="22" y="{y}">{esc(text)}</text>'
        if typing:
            w = len(text) * CHAR_W + 6
            css.append(typing_keyframes(i, text, s, typing, T))
            line += f'<rect class="c{i} moving" x="20" y="{y - 15}" width="{w:.0f}" height="21" fill="{t["term_bg"]}"/>'
        if text == "$":
            line += f'<rect class="blink" x="{22 + 2 * CHAR_W}" y="{y - 13}" width="8" height="17" fill="{t["accent"]}"/>'
        if cls == "err":
            line += chomp(t, css, text, y, T)
        body.append(line + "</g>")
    return svg(W, H, "\n".join(css), "\n".join(body), BUG)


def chomp(t, css, text, y, T):
    """The cursor races along the failing line and eats the three bugs, then the failure gets struck out."""
    bx, by, gap = 22 + (len(text) + 2) * CHAR_W, y - 21, 26
    start, end = 22 + len(text) * CHAR_W + 4, bx + 2 * gap + 30
    t0, bites = 4.0, [4.45, 4.85, 5.25]
    out = []
    for k, bite in enumerate(bites):
        b = pct(bite, T)
        css.append(f"@keyframes eat{k} {{ 0%,{b - .6}% {{ transform: scale(1); }} {b - .3}% {{ transform: scale(1.25) rotate(8deg); }} {b}%,100% {{ transform: scale(0); }} }}"
                   f".eat{k} {{ transform-box: fill-box; transform-origin: center; animation: eat{k} {T}s ease-in infinite; }}"
                   f"@keyframes pop{k} {{ 0%,{b}% {{ opacity: 0; transform: scale(.2); }} {b + .2}% {{ opacity: 1; }} {b + 3}%,100% {{ opacity: 0; transform: scale(1.8); }} }}"
                   f".pop{k} {{ transform-box: fill-box; transform-origin: center; animation: pop{k} {T}s ease-out infinite; }}")
        cx = bx + k * gap
        out.append(f'<g transform="translate({cx:.0f},{by}) scale(.5)"><g class="eat{k}"><g class="wig" style="animation-delay:-{k * .3}s"><use href="#bug"/></g></g></g>'
                   f'<circle class="pop{k} moving" cx="{cx + 12:.0f}" cy="{by + 12}" r="7" fill="none" stroke="{t["accent"]}" stroke-width="1.5"/>')
    # cursor: appears, lunges from bite to bite (slight stretch while moving), then dashes off
    stops = [f"0%,{pct(t0, T)}% {{ opacity: 0; transform: translateX(0); }}", f"{pct(t0 + .1, T)}% {{ opacity: 1; transform: translateX(0); }}"]
    for k, bite in enumerate(bites):
        x = bx + k * gap - start + 4
        stops += [f"{pct(bite - .12, T)}% {{ opacity: 1; transform: translateX({x - 6:.0f}px) scaleX(1.6); }}",
                  f"{pct(bite, T)}% {{ opacity: 1; transform: translateX({x:.0f}px) scaleX(1); }}"]
    stops += [f"{pct(5.6, T)}% {{ opacity: 1; transform: translateX({end - start:.0f}px); }}",
              f"{pct(5.75, T)}%,100% {{ opacity: 0; transform: translateX({end - start:.0f}px); }}"]
    css.append(f"@keyframes cur {{ {' '.join(stops)} }} .cur {{ transform-box: fill-box; transform-origin: left; animation: cur {T}s cubic-bezier(.5,0,.3,1) infinite; }}"
               f"@keyframes strike {{ 0%,{pct(5.4, T)}% {{ stroke-dashoffset: 1; }} {pct(5.8, T)}%,100% {{ stroke-dashoffset: 0; }} }}"
               f".strike {{ stroke-dasharray: 1; animation: strike {T}s ease-out infinite; }}")
    out.append(f'<rect class="cur moving" x="{start:.0f}" y="{y - 13}" width="9" height="17" fill="{t["accent"]}"/>')
    out.append(f'<path class="strike" d="M20 {y - 5} H{22 + len(text) * CHAR_W + 2:.0f}" pathLength="1" stroke="{t["err"]}" stroke-width="1.5"/>')
    return "".join(out)


# ---------------------------------------------------------------- data
LEVELS = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]


def fetch():
    token = os.environ.get("GH_TOKEN") or subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()
    q = ('{ user(login: "%s") {'
         ' contributionsCollection { contributionCalendar { weeks { contributionDays { contributionCount contributionLevel weekday date } } } }'
         ' } }') % USER
    req = urllib.request.Request("https://api.github.com/graphql", json.dumps({"query": q}).encode(),
                                 {"Authorization": f"bearer {token}", "Content-Type": "application/json"})
    user = json.load(urllib.request.urlopen(req))["data"]["user"]
    return [w["contributionDays"] for w in user["contributionsCollection"]["contributionCalendar"]["weeks"]]


# ---------------------------------------------------------------- contribution graph
def graph(t, theme, weeks, hits_n=6):
    cell, gap, x0, y0, T = 12, 3, 20, 84, 15
    step = cell + gap
    W, H = x0 * 2 + len(weeks) * step - gap, y0 + 7 * step + 26
    days = [(wi, d) for wi, w in enumerate(weeks) for d in w]
    targets = sorted(sorted(days, key=lambda wd: (-wd[1]["contributionCount"], wd[1]["date"]))[:hits_n], key=lambda wd: wd[1]["date"])
    hits = [(wi, d["weekday"], pct(1.4 + i * 2.1, T)) for i, (wi, d) in enumerate(targets)]
    total = sum(d["contributionCount"] for _, d in days)
    pos = lambda wi, wd: (x0 + wi * step, y0 + wd * step)
    css = [".c { transform-box: fill-box; transform-origin: center bottom; }",
           f".note {{ font: 12px {SANS}; fill: {t['muted']}; }}"]

    # Shockwave: every cell within R of an impact hops, later and smaller the further out it is.
    R, rects = 8, []
    for n, (wi, d) in enumerate(days):
        x, y = pos(wi, d["weekday"])
        stops = []
        for hx, hy, h in hits:
            dist = math.hypot(wi - hx, d["weekday"] - hy)
            if 0 < dist <= R:
                a, off = round(5 * (1 - dist / R) + .6, 1), dist * .045 / T * 100
                stops += [f"{h + off:.2f}% {{ transform: none; }}", f"{h + off + .45:.2f}% {{ transform: translateY(-{a}px) scaleY(1.12); }}",
                          f"{h + off + 1.3:.2f}% {{ transform: none; }}"]
        cls = ""
        if stops:
            css.append(f"@keyframes q{n} {{ {' '.join(stops)} }} .q{n} {{ animation: q{n} {T}s ease-out infinite; }}")
            cls = f' class="c q{n}"'
        rects.append(f'<rect{cls} x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2.5" fill="{t["cells"][LEVELS.index(d["contributionLevel"])]}"/>')

    # Fist: wind-up (rise + lean back), stretched fall, squashed impact, rebound.
    fist_kf, shake_kf, fx = [], [], []
    for i, (hx, hy, h) in enumerate(hits):
        x, y = pos(hx, hy)
        cx, cy = x + cell / 2, y + cell / 2
        tf = lambda sx, sy, dy, rot=0: f"transform: translate({cx - 32 * sx:.1f}px,{dy:.1f}px) rotate({rot}deg) scale({sx},{sy});"
        fist_kf += [f"{h - 6.5:.2f}% {{ {tf(.5, .5, 8)} animation-timing-function: cubic-bezier(.3,0,.2,1); }}",
                    f"{h - 3:.2f}% {{ {tf(.5, .5, -4, -14)} animation-timing-function: cubic-bezier(.8,0,1,.6); }}",
                    f"{h - .5:.2f}% {{ {tf(.44, .6, y - 36 * .6 - 14, 4)} animation-timing-function: linear; }}",
                    f"{h:.2f}% {{ {tf(.58, .42, y - 60 * .42 + 1)} animation-timing-function: ease-out; }}",
                    f"{h + 1.6:.2f}% {{ {tf(.48, .52, y - 60 * .52 - 10)} }}",
                    f"{h + 4:.2f}% {{ {tf(.5, .5, 8)} }}"]
        shake_kf += [f"{h}% {{ transform: none; }}", f"{h + .4:.2f}% {{ transform: translate(0,3px); }}",
                     f"{h + .9:.2f}% {{ transform: translate(-2px,-1px); }}", f"{h + 1.5:.2f}% {{ transform: none; }}"]
        css.append(f"@keyframes f{i} {{ 0%,{h}% {{ opacity: 0; }} {h + .3:.2f}% {{ opacity: 1; }} {h + 6:.2f}%,100% {{ opacity: 0; }} }} .f{i} {{ animation: f{i} {T}s linear infinite; }}"
                   f"@keyframes r{i} {{ 0%,{h}% {{ opacity: 0; transform: scale(.3); }} {h + .3:.2f}% {{ opacity: 1; }} {h + 7:.2f}%,100% {{ opacity: 0; transform: scale(5); }} }}"
                   f".r{i} {{ transform-box: fill-box; transform-origin: center; animation: r{i} {T}s cubic-bezier(.1,.6,.3,1) infinite; }}"
                   f"@keyframes k{i} {{ 0%,{h}% {{ opacity: 0; }} {h + .3:.2f}%,95% {{ opacity: 1; }} 99%,100% {{ opacity: 0; }} }} .k{i} {{ animation: k{i} {T}s linear infinite; }}"
                   f"@keyframes l{i} {{ 0%,{h - 1.2:.2f}% {{ opacity: 0; transform: translateY(-10px); }} {h - .5:.2f}% {{ opacity: .8; }} {h + .6:.2f}%,100% {{ opacity: 0; transform: translateY(4px); }} }}"
                   f".l{i} {{ animation: l{i} {T}s linear infinite; }}")
        # dust kicked up sideways from the impact
        dust = []
        for k, (dx, dy) in enumerate([(-16, -10), (-9, -17), (9, -17), (16, -10), (0, -20)]):
            css.append(f"@keyframes d{i}{k} {{ 0%,{h}% {{ opacity: 0; transform: none; }} {h + .3:.2f}% {{ opacity: 1; }} {h + 4.5:.2f}%,100% {{ opacity: 0; transform: translate({dx}px,{dy}px) scale(.3); }} }}"
                       f".d{i}{k} {{ transform-box: fill-box; transform-origin: center; animation: d{i}{k} {T}s cubic-bezier(.1,.7,.3,1) infinite; }}")
            dust.append(f'<circle class="d{i}{k} moving" cx="{cx}" cy="{y}" r="2.2" fill="{t["accent"]}"/>')
        fx.append(f'<rect class="f{i} moving" x="{x - 1}" y="{y - 1}" width="{cell + 2}" height="{cell + 2}" rx="3" fill="{t["flash"]}"/>'
                  f'<path class="k{i}" d="M{cx - 5} {cy - 5} L{cx - 1} {cy - 1} L{cx - 2} {cy + 3} L{cx + 4} {cy + 6} M{cx - 1} {cy - 1} L{cx + 5} {cy - 3}" stroke="{t["bg"]}" stroke-width="1.4" fill="none" stroke-linecap="round"/>'
                  f'<circle class="r{i} moving" cx="{cx}" cy="{cy}" r="7" fill="none" stroke="{t["accent"]}" stroke-width="1.5"/>'
                  + "".join(dust) +
                  f'<path class="l{i} moving" d="M{cx - 11} {y - 34} v12 M{cx} {y - 42} v16 M{cx + 11} {y - 34} v12" stroke="{t["muted"]}" stroke-width="1.5" stroke-linecap="round"/>')
    x_first = pos(hits[0][0], hits[0][1])[0] + cell / 2 - 16
    rest = f"transform: translate({x_first}px,8px) rotate(0deg) scale(.5,.5);"
    css.append(f"@keyframes fist {{ 0% {{ {rest} }} {' '.join(fist_kf)} 100% {{ {rest} }} }} .fist {{ {rest} animation: fist {T}s infinite; }}"
               f"@keyframes shake {{ 0%,100% {{ transform: none; }} {' '.join(shake_kf)} }} .grid {{ animation: shake {T}s linear infinite; }}")
    body = (f'<g class="grid">{"".join(rects)}{"".join(fx)}</g>'
            f'<text class="note" x="{W - x0}" y="{H - 6}" text-anchor="end">{total:,} bugs smashed in the last year</text>'
            f'<g class="fist">{FIST}</g>')
    return svg(W, H, "\n".join(css), body)


# ---------------------------------------------------------------- link buttons
def button(t, theme, label):
    W, H = 168, 40
    css = f"text {{ font: 600 14px {SANS}; fill: {t['ink']}; }}"
    body = (f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="20" fill="{t["term_bg"]}" stroke="{t["border"]}"/>'
            f'<circle cx="24" cy="20" r="4" fill="{t["accent"]}"/>'
            f'<text x="{W / 2 + 8}" y="25" text-anchor="middle">{label} ↗</text>')
    return svg(W, H, css, body)


def main():
    OUT.mkdir(exist_ok=True)
    daily = sys.argv[1:] == ["daily"]
    weeks = fetch()
    for theme, t in THEMES.items():
        files = {f"graph-{theme}.svg": graph(t, theme, weeks)}
        if not daily:
            files |= {f"signature-{theme}.svg": signature(t, theme), f"terminal-{theme}.svg": terminal(t, theme),
                      f"btn-linkedin-{theme}.svg": button(t, theme, "LinkedIn"),
                      f"btn-contact-{theme}.svg": button(t, theme, "Get in touch")}
        for name, content in files.items():
            (OUT / name).write_text(content)
    print("built", sorted(p.name for p in OUT.glob("*.svg")))


if __name__ == "__main__":
    main()
