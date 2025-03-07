from coldtype import *
from coldtype.midi.controllers import midi_controller_lookup_fn

# Running `coldtype -mi 1` will list the midi devices coldtype recognizes.
# Change the first argument of midi_controller_lookup_fn to correspond to your midi interface.
# This flag also streams input midi messages in the terminal, which you can use to
# figure out what controller numbers you need to put in `fader_nums`.
# 
# I had to create a .coldtype.py in my home directory with the names of my midi
# devices to get this to work:
#   MIDI = {
#        "16n Port 1": {
#            "channel": "1",
#            "controller": {
#            }
#        },
#        "nanoKONTROL2 SLIDER/KNOB": {
#            "channel": "1",
#            "controller": {
#            }
#        }
#   }

canvas_aspect_ratio = 16/9
height = 1080
width = height * canvas_aspect_ratio

@animation((width, height), bg=0, rstate=1)
def simple_midi(f, rs):

    # assign CC numbers
    cc_assignments = {
            "hue": 32,
            "x_offset": 33,
            "y_offset": 34,
            "radius": 35
    }

    # Get our midi controller
    controller = midi_controller_lookup_fn(
        "16n Port 1",
        cmc=rs.midi,
        channel="1"
    )

    # Declare a controller for each param
    controllers = {
            param_name: controller(cc_number)
            for param_name, cc_number in cc_assignments.items()
    }

    # Convert each fader's normalized values to interesting ranges
    circle_radius = controllers['radius'] * 500
    x_offset = width*(-1/2 + controllers['x_offset']) # -width/2, +width/2
    y_offset = height*(-1/2 + controllers['y_offset']) # -height/2, +height/2
    hue = controllers['hue']
    
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
