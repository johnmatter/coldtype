from coldtype import *
from coldtype.fx.skia import phototype

aspect = 11/8.5
width = 1080
height = width * aspect

# Font path
eb_garamond_path = "/Users/matter/Library/Fonts/EBGaramond-VariableFont_wght.ttf"
decovar_path = "/Users/matter/Library/Fonts/DecovarAlpha-VF.ttf"

# Create MIDI timeline
midi_file = ººsiblingºº("media/tsc_beat1.mid")
midi = MidiTimeline(midi_file, fps=30)

class KeyFrame:
    """
    A wrapper class for storing multiple strings with their transformation information.
    """
    def __init__(self, midi_notes=None, methods=None):
        """
        Initialize a KeyFrame.
        
        Args:
            midi_notes: MIDI note number(s) to trigger this keyframe (int or list of ints)
            methods: Dictionary of methods to apply for each string, with their parameters
        """
        self.midi_notes = midi_notes if isinstance(midi_notes, list) else [midi_notes] if midi_notes else []
        # Methods is a dictionary where keys are string identifiers and values are the parameters for that string
        self.methods = methods if methods else {}
    
    def render(self, frame, active_level=1.0):
        """
        Render all strings in the KeyFrame with the given activation level.
        
        Args:
            frame: The animation frame
            active_level: Float from 0-1 indicating how "active" this keyframe is
        
        Returns:
            A Coldtype P object containing all three StSt objects
        """
        result = []
        
        # For each text string in the methods dictionary
        for text_id, params in self.methods.items():
            # Create base StSt object with the text and base parameters
            st = StSt(
                params.get("text", ""),
                params.get("font", "EBGaramond"),
                params.get("size", 130),
                wdth=params.get("wdth", 0.5),
                wght=params.get("wght", 0.5),
                tu=params.get("tu", 0),
                kp=params.get("kp", {}),
                leading=params.get("leading", 0)
            )
            
            # Apply chained methods according to the params
            if "translate" in params:
                st = st.translate(params["translate"][0], params["translate"][1])
                
            if "align" in params:
                align_params = params["align"]
                st = st.align(frame.a.r, tx=align_params.get("tx", 0.5), ty=align_params.get("ty", 0.5))
                
            if "rotate" in params:
                st = st.rotate(params["rotate"])
                
            if "fssw" in params:
                fill, stroke, sw, blur = params["fssw"]
                st = st.fssw(fill, stroke, sw, blur)
                
            if "ch" in params and params["ch"].get("type") == "phototype":
                pt_params = params["ch"].get("params", {})
                st = st.ch(phototype(
                    frame.a.r,
                    blur=pt_params.get("blur", 1),
                    cut=pt_params.get("cut", 20),
                    cutw=pt_params.get("cutw", 10),
                    fill=hsl(
                        pt_params.get("h", 0.07),
                        pt_params.get("s", 0.04),
                        pt_params.get("l", 0.83)
                    )
                ))
                
            if "f" in params:
                h, s, l = params["f"]
                st = st.f(hsl(h, s, l))
                
            if "reverse" in params:
                st = st.reverse(recursive=params["reverse"])
                
            result.append(st)
        
        return P(*result)

def custom_exporter(a:animation):
    """
    Custom exporter function for the animation
    """
    a.export_video("h264")
    a.export_gif()

