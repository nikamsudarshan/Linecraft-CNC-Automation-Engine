import fonts
from graphics import SvgArtist
import utils
import os

class SimpleFontEngine:
    def __init__(self):
        self.artist = SvgArtist()

    def generate_static_card(self, text, filename):
        """
        Generates a card using Mode 2 (No Variation).
        """
        print(f"🔤 Generating Static Font Card: {filename}")

        # 1. Wrap Text (Approx 40 chars per line)
        lines = utils.wrap_text_block(text, max_chars_per_line=40)

        # 2. Render
        self.artist.render_font_page(
            filename=filename,
            text_lines=lines,
            font_data=fonts.STATIC_FONT,
            char_width_mm=fonts.CHAR_WIDTH_MM,
            line_height_mm=fonts.LINE_HEIGHT_MM,
            font_scale=fonts.FONT_SCALE
        )

# --- TEST RUNNER ---
if __name__ == "__main__":
    engine = SimpleFontEngine()

    # Check if folder exists
    if not os.path.exists("test_output"):
        os.makedirs("test_output")

    # Test Text (Using chars that exist in our placeholder fonts.py)
    # Since we only have A, B, C, a, b defined, let's use those.
    text = "A B C a b\nC B A b a"

    filename = "test_output/test_static_font.svg"
    engine.generate_static_card(text, filename)

    print("------------------------------------------------")
    print(f"Test complete! Open '{filename}' to see the result.")
    print("If it looks good, go to fonts.py and paste your real paths!")
