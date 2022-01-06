from copy import deepcopy

from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.reverseContourPen import ReverseContourPen

from coldtype.geometry import Rect
from coldtype.runon.runon import Runon

from coldtype.pens.mixins.FXMixin import FXMixin
from coldtype.pens.mixins.GlyphMixin import GlyphMixin
from coldtype.pens.mixins.LayoutMixin import LayoutMixin
from coldtype.pens.mixins.StylingMixin import StylingMixin
from coldtype.pens.mixins.DrawingMixin import DrawingMixin
from coldtype.pens.mixins.PathopsMixin import PathopsMixin
from coldtype.pens.mixins.ShorthandMixin import ShorthandMixin
from coldtype.pens.mixins.SegmentingMixin import SegmentingMixin
from coldtype.pens.mixins.SerializationMixin import SerializationMixin

class RunonPen(Runon,
    StylingMixin,
    LayoutMixin,
    DrawingMixin,
    PathopsMixin,
    SegmentingMixin,
    SerializationMixin,
    ShorthandMixin,
    GlyphMixin,
    FXMixin
    ):
    def FromPens(pens):
        if hasattr(pens, "_pens"):
            out = RunonPen()
            for p in pens:
                out.append(RunonPen.FromPens(p))
        elif hasattr(pens, "_els") and len(pens._els) > 0:
            out = pens
        elif hasattr(pens, "_val") and pens.val_present():
            out = pens
        else:
            p = pens
            rp = RecordingPen()
            p.replay(rp)
            out = RunonPen(rp)
            
            attrs = p.attrs.get("default", {})
            if "fill" in attrs:
                out.f(attrs["fill"])
            if "stroke" in attrs:
                out.s(attrs["stroke"]["color"])
                out.sw(attrs["stroke"]["weight"])

            # TODO also the rest of the styles

            if hasattr(pens, "_frame"):
                out.data(frame=pens._frame)
            if hasattr(pens, "glyphName"):
                out.data(glyphName=pens.glyphName)
        return out
    
    def __init__(self, *vals):        
        super().__init__(*vals)

        if isinstance(self._val, RecordingPen):
            pass
        elif isinstance(self._val, Rect):
            r = self._val
            self._val = RecordingPen()
            self.rect(r)
        else:
            raise Exception("Can’t understand _val", self._val)
        
        self._last = None
        ShorthandMixin.__init__(self)

    def reset_val(self):
        self._val = RecordingPen()
        return self
    
    def val_present(self):
        return self._val and len(self._val.value) > 0
    
    def copy_val(self, val):
        copy = RecordingPen()
        copy.value = deepcopy(self._val.value)
        return copy
    
    def printable_val(self):
        if self.val_present():
            return f"{len(self._val.value)}mvs"
    
    def printable_data(self):
        out = {}
        exclude = ["_last_align_rect"]
        for k, v in self._data.items():
            if k not in exclude:
                out[k] = v
        return out

    def style(self, style="_default"):
        """for compatibility with defaults and grouped-stroke-properties from DATPen"""
        st = {**super().style(style)}
        return self.groupedStyle(st)
    
    def pen(self):
        """collapse and combine into a single vector"""
        if len(self) == 0:
            return self
        
        frame = self.ambit()
        self.collapse()

        for el in self._els:
            el._val.replay(self._val)
            #self._val.record(el._val)

        self._attrs = {**self._els[0]._attrs, **self._attrs}
            
        self.data(frame=frame)
        self._els = []
        return self

    # multi-use overrides
    
    def reverse(self, recursive=False):
        """Reverse elements; if pen value present, reverse the winding direction of the pen."""
        if self.val_present():
            if self.unended():
                self.closePath()
            dp = RecordingPen()
            rp = ReverseContourPen(dp)
            self.replay(rp)
            self._val.value = dp.value
            return self

        return super().reverse(recursive=recursive)
    
    def reversePens(self):
        """for backwards compatibility"""
        return self.reverse(recursive=False)
    
    # backwards compatibility

    @property
    def glyphName(self):
        return self.data("glyphName")

    # @property
    # def _frame(self):
    #     return self.data("frame")

def runonCast():
    def _runonCast(p):
        return RunonPen.FromPens(p)
    return _runonCast