from coldtype import *
from coldtype.fx.dither import *
from coldtype.fx.skia import *
from coldtype.renderable.tools import set_ffmpeg_command

import numpy as np

set_ffmpeg_command("/opt/homebrew/bin/ffmpeg")

aspect = 16 / 9
width = 1920
height = width / aspect

leading = -203
font_names = [Font.MuSan(), Font.RecMono(), Font.ColdObvi(), Font.JBMono()]

apply_dither = True

# dither_kernel = list(ERROR_DIFFUSION_KERNELS.keys())[4]
dither_kernel = "bayer"
matrix_size = 2**3

keyframes = [
  dict(
    font_size=280,
    wdth=0.63,
    rotate=12,
    tu=166,
    sine_offset=30
  ),
  dict(font_size=280,
    wdth=1.00,
    rotate=2,
    tu=88,
    sine_offset=-24
  ),
   
  dict(font_size=280,
    wdth=0.25,
    rotate=15,
    tu=57,
    sine_offset=0
  ),
   
  dict(font_size=320,
    wdth=0.80,
    rotate=15,
    tu=0,
    sine_offset=0
  )
]

at = AsciiTimeline(8, 24, """
                <
0   1   2   3   
""", keyframes).shift("end", +10)

keyframes_dict = {str(i): kf for i, kf in enumerate(keyframes)}

@animation((width, height), timeline=at)
def dither_gradient(f:Frame):
  state = f.t.kf("eei")
  # font_index = int(f.i%f.t.duration / f.t.duration * len(keyframes))
  font_index=2

  comp = P()

  low = hsl(f.i/f.t.duration)
  high = hsl(f.i/f.t.duration+0.52)
  comp += P(f.a.r).f(Gradient.Horizontal(f.a.r, high, low)).rotate(-161).scale(1.16).translate(-170, -523)
  comp += P(f.a.r).f(Gradient.Vertical(f.a.r, high, low))
  comp += P(f.a.r).f(Gradient.Horizontal(f.a.r, low, high)).rotate(-26).translate(0, -136).scale(1.33)
  comp.blendmode(BlendMode.Darken)


  center_bar_width = f.e("eeio", rng=(0.10, 0.5))
  comp += P().rect(f.a.r
    .inset(center_bar_width*width,0)
  ).f(bw(f.e("eeio", loops=3, rng=(0.01, 1.00))))


  comp += (
    (
      StSt("COLD\nTYPE", font_names[font_index], **state, reverse=1)
      .flatten(20)
      .remove_overlap()
      .fssw(bw(1.00), bw(0.00), 30)
      .xalign()
      .mapv(lambda e, p: p.scale(1.40, 1.40))
      # .mapv(lambda e, p: p.rotate(18))
      .stack(leading)
      .scale(1.21)
      .align(f.a.r)
      .mapv(lambda e, p: p.translate(0, state["sine_offset"]*np.sin(2*np.pi*(e%4*-0.20))))
    )
    .translate(0, 20*np.sin(2*np.pi*f.i/f.t.duration))
    .mapv(lambda e, p: p.f(hsl(e/8+0.60)))
  )

  if apply_dither:

    dither_chainable = dither(
          kernel=dither_kernel,
          threshold=150,
          matrix_size=matrix_size,
          scale=15
    )

    comp_rgb = [comp.copy().ch(channel(c)) for c in range(3)]
    comp = [c.ch(dither_chainable, f.a.r).ch(luma(f.a.r, rgb(*[1 if i==ci else 0 for i in range(3)]))) for ci,c in enumerate(comp_rgb)]
    comp = P(comp).blendmode(BlendMode.Plus)

  return P(
    P().rect(f.a.r).f(bw(0)) if apply_dither else None,
    comp,
  )

release = dither_gradient.export("h264", loops=4)