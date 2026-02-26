import xml.etree.ElementTree as ET
import re
import os

def convert_font(svg_filename, output_name, scale_factor=0.02, flip_y=True):
    """
    Reads an SVG Font file (Hershey/EMS) and creates a python font file.
    Uses repr() for bulletproof character escaping.
    """
    print(f"🔨 Converting '{svg_filename}'...")

    if not os.path.exists(svg_filename):
        print(f"❌ Error: File '{svg_filename}' not found.")
        return

    try:
        tree = ET.parse(svg_filename)
        root = tree.getroot()
    except ET.ParseError:
        print("❌ Error: Could not parse SVG XML.")
        return

    # Namespaces often used in SVG fonts
    ns = {'svg': 'http://www.w3.org/2000/svg'}

    # FIND GLYPHS
    glyphs = root.findall(".//svg:glyph", ns)
    if not glyphs:
        glyphs = root.findall(".//glyph")

    print(f"   Found {len(glyphs)} glyphs.")

    extracted_font = {}
    extracted_widths = {}

    total_width = 0
    count_width = 0

    for glyph in glyphs:
        char = glyph.get('unicode')
        path_d = glyph.get('d')
        raw_width = glyph.get('horiz-adv-x')

        if not char or not path_d:
            continue

        # Fix XML entity characters
        if char == "&quot;": char = '"'
        if char == "&amp;": char = '&'
        if char == "&lt;": char = '<'
        if char == "&gt;": char = '>'

        # TRANSFORM
        cleaned_path = transform_path(path_d, scale_factor, flip_y)
        extracted_font[char] = cleaned_path

        if raw_width:
            w = float(raw_width) * scale_factor
            extracted_widths[char] = w
            total_width += w
            count_width += 1

    avg_width = (total_width / count_width) if count_width > 0 else 10.0

    # WRITE FILE
    output_path = f"font_library/{output_name}.py"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f'"""\nConverted from {svg_filename}\nScale: {scale_factor}\n"""\n\n')

        f.write(f"# GLOBAL SETTINGS\n")
        f.write(f"LINE_HEIGHT_MM = 30.0\n")
        f.write(f"SPACE_WIDTH_MM = {avg_width * 0.4:.2f}\n")
        f.write(f"CHAR_WIDTH_MM = {avg_width:.2f}\n\n")

        f.write(f"# VARIABLE WIDTHS\n")
        f.write(f"CHAR_WIDTHS = {{\n")
        for char, w in extracted_widths.items():
            # repr(char) automatically wraps ' in "..." and " in '...'
            f.write(f"    {repr(char)}: {w:.2f},\n")
        f.write(f"}}\n\n")

        f.write(f"# GLYPH PATHS\n")
        f.write(f"STATIC_FONT = {{\n")
        for char, path in extracted_font.items():
            f.write(f"    {repr(char)}: {repr(path)},\n")
        f.write(f"}}\n")

    print(f"✅ Success! Saved to '{output_path}'")

def transform_path(d_string, scale, flip_y):
    """
    Parses SVG path data, scales numbers, and flips Y axis.
    """
    tokens = re.split(r'[, \t]+', d_string)
    new_tokens = []

    axis_counter = 0 # 0=X, 1=Y

    for token in tokens:
        if not token: continue

        if token[0].isalpha():
            new_tokens.append(token)
            axis_counter = 0
        else:
            try:
                val = float(token)
                val = val * scale

                if axis_counter % 2 == 1 and flip_y:
                    val = -val

                new_tokens.append(f"{val:.2f}")
                axis_counter += 1
            except ValueError:
                new_tokens.append(token)

    return " ".join(new_tokens)

if __name__ == "__main__":
    # CONFIGURATION
    INPUT_FILE = "EMSReadability.svg"
    OUTPUT_NAME = "EMSReadability"
    SCALE = 0.02

    convert_font(INPUT_FILE, OUTPUT_NAME, scale_factor=SCALE, flip_y=True)
