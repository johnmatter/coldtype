from coldtype import *
import numpy as np

# Path to your MIDI file and WAV audio file
midi_file = ººsiblingºº("media/tsc_beat1.mid")  # Using sibling function like in drumkit.py
audio_file = ººsiblingºº("media/tsc_beat1_simple.wav")  # Using sibling function like in drumkit.py

# Create a MIDI timeline
midi = MidiTimeline(midi_file)

# Set up dimensions
aspect = 16/9
height = 1080
width = height * aspect

class KeyFrame:
    """
    A wrapper class for storing string data and transformation information.
    """
    def __init__(self, strings, positions=None, sizes=None, colors=None, midi_note=None, font=None, 
                normalized_positions=True, transforms=None, use_envelope_for_color=True):
        """
        Initialize a KeyFrame.
        
        Args:
            strings: List of strings to display
            positions: List of (x,y) tuples for each string position (or None for automatic)
                If normalized_positions is True, these values should be in range 0-1
            sizes: List of font sizes for each string (or None for default)
            colors: List of hsl tuples (h,s,l) in range 0-1 (or None for default)
            midi_note: MIDI note number(s) to trigger this keyframe (int or list of ints)
            font: Font to use for this keyframe (or None for default)
            normalized_positions: Whether positions are normalized (0-1) or absolute pixels
            transforms: List of transform dictionaries for each string, with operations like
                'inset', 'rotate', 'translate', etc.
            use_envelope_for_color: Whether to apply the ADSR envelope to modify color saturation/lightness
        """
        self.strings = strings if isinstance(strings, list) else [strings]
        self.normalized_positions = normalized_positions
        self.use_envelope_for_color = use_envelope_for_color
        
        # Ensure midi_note is a list
        if midi_note is not None:
            self.midi_note = midi_note if isinstance(midi_note, list) else [midi_note]
        else:
            self.midi_note = None
        
        # Set default positions if none provided (centered grid)
        if positions is None:
            columns = min(3, len(self.strings))
            rows = (len(self.strings) + columns - 1) // columns
            
            if normalized_positions:
                # Normalized grid positions (0-1 range)
                spacing_x, spacing_y = 0.2, 0.15
                self.positions = []
                for i, _ in enumerate(self.strings):
                    row = i // columns
                    col = i % columns
                    x = 0.5 + (col - (columns - 1) / 2) * spacing_x
                    y = 0.5 + ((rows - 1) / 2 - row) * spacing_y
                    self.positions.append((x, y))
            else:
                # Absolute pixel positions
                spacing_x, spacing_y = 300, 200
                self.positions = []
                for i, _ in enumerate(self.strings):
                    row = i // columns
                    col = i % columns
                    x = (col - (columns - 1) / 2) * spacing_x
                    y = ((rows - 1) / 2 - row) * spacing_y
                    self.positions.append((x, y))
        else:
            # Cycle through provided positions if there are more strings than positions
            self.positions = [positions[i % len(positions)] for i in range(len(self.strings))]
            
        # Set sizes, cycling through provided values if necessary
        if sizes is not None:
            self.sizes = [sizes[i % len(sizes)] for i in range(len(self.strings))]
        else:
            self.sizes = [200] * len(self.strings)
        
        # Set colors, cycling through provided values if necessary
        if colors is not None:
            self.colors = [colors[i % len(colors)] for i in range(len(self.strings))]
        else:
            self.colors = [(0.5, 0.5, 0.5)] * len(self.strings)
        
        # Store the font
        self.font = font if font is not None else "ObviouslyV"
        
        # Store transformations, cycling through if necessary
        if transforms is not None:
            import random
            self.transforms = []
            for i in range(len(self.strings)):
                if i < len(transforms):
                    self.transforms.append(transforms[i])
                else:
                    # Pick a base transform to modify from existing ones
                    base_transform = transforms[i % len(transforms)].copy()
                    
                    # Slightly modify transform values to create variations
                    for key in base_transform:
                        if key == 'rotate':
                            # Adjust rotation by a small random amount
                            base_transform[key] += random.uniform(-10, 10)
                        elif key == 'inset':
                            # Adjust inset by a small random amount
                            base_transform[key] += random.uniform(-5, 5)
                        elif key == 'translate' and isinstance(base_transform[key], tuple):
                            # Adjust translation by a small random amount
                            dx, dy = base_transform[key]
                            base_transform[key] = (dx + random.uniform(-10, 10), 
                                                  dy + random.uniform(-10, 10))
                        elif key == 'scale':
                            # Adjust scale by a small random amount
                            base_transform[key] *= random.uniform(0.9, 1.1)
                    
                    self.transforms.append(base_transform)
        else:
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
            
        # Get position (normalized or absolute)
        pos_x, pos_y = self.positions[index]
        
        # If positions are normalized, convert to absolute coordinates
        if self.normalized_positions:
            pos_x = pos_x * frame.a.r.w
            pos_y = pos_y * frame.a.r.h
        
        # Create a box centered at the position
        # Size based on the string size
        box_size = self.sizes[index] * 1.5
        return Rect(pos_x - box_size/2, pos_y - box_size/2, box_size, box_size)
    
    def apply_transforms(self, box, transforms):
        """
        Apply a series of transformations to a bounding box.
        
        Args:
            box: The Rect object to transform
            transforms: Dictionary of transformations to apply
            
        Returns:
            The transformed Rect
        """
        transformed_box = box
        
        # Apply each transformation in the dictionary
        for op, value in transforms.items():
            if op == 'inset':
                transformed_box = transformed_box.inset(value)
            elif op == 'rotate':
                transformed_box = transformed_box.rotate(value)
            elif op == 'offset':
                if isinstance(value, tuple) and len(value) == 2:
                    transformed_box = transformed_box.offset(*value)
                else:
                    transformed_box = transformed_box.offset(value)
            elif op == 'scale':
                transformed_box = transformed_box.scale(value)
            # Add other transformations as needed
        
        return transformed_box
    
    def render(self, frame, active_level=1.0, blend_with=None, blend_amount=0.0):
        """
        Render the KeyFrame with the given activation level.
        
        Args:
            frame: The animation frame
            active_level: Float from 0-1 indicating how "active" this keyframe is
            blend_with: Another KeyFrame to blend with (or None)
            blend_amount: Amount to blend with the other keyframe (0-1)
        
        Returns:
            A Coldtype Path object with all strings rendered
        """
        result = []
        
        # If we're blending with another keyframe
        if blend_with and blend_amount > 0:
            # Get the maximum number of strings between the two keyframes
            max_strings = max(len(self.strings), len(blend_with.strings))
            
            for i in range(max_strings):
                # If this index exists in both keyframes, blend them
                if i < len(self.strings) and i < len(blend_with.strings):
                    # Get values from both keyframes
                    string1 = self.strings[i]
                    string2 = blend_with.strings[i]
                    
                    # Choose string based on blend amount threshold
                    # This creates a more discrete transition for text
                    string = string1 if blend_amount < 0.5 else string2
                    
                    # Get bounding boxes for positioning and transformation
                    box1 = self.get_bounding_box(frame, i)
                    box2 = blend_with.get_bounding_box(frame, i)
                    
                    # Safeguard against None bounding boxes
                    if box1 is None and box2 is None:
                        continue  # Skip this string if both boxes are None
                    
                    # Handle case where one box might be None
                    if box1 is None:
                        box = box2
                        size = box2.w
                        center_x, center_y = box2.center()
                    elif box2 is None:
                        box = box1
                        size = box1.w
                        center_x, center_y = box1.center()
                    else:
                        # Interpolate between the two boxes
                        center_x = box1.center()[0] * (1 - blend_amount) + box2.center()[0] * blend_amount
                        center_y = box1.center()[1] * (1 - blend_amount) + box2.center()[1] * blend_amount
                        size = box1.w * (1 - blend_amount) + box2.w * blend_amount
                        box = Rect(center_x - size/2, center_y - size/2, size, size)
                    
                    # Apply transforms
                    if i < len(self.transforms) and i < len(blend_with.transforms):
                        # Blend transforms based on blend_amount
                        # This is a simplified approach that chooses one set of transforms
                        transforms = self.transforms[i] if blend_amount < 0.5 else blend_with.transforms[i]
                        box = self.apply_transforms(box, transforms)
                    
                    # Interpolate size
                    size1 = self.sizes[i]
                    size2 = blend_with.sizes[i]
                    size = size1 * (1 - blend_amount) + size2 * blend_amount
                    
                    # Interpolate color (HSL)
                    h1, s1, l1 = self.colors[i]
                    h2, s2, l2 = blend_with.colors[i]
                    
                    # Handle hue wrapping (shortest path)
                    if abs(h1 - h2) > 0.5:
                        if h1 > h2:
                            h2 += 1.0
                        else:
                            h1 += 1.0
                    
                    h = (h1 * (1 - blend_amount) + h2 * blend_amount) % 1.0
                    s = s1 * (1 - blend_amount) + s2 * blend_amount
                    l = l1 * (1 - blend_amount) + l2 * blend_amount
                    
                    # Apply active level enhancement
                    adjusted_size = size * (0.8 + active_level * 0.2)
                    
                    # Apply envelope to color based on flag
                    # Choose which envelope setting to use based on blend amount
                    use_envelope = self.use_envelope_for_color if blend_amount < 0.5 else blend_with.use_envelope_for_color
                    
                    if use_envelope:
                        adjusted_s = s * (0.85 + active_level * 0.15)  # Less effect on saturation
                        adjusted_l = l * (0.7 + active_level * 0.3)    # More effect on lightness
                    else:
                        adjusted_s = s
                        adjusted_l = l
                    
                    # Choose font
                    font = self.font if blend_amount < 0.5 else blend_with.font
                    
                    # Create the StSt object - position using the box center
                    st = (
                        StSt(string, font, adjusted_size)
                        .align(box, "C")  # Align to the center of the bounding box
                        .f(hsl(h, adjusted_s, adjusted_l))
                    )
                    result.append(st)
                    
                # If this index only exists in the current keyframe
                elif i < len(self.strings):
                    # Fade out as blend amount increases
                    if blend_amount < 0.7:  # Only show if blend is less than 70%
                        fade_factor = 1 - (blend_amount / 0.7)
                        
                        # Get and transform the bounding box
                        box = self.get_bounding_box(frame, i)
                        if box is None:
                            continue  # Skip if box is None
                            
                        if i < len(self.transforms):
                            box = self.apply_transforms(box, self.transforms[i])
                        
                        size = self.sizes[i] * fade_factor
                        h, s, l = self.colors[i]
                        
                        # Apply envelope to color if enabled
                        if self.use_envelope_for_color:
                            adjusted_s = s * fade_factor * (0.85 + active_level * 0.15)
                            adjusted_l = l * fade_factor * (0.7 + active_level * 0.3)
                        else:
                            adjusted_s = s * fade_factor
                            adjusted_l = l * fade_factor
                        
                        st = (
                            StSt(self.strings[i], self.font, size)
                            .align(box, "C")  # Align to the box
                            .f(hsl(h, adjusted_s, adjusted_l))
                        )
                        result.append(st)
                        
                # If this index only exists in the blend_with keyframe
                elif i < len(blend_with.strings):
                    # Fade in as blend amount increases
                    if blend_amount > 0.3:  # Only show if blend is more than 30%
                        fade_factor = (blend_amount - 0.3) / 0.7
                        
                        # Get and transform the bounding box
                        box = blend_with.get_bounding_box(frame, i)
                        if box is None:
                            continue  # Skip if box is None
                            
                        if i < len(blend_with.transforms):
                            box = blend_with.apply_transforms(box, blend_with.transforms[i])
                        
                        size = blend_with.sizes[i] * fade_factor
                        h, s, l = blend_with.colors[i]
                        
                        # Apply envelope to color if enabled
                        if blend_with.use_envelope_for_color:
                            adjusted_s = s * fade_factor * (0.85 + active_level * 0.15)
                            adjusted_l = l * fade_factor * (0.7 + active_level * 0.3)
                        else:
                            adjusted_s = s * fade_factor
                            adjusted_l = l * fade_factor
                        
                        st = (
                            StSt(blend_with.strings[i], blend_with.font, size)
                            .align(box, "C")  # Align to the box
                            .f(hsl(h, adjusted_s, adjusted_l))
                        )
                        result.append(st)
                        
        # If not blending, just render this keyframe
        else:
            for i, string in enumerate(self.strings):
                # Get and transform the bounding box
                box = self.get_bounding_box(frame, i)
                if box is None:
                    continue  # Skip if box is None
                    
                if i < len(self.transforms):
                    box = self.apply_transforms(box, self.transforms[i])
                
                size = self.sizes[i]
                h, s, l = self.colors[i]
                
                # Apply activation level enhancement to size
                adjusted_size = size * (0.8 + active_level * 0.2)
                
                # Apply envelope to color based on flag
                if self.use_envelope_for_color:
                    adjusted_s = s * (0.85 + active_level * 0.15)  # Less effect on saturation
                    adjusted_l = l * (0.7 + active_level * 0.3)    # More effect on lightness
                else:
                    adjusted_s = s
                    adjusted_l = l
                
                # Add a slight pulsing effect based on frame count
                pulse = 1.0 + 0.05 * np.sin(frame.i * 0.1)
                
                # For debugging, uncomment to see bounding boxes
                # result.append(P().rect(box).s(hsl(h+0.1, s, adjusted_l), 1))
                
                st = (
                    StSt(string, self.font, adjusted_size * pulse)
                    .align(box, "C")  # Align to the center of the box
                    .f(hsl(h, adjusted_s, adjusted_l))
                )
                result.append(st)
        
        return P(*result)


