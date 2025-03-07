from coldtype import *
from coldtype.midi.controllers import midi_controller_lookup_fn
import math
import numpy as np

fader_nums = list(range(32, 42))

canvas_aspect_ratio = 16/9
height = 1080
width = height * canvas_aspect_ratio

# Cache to store the last background when parameters haven't changed
dither_cache = {
    'background': None,
    'params': None
}

def floyd_steinberg_dither(width, height, hue_fn, saturation=0.7, lightness=0.50, scale=12):
    """
    Create a dithered color field using Floyd-Steinberg dithering.
    hue_fn: Function that takes x, y and returns a hue value (0-1)
    scale: Scale factor for dithering resolution - higher values mean coarser dithering but faster performance
    """
    # Calculate dimensions
    dither_width = int(width / scale)
    dither_height = int(height / scale)
    
    # Create the base HSL values based on position using NumPy for speed
    x_coords = np.linspace(0, 1, dither_width)
    y_coords = np.linspace(0, 1, dither_height)
    X, Y = np.meshgrid(x_coords, y_coords)
    
    # Vectorize the hue function if possible
    try:
        # Try to vectorize for speed
        hues = np.vectorize(hue_fn)(X, Y)
    except:
        # Fall back to slower loop if vectorization fails
        hues = np.zeros((dither_height, dither_width))
        for y in range(dither_height):
            for x in range(dither_width):
                hues[y, x] = hue_fn(x_coords[x], y_coords[y])
    
    # Apply Floyd-Steinberg dithering to quantize hues to discrete values
    # Number of discrete hue levels - lower is faster but less detailed
    num_hue_levels = 64
    
    # Make a copy for dithering
    dithered_field = hues.copy()
    
    # Apply the dithering algorithm
    for y in range(dither_height):
        for x in range(dither_width):
            old_hue = dithered_field[y, x]
            
            # Quantize the hue to discrete levels
            new_hue = round(old_hue * num_hue_levels) / num_hue_levels
            
            # Calculate the error
            error = old_hue - new_hue
            
            # Store the new hue
            dithered_field[y, x] = new_hue
            
            # Distribute the error to neighboring pixels
            if x < dither_width - 1:
                dithered_field[y, x + 1] += error * 7/16
            if y < dither_height - 1:
                if x > 0:
                    dithered_field[y + 1, x - 1] += error * 3/16
                dithered_field[y + 1, x] += error * 5/16
                if x < dither_width - 1:
                    dithered_field[y + 1, x + 1] += error * 1/16
    
    rects = []
    unique_hues = {}
    
    for y in range(dither_height):
        for x in range(dither_width):
            hue = dithered_field[y, x]
            # Round to reduce the number of unique colors
            hue_key = round(hue, 2)
            
            if hue_key not in unique_hues:
                unique_hues[hue_key] = []
            
            unique_hues[hue_key].append((x, y))
    
    for hue, positions in unique_hues.items():
        color_path = P()
        for x, y in positions:
            pixel_rect = Rect(scale, scale).offset(x * scale, y * scale)
            color_path.rect(pixel_rect)
        
        rects.append(color_path.f(hsl(hue, saturation, lightness)))
    
    # Combine all the rectangles into a single path
    return P(rects)

@animation((width, height), bg=0, rstate=1, timeline=1200)
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
    
    # Add controls for dithering parameters
    dither_speed = controller(fader_nums[4], 0.5) # Speed of the hue function animation
    dither_complexity = controller(fader_nums[5], 0.5) * 10 + 1  # Controls the complexity of the gradient
    dither_scale = int(controller(fader_nums[6], 0.5) * 20 + 8)  # Controls resolution of dithering (8-28)

    # Create a rectangle to contain the circle
    circle_rect = (
            Rect(circle_radius*2, circle_radius*2)
                .align(f.a.r)
                .offset(x_offset, y_offset)
    )
    
    # Create a time-based animated hue function
    time_factor = f.i / 50 * dither_speed
    
    def hue_function(x, y):
        angle = math.atan2(y - 0.5, x - 0.5)
        dist = math.sqrt((x - 0.5)**2 + (y - 0.5)**2) * 2
        
        h = (math.sin(angle * dither_complexity + time_factor) * 0.3 + 
             math.cos(dist * dither_complexity + time_factor) * 0.3 +
             hue + 
             time_factor * 2.5) % 1.0
        
        return h
    
    # Check if we can use the cached background
    current_params = (time_factor, dither_complexity, hue, dither_scale)
    if dither_cache['params'] != current_params:
        # Parameters changed, regenerate the background
        background = floyd_steinberg_dither(width, height, hue_function,
                                            saturation=0.3, lightness=0.5, scale=dither_scale)
        # Update the cache
        dither_cache['background'] = background
        dither_cache['params'] = current_params
    else:
        # Use cached background
        background = dither_cache['background']
    
    # Create the circle on top
    circle = P().oval(circle_rect).f(hsl(hue, 0.6, 0.5))
    
    # Return both the background and the circle
    return P([
        background,  # Dithered background
        circle       # Circle on top
    ])
