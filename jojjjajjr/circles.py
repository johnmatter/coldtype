from coldtype import *
from coldtype.midi.controllers import midi_controller_lookup_fn
import math
import random

@animation((1080, 1080), bg=0, rstate=1, timeline=1200)
def circles(f, rs):
    if not rs.midi:
        return (StSt(
            "No MIDI Input Detected",
            Font.MutatorSans(),
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
    
    # Get values from sliders for circles
    num_circles = int(controller(0, 0.3) * 15 + 3)  # 3 to 18 circles
    circle_radius = controller(1, 0.3) * 250  # 0 to 250 units
    max_path_radius = controller(2, 0.5) * 1000  # 0 to 400 units
    rotation_speed = controller(3, 0.0) * 0.4 - 0.2
    hue_rotation = controller(4, 0.0)  # 0 to 1 for color wheel rotation
    num_rings = int(controller(17, 0.3) * 5 + 1)  # 1 to 6 rings
    
    # Get values from sliders for text wave
    wave_amplitude = controller(5, 0.3) * 5  # 0 to 5 for font weight range
    wave_phase = controller(6, 0.0) * math.pi * 2  # 0 to 2π radians
    wave_frequency = controller(7, 0.5) * 2 + 0.5  # 0.5 to 2.5 Hz
    vertical_amplitude = controller(16, 0.3) * 1000  # 0 to 100 units for vertical movement
    
    # Create random parameters for each ring if they don't exist
    if not hasattr(circles, 'ring_params'):
        circles.ring_params = []
        for _ in range(10):  # Pre-generate for up to 10 rings
            circles.ring_params.append({
                'direction': random.choice([-0.1, 0.1]),  # Random direction
                'frequency': random.uniform(1, 5),  # Random speed multiplier
                'base_phase': random.uniform(0, math.pi * 2)  # Initial phase offset
            })
    
    # Create the circles for each ring
    circles_list = []
    for ring in range(num_rings):
        # Calculate this ring's radius as a fraction of max_path_radius
        ring_radius = max_path_radius * (ring + 1) / num_rings
        
        # Get this ring's rotation parameters
        params = circles.ring_params[ring]
        # Calculate continuous rotation based on frame
        ring_rotation = (
            params['base_phase'] + 
            (f.i/60) * math.pi * 2 * rotation_speed * params['frequency'] * params['direction']
        )
        
        for i in range(num_circles):
            # Calculate position on the circular path
            angle = (i / num_circles) * math.pi * 2 + ring_rotation
            x = math.cos(angle) * ring_radius
            y = math.sin(angle) * ring_radius
            
            # Calculate color (evenly spaced hues, vary by ring and position)
            hue = ((i / num_circles) + (ring / num_rings) + hue_rotation) % 1
            
            # Create circle at position
            circle = (P()
                .oval(Rect(circle_radius*2, circle_radius*2))
                .translate(x, y)
                .f(hsl(hue, 0.6, 0.5)))
            circles_list.append(circle)
    
    # Create undulating text using Glyphwise
    def wave_style(g):
        # Wave for font weight
        weight_wave = math.sin(wave_frequency * g.i + wave_phase + f.i/100)
        weight = (weight_wave + 1) / 2 * wave_amplitude
        
        # Wave for vertical position (offset phase by π/2 for interesting motion)
        position_wave = math.sin(wave_frequency * g.i + wave_phase + f.i/100 + math.pi/2)
        vertical_offset = position_wave * vertical_amplitude
        
        return Style(
            Font.MutatorSans(),
            450,
            wght=weight,
            tu=vertical_offset,
            ro=1
        )
    
    # Combine circles and text
    return P([
        P(circles_list).translate(f.a.r.w/2, f.a.r.h/2),  # Centered circles
        (Glyphwise("JOJ\nJJA\nJJR", wave_style)
            .align(f.a.r)
            .f(1))  # White text
    ])

