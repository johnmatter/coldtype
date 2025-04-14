#!/usr/bin/env python
from coldtype import *
from coldtype.fx.skia import precompose, phototype

# This example demonstrates GPU acceleration with basic rendering operations.
#
# To run with GPU acceleration:
# coldtype examples/gpu_test_simple.py -w 1 --gpu
#
# To run with CPU rendering:
# coldtype examples/gpu_test_simple.py -w 1

# Create a base canvas
r = Rect(1080, 540)

@animation(r, tl=Timeline(60, 30), bg=0)
def gpu_test_simple(f):
    # Create a complex scene with many shapes and effects that should benefit from GPU acceleration
    
    # Base shapes
    shapes = P()
    
    # Add many rotating rectangles
    count = 1000
    for i in range(count):
        angle = 360 * (i/count)
        distance = f.e("eeio", i % 30, rng=(50, 250))
        size = 10 + (i % 10)
        
        x = r.w/2 + math.cos(math.radians(angle + f.i*2)) * distance
        y = r.h/2 + math.sin(math.radians(angle + f.i*2)) * distance
        
        hue = (i/count + f.i/f.t.duration) % 1
        shapes.append(
            P().rect(Rect(x, y, size, size))
            .rotate(angle + f.i)
            .f(hsl(hue, 0.7, 0.5))
        )
    
    # Add text in the center
    text = StSt("GPU TEST", Font.ColdObvi(), 150, wdth=0.5, tu=-50).align(r)
    
    # Create layers with different effects
    result = P(
        # Layer 1: Background gradient
        P().rect(r).f(Gradient.Horizontal(
            hsl(f.e("l", loops=1, rng=(0, 1)), 0.7, 0.5),
            hsl(f.e("l", loops=1, rng=(0.5, 1.5)), 0.7, 0.5)
        )),
        
        # Layer 2: Many small shapes
        shapes,
        
        # Layer 3: Text with blur effect using Skia directly
        text.f(1).ch(precompose(r))
            .attr(skp=dict(ImageFilter=skia.ImageFilters.Blur(
                10 * f.e("seio", loops=1, rng=(0.5, 1)), 
                10 * f.e("seio", loops=1, rng=(0.5, 1))
            )))
    )
    
    return result

# To make this runnable standalone for quick testing:
# if __name__ == "__main__":
#    from coldtype.renderer import Renderer
#    Renderer(gpu_test_simple).main() 