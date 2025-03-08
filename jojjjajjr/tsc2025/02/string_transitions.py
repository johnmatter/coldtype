from coldtype import *
import numpy as np
import colorspacious as cs

# MIDI timeline
midi_file = ººsiblingºº("media/tsc_beat1.mid")
midi = MidiTimeline(midi_file)

# canvas dimensions
aspect = 16/9
height = 1080
width = height * aspect

# exporter with transparency
def custom_exporter(a:animation):
    exporter  = FFMPEGExport(a)
    exporter.fmt = "mov"
    exporter.args = exporter.args[:-4]
    exporter.args.extend([
        "-c:v", "prores_ks",
        "-c:a", "pcm_s16le",
        "-profile:v", "5",
        "-pix_fmt", "yuva422p10le",
    ])
    exporter.write(verbose=True)

class Palette:
    def __init__(self, colors = None):
        self.colors = colors

    def get_color(self, index):
        return self.colors[index % len(self.colors)]
    
    def get_colors(self):
        return self.colors

    def normalize_hsl(h, s, l):
        """Converts HSL from (0–360, 0–100, 0–100) to (0–1, 0–1, 0–1)."""
        return (h / 360, s / 100, l / 100)

    def cube_helix(self, n_colors=16, start=0.5, rot=1.0, hue=0.8, gamma=1.0):
        """
        Generate a color palette using the cube helix algorithm.
        
        Args:
            n_colors: Number of colors in the palette
            start: Starting position in the helix, in rotations (0 to 3)
            rot: Number of rotations
            hue: Saturation factor
            gamma: Gamma correction factor
            
        Returns:
            List of HSL colors normalized to 0-1 range
            
        Reference:
            Green, D. A. (2011), "A colour scheme for the display of astronomical intensity images"
            https://astron-soc.in/bulletin/11June/289392011.pdf
        """
        # generate angle values
        phi = 2 * np.pi * (start/3 + rot * np.linspace(0, 1, n_colors))
        
        # calculate rgb values
        a = hue * np.cos(phi)
        b = hue * np.sin(phi)
        
        # generate lightness values, gamma corrected
        l = np.linspace(0, 1, n_colors) ** gamma
        
        # calculate rgb channels
        r = l + a
        g = l + b * 0.5 - a * 0.5
        b = l - a * 0.5 - b * 0.5
        
        # clip to [0, 1] range
        r = np.clip(r, 0, 1)
        g = np.clip(g, 0, 1)
        b = np.clip(b, 0, 1)
        
        # convert rgb to hsl
        rgb_colors = list(zip(r, g, b))
        hsl_colors = [rgb_to_hsl(*c) for c in rgb_colors]
        return hsl_colors

    def complementary(self, base_hue=0.0, saturation=0.8, lightness=0.6, variations=5):
        """
        Generate a palette with complementary colors (colors opposite on the color wheel).
        
        Args:
            base_hue: Base hue value (0-1)
            saturation: Saturation value (0-1)
            lightness: Lightness value (0-1)
            variations: Number of variations for each complementary color
            
        Returns:
            List of HSL colors
        """
        complementary_hue = (base_hue + 0.5) % 1.0
        
        colors = []
        
        # Generate variations for the base hue
        for i in range(variations):
            # Vary lightness for the base hue
            l_var = max(0.2, min(0.9, lightness - 0.2 + (i * 0.4 / variations)))
            colors.append((base_hue, saturation, l_var))
            
        # Generate variations for the complementary hue
        for i in range(variations):
            # Vary lightness for the complementary hue
            l_var = max(0.2, min(0.9, lightness - 0.2 + (i * 0.4 / variations)))
            colors.append((complementary_hue, saturation, l_var))
            
        return colors
    
    def triadic(self, base_hue=0.0, saturation=0.8, lightness=0.6, variations=3):
        """
        Generate a palette with triadic colors (three colors equally spaced on the color wheel).
        
        Args:
            base_hue: Base hue value (0-1)
            saturation: Saturation value (0-1)
            lightness: Lightness value (0-1)
            variations: Number of variations for each triad color
            
        Returns:
            List of HSL colors
        """
        triad_hue1 = (base_hue + 1/3) % 1.0
        triad_hue2 = (base_hue + 2/3) % 1.0
        
        colors = []
        
        # Generate variations for each hue in the triad
        for hue in [base_hue, triad_hue1, triad_hue2]:
            for i in range(variations):
                # Vary saturation and lightness
                s_var = max(0.3, min(1.0, saturation - 0.1 + (i * 0.2 / variations)))
                l_var = max(0.3, min(0.9, lightness - 0.1 + (i * 0.2 / variations)))
                colors.append((hue, s_var, l_var))
                
        return colors
    
    def gradient(self, start_hue=0.0, end_hue=0.6, saturation=0.8, lightness=0.6, steps=10):
        """
        Generate a smooth gradient between two hues.
        
        Args:
            start_hue: Starting hue value (0-1)
            end_hue: Ending hue value (0-1)
            saturation: Saturation value (0-1)
            lightness: Lightness value (0-1)
            steps: Number of steps in the gradient
            
        Returns:
            List of HSL colors
        """
        # Handle hue wrapping for shortest path
        if abs(start_hue - end_hue) > 0.5:
            if start_hue > end_hue:
                end_hue += 1.0
            else:
                start_hue += 1.0
                
        colors = []
        
        for i in range(steps):
            t = i / (steps - 1)
            hue = (start_hue * (1 - t) + end_hue * t) % 1.0
            colors.append((hue, saturation, lightness))
            
        return colors

