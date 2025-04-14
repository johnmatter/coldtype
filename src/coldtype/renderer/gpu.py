import glfw
from OpenGL.GL import *
import skia
import logging

logger = logging.getLogger(__name__)

class GPUContext:
    def __init__(self, width=1920, height=1080, visible=False):
        self.width = width
        self.height = height
        self.window = None
        self.context = None
        self.surface = None
        self.backend_rt = None
        self.fb_info = None

        try:
            if not glfw.init():
                raise Exception("Could not initialize GLFW")

            glfw.window_hint(glfw.VISIBLE, glfw.TRUE if visible else glfw.FALSE)
            # Request specific OpenGL Core Profile version (e.g., 3.3)
            # Adjust versions as needed, be mindful of compatibility
            glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
            glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
            glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE) # Necessary for macOS
            glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
            glfw.window_hint(glfw.STENCIL_BITS, 8) # Recommended for Skia

            self.window = glfw.create_window(width, height, "ColdtypeGPU", None, None)
            if not self.window:
                glfw.terminate()
                raise Exception("Failed to create GLFW window")

            glfw.make_context_current(self.window)
            logger.info(f"OpenGL Version: {glGetString(GL_VERSION).decode()}")

            self.context = skia.GrDirectContext.MakeGL()
            if not self.context:
                self.terminate()
                raise Exception("Failed to create Skia GrDirectContext")

            self._init_skia_surface()
            logger.info("GPU context initialized successfully.")

        except Exception as e:
            logger.error(f"GPU context initialization failed: {e}")
            self.terminate() # Clean up if init fails
            self.context = None # Ensure context is None if failed

    def _init_skia_surface(self):
        """Initializes or reinitializes the Skia Surface."""
        if not self.context or not self.window:
             return

        glfw.make_context_current(self.window) # Ensure context is current

        # Get framebuffer info
        fb_id = glGetIntegerv(GL_FRAMEBUFFER_BINDING)
        # stencil_bits = glGetIntegerv(GL_STENCIL_BITS) # Get actual stencil bits
        stencil_bits = 8 # TODO: Get stencil bits properly if needed, hardcoding for now

        #self.fb_info = skia.GrGLFramebufferInfo(fboID=fb_id, format=GL_RGBA8) # Use GL_RGBA8 directly
        # Ensure fboID is a standard Python int and use the integer value for the format
        #self.fb_info = skia.GrGLFramebufferInfo(fboID=int(fb_id), format=0x8058) # GL_RGBA8 = 0x8058
        # Try positional arguments
        self.fb_info = skia.GrGLFramebufferInfo(int(fb_id), 0x8058)

        self.backend_rt = skia.GrBackendRenderTarget(
            self.width, self.height,
            0,  # sampleCnt
            stencil_bits,
            self.fb_info
        )

        self.surface = skia.Surface.MakeFromBackendRenderTarget(
            self.context,
            self.backend_rt,
            skia.kBottomLeft_GrSurfaceOrigin,
            skia.kRGBA_8888_ColorType,
            skia.ColorSpace.MakeSRGB()
            #None # Use default ColorSpace
        )

        if not self.surface:
            raise Exception("Failed to create Skia GPU surface")

    def resize(self, width, height):
        if width == self.width and height == self.height:
            return

        self.width = width
        self.height = height
        # Recreate framebuffer and surface if necessary, or resize existing ones
        # For simplicity, let's recreate the surface here. More complex apps might resize FBOs.
        logger.info(f"Resizing GPU context to {width}x{height}")
        if self.context and self.window:
            try:
                 # Clean up old resources if necessary before recreating
                 # self.surface = None # Let Python GC handle this? Check Skia specifics.
                 # self.backend_rt = None
                glfw.set_window_size(self.window, width, height) # Resize underlying window if necessary
                self._init_skia_surface()
            except Exception as e:
                logger.error(f"Failed to resize GPU surface: {e}")
                self.surface = None
                self.context = None # Mark context as potentially invalid

    def get_canvas(self):
        if not self.surface:
            #logger.warning("Attempted to get canvas from invalid surface.")
            return None
        return self.surface.getCanvas()

    def flush_and_submit(self):
        """Flushes Skia commands and submits them to the GPU."""
        if self.surface:
            self.surface.flushAndSubmit()
            # No need to call context.flush() separately if using surface.flushAndSubmit()
        elif self.context:
            self.context.flush()

    def swap_buffers(self):
        """Swaps the GLFW window buffers if the window is visible."""
        if self.window and glfw.get_window_attrib(self.window, glfw.VISIBLE):
             glfw.swap_buffers(self.window)

    def clear(self, color=skia.ColorBLACK):
        """Clears the canvas with a specified color."""
        canvas = self.get_canvas()
        if canvas:
            canvas.clear(color)

    def read_pixels(self):
        """Reads the pixels from the GPU surface back to CPU memory."""
        if not self.surface:
            return None
        
        # Ensure operations are complete before reading
        self.flush_and_submit()
        # self.context.submit(syncCpu=True) # Ensure GPU commands are finished

        img_info = skia.ImageInfo.Make(
            self.width, self.height,
            skia.kRGBA_8888_ColorType,
            skia.kPremul_AlphaType # Or kUnpremul based on needs
        )
        
        # Allocate buffer for pixel data
        #dst_pixels = bytearray(img_info.computeMinByteSize())
        
        # Read pixels
        #success = self.surface.readPixels(img_info, dst_pixels, img_info.minRowBytes(), 0, 0)

        #if success:
        #    return dst_pixels # Or convert to numpy array / PIL image
        #else:
        #    logger.error("Failed to read pixels from GPU surface")
        #    return None
        
        # Use makeImageSnapshot for easier CPU access
        image = self.surface.makeImageSnapshot()
        if image:
            #logger.debug("GPU Surface snapshot created for pixel reading.")
             # Convert to a CPU-accessible format if needed, e.g., NumPy array
             # return image.toarray(colorType=skia.kRGBA_8888_ColorType) # Example conversion
            return image # Return the Skia Image object directly
        else:
            logger.error("Failed to create snapshot from GPU surface")
            return None

    def terminate(self):
        logger.info("Terminating GPU context...")
        # Explicitly release Skia resources if necessary
        self.surface = None
        self.backend_rt = None
        #self.context.abandonContext() # Or let Python GC handle context? Check Skia docs.
        self.context = None

        if self.window:
            glfw.destroy_window(self.window)
            self.window = None
        # Terminate GLFW only if this is the last context
        # In a multi-context app, this logic would be more complex
        # For Coldtype's likely single GPU context, terminating is probably fine
        try:
            # Check if GLFW is still initialized before terminating
            # There's no direct glfw.is_initialized() in the python bindings
            # We can try a benign call and catch the error if not initialized
            glfw.get_version()
            glfw.terminate()
            logger.info("GLFW terminated.")
        except glfw.GLFWError as e:
             # GLFW might already be terminated or failed to initialize
             if "library not initialized" not in str(e).lower():
                 logger.warning(f"Error during GLFW termination: {e}")
        except Exception as e:
             logger.warning(f"Unexpected error during GLFW termination: {e}")
