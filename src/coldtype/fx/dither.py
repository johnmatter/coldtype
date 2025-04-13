import numpy as np
from coldtype.pens.skiapen import SkiaPen
from coldtype.geometry import Rect
import skia
from coldtype.runon.path import P

# https://tannerhelland.com/2012/12/28/dithering-eleven-algorithms-source-code.html
ERROR_DIFFUSION_KERNELS = {
    # list elements are of the form: 
    #   ((dx, dy), weight)
    # The origin is in the top left, contra Rob's convention putting it in the bottom left.
    # dx is to the right
    # dy is down.

    #     x 7 .
    # . 3 5 1 .
    # . . . . .
    # (1/16)
    "floyd-steinberg": [
        ((1, 0), 7/16),
        ((-1, 1), 3/16),
        ((0, 1), 5/16),
        ((1, 1), 1/16)
    ],

    #     x 3 .
    # . . 3 2 .
    # . . . . .
    # (1/8)
    "false-floyd-steinberg": [
        ((1, 0), 3/8),
        ((0, 1), 3/8),
        ((1, 1), 2/8),
    ],

    #     x 1 1
    # . 1 1 1 .
    # . . 1 . .
    # (1/8)
    "atkinson": [
        ((1,0),1/8),
        ((2,0),1/8),

        ((-1,1),1/8),
        ((0,1),1/8),
        ((1,1),1/8), 

        ((0,2),1/8)
    ],

    #     x 7 5
    # 3 5 7 5 3
    # 1 3 5 3 1
    # (1/48)
    "jarvis-judice-ninke": [
        ((1,0),7/48),
        ((2,0),5/48),

        ((-2,1),3/48),
        ((-1,1),5/48),
        ((0,1),7/48),
        ((1,1),5/48),
        ((2,1),3/48),

        ((-2,2),1/48),
        ((-1,2),3/48),
        ((0,2),5/48),
        ((1,2),3/48),
        ((2,2),1/48)
    ],

    #     x 8 4
    # 2 4 8 4 2
    # 1 2 4 2 1
    # (1/42)
    "stucki": [
        ((1,0),8/42),
        ((2,0),4/42),

        ((-2,1),2/42),
        ((-1,1),4/42),
        ((0,1),8/42),
        ((1,1),4/42),
        ((2,1),2/42),

        ((-2,2),1/42),
        ((-1,2),2/42),
        ((0,2),4/42),
        ((1,2),2/42),
        ((2,2),1/42)
    ],

    #     x 8 4
    # 2 4 8 4 2
    # . . . . .
    # (1/32)
    "burkes": [
        ((1,0),8/32),
        ((2,0),4/32),

        ((-2,1),2/32),
        ((-1,1),4/32),
        ((0,1),8/32),
        ((1,1),4/32),
        ((2,1),2/32),
    ],

    #     x 5 3
    # 2 4 5 4 2
    # . 2 3 2 .
    # (1/32)
    "sierra": [
        ((1,0),5/32),
        ((2,0),3/32),

        ((-2,1),2/32),
        ((-1,1),4/32),
        ((0,1),5/32),
        ((1,1),4/32),
        ((2,1),2/32),

        ((-1,2),2/32),
        ((0,2),3/32),
        ((1,2),2/32),
    ],

    #     x 4 3
    # 2 4 5 4 2
    # . . . . .
    # (1/16)
    "two-row-sierra": [
        ((1,0),4/16),
        ((2,0),3/16),

        ((-2,1),1/16),
        ((-1,1),2/16),
        ((0,1),3/16),
        ((1,1),2/16),
        ((2,1),1/16),
    ],

    #     x 2 .
    # . 1 1 . .
    # . . . . .
    # (1/4)
    "sierra-lite": [
        ((1,0),2/4),
        ((-1,1),1/4),
        ((0,1),1/4),
    ]
}

def apply_error_diffusion(img_array, kernel, threshold=128):
    """Apply dithering to a grayscale image"""
    h, w = img_array.shape
    result = img_array.copy()
    for y in range(h):
        for x in range(w):
            old_pixel = result[y, x]
            new_pixel = 255 if old_pixel > threshold else 0
            result[y, x] = new_pixel
            error = int(old_pixel) - int(new_pixel)
            for (dx, dy), weight in kernel:
                nx, ny = x + dx, y + dy
                # make sure we're not out of bounds
                if 0 <= nx < w and 0 <= ny < h:
                    result[ny, nx] = np.clip(result[ny, nx] + error * weight, 0, 255)
    return result

def dither(kernel="floyd-steinberg", threshold=128, scale=1):
    """
    parameters:
        kernel: Name of the error diffusion kernel (e.g., "floyd-steinberg", "atkinson")
        threshold: Grayscale threshold (0-255) for dithering
        scale: Factor to scale the image resolution *before* dithering
                  scale=1 means original resolution
                  scale=2 means dither at half resolution
                  scale=0.5 means dither at double resolution
    """
    kernel_def = ERROR_DIFFUSION_KERNELS.get(kernel)
    if not kernel_def:
        raise ValueError(f"Dithering kernel '{kernel}' not supported")

    def _dither(pen: P, rect: Rect):
        # Calculate scale factor for Precompose (inverse of user scale)
        precompose_scale = 1 / scale if scale != 0 else 1

        # Rasterize at the potentially scaled resolution
        skimg = SkiaPen.Precompose(pen, rect, scale=precompose_scale)
        if skimg is None:
            return pen

        # Convert Skia image to grayscale numpy array
        skrgba = skimg.toarray()
        gray = np.dot(skrgba[...,:3], [0.299, 0.587, 0.114]).astype(np.uint8)

        # Apply dithering
        dithered = apply_error_diffusion(gray, kernel_def, threshold)

        # Convert back to RGBA: black & white only
        rgba = np.stack((dithered,)*3 + (255*np.ones_like(dithered),), axis=-1).astype(np.uint8)

        # Convert NumPy array back to Skia Image
        dithered_image = skia.Image.fromarray(rgba)

        # Put result back into a NEW pen object, using the original rect
        # I *think* this will stretch/shrink the scaled dithered image appropriately
        return (P()
                .rect(rect)
                .img(dithered_image, rect, pattern=False)
                .f(None))

    return _dither