keyframes = {
    "kick": KeyFrame(
        strings=["kick", "kick", "ki", "ck"],
        positions=[(0.54, 0.70), (0.70, 0.16), (0.22, 0.30), (0.44, 0.36)],
        sizes=[611, 249, 401, 283],
        colors=[(0.60, 0.50, 0.5), (0.62, 0.34, 0.68), (0.58, 0.50, 0.5), (0.52, 0.34, 0.46)],
        midi_note=[20, 36],
        font="GT-Maru-Mono",
        use_envelope_for_color=False,
    ),
    
    "snare": KeyFrame(
        strings=["snare", "are", "sn", "snare"],
        positions=[(0.34, 0.80), (0.56, 0.58), (0.22, 0.50), (0.68, 0.40)],
        sizes=[317, 264, 496, 284],
        colors=[(0.00, 0.36, 0.6), (0.85, 0.80, 0.80), (-0.06, 0.85, 0.6), (0.10, 0.56, 0.6)],
        midi_note=[25, 41],
        font="GT-Maru-Mono",
        use_envelope_for_color=False,
    ),
    
    "hat": KeyFrame(
        strings=["hi", "hat", "hihat", "hh"],
        positions=[(0.40, 0.6), (0.61, 0.60), (0.42, 0.36), (0.68, 0.41)],
        sizes=[467, 150, 150, 308],
        colors=[(0.16, 0.39, 0.6), (0.27, 0.62, 0.6), (0.08, 0.28, 0.6), (0.24, 0.08, 0.48)],
        midi_note=[54],
        font="GT-Maru-Mono",
        use_envelope_for_color=False,
    )
    
}