class KeyFrame:
    """
    A wrapper class for storing string data and transformation information.
    """
    def __init__(self, strings, positions=None, sizes=None, colors=None, midi_note=None, font=None):
        """
        Initialize a KeyFrame.
        
        Args:
            strings: List of strings to display
            positions: List of (x,y) tuples for each string position (or None for automatic)
            sizes: List of font sizes for each string (or None for default)
            colors: List of hsl tuples (h,s,l) in range 0-1 (or None for default)
            midi_note: MIDI note number(s) to trigger this keyframe (int or list of ints)
            font: Font to use for this keyframe (or None for default)
            transforms: List of transform dictionaries for each string, with operations like
                'rotate', 'translate', etc.
        """
        self.strings = strings if isinstance(strings, list) else [strings]
        
        # midi_note should be a list
        if midi_note is not None:
            self.midi_note = midi_note if isinstance(midi_note, list) else [midi_note]
    
        # cycle through provided positions if there are more strings than positions
        self.positions = [positions[i % len(positions)] for i in range(len(self.strings))]
        
        # set sizes, cycling through provided values if necessary
        self.sizes = [sizes[i % len(sizes)] for i in range(len(self.strings))]
        
        # set colors, cycling through provided values if necessary
        self.colors = [colors[i % len(colors)] for i in range(len(self.strings))]
        
        # set font
        self.font = font if font is not None else "ObviouslyV"
        
        self.transforms = [{}] * len(self.strings)
    
    def get_bounding_box(self, frame, index=0):
        """
        Get a bounding box (Rect) for a string element based on its position.
        
        Args:
            frame: The animation frame
            index: Index of the string element
            
        Returns:
            A Rect object representing the bounding box
        """
        if index >= len(self.positions):
            return None
        
        # convert to absolute coordinates
        pos_x, pos_y = self.positions[index]
        pos_x = pos_x * frame.a.r.w
        pos_y = pos_y * frame.a.r.h
        
        return Rect(pos_x, pos_y, 0, 0)
    
    def render(self, frame, active_level=1.0):
        """
        Render the KeyFrame with the given activation level.
        
        Args:
            frame: The animation frame
            active_level: Float from 0-1 indicating how "active" this keyframe is
        
        Returns:
            A Coldtype Path object with all strings rendered
        """
        result = []
        
        for i, string in enumerate(self.strings):

            # get and transform the bounding box
            box = self.get_bounding_box(frame, i)
            if box is None:
                continue
            
            size = self.sizes[i]
            h, s, l = self.colors[i]
            
            # apply activation level enhancement to size
            adjusted_size = size * (0.8 + active_level * 0.2)

            st = (
                StSt(string, self.font, adjusted_size)
                .align(box, "C") # align string to the center of the box
                .f(hsl(h, s, l))
            )
            result.append(st)
        
        return P(*result)

