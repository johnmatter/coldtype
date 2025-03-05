from coldtype import *
from coldtype.midi.controllers import midi_controller_lookup_fn
import math

fader_nums = list(range(32, 42))

canvas_aspect_ratio = 16/9
height = 1080
width = height * canvas_aspect_ratio

@animation((width, height), bg=0, rstate=1)
def simple_midi(f, rs):
    # shortcircuit if we don't see any MIDI input
    if not rs.midi:
        return (
            StSt(
                "No MIDI Input Detected",
                Font.RecMono(),
                60,
                align="center")
                .align(f.a.r)
                .f(1)
            )
    
    # Try to find a working controller from our list of devices
    controller = midi_controller_lookup_fn(
        "16n Port 1",
        cmc=rs.midi,
        channel="1"
    )

    # Get normalized values for each fader
    circle_radius = controller(fader_nums[0]) * 500
    x_offset = width*(-1/2 + controller(fader_nums[1])) # -width/2, +width/2
    y_offset = height*(-1/2 + controller(fader_nums[2])) # -height/2, +height/2
    hue = controller(fader_nums[3])
    
    # Create a rectangle to contain the circle
    circle_rect = (
            Rect(circle_radius*2, circle_radius*2)
                .align(f.a.r)
                .offset(x_offset, y_offset)
    )
    
    return (P()
        .oval(circle_rect)
        .f(hsl(hue, 0.3, 0.5))
    )
