from coldtype import *
from coldtype.midi.controllers import midi_controller_lookup_fn
import math
import random

# Global scale factor - adjust this to scale everything
SCALE = 2.0
ASPECT = 16/9

@animation((1080 * SCALE * ASPECT, 1080 * SCALE), bg=0, rstate=1, timeline=1200)
def circles(f, rs):
    if not rs.midi:
        return (StSt(
            "No MIDI Input Detected",
            Font.MutatorSans(),
            30 * SCALE,
            align="center")
            .align(f.a.r)
            .f(1))
    
    # Cache the controller function to avoid repeated creation
    if not hasattr(circles, 'controller'):
        circles.controller = midi_controller_lookup_fn(
            "nanoKONTROL2 SLIDER/KNOB",
            cmc=rs.midi,
            channel="1"
        )
    controller = circles.controller
    
    # Get values from sliders for circles
    num_circles = int(controller(0, 0.3) * 15 + 3)  # 3 to 18 circles
    circle_radius = controller(1, 0.3) * 500 * SCALE  # 0 to 250 units
    max_path_radius = controller(2, 0.5) * 2000 * SCALE  # 0 to 1000 units
    rotation_speed = controller(3, 0.0) * 0.4 - 0.2
    hue_rotation = controller(4, 0.0)  # 0 to 1 for color wheel rotation
    
    # Get values from sliders for text wave effect
    wave_amplitude = controller(5, 0.3) * 5  # 0 to 5 for font weight range
    wave_phase = controller(6, 0.0) * math.pi * 2  # 0 to 2π radians
    wave_frequency = controller(7, 0.5) * 2 + 0.5  # 0.5 to 2.5 Hz
    vertical_amplitude = controller(16, 0.3) * 100 * SCALE  # 0 to 100 units for vertical movement
    
    # Get values from sliders for shadow effect
    shadow_angle = controller(17, 0.5) * 360 - 180  # -180 to 180 degrees
    shadow_width = controller(18, 0.3) * 100 * SCALE + 0.1  # 0 to 100 units
    shadow_blur = controller(19, 0.3) * 20 * SCALE + 0.5  # 0 to 20 units
    stroke_width = controller(20, 0.3) * 10 * SCALE + 0.1  # 0 to 10 units
    
    # Additional controls
    num_rings = int(controller(21, 0.3) * 5 + 1)  # 1 to 6 rings
    shadow_hue = controller(22, 0.0)  # 0 to 1 for shadow color hue
    stroke_hue = controller(23, 0.0)  # 0 to 1 for stroke color hue
    
    # Create random parameters for each ring if they don't exist
    if not hasattr(circles, 'ring_params'):
        circles.ring_params = []
        for _ in range(10):  # Pre-generate for up to 10 rings
            circles.ring_params.append({
                'direction': random.choice([-0.1, 0.1]),  # Random direction
                'frequency': random.uniform(1, 5),  # Random speed multiplier
                'base_phase': random.uniform(0, math.pi * 2)  # Initial phase offset
            })
    
    # Pre-calculate common values
    two_pi = math.pi * 2
    frame_rotation = f.i/60 * two_pi
    circle_rect = Rect(circle_radius*2, circle_radius*2)
    
    # Create the circles for each ring
    circles_list = []
    circles_list.extend(
        P()
        .oval(circle_rect)
        .translate(
            math.cos((i / num_circles) * two_pi + 
                    params['base_phase'] + 
                    frame_rotation * rotation_speed * params['frequency'] * params['direction']) 
                    * (max_path_radius * (ring + 1) / num_rings),
            math.sin((i / num_circles) * two_pi + 
                    params['base_phase'] + 
                    frame_rotation * rotation_speed * params['frequency'] * params['direction']) 
                    * (max_path_radius * (ring + 1) / num_rings))
        .f(hsl(((i / num_circles) + (ring / num_rings) + hue_rotation) % 1, 0.6, 0.5))
        for ring in range(num_rings)
        for i in range(num_circles)
        for params in [circles.ring_params[ring]]  # List comprehension trick to use ring_params
    )
    
    # Pre-calculate wave values for text
    time_phase = f.i/100
    base_wave = wave_frequency * time_phase + wave_phase
    
    def wave_style(g):
        g_phase = wave_frequency * g.i + base_wave
        return Style(
            Font.MutatorSans(),
            450 * SCALE,  # Scale the font size
            wght=((math.sin(g_phase) + 1) / 2) * wave_amplitude,
            tu=math.sin(g_phase + math.pi/2) * vertical_amplitude,
            ro=1
        )
    
    # Define shadow function with current parameters
    def shadow_and_clean(p):
        return (p
            .outline(shadow_blur)
            .reverse()
            .remove_overlap()
            .castshadow(shadow_angle, shadow_width, fill=hsl(shadow_hue, s=0.8, l=0.3))
            .explode()
            .filter(lambda j, c: c.bounds().w > 20 * SCALE)  # Scale the filter threshold
            .implode()
            .f(hsl(shadow_hue, s=0.6, l=0.5))  # Fill the main text
            .s(hsl(stroke_hue, s=1, l=0.5))  # Stroke color
            .sw(stroke_width))
    
    # Create text with both wave and shadow effects
    text = (Glyphwise("JOJ\nJJA\nJJR", wave_style)
        .align(f.a.r)
        .f(1)
        .layer(
            lambda ps: ps.mapv(shadow_and_clean)))
    
    # Combine circles and text
    return P([
        P(circles_list).translate(f.a.r.w/2, f.a.r.h/2),  # Centered circles
        text  # Text with wave and shadow effects
    ])