# Generate palettes
pallete = Palette()

cube_helix_colors = pallete.cube_helix(
    n_colors=6,
    start=0.21,
    rot=0.45,
    hue=0.58,
    gamma=0.00
)

complementary_colors = pallete.complementary(
    base_hue=-0.02,
    saturation=0.66,
    lightness=0.85,
    variations=2
)

triadic_colors = pallete.triadic(
    base_hue=0.54,
	saturation=0.56,
	lightness=0.77,
	variations=2
)

gradient_colors = pallete.gradient(
    start_hue=0.04,
	end_hue=0.45,
	saturation=0.61,
	lightness=0.39,
	steps=5
)

# Choose which palette to use for the animation
# active_palette = cube_helix_colors
active_palette = complementary_colors
# active_palette = triadic_colors
# active_palette = gradient_colors

# active_palette = active_palette[2:5]

# prepend white
active_palette = [(0, 0, 1)] + active_palette

# use average hue for background
avg_hue = sum(c[0] for c in active_palette) / len(active_palette)
avg_hue = (avg_hue + 0.5) % 1.0 # complement
bg_hsl = hsl(avg_hue, 0.54, 0.10)

keyframes = {
    "kick": KeyFrame(
        strings=["kick", "kick", "ki", "ck"],
        positions=[(0.54, 0.26), (0.62, 0.45), (0.22, 0.61), (0.44, 0.62)],
        sizes=[611, 200, 401, 283],
        colors=active_palette,
        midi_note=[20, 36],
        font="GT-Maru-Mono",
    ),
    
    "snare": KeyFrame(
        strings=["snare", "snare", "sn", "are"],
        positions=[(0.36, 0.60), (0.57, 0.80), (0.23, 0.41), (0.46, 0.44)],
        sizes=[317, 364, 317, 217],
        colors=active_palette,
        midi_note=[25, 41],
        font="GT-Maru-Mono",
    ),
    
    "hat": KeyFrame(
        strings=["hihat", "hh", "hi", "hat"],
        positions=[(0.43, 0.73), (0.37, 0.36), (0.73, 0.45), (0.72, 0.25)],
        sizes=[367, 550, 350, 208],
        colors=active_palette,
        midi_note=[54],
        font="GT-Maru-Mono",
    )
}

@animation(
    (width, height),
	tl=midi,
	bg=1,
	release=custom_exporter
)
def string_transitions(f:Frame):
    """
    smoothly transition between keyframes based on MIDI triggers.
    """
    # create dictionary to store MIDI key input handlers for each keyframe
    midi_handlers = {}
    active_levels = {}
    
    # set up MIDI handlers for each keyframe
    for key, keyframe in keyframes.items():
        if keyframe.midi_note is not None:
            # create handlers for each midi note in the list
            midi_handlers[key] = [midi.ki(note) for note in keyframe.midi_note]
            
            # calculate activation level using ADSR envelope from all notes
            # take the maximum level from any of the MIDI notes
            if midi_handlers[key]:
                envelopes = [handler.adsr(a=0.1, d=0.2, s=0.7, r=1.0) for handler in midi_handlers[key]]
                active_levels[key] = max(envelopes) if envelopes else 0
            else:
                active_levels[key] = 0
    
    # draw background first
    bg = P(Rect(width, height)).f(bg_hsl)
    elements = [bg]
    
    # find the most active keyframe
    active_keys = [(k, v) for k, v in active_levels.items() if v > 0.01]
    active_keys.sort(key=lambda x: x[1], reverse=True)
    
    # if we have active keyframes, draw the most active one
    if active_keys:
        # get the most active keyframe
        primary_key, primary_level = active_keys[0]
        primary_keyframe = keyframes[primary_key]
        rendered = primary_keyframe.render(f, active_level=primary_level)
        elements.append(rendered)

    composition = P(*elements)
    
    # return the pens for this frame
    return P(composition) 
