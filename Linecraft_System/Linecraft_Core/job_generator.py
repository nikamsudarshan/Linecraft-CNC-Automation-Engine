import csv
import os
import shutil
import json # <--- Added json
from template_engine import VisualTemplateEngine

def generate_batch_api(project_path, font_name="primary_variation", body_template="", offset_x=0.0, offset_y=0.0):
    print(f"🚀 Generator: Working in {project_path}")

    csv_file = os.path.join(project_path, "input.csv")
    template_file = os.path.join(project_path, "template.svg")
    output_dir = os.path.join(project_path, "generated_batch")

    if not os.path.exists(csv_file): return {"success": False, "error": "input.csv missing."}
    if not os.path.exists(template_file): return {"success": False, "error": "template.svg missing."}

    if os.path.exists(output_dir): shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    try:
        engine = VisualTemplateEngine(template_file, font_name=font_name, offset_x=offset_x, offset_y=offset_y)
    except Exception as e: return {"success": False, "error": f"Engine Error: {str(e)}"}

    generated_count = 0
    batch_stats = {} # <--- Store ink data here

    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if not body_template: body_template = "Hi {NAME},\nYour order is ready."

            for i, row in enumerate(reader):
                clean_row = {k.strip(): v for k, v in row.items()}

                filled_text = body_template
                for key, val in clean_row.items():
                    filled_text = filled_text.replace(f"{{{key}}}", val)
                clean_row['BODY'] = filled_text

                safe_name = clean_row.get('NAME', 'card').replace(" ", "_")
                filename = f"{i+1:03d}_{safe_name}.svg"
                output_path = os.path.join(output_dir, filename)

                # GET INK USAGE (Meters)
                ink_meters = engine.process_template(clean_row, output_path)

                # Save to stats dict
                batch_stats[filename] = round(ink_meters, 4)

                generated_count += 1

        # WRITE STATS FILE
        with open(os.path.join(output_dir, "batch_stats.json"), "w") as f:
            json.dump(batch_stats, f, indent=4)

        return {"success": True, "count": generated_count}

    except Exception as e:
        return {"success": False, "error": f"Processing Error: {str(e)}"}
