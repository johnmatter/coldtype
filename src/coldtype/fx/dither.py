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

# Bayer matrices of different sizes
BAYER_MATRICES = {
    # 2x2 Bayer matrix (normalized to 0-1 range)
    2: np.array([
        [0, 2],
        [3, 1]
    ]) / 4,
    
    # 4x4 Bayer matrix
    4: np.array([
        [0,  8,  2, 10],
        [12, 4,  14, 6],
        [3,  11, 1,  9],
        [15, 7,  13, 5]
    ]) / 16,
    
    # 8x8 Bayer matrix
    8: np.array([
        [0,  32, 8,  40, 2,  34, 10, 42],
        [48, 16, 56, 24, 50, 18, 58, 26],
        [12, 44, 4,  36, 14, 46, 6,  38],
        [60, 28, 52, 20, 62, 30, 54, 22],
        [3,  35, 11, 43, 1,  33, 9,  41],
        [51, 19, 59, 27, 49, 17, 57, 25],
        [15, 47, 7,  39, 13, 45, 5,  37],
        [63, 31, 55, 23, 61, 29, 53, 21]
    ]) / 64
}

# Blue noise dithering matrices (64x64)
def generate_blue_noise_matrix(size=64):
    # This is a placeholder - in a real implementation you'd load a precomputed blue noise texture
    # Here we're just creating a random matrix for demonstration
    # Blue noise has special spectral characteristics that make it better for dithering
    np.random.seed(42)  # For reproducibility
    return np.random.rand(size, size)

BLUE_NOISE = generate_blue_noise_matrix()

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

def apply_ordered_dithering(img_array, matrix, threshold=128):
    """Apply ordered dithering using a threshold matrix (e.g., Bayer matrix)"""
    h, w = img_array.shape
    matrix_h, matrix_w = matrix.shape
    
    # Scale threshold matrix to full range (0-255)
    threshold_matrix = matrix * 255
    
    result = np.zeros_like(img_array)
    for y in range(h):
        for x in range(w):
            # Find the corresponding threshold from the matrix
            matrix_x, matrix_y = x % matrix_w, y % matrix_h
            threshold_value = threshold_matrix[matrix_y, matrix_x]
            
            # Apply threshold
            result[y, x] = 255 if img_array[y, x] > threshold_value else 0
            
    return result

def apply_blue_noise_dithering(img_array, noise_matrix, threshold=128):
    """Apply blue noise dithering"""
    h, w = img_array.shape
    matrix_h, matrix_w = noise_matrix.shape
    
    # Scale blue noise to full range (0-255)
    threshold_matrix = noise_matrix * 255
    
    result = np.zeros_like(img_array)
    for y in range(h):
        for x in range(w):
            # Find the corresponding threshold from the matrix
            matrix_x, matrix_y = x % matrix_w, y % matrix_h
            threshold_value = threshold_matrix[matrix_y, matrix_x]
            
            # Apply threshold
            result[y, x] = 255 if img_array[y, x] > threshold_value else 0
            
    return result

def dither(kernel="floyd-steinberg", threshold=128, scale=1, matrix_size=4):
    """
    parameters:
        kernel: Name of the error diffusion kernel (e.g., "floyd-steinberg", "atkinson")
               or "bayer" for ordered dithering using Bayer matrices
               or "blue-noise" for blue noise dithering
        threshold: Grayscale threshold (0-255) for dithering
        scale: Factor to scale the image resolution *before* dithering
                  scale=1 means original resolution
                  scale=2 means dither at half resolution
                  scale=0.5 means dither at double resolution
        matrix_size: Size of the Bayer matrix to use (2, 4, or 8)
                    Only relevant when kernel="bayer"
    """
    # Determine the dithering method
    if kernel == "bayer":
        matrix = BAYER_MATRICES.get(matrix_size, BAYER_MATRICES[matrix_size])
        
        def _dither_bayer(pen: P, rect: Rect):
            # Calculate scale factor for Precompose (inverse of user scale)
            precompose_scale = 1 / scale if scale != 0 else 1
            
            # Rasterize at the potentially scaled resolution
            skimg = SkiaPen.Precompose(pen, rect, scale=precompose_scale)
            if skimg is None:
                return pen
                
            # Convert Skia image to grayscale numpy array
            skrgba = skimg.toarray()
            gray = np.dot(skrgba[...,:3], [0.299, 0.587, 0.114]).astype(np.uint8)
            
            # Apply Bayer dithering
            dithered = apply_ordered_dithering(gray, matrix, threshold)
            
            # Convert back to RGBA: black & white only
            rgba = np.stack((dithered,)*3 + (255*np.ones_like(dithered),), axis=-1).astype(np.uint8)
            
            # Convert NumPy array back to Skia Image
            dithered_image = skia.Image.fromarray(rgba)
            
            # Put result back into a NEW pen object, using the original rect
            return (P()
                    .rect(rect)
                    .img(dithered_image, rect, pattern=False)
                    .f(None))
                    
        return _dither_bayer
        
    elif kernel == "blue-noise":
        def _dither_blue_noise(pen: P, rect: Rect):
            # Calculate scale factor for Precompose (inverse of user scale)
            precompose_scale = 1 / scale if scale != 0 else 1
            
            # Rasterize at the potentially scaled resolution
            skimg = SkiaPen.Precompose(pen, rect, scale=precompose_scale)
            if skimg is None:
                return pen
                
            # Convert Skia image to grayscale numpy array
            skrgba = skimg.toarray()
            gray = np.dot(skrgba[...,:3], [0.299, 0.587, 0.114]).astype(np.uint8)
            
            # Apply blue noise dithering
            dithered = apply_blue_noise_dithering(gray, BLUE_NOISE, threshold)
            
            # Convert back to RGBA: black & white only
            rgba = np.stack((dithered,)*3 + (255*np.ones_like(dithered),), axis=-1).astype(np.uint8)
            
            # Convert NumPy array back to Skia Image
            dithered_image = skia.Image.fromarray(rgba)
            
            # Put result back into a NEW pen object, using the original rect
            return (P()
                    .rect(rect)
                    .img(dithered_image, rect, pattern=False)
                    .f(None))
                    
        return _dither_blue_noise
    
    else:
        # Use error diffusion
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
