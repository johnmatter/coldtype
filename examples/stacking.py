from coldtype import *
from coldtype.text.richtext import RichText

txt = """
a few lines

Of Text [b]

right here

etaoin [h]
shrdlu [b]
"""

grafs = txt.strip().split("\n\n")

@renderable()
def stacking(r):
    def graf(txt):
        return (RichText(r, txt, lambda t, s:
            (t, Style("Trebuchet" if "h" in s else "Georgia", 150 if "b" in s else 50)))
            .f(hsl(0.7)))
        
    return (PS([
            graf(grafs[0]),
            P().oval(Rect(50, 50)).ups().f(hsl(0.07, 0.9)),
            graf(grafs[1]),
            graf(grafs[2]),
            P().oval(Rect(50, 50)).outline(10).ups().f(hsl(0.07, 0.9)),
            graf(grafs[3])
        ])
        .stack(20, zero=1)
        .map(lambda p: p
            .xalign(r)
            #.map(lambda s: s.xalign(r))
            .insert(0, P(p.ambit(th=1))
                .fssw(-1, hsl(0.3, a=0.6), 2)))
        .align(r))
