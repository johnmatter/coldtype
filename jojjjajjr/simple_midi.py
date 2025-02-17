from coldtype import *
from coldtype.midi.controllers import midi_controller_lookup_fn
import math

fader_nums = list(range(16, 28))

canvas_aspect_ratio = 16/9
height = 1080
width = height * canvas_aspect_ratio

@animation((width, height), bg=0, rstate=1)
def simple_midi(f, rs):
    if not rs.midi:
        return (StSt(
            "No MIDI Input Detected",
            Font.RecMono(),
            60,
            align="center")
            .align(f.a.r)
            .f(1))
    
    # Try to find a working controller from our list of devices
    controller = midi_controller_lookup_fn(
        "from Max 1",
        cmc=rs.midi,
        channel="1"
    )

    # Get normalized values for each fader
    circle_radius = controller(fader_nums[0], 0.3) * 500
    x_offset = controller(fader_nums[1], 0.5) * width - width/2 # -width/2, +width/2
    y_offset = controller(fader_nums[2], 0.5) * height - height/2 # -height/2, +height/2
    hue = controller(fader_nums[3], 0.0)
    
    # Create a rectangle for the circle that's centered in the frame
    circle_rect = (Rect(circle_radius*2, circle_radius*2)  # Create rect sized for circle
        .align(f.a.r)  # Center it in the frame
        .offset(x_offset, y_offset))  # Apply the offset from sliders 2 and 3
    
    # Create the centered circle
    return (P()
        .oval(circle_rect)  # Draw circle in the centered rect
        .f(hsl(hue, 0.6, 0.5)))  # Fill with color from slider 1