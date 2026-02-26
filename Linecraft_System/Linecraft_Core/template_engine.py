import xml.etree.ElementTree as ET
import random
import importlib
import math
import re

ET.register_namespace('', "http://www.w3.org/2000/svg")
ET.register_namespace('inkscape', "http://www.inkscape.org/namespaces/inkscape")
ET.register_namespace('sodipodi', "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd")

class VisualTemplateEngine:
    def __init__(self, template_path, font_name="primary_variation", offset_x=0.0, offset_y=0.0):
        self.template_path = template_path
        self.offset_x = float(offset_x)
        self.offset_y = float(offset_y)

        # 1. SMART IMPORT: Try Variable folder first, then Standard
        self.loaded_font = None
        try:
            self.loaded_font = importlib.import_module(f"font_library.variable.{font_name}")
            print(f"🔹 Loaded Variable Font: {font_name}")
        except ModuleNotFoundError:
            try:
                self.loaded_font = importlib.import_module(f"font_library.standard.{font_name}")
                print(f"🔹 Loaded Standard Font: {font_name}")
            except ModuleNotFoundError:
                print(f"❌ CRITICAL: Font '{font_name}' not found in variable or standard folders!")

        self.FONT_REF_HEIGHT = 20.0

# ... inside VisualTemplateEngine class ...

    def process_template(self, replacements, output_filename):
        # 1. RELOAD TEMPLATE
        tree = ET.parse(self.template_path)
        root = tree.getroot()

        items_to_replace = []
        total_ink_length_mm = 0.0  # Track ink in Millimeters

        # 2. SCAN
        for elem in root.iter():
            tag_name = elem.tag.split('}')[-1]
            if tag_name in ['text', 'tspan', 'flowPara']:
                content = elem.text
                if content:
                    clean_content = content.replace(" ", "")
                    for key, value in replacements.items():
                        clean_key = key.replace(" ", "")
                        if clean_key in clean_content:
                            items_to_replace.append((elem, key, value))

        if not items_to_replace:
            tree.write(output_filename, encoding='utf-8', xml_declaration=True)
            return 0.0 # Return 0 ink if nothing replaced

        parent_map = {c: p for p in root.iter() for c in p}

        # 3. REPLACE & MEASURE
        for elem, key, value in items_to_replace:
            target_elem = elem
            parent = parent_map.get(elem)

            while parent is not None:
                p_tag = parent.tag.split('}')[-1]
                if p_tag == 'text':
                    target_elem = parent
                    break
                if parent == root: break
                parent = parent_map.get(parent)

            x, y = self._get_position(target_elem)
            scale = self._get_scale(target_elem)

            new_group, ink_len = self._generate_path_group(value, x, y, scale)
            total_ink_length_mm += ink_len # Add length of this text block

            text_parent = parent_map.get(target_elem)
            if text_parent:
                text_parent.append(new_group)
                try: text_parent.remove(target_elem)
                except ValueError: pass

        # 4. SAVE
        tree.write(output_filename, encoding='utf-8', xml_declaration=True)

        # 5. RETURN INK IN METERS (mm / 1000)
        return total_ink_length_mm / 1000.0
    # (Keep _get_position, _get_scale, _generate_path_group, _estimate_path_length EXACTLY as they were)
    # I am omitting them here to save space, but DO NOT DELETE THEM from your file.
    # Just replace the __init__ method at the top.

    # ... [Paste the rest of the helper functions from the previous version here] ...

    def _get_position(self, elem):
        try:
            x = elem.get('x', '0').replace('px','').split()[0]
            y = elem.get('y', '0').replace('px','').split()[0]
            return float(x), float(y)
        except: return 0.0, 0.0

    def _get_scale(self, elem):
        style = elem.get('style', '')
        font_size = 12.0
        for item in style.split(';'):
            if 'font-size' in item:
                try:
                    val = item.split(':')[1].strip()
                    val = val.replace('px','').replace('pt','')
                    font_size = float(val)
                except: pass
        return font_size / self.FONT_REF_HEIGHT

    def _generate_path_group(self, text, start_x, start_y, scale):
        group = ET.Element('g')
        group_ink_length = 0.0
        cursor_x = start_x + self.offset_x
        cursor_y = start_y + self.offset_y

        space_width = 10.0
        line_height = 30.0
        static_font_data = {}
        static_widths = {}
        default_width = 18.0

        if self.loaded_font:
            space_width = getattr(self.loaded_font, 'SPACE_WIDTH_MM', 10.0)
            line_height = getattr(self.loaded_font, 'LINE_HEIGHT_MM', 30.0)
            static_font_data = getattr(self.loaded_font, 'STATIC_FONT', {})
            static_widths = getattr(self.loaded_font, 'CHAR_WIDTHS', {})
            default_width = getattr(self.loaded_font, 'CHAR_WIDTH_MM', 18.0)

        for char in text:
            if char == '\n':
                cursor_x = start_x + self.offset_x
                cursor_y += (line_height * scale)
                continue
            if char == ' ':
                cursor_x += (space_width * scale)
                continue

            path_d = ""
            current_char_width = default_width
            raw_data = static_font_data.get(char, static_font_data.get('?'))

            if raw_data:
                if isinstance(raw_data, list):
                    choice = random.choice(raw_data)
                    if isinstance(choice, tuple) or isinstance(choice, list):
                        path_d = choice[0]
                        current_char_width = float(choice[1])
                    else:
                        path_d = choice
                        current_char_width = static_widths.get(char, default_width)
                elif isinstance(raw_data, str):
                    path_d = raw_data
                    current_char_width = static_widths.get(char, default_width)

            if path_d:
                path = ET.SubElement(group, 'path')
                path.set('d', path_d)
                path.set('style', 'fill:none;stroke:black;stroke-width:2;stroke-linecap:round;stroke-linejoin:round')
                transform = f"translate({cursor_x},{cursor_y}) scale({scale})"
                path.set('transform', transform)
                group_ink_length += (self._estimate_path_length(path_d) * scale)

            cursor_x += (current_char_width * scale)

        return group, group_ink_length

    def _estimate_path_length(self, d_string):
        tokens = re.findall(r'[A-Za-z]|[-+]?[0-9]*\.?[0-9]+', d_string)
        total_dist = 0.0
        current_x, current_y = 0.0, 0.0
        start_x, start_y = 0.0, 0.0
        i = 0
        while i < len(tokens):
            cmd = tokens[i]
            if cmd in ['M','L','C','Q','A','Z','m','l','c','q','a','z']: i += 1
            else: i += 1; continue
            if cmd == 'M':
                if i+1 < len(tokens):
                    current_x, current_y = float(tokens[i]), float(tokens[i+1])
                    start_x, start_y = current_x, current_y
                    i += 2
            elif cmd == 'L':
                if i+1 < len(tokens):
                    tx, ty = float(tokens[i]), float(tokens[i+1])
                    total_dist += math.sqrt((tx-current_x)**2 + (ty-current_y)**2)
                    current_x, current_y = tx, ty
                    i += 2
            elif cmd in ['C', 'Q']:
                skip = 6 if cmd == 'C' else 4
                if i+(skip-1) < len(tokens):
                    tx, ty = float(tokens[i+(skip-2)]), float(tokens[i+(skip-1)])
                    dist = math.sqrt((tx-current_x)**2 + (ty-current_y)**2)
                    total_dist += (dist * 1.2)
                    current_x, current_y = tx, ty
                    i += skip
            elif cmd in ['Z', 'z']:
                total_dist += math.sqrt((start_x-current_x)**2 + (start_y-current_y)**2)
                current_x, current_y = start_x, start_y
        return total_dist