# Define keyframes with their JSON dictionaries
keyframes = {
    "default": KeyFrame(
        midi_notes=None,  # Default keyframe, always active when no MIDI input
        methods={
            "line1": {
                "text": "it's",
                "font": "EBGaramond",
                "size": 166,
                "wdth": 0.49,
                "wght": 0.21,
                "tu": 71,
                "kp": {"n/o": -29},
                "leading": 0,
                "translate": [62, 76],
                "fssw": [1, 0, 0, 1],
                "ch": {
                    "type": "phototype",
                    "params": {
                        "blur": 1,
                        "cut": 20,
                        "cutw": 10,
                        "h": 0.07,
                        "s": 0.04,
                        "l": 0.83
                    }
                }
            },
            "line2": {
                "text": "not",
                "font": "EBGaramond",
                "size": 130,
                "wdth": 0.49,
                "wght": 0.21,
                "tu": 71,
                "kp": {"n/o": -29},
                "leading": 0,
                "translate": [702, 6],
                "fssw": [1, 0, 0, 1],
                "ch": {
                    "type": "phototype",
                    "params": {
                        "blur": 1.5,
                        "cut": 20,
                        "cutw": 10,
                        "h": 0.07,
                        "s": 0.04,
                        "l": 0.83
                    }
                }
            },
            "line3": {
                "text": "pathological",
                "font": "EBGaramond",
                "size": 130,
                "wdth": 0.49,
                "wght": 0.21,
                "tu": 71,
                "kp": {"n/o": -29},
                "leading": 0,
                "translate": [84, -151],
                "fssw": [1, 0, 0, 1],
                "ch": {
                    "type": "phototype",
                    "params": {
                        "blur": 2,
                        "cut": 20,
                        "cutw": 10,
                        "h": 0.07,
                        "s": 0.04,
                        "l": 0.83
                    }
                }
            }
        }
    ),
    "keyframe2": KeyFrame(
        midi_notes=[28],  # MIDI notes that trigger this keyframe
        methods={
            "line1": {
                "text": "it's",
                "font": "EBGaramond",
                "size": 175,  # Larger size
                "wght": 0.96,  # Different weight
                "tu": -94,
                "translate": [84, 648],  # Different position
                "fssw": [1, 0, 0, 1],
                
            },
            "line2": {
                "text": "not",
                "font": "EBGaramond",
                "size": 164,
                "wdth": 0.49,
                "wght": -0.67,
                "tu": 2,
                # "kp": {"o/t": -99, "n/o": -29},
                "leading": 0,
                "translate": [268, 651],  # Different position
                "fssw": [1, 0, 0, 1],
                
            },
            "line3": {
                "text": "pathological",
                "font": "EBGaramond",
                "size": 74,
                "wdth": 0.53,
                "wght": 0.29,
                "tu": -62,
                "translate": [174, 573],  # Different position
                "fssw": [1, 0, 0, 1],
            }
        }
    ),
    "keyframe1": KeyFrame(
        midi_notes=[20, 61],  # MIDI notes that trigger this keyframe
        methods={
            "line1": {
                "text": "it's",
                "font": "EBGaramond",
                "size": 175,  # Larger size
                "wght": 0.96,  # Different weight
                "tu": 311,
                "translate": [84, 648],  # Different position
                "fssw": [1, 0, 0, 1],
                
            },
            "line2": {
                "text": "not",
                "font": "EBGaramond",
                "size": 426,
                "wdth": 0.49,
                "wght": 0.21,
                "tu": 13,
                # "kp": {"o/t": -99, "n/o": -29},
                "leading": 0,
                "translate": [482, 627],  # Different position
                "fssw": [1, 0, 0, 1],
                
            },
            "line3": {
                "text": "pathological",
                "font": "EBGaramond",
                "size": 74,
                "wdth": 0.53,
                "wght": 0.29,
                "tu": -62,
                "translate": [174, 573],  # Different position
                "fssw": [1, 0, 0, 1],
            }
        }
    ),
}

# Store the last active keyframe (persistent between frames)
last_active_keyframe = "keyframe1"


@animation((width, height), tl=midi, release=custom_exporter)
def paper_typography(f:Frame):
    """
    Typography animation with MIDI control for different arrangements of the same text.
    The state persists, keeping the last MIDI-triggered keyframe active.
    """
    global last_active_keyframe
    
    # Create dictionary to store MIDI key input handlers for each keyframe
    midi_handlers = {}
    active_levels = {}
    
    # Set up MIDI handlers for each keyframe
    for key, keyframe in keyframes.items():
        if key == "default":
            continue  # Skip default keyframe for MIDI handling
            
        if keyframe.midi_notes:
            # Create handlers for each midi note in the list
            midi_handlers[key] = [midi.ki(note) for note in keyframe.midi_notes]
            
            # Calculate activation level using ADSR envelope from all notes
            # Take the maximum level from any of the MIDI notes
            if midi_handlers[key]:
                envelopes = [handler.adsr(a=0.1, d=0.2, s=0.7, r=1.0) for handler in midi_handlers[key]]
                active_levels[key] = max(envelopes) if envelopes else 0
            else:
                active_levels[key] = 0
    
    # Background and guides
    bg_outer = P(Rect(f.a.r.inset(0))).f(hsl(0.70, 0.25, 0.11))
    bg_inner = P(Rect(606)).f(hsl(0.58, 0.69, 0.27)).translate(78, 638)
    circle_guide = P().oval(Rect(586)).fssw(-0.8, 0.7, 2).translate(488, 391)
    
    # Collect elements
    elements = [bg_outer, bg_inner, circle_guide]
    
    # Find the most active keyframe
    active_items = [(k, v) for k, v in active_levels.items() if v > 0.01]
    active_items.sort(key=lambda x: x[1], reverse=True)

    if active_items is not None and len(active_items) > 0:
        last_active_keyframe = active_items[0][0]
    rendered = keyframes[last_active_keyframe].render(f)
    elements.append(rendered)

    return P(*elements)
