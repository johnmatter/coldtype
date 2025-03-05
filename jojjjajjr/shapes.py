from coldtype import *
from coldtype.midi.controllers import midi_controller_lookup_fn
import numpy as np

fader_nums = list(range(32, 50))

# Quality settings that scale together
QUALITY_SCALE = 2.0  # Adjust this to globally control performance vs quality
BASE_RESOLUTION = int(400 * QUALITY_SCALE)  # Base resolution for calculations
MAX_RESOLUTION = int(800 * QUALITY_SCALE)   # Maximum resolution at high zoom
BASE_POINTS = int(400 * QUALITY_SCALE)      # Base points per curve
MAX_POINTS = int(2000 * QUALITY_SCALE)      # Maximum points at high zoom
MAX_BEZIER_SEGMENTS = int(200 * QUALITY_SCALE)  # Maximum bezier segments per curve

def mandelbrot_isoclines(width, height, max_iter, threshold, zoom, center_x, center_y):
    """Generate isoclines of the Mandelbrot set"""
    x = np.linspace(center_x - 2/zoom, center_x + 2/zoom, width)
    y = np.linspace(center_y - 2/zoom, center_y + 2/zoom, height)
    c = x[:, np.newaxis] + 1j * y[np.newaxis, :]
    
    z = np.zeros_like(c)
    divergence_time = np.zeros_like(z, dtype=int)
    
    for i in range(max_iter):
        mask = np.abs(z) <= threshold
        z[mask] = z[mask]**2 + c[mask]
        divergence_time[mask & (np.abs(z) > threshold)] = i
    
    return divergence_time

def find_isocline_points(divergence_time, level, max_points=1000):
    """Find points along an isocline with point budget"""
    contours = []
    h, w = divergence_time.shape
    
    # Find points where divergence time equals our level
    points = np.where(divergence_time == level)
    if len(points[0]) < 2:
        return []
    
    # Convert to complex coordinates for easier manipulation
    points = points[1] + 1j * points[0]
    
    # If we have too many points, subsample them
    if len(points) > max_points:
        step = len(points) // max_points
        points = points[::step]
    
    # Sort points by proximity to create smoother curves
    ordered_points = [points[0]]
    points = points[1:]
    
    while len(points) > 0 and len(ordered_points) < max_points:
        # Find closest point
        dists = np.abs(points - ordered_points[-1])
        closest = np.argmin(dists)
        ordered_points.append(points[closest])
        points = np.delete(points, closest)
        
        # Break into new contour if distance is too large
        if len(points) > 0 and np.min(dists) > 5:
            contours.append(ordered_points)
            ordered_points = [points[0]]
            points = points[1:]
            
            # Check if we've exceeded our point budget
            if sum(len(c) for c in contours) + len(ordered_points) >= max_points:
                break
    
    if ordered_points:
        contours.append(ordered_points)
    return contours

@animation((1920, 1080), bg=0, rstate=1)
def shapes(f, rs):
    if not rs.midi:
        return (StSt(
            "No MIDI Input Detected",
            Font.RecMono(),
            60,
            align="center")
            .align(f.a.r)
            .f(1))
    
    # Try to find a working controller
    controller = midi_controller_lookup_fn(
        "16n Port 1",
        cmc=rs.midi,
        channel="1"
    )
    
    # Get values from MIDI faders
    zoom = np.exp(controller(fader_nums[0], 0.5) * 5)       # Exponential zoom range
    max_iter = int(controller(fader_nums[1], 0.5) * 50 + 10) # 10-60 iterations
    num_curves = int(controller(fader_nums[2], 0.5) * 8 + 2) # 2-10 isocline curves
    center_x = controller(fader_nums[3], 0.4) * 3 - 2       # -2 to 1 range
    center_y = controller(fader_nums[4], 0.5) * 3 - 1.5     # -1.5 to 1.5 range
    stroke_width = controller(fader_nums[5], 0.5) * 35       # 0-5 range for stroke width
    hue_base = controller(fader_nums[6], 0.0)               # 0-1 range for color
    
    # Calculate resolution and point budgets based on zoom level
    zoom_scale = np.sqrt(zoom)  # Scale factor based on zoom
    resolution = min(int(BASE_RESOLUTION * zoom_scale), MAX_RESOLUTION)
    points_per_curve = min(int(BASE_POINTS * zoom_scale), MAX_POINTS)
    bezier_segments = min(int(MAX_BEZIER_SEGMENTS * zoom_scale), MAX_BEZIER_SEGMENTS)
    
    # Scale stroke width with zoom for consistent visual weight
    scaled_stroke_width = stroke_width / np.sqrt(zoom)
    
    # Calculate Mandelbrot set
    width, height = resolution, resolution
    divergence = mandelbrot_isoclines(width, height, max_iter, 2.0, zoom, center_x, center_y)
    
    # Create curves for multiple isoclines
    curves = []
    for i in range(num_curves):
        level = int(max_iter * (i + 1) / (num_curves + 1))
        contours = find_isocline_points(divergence, level, max_points=points_per_curve)
        
        for points in contours:
            if len(points) < 4:
                continue
                
            # Convert complex points to real coordinates
            real_points = [(p.real/width * f.a.r.w - f.a.r.w/2, 
                          p.imag/height * f.a.r.h - f.a.r.h/2) for p in points]
            
            # Create a smooth curve through the points
            curve = P()
            curve.moveTo(real_points[0])
            
            # Adjust point sampling based on total points
            step = max(1, len(real_points) // bezier_segments)
            for i in range(1, len(real_points)-2, step*2):
                p1 = real_points[i]
                p2 = real_points[min(i+step, len(real_points)-1)]
                # Calculate control points for smooth curve
                c1 = (p1[0] + (p2[0]-p1[0])/3, p1[1] + (p2[1]-p1[1])/3)
                c2 = (p2[0] - (p2[0]-p1[0])/3, p2[1] - (p2[1]-p1[1])/3)
                curve.curveTo(c1, c2, p2)
            
            hue = (hue_base + i/num_curves) % 1
            curves.append(curve.f(None).s(hsl(hue, 0.8, 0.5)).sw(scaled_stroke_width))
    
    return P(curves).align(f.a.r)