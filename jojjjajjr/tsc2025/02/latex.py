import subprocess
import tempfile
import os
import shutil
from pathlib import Path

def latex_to_svg(latex_code, output_dir="output", font_size="huge"):
    """
    Generates an SVG from LaTeX and returns the file path.
    
    Args:
        latex_code: The LaTeX math code to render
        output_dir: Directory to save output files
        font_size: LaTeX font size - can be "large", "Large", "LARGE", "huge", "Huge"
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = Path(tmpdir) / "equation.tex"
        pdf_path = Path(tmpdir) / "equation.pdf"
        svg_path = output_dir / "equation.svg"
        
        # Also save PDF to output dir for debugging
        output_pdf_path = output_dir / "equation.pdf"

        # Get the appropriate font size command
        if font_size == "large":
            font_cmd = "\\large"
        elif font_size == "Large":
            font_cmd = "\\Large"
        elif font_size == "LARGE":
            font_cmd = "\\LARGE"
        elif font_size == "huge":
            font_cmd = "\\huge"
        elif font_size == "Huge":
            font_cmd = "\\Huge"
        else:
            # Custom font size
            try:
                size_pt = int(font_size)
                font_cmd = f"\\fontsize{{{size_pt}pt}}{{1.2\\baselineskip}}\\selectfont"
            except ValueError:
                # Default to Huge if not recognized
                font_cmd = "\\Huge"

        # Write LaTeX code to a file
        tex_code = f"""
\\documentclass{{standalone}}
\\usepackage{{amsmath}}
\\usepackage{{anyfontsize}}
\\begin{{document}}
{font_cmd}
${latex_code}$
\\end{{document}}
"""
        tex_path.write_text(tex_code)
        print(f"LaTeX code written to temporary file: {tex_path}")

        # Compile LaTeX to PDF
        print("Running pdflatex...")
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "-output-directory", tmpdir, str(tex_path)], check=True)
        
        # Copy PDF to output dir for debugging
        if os.path.exists(pdf_path):
            shutil.copy(pdf_path, output_pdf_path)
            print(f"PDF saved for debugging: {output_pdf_path}")
        else:
            print(f"Warning: PDF file not generated at {pdf_path}")

        # Convert PDF to SVG using pdf2svg (needs to be installed)
        print("Converting PDF to SVG...")
        try:
            subprocess.run(["pdf2svg", str(pdf_path), str(svg_path)], check=True)
            print(f"SVG created: {svg_path}")
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"pdf2svg error: {e}, trying pdftocairo...")
            try:
                subprocess.run(["pdftocairo", "-svg", str(pdf_path), str(svg_path)], check=True)
                print(f"SVG created with pdftocairo: {svg_path}")
            except (subprocess.SubprocessError, FileNotFoundError) as e:
                print(f"pdftocairo error: {e}")
                print("Neither pdf2svg nor pdftocairo works. Please install either pdf2svg or poppler-utils.")
                raise

        return svg_path

from coldtype import *
from coldtype.raster import *
from coldtype.img.skiasvg import SkiaSVG
import skia

def load_svg(svg_path):
    """Load an SVG file with error handling"""
    print(f"Attempting to load SVG: {svg_path}")
    try:
        if not os.path.exists(svg_path):
            print(f"SVG file does not exist: {svg_path}")
            raise FileNotFoundError(f"SVG file not found: {svg_path}")
            
        svg_content = svg_path.read_text()
        print(f"SVG content length: {len(svg_content)} bytes")
        print(f"SVG content preview: {svg_content[:200]}...")
        
        dom = skia.SVGDOM.MakeFromStream(skia.MemoryStream(svg_content.encode('utf-8')))
        if dom is None:
            print(f"Failed to parse SVG file: {svg_path}")
            # Create a simple fallback SVG
            fallback_svg = """<svg width="800" height="400" xmlns="http://www.w3.org/2000/svg">
                <text x="50%" y="50%" font-family="serif" font-size="20" text-anchor="middle">
                    Error loading LaTeX equation
                </text>
            </svg>"""
            print("Using fallback SVG")
            dom = skia.SVGDOM.MakeFromStream(skia.MemoryStream(fallback_svg.encode('utf-8')))
        else:
            print("SVG loaded successfully")
        return dom
    except Exception as e:
        print(f"Error loading SVG: {e}")
        # Create a simple fallback SVG
        fallback_svg = """<svg width="800" height="400" xmlns="http://www.w3.org/2000/svg">
            <text x="50%" y="50%" font-family="serif" font-size="20" text-anchor="middle">
                Error loading LaTeX equation
            </text>
        </svg>"""
        print("Using fallback SVG due to exception")
        return skia.SVGDOM.MakeFromStream(skia.MemoryStream(fallback_svg.encode('utf-8')))

print("Starting LaTeX to SVG conversion...")
# Generate the SVG file from LaTeX with an extremely large font size (72pt)
eq_svg_path = latex_to_svg("e^{i\\pi} + 1 = 0", font_size="72")
print(f"LaTeX SVG path: {eq_svg_path}")

# Load the SVG with error handling
dom = load_svg(eq_svg_path)
print("Setting container size...")
dom.setContainerSize(skia.Size(800, 400))  # Adjust size as needed

@renderable((800, 400))
def latex_equation(r):
    print("Rendering equation...")
    return SkiaSVG(dom)

# Animation example inspired by the "flying" animation
@animation((800, 800), bg=0, timeline=24)
def animated_equation(f):
    bg_rect = P().rect(f.a.r).f(hsl(f.e("qeio", 0), 0.2, 0.45))
    equation = (SkiaSVG(dom)
        .scale(f.e("eei", 0, rng=(0.2, 5)))
        .rotate(f.e("qeio", 0, rng=(0, 360)))
        .align(f.a.r)
    )
    return P(bg_rect, equation)