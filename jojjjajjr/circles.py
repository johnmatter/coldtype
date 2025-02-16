from coldtype import *
from coldtype.midi.controllers import midi_controller_lookup_fn
import math

@animation((1080, 1080), bg=0, rstate=1)
def circles(f, rs):
    if not rs.midi:
        return (StSt(
            "No MIDI Input Detected\nRun with: coldtype mine/circles.py -mi 1",
            Font.RecMono(),
            30,
            align="center")
            .align(f.a.r)
            .f(1))
        
    # Create a controller lookup function
    controller = midi_controller_lookup_fn(
        "nanoKONTROL2 SLIDER/KNOB",
        cmc=rs.midi,
        channel="1"
    )
    
    # Get values from sliders
    num_circles = int(controller(0, 0.3) * 15 + 3)  # 3 to 18 circles
    circle_radius = controller(1, 0.3) * 50  # 0 to 50 units
    path_radius = controller(2, 0.5) * 400  # 0 to 400 units
    position_rotation = controller(3, 0.0) * math.pi * 2  # 0 to 2π radians
    hue_rotation = controller(4, 0.0)  # 0 to 1 for color wheel rotation
    
    # Create the circles
    circles = []
    for i in range(num_circles):
        # Calculate position on the circular path
        angle = (i / num_circles) * math.pi * 2 + position_rotation
        x = math.cos(angle) * path_radius
        y = math.sin(angle) * path_radius
        
        # Calculate color (evenly spaced hues)
        hue = (i / num_circles + hue_rotation) % 1
        
        # Create circle at position
        circle = (P()
            .oval(Rect(circle_radius*2, circle_radius*2))
            .translate(x, y)
            .f(hsl(hue, 0.6, 0.5)))
        circles.append(circle)
    
    # Combine all circles and center in frame
    return P(circles).translate(f.a.r.w/2, f.a.r.h/2)

