import svgwrite
import numpy as np
from scipy.signal import savgol_filter

class SvgArtist:
    def __init__(self):
        # A4 Dimensions in mm
        self.A4_WIDTH_MM = '210mm'
        self.A4_HEIGHT_MM = '297mm'

        # 96 DPI viewbox conversion (1mm = 3.7795 px)
        self.view_width = 793.7
        self.view_height = 1122.5
        self.mm_to_px = 3.7795

    def render_font_page(self, filename, text_lines, font_data, char_width_mm, line_height_mm, font_scale):
        """
        Renders standard SVG font paths (Mode 2).
        """
        print(f"Creating SVG: {filename}")
        dwg = svgwrite.Drawing(
            filename=filename,
            size=(self.A4_WIDTH_MM, self.A4_HEIGHT_MM),
            viewBox=f"0 0 {self.view_width} {self.view_height}"
        )
        dwg.add(dwg.rect(insert=(0, 0), size=(self.view_width, self.view_height), fill='white'))

        # Starting Position (Top-Left Margin)
        # 20mm margin * 3.77 px/mm ≈ 75px
        cursor_x_start = 75.0
        cursor_y = 100.0

        for line in text_lines:
            cursor_x = cursor_x_start

            for char in line:
                # 1. Handle Space
                if char == ' ':
                    cursor_x += (char_width_mm * 0.6) * self.mm_to_px
                    continue

                # 2. Get Path Data
                # Use '?' if char is missing from your fonts.py
                path_d = font_data.get(char, font_data.get('?'))

                if path_d:
                    # Create a group <g> to move and scale the letter
                    transform_cmd = f"translate({cursor_x},{cursor_y}) scale({font_scale})"
                    letter_grp = dwg.g(transform=transform_cmd)

                    path = dwg.path(d=path_d, stroke='black', fill='none', stroke_width=2)
                    letter_grp.add(path)
                    dwg.add(letter_grp)

                # 3. Move Cursor
                cursor_x += char_width_mm * self.mm_to_px

            # End of Line: Reset X, Move Y down
            cursor_y += line_height_mm * self.mm_to_px

        dwg.save()
        print(f"✅ Saved Font Plot: {filename}")

    # --- KEEP THESE FOR LATER (Mode 1: RNN Support) ---
    def _offsets_to_coords(self, offsets):
        return np.concatenate([np.cumsum(offsets[:, :2], axis=0), offsets[:, 2:3]], axis=1)

    def _denoise(self, coords):
        split_indices = np.where(coords[:, 2] == 1)[0] + 1
        strokes = np.split(coords, split_indices, axis=0)
        new_coords = []
        for stroke in strokes:
            if len(stroke) > 3:
                try:
                    stroke[:, 0] = savgol_filter(stroke[:, 0], 7, 3, mode='nearest')
                    stroke[:, 1] = savgol_filter(stroke[:, 1], 7, 3, mode='nearest')
                except ValueError:
                    pass
            if len(stroke) > 0:
                new_coords.append(stroke)
        return np.vstack(new_coords) if new_coords else coords

    def _align(self, coords):
        coords = np.copy(coords)
        X, Y = coords[:, 0].reshape(-1, 1), coords[:, 1].reshape(-1, 1)
        X = np.concatenate([np.ones([X.shape[0], 1]), X], axis=1)
        try:
            offset, slope = np.linalg.inv(X.T.dot(X)).dot(X.T).dot(Y).squeeze()
            theta = np.arctan(slope)
            rotation_matrix = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
            coords[:, :2] = np.dot(coords[:, :2], rotation_matrix) - offset
        except:
            pass
        return coords
