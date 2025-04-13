from coldtype import *
from coldtype.fx.dither import *
from coldtype.fx.skia import *
from coldtype.renderable.tools import set_ffmpeg_command

import numpy as np

set_ffmpeg_command("/opt/homebrew/bin/ffmpeg")

aspect = 16 / 9
width = 1920
height = width / aspect

tracking = 44
leading = -203
font_size = 280
# font = Font.MuSan()
# font = Font.RecMono()
# font = Font.JBMono()
font = Font.ColdObvi()


apply_dither = 1 != 0
dither_kernel = list(ERROR_DIFFUSION_KERNELS.keys())[8]

@animation((width, height), timeline=Timeline(90,30))
def dither_gradient(f:Frame):

  comp = P()

  low = bw(0.44)
  high = bw(0.00)
  comp += P(f.a.r).f(Gradient.Vertical(f.a.r, low, high))
  comp += P(f.a.r).f(Gradient.Vertical(f.a.r, high, low))
  comp.blendmode(BlendMode.Darken)


  center_bar_width = 0.23
  comp += P().rect(f.a.r
    .inset(center_bar_width*width,0)
  ).f(bw(0))

  comp += (
    StSt("COLD\nTYPE", font, font_size,
      tu=tracking,
      wdth=1.00,
      reverse=1
    )
    .flatten(20)
    .remove_overlap()
    .fssw(bw(1.00), bw(0.00), 27)
    .xalign()
    .mapv(lambda e, p: p.scale(1.40, 1.40))
    .stack(leading)
    .scale(1.21)
    .align(f.a.r)
  ).mapv(lambda e, p: p.translate(0, 100*np.sin(2*np.pi*(e%4*0.1 + f.i/f.t.duration))))

  if apply_dither:
    comp = (
      comp
      .ch(
        dither(
          kernel=dither_kernel,
          threshold=2,
          scale=abs(max(12.71,3))
        ),
        f.a.r
      )
    )

  return comp

release = dither_gradient.export("h264", loops=4)