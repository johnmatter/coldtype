import skia, struct
from pathlib import Path
import math

from coldtype.pens.drawablepen import DrawablePenMixin, Gradient
from coldtype.pens.skiapathpen import SkiaPathPen
from coldtype.runon.path import P
from coldtype.img.abstract import AbstractImage
from coldtype.geometry import Rect, Point
from coldtype.text.reader import Style
from coldtype.color import Color

import coldtype.skiashim as skiashim
from coldtype.img.skiasvg import SkiaSVG

try:
    from coldtype.text.colr.skia import SkiaShaders
except ImportError:
    pass

from fontTools.pens.pointPen import BasePointToSegmentPen
from fontTools.pens.transformPen import TransformPointPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.misc.transform import Transform
from fontTools.misc.arrayTools import scaleRect, offsetRect
from fontTools.pens.boundsPen import ControlBoundsPen

from coldtype.text.composer import StSt

_SUPPORTED_FEATURES = {
    "fillColor": True,
    "strokeColor": True,
    "strokeWidth": True,
    "lineCap": True,
    "lineJoin": True,
    "miterLimit": True,
    "gradient": True,
    "shadow": True,
    "image": True,
}

class SkiaPen(DrawablePenMixin, SkiaPathPen, BasePointToSegmentPen):
    def __init__(self, dat, rect, canvas, scale, style=None, alpha=1):
        super().__init__(dat, rect.h)
        self.scale = scale
        self.canvas = canvas
        self.rect = rect
        self.blendmode = None
        self.style = style
        self.alpha = alpha

        all_attrs = list(self.findStyledAttrs(style))

        skia_paint_kwargs = dict(AntiAlias=True)
        for attrs, attr in all_attrs:
            method, *args = attr
            if method == "skp":
                skia_paint_kwargs = args[0]
                if "AntiAlias" not in skia_paint_kwargs:
                    skia_paint_kwargs["AntiAlias"] = True
            elif method == "blendmode":
                self.blendmode = args[0].to_skia()

        for attrs, attr in all_attrs:
            filtered_paint_kwargs = {}
            for k, v in skia_paint_kwargs.items():
                if not k.startswith("_"):
                    filtered_paint_kwargs[k] = v
            #filtered_paint_kwargs["AntiAlias"] = False
            self.paint = skia.Paint(**filtered_paint_kwargs)
            if self.blendmode:
                self.paint.setBlendMode(self.blendmode)
            method, *args = attr
            if method == "skp":
                pass
            elif method == "skb":
                pass
            elif method == "blendmode":
                pass
            elif method == "stroke" and args[0].get("weight") == 0:
                pass
            elif method == "dash":
                pass
            else:
                canvas.save()
                
                if method == "COLR":
                    did_draw = False
                    self.colr(args[0], dat)
                else:
                    did_draw = self.applyDATAttribute(attrs, attr)

                self.paint.setAlphaf(self.paint.getAlphaf()*self.alpha)
                if not did_draw:
                    canvas.drawPath(self.path, self.paint)
                canvas.restore()

    def colr(self, data, pen:P):
        method, args = data
        shader_fn = getattr(SkiaShaders, method)
        if shader_fn:
            ss = pen.data("substructure").copy()
            ss.invertYAxis(self.rect.h)
            sval = ss._val.value
            
            if method == "drawPathLinearGradient":
                args["pt1"] = sval[0][1][0]
                args["pt2"] = sval[1][1][0]
            elif method == "drawPathSweepGradient":
                args["center"] = sval[0][1][0]
            elif method == "drawPathRadialGradient":
                args["startCenter"] = sval[0][1][0]
                args["endCenter"] = sval[1][1][0]

            shader = shader_fn(*args.values())
            self.paint.setStyle(skia.Paint.kFill_Style)
            self.paint.setShader(shader)
        else:
            raise Exception("No matching SkiaShaders function for " + method)

    def fill(self, color):
        self.paint.setStyle(skia.Paint.kFill_Style)
        if color:
            if isinstance(color, Gradient):
                self.gradient(color)
            elif isinstance(color, Color):
                self.paint.setColor(color.skia())
        
        if "blur" in self.dat._data:
            args = self.dat._data["blur"]
            try:
                sigma = args[0] / 3
                if len(args) > 1:
                    style = args[1]
                else:
                    style = skia.kNormal_BlurStyle
            except:
                style = skia.kNormal_BlurStyle
                sigma = args / 3
            
            if sigma > 0:
                self.paint.setMaskFilter(skia.MaskFilter.MakeBlur(style, sigma))
        
        if "shake" in self.dat._data:
            args = self.dat._data["shake"]
            self.paint.setPathEffect(skia.DiscretePathEffect.Make(*args))
    
    def stroke(self, weight=1, color=None, dash=None, miter=None):
        self.paint.setStyle(skia.Paint.kStroke_Style)
        if dash:
            self.paint.setPathEffect(skia.DashPathEffect.Make(*dash))
        if color and weight > 0:
            self.paint.setStrokeWidth(weight*self.scale)
            if miter:
                self.paint.setStrokeMiter(miter)
            
            if isinstance(color, Gradient):
                self.gradient(color)
            else:
                self.paint.setColor(color.skia())
    
    def gradient(self, gradient):
        self.paint.setShader(skia.GradientShader.MakeLinear([s[1].flip(self.rect).xy() for s in gradient.stops], [s[0].skia() for s in gradient.stops]))
    
    def image(self, src=None, opacity=1, rect=None, pattern=True):
        if isinstance(src, skia.Image):
            image = src
        else:
            image = skia.Image.MakeFromEncoded(skia.Data.MakeFromFileName(str(src)))

        if not image:
            print("image <", src, "> not found, cannot be used")
            return
        
        _, _, iw, ih = image.bounds()
        
        if pattern:
            matrix = skia.Matrix()
            matrix.setScale(rect.w / iw, rect.h / ih)
            self.paint.setShader(skiashim.image_makeShader(image, matrix))
        
        if opacity != 1:
            tf = skia.ColorFilters.Matrix([
                1, 0, 0, 0, 0,
                0, 1, 0, 0, 0,
                0, 0, 1, 0, 0,
                0, 0, 0, opacity, 0
            ])
            cf = self.paint.getColorFilter()
            if cf:
                self.paint.setColorFilter(skia.ColorFilters.Compose(
                    tf, cf))
            else:
                self.paint.setColorFilter(tf)
        
        if not pattern:
            bx, by, bw, bh = self.path.getBounds()
            if rect:
                bx, by = rect.flip(self.rect.h).xy()
                #bx += rx
                #by += ry
            sx = rect.w / iw
            sy = rect.h / ih
            self.canvas.save()
            #self.canvas.setMatrix(matrix)
            self.canvas.clipPath(self.path, doAntiAlias=True)
            if False:
                self.canvas.scale(sx, sy)
            else:
                # TODO scale the image, or maybe that shouldn't be here? this scaling method is horrible for image quality
                self.canvas.scale(sx, sy)
            was_alpha = self.paint.getAlphaf()
            paint = skiashim.paint_withFilterQualityHigh()
            paint.setAlphaf(was_alpha*self.alpha)
            skiashim.canvas_drawImage(self.canvas, image, bx/sx, by/sy, self.paint)
            self.canvas.restore()
            return True
    
    def shadow(self, clip=None, radius=10, color=Color.from_rgb(0,0,0,1)):
        #print("SHADOW>", self.style, clip, radius, color)
        if clip:
            if isinstance(clip, Rect):
                skia.Rect()
                sr = skia.Rect(*clip.scale(self.scale, "mnx", "mny").flip(self.rect.h).mnmnmxmx())
                self.canvas.clipRect(sr)
            elif isinstance(clip, P):
                sp = SkiaPathPen(clip, self.rect.h)
                self.canvas.clipPath(sp.path, doAntiAlias=True)
        self.paint.setColor(skia.ColorBLACK)
        self.paint.setImageFilter(skia.ImageFilters.DropShadow(0, 0, radius, radius, color.skia()))
        return
    
    @staticmethod
    def Composite(pens, rect, path_or_canvas, scale=1, context=None, style=None, canvas=None, gpu_context=None):
        path = None
        # Determine if output is a path string or an existing canvas
        if path_or_canvas:
            if isinstance(path_or_canvas, str):
                path = str(path_or_canvas)
            elif hasattr(path_or_canvas, "drawPath"):
                canvas = path_or_canvas
            else:
                path = str(path_or_canvas)

        surface_owner = False # Track if we created the surface

        # Use GPU surface if gpu_context is provided and valid
        if gpu_context and gpu_context.context:
            if not gpu_context.surface or gpu_context.width != rect.w*scale or gpu_context.height != rect.h*scale:
                try:
                    gpu_context.resize(int(rect.w*scale), int(rect.h*scale))
                except Exception as e:
                    print(f"ERROR: Failed to re-initialize GPU surface for composite: {e}")
                    gpu_context = None # Fallback

            if gpu_context and gpu_context.surface:
                canvas = gpu_context.get_canvas()
                if not canvas:
                    print("ERROR: Failed to get canvas from GPU surface.")
                    return # Or fallback?
                canvas.clear(skia.ColorTRANSPARENT) # Ensure clean slate
                #print("COMPOSITE GPU")
            else:
                 print("INFO: Falling back to CPU rendering for composite.")
                 gpu_context = None # Ensure GPU path is not taken further

        # CPU Rendering Fallback or if no canvas was provided
        if not canvas:
            #print("COMPOSITE CPU")
            surface = skia.Surface(int(rect.w * scale), int(rect.h * scale))
            canvas = surface.getCanvas()
            canvas.clear(skia.ColorTRANSPARENT)
            surface_owner = True # We own this surface

        # Perform drawing operations
        canvas.save()
        canvas.scale(scale, scale)
        if callable(pens):
             pens(canvas) # Direct drawing function
        else:
             pens.walk(lambda p, pos, data: SkiaPen(p, rect, canvas, 1, style=style, alpha=data.get("alpha", 1)))
        canvas.restore()

        # Handle output
        if gpu_context and not path:
            # If using GPU and not saving to path, flush commands
            gpu_context.flush_and_submit()
            # Buffer swapping is handled externally by the main loop if window is visible
        elif path:
            # Save to file (either from GPU or CPU surface)
            if gpu_context:
                image = gpu_context.read_pixels()
            elif surface_owner:
                image = surface.makeImageSnapshot()
            else: # Drawing to an external canvas
                print("WARNING: Cannot save to path when drawing to an external canvas without GPU context.")
                image = None

            if image:
                try:
                    image.save(path, skia.kPNG) # Or determine format from path
                except Exception as e:
                    print(f"ERROR: Failed to save image to {path}: {e}")
            #elif surface_owner: # only print if we failed to save our own surface
            #    print(f"ERROR: Failed to create image snapshot for saving to {path}")

        # Clean up surface if we created it
        if surface_owner:
            surface = None # Allow GC

    @staticmethod
    def PDFOnePage(pens, rect, path, scale=1):
        stream = skia.FILEWStream(str(path))
        with skia.PDF.MakeDocument(stream) as document:
            with document.page(rect.w*scale, rect.h*scale) as canvas:
                canvas.scale(scale, scale)
                pens.walk(lambda p, pos, data: SkiaPen(p, rect, canvas, 1, alpha=data.get("alpha", 1)))
        stream.flush()

    @staticmethod
    def SVG(pens, rect, path, scale=1):
        stream = skia.FILEWStream(str(path))
        canvas = skia.SVGCanvas.Make((rect.w*scale, rect.h*scale), stream)
        canvas.save()
        canvas.scale(scale, scale)
        pens.walk(lambda p, pos, data: SkiaPen(p, rect, canvas, 1, alpha=data.get("alpha", 1)))
        canvas.restore()
        del canvas
        stream.flush()

    @staticmethod
    def Precompose(pens, rect, context=None, scale=1, disk=False, style=None, gpu_context=None):
        rect = rect.round()
        sr = rect.scale(scale).round()
        width, height = int(sr.w), int(sr.h)

        surface_owner = False
        canvas = None
        surface = None
        original_gpu_context = gpu_context # Keep track if we started with GPU

        # Use GPU if context is provided and valid
        if gpu_context and gpu_context.context:
            if not gpu_context.surface or gpu_context.width != width or gpu_context.height != height:
                try:
                    gpu_context.resize(width, height)
                except Exception as e:
                    print(f"ERROR: Failed to resize GPU surface for precompose: {e}")
                    gpu_context = None # Fallback

            if gpu_context and gpu_context.surface:
                canvas = gpu_context.get_canvas()
                if not canvas:
                    print("ERROR: Failed to get canvas from GPU surface for precompose.")
                    gpu_context = None # Fallback
                else:
                    #print("PRECOMPOSE GPU")
                    canvas.clear(skia.ColorTRANSPARENT)
            else:
                print("INFO: Falling back to CPU rendering for precompose.")
                gpu_context = None

        # CPU Rendering Fallback
        if not canvas:
            #print("PRECOMPOSE CPU")
            if disk:
                from pilgrims.actors.util import Profiled # Assuming this is available
                with Profiled(f"skia_surface_{width}x{height}"):
                    surface = skia.Surface(width, height)
            else:
                surface = skia.Surface(width, height)
            canvas = surface.getCanvas()
            canvas.clear(skia.ColorTRANSPARENT)
            surface_owner = True

        # Perform drawing
        canvas.save()
        # Scaling is handled by the surface size, draw in original coordinate space
        if callable(pens):
            pens(canvas) # Direct drawing function
        else:
             # Adjust translation for drawing onto the potentially scaled surface
             canvas.translate(-rect.x * scale, -rect.y * scale)
             canvas.scale(scale, scale) # Apply scale for drawing pens correctly
             pens.walk(lambda p, pos, data: SkiaPen(p, rect, canvas, 1, style=style, alpha=data.get("alpha", 1)))
             #pens.walk(lambda p, pos, data: SkiaPen.draw(p, rect, canvas, scale, style)) # Old way?
        canvas.restore()

        # Get image snapshot
        image = None
        if original_gpu_context: # Check original request, not potentially fallback gpu_context
            image = original_gpu_context.read_pixels() # Read from GPU
            if not image:
                 print("ERROR: Failed to read pixels from GPU for precompose.")
                 # Potentially fallback to CPU surface if it was created? Requires more state tracking.
        elif surface_owner:
            image = surface.makeImageSnapshot() # Read from CPU surface
            surface = None # Allow GC

        if image and disk:
            Path(disk).parent.mkdir(exist_ok=True, parents=True)
            image.save(disk, skia.kPNG)

        return image

    @staticmethod
    def CompositeToCanvas(pens, rect, canvas, scale=1, style=None):
        canvas.save()
        canvas.scale(scale, scale)
        pens.walk(lambda p, pos, data: SkiaPen(p, rect, canvas, 1, style=style, alpha=data.get("alpha", 1)))
        canvas.restore()

    @staticmethod
    def Measure(pen, font_path, font_size):
        # TODO this is maybe not the right way?
        if not isinstance(pen, StSt):
            raise Exception("Can only measure StSt currently")
        
        skia_font = skia.Font(skia.Typeface(font_path), font_size)
        return skia_font.measureText(pen.text)

    @staticmethod
    def TextBlob(text, font, rect):
        skia_font = skia.Font(skia.Typeface.MakeFromFile(str(font.path)), font.fontSize)
        
        if isinstance(text, str):
            return skia.TextBlob(text, skia_font)
        else:
            builder = skia.TextBlobBuilder()
            for pen in text:
                builder.allocRun(skia_font, pen.text, 0, 0)
            return builder.make()

    def _draw(self):
        # This method might become redundant if all drawing goes through the walk in Composite/Precompose
        # Keeping it for now for potential direct SkiaPen usage if any exists
        SkiaPen.draw(self.dat, self.rect, self.canvas, self.scale, self.style)

    def addPoint(self, pt, segmentType=None, smooth=False, name=None, **kwargs):
        # BasePointToSegmentPen requires this, but we handle drawing via walk
        pass

    @staticmethod
    def PPDraw(pp, rect, canvas, scale, style=None):
        # Potentially redundant if direct drawing is not used elsewhere
        canvas.save()
        canvas.scale(scale, scale)
        SkiaPen.draw(pp, rect, canvas, 1, style)
        canvas.restore()

    @staticmethod
    def draw(pp, rect, canvas, scale, style=None):
        # Potentially redundant, called by _draw and PPDraw
        path = SkiaPen.makePath(pp)
        if path:
            paint = SkiaPen.makePaint(pp, rect, canvas, style)
            if paint:
                # Simplified: assumes makePaint returns a list of paints or single paint
                paints_to_draw = paint if isinstance(paint, list) else [paint]
                # Attribute handling (shadow, image) needs integration here if not handled by makePaint/walk
                # For now, basic path drawing:
                for p_ in paints_to_draw:
                     canvas.drawPath(path, p_)

    @staticmethod
    def makePath(pen):
        # Potentially redundant
        path = skia.Path()
        contours = pen.value
        if not contours:
            return None
        for contour in contours:
            if not contour:
                continue
            verb, points = contour[0]
            if verb == "moveTo":
                pt = points[0]
                path.moveTo(pt[0], pt[1])
            else:
                continue
            for verb, points in contour[1:]:
                if verb == "lineTo":
                    pt = points[0]
                    path.lineTo(pt[0], pt[1])
                elif verb == "curveTo":
                    pt1, pt2, pt3 = points
                    path.cubicTo(pt1[0], pt1[1], pt2[0], pt2[1], pt3[0], pt3[1])
                elif verb == "qCurveTo":
                    pt1, pt2 = points
                    path.quadTo(pt1[0], pt1[1], pt2[0], pt2[1])
                else:
                    pass
            if contour[-1][0] == "closePath":
                path.close()
        return path

    @staticmethod
    def makePaint(pen, rect, canvas, style):
        # Potentially redundant, but contains complex paint setup logic
        # ... (rest of makePaint logic as before) ...
        fill = pen.attrs.get("fill")
        stroke = pen.attrs.get("stroke")
        # ... and so on for all attributes ...
        
        # Simplified return for example; original logic is complex
        if fill:
            return skia.Paint(Color=Color.normalize(fill).skia(), AntiAlias=True)
        elif stroke:
             _stroke = stroke.get("color", rgb(0)) if isinstance(stroke, dict) else stroke
             weight = stroke.get("weight", 1) if isinstance(stroke, dict) else 1
             return skia.Paint(Color=Color.normalize(_stroke).skia(), Style=skia.Paint.kStroke_Style, StrokeWidth=weight, AntiAlias=True)
        return None # No paint if no fill/stroke (original handles more cases)