@animation((width, height), tl=midi, bg=1, audio=audio_file, release=λ.export("h264", loops=4))
def string_transitions(f:Frame):
    """
    smoothly transition between keyframes based on MIDI triggers.
    """
    # Create dictionary to store MIDI key input handlers for each keyframe
    midi_handlers = {}
    active_levels = {}
    
    # Set up MIDI handlers for each keyframe
    for key, keyframe in keyframes.items():
        if keyframe.midi_note is not None:
            # Create handlers for each midi note in the list
            midi_handlers[key] = [midi.ki(note) for note in keyframe.midi_note]
            
            # Calculate activation level using ADSR envelope from all notes
            # Take the maximum level from any of the MIDI notes
            if midi_handlers[key]:
                envelopes = [handler.adsr(a=0.1, d=0.2, s=0.7, r=1.0) for handler in midi_handlers[key]]
                active_levels[key] = max(envelopes) if envelopes else 0
            else:
                active_levels[key] = 0
    
    # Background element that reacts to the overall energy
    total_energy = sum(level for level in active_levels.values())
    # bg_intensity = min(0.2 + total_energy * 0.1, 0.3)
    # bg = P(Rect(width, height)).f(hsl(0.14, 0.86, bg_intensity))
    bg = P(Rect(width, height)).f(hsl(0.47, 0.33, 0.26))
    
    # Find the most active keyframe for blending
    active_keys = [(k, v) for k, v in active_levels.items() if v > 0.01]
    active_keys.sort(key=lambda x: x[1], reverse=True)
    
    elements = []
    
    # If we have active keyframes
    if active_keys:
        # Get the most active keyframe
        primary_key, primary_level = active_keys[0]
        primary_keyframe = keyframes[primary_key]
        
        # If we have a second active keyframe, blend between them
        if len(active_keys) > 1:
            secondary_key, secondary_level = active_keys[1]
            secondary_keyframe = keyframes[secondary_key]
            
            # Calculate blend amount based on relative activation levels
            total = primary_level + secondary_level
            blend_amount = secondary_level / total if total > 0 else 0
            
            # Render with blending
            rendered = primary_keyframe.render(
                f,
                active_level=primary_level,
                blend_with=secondary_keyframe,
                blend_amount=blend_amount
            )
            elements.append(rendered)
        else:
            # Render just the primary keyframe
            rendered = primary_keyframe.render(f, active_level=primary_level)
            elements.append(rendered)
    composition = P(*elements)
    
    # Return the complete frame
    return P(bg, composition) 
