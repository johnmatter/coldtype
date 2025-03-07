from coldtype import *
from coldtype.midi.controllers import midi_controller_lookup_fn
import numpy as np
import random

aspect =  16/9
height = 1024
width = height * aspect
font_size = 330

@animation((width, height), rstate=1, timeline=Timeline(120,60))
def scratch(f, rs):
    # Get our midi controller
    controller = midi_controller_lookup_fn(
        "16n Port 1",
        cmc=rs.midi,
        channel="1"
    )

    # get font
    # font_regex = "GT-Maru-Black-Trial"
    # font_regex = "GT-Super.*"
    font_regex = "GT-Flexa.*"
    font = Font.Find(font_regex)

    # assign CC numbers to and define a controller for each param
    low_cc_num = 32
    variable_font = False

    if variable_font:
        params = font.variations().keys()
    else:
        params = [
                "x",
                "y",
                "z",
                "u",
                "v",
                "w",
                "a",
                "b",
                "c",
        ]

    controllers = {
            param: controller(cc)
            for param, cc in zip(params, range(low_cc_num, low_cc_num+len(params)))
    }

    # print(len(params))

    text_pairs = ["jo", "jj", "ja", "jj", "r"]
    
    # Create a grid of StSt objects
    cols = 3
    rows = 3
    col_spacing = 500
    row_spacing = 320
    
    grid = []
    for col in range(cols):
        for row in range(rows):
            syllable = text_pairs[(col+row+5)%len(text_pairs)]
            norm_x = float(row) / cols;
            norm_y = float(col) / len(text_pairs);
            st = (
                StSt(
                    syllable.upper(),
                    font_regex,
                    font_size*f.e("eeo", rng=(0.7, 0.8)),
                    width=controllers['w']
                    # **controllers
                )
                .layer(1)
                .offset(
                    (col - 1) * col_spacing,
                    (1.5 - row) * row_spacing
                )
                .rotate(0*(0.1+norm_x)+2*(np.cos(norm_y)+np.sin(norm_x*2+0.2))*controllers['z']*f.e("eeo"))
                .f(hsl(
                        (
                            0.1*np.tan(10*controllers['z']) +
                            np.cos(np.pi * (
                                norm_y*controllers['x']
                                )
                            ) * 
                            np.cos(np.pi * (
                                norm_x*controllers['y']
                                )
                            )
                        ) % 1.0,
                        controllers['u'], # 0.54,
                        controllers['v'] # 0.62
                    )
                )
            )
            grid.append(st)
    
    # Combine all StSt objects and center the entire composition

    p2 = P(Rect(width,height)).f(hsl(controllers['w'],controllers['a'],controllers['b'])).align(f.a.r, "C")
    p = P(*grid).align(f.a.r, "C")

    return (p2,p)
