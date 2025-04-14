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

apply_dither = 1 != 0
dither_kernel = list(ERROR_DIFFUSION_KERNELS.keys())[8]
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
  state = f.t.kf("eeio")
  # font_index = int(f.i%f.t.duration / f.t.duration * len(keyframes))
  font_index=2

  comp = P()

  low = bw(0.68)
  high = bw(0.11)
  comp += P(f.a.r).f(Gradient.Horizontal(f.a.r, high, low)).rotate(-162).scale(1.2).translate(-170, -523)
  comp += P(f.a.r).f(Gradient.Vertical(f.a.r, high, low))
  comp += P(f.a.r).f(Gradient.Horizontal(f.a.r, low, high)).rotate(-26).translate(0, -136).scale(1.33)
  comp.blendmode(BlendMode.Darken)


  center_bar_width = 0.50
  comp += P().rect(f.a.r
    .inset(center_bar_width*width,0)
  ).f(bw(0))

  comp += (
    StSt("COLD\nTYPE", font_names[font_index], **state, reverse=1)
    .flatten(20)
    .remove_overlap()
    .fssw(bw(1.00), bw(0.00), 27)
    .xalign()
    .mapv(lambda e, p: p.scale(1.40, 1.40))
    # .mapv(lambda e, p: p.rotate(18))
    .stack(leading)
    .scale(1.21)
    .align(f.a.r)
    .mapv(lambda e, p: p.translate(0, state["sine_offset"]*np.sin(2*np.pi*(e%4*-0.20))))
  ).translate(0, 20*np.sin(2*np.pi*f.i/f.t.duration))

  if apply_dither:
    comp = (
      comp
      .ch(
        dither(
          kernel=dither_kernel,
          threshold=2,
          matrix_size=matrix_size,
          scale=abs(max(4,3))
        ),
        f.a.r
      )
    )

  return comp

release = dither_gradient.export("h264", loops=4)