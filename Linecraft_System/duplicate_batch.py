import os
import shutil
import sys

# --- 📝 INPUT CONFIGURATION 📝 ---
# Add the paths to your source SVGs here.
# You can add as many as you want (comma-separated).
SOURCE_FILES = [
    "Projects/client_test/001_Ravi.svg",
    "Projects/client_test/002_Arnav.svg",
    "Projects/client_test/003_Rishab.svg",
    "Projects/client_test/template.svg",
]
# --------------------------------

def create_duplicates():
    print("--- 🖨️  Linecraft Bulk Multiplier 🖨️  ---")

    # 1. VALIDATE SOURCES
    valid_sources = []
    for path in SOURCE_FILES:
        # Clean path formatting (remove quotes if pasted)
        clean_path = path.strip().strip("'").strip('"')
        if os.path.exists(clean_path) and clean_path.lower().endswith('.svg'):
            valid_sources.append(clean_path)
        else:
            print(f"⚠️  Skipping invalid/missing file: {clean_path}")

    if not valid_sources:
        print("❌ Error: No valid SVG files found in SOURCE_FILES list.")
        return

    print(f"✅ Found {len(valid_sources)} unique templates.")

    # 2. GET COUNT
    try:
        copies_per_file = int(input(f"How many copies of EACH template? "))
    except ValueError:
        print("❌ Error: Please enter a number.")
        return

    total_output = len(valid_sources) * copies_per_file
    print(f"📊 Plan: {len(valid_sources)} templates x {copies_per_file} copies = {total_output} total cards.")

    # 3. SETUP OUTPUT
    output_dir = "duplicates_ready_to_plot"
    if os.path.exists(output_dir):
        if input(f"⚠️  Folder '{output_dir}' exists. Clear it? (y/n): ").lower() == 'y':
            shutil.rmtree(output_dir)
            os.makedirs(output_dir)
        else:
            print("❌ Aborted.")
            return
    else:
        os.makedirs(output_dir)

    # 4. GENERATE
    global_index = 1

    # Logic: We cycle through the source files.
    # If you want them mixed (A, B, C, A, B, C...), output order matters.
    # Currently, this loops: Template A (10 times), then Template B (10 times).

    for src_file in valid_sources:
        # Get a clean name (e.g., "template_var1")
        base_name = os.path.splitext(os.path.basename(src_file))[0]

        print(f"   Processing: {base_name}...")

        for i in range(copies_per_file):
            # Naming convention: 001_template_var1.svg, 002_template_var1.svg...
            # The robot reads them in numbered order (001, 002, 003...)
            new_filename = f"{global_index:03d}_{base_name}.svg"
            destination = os.path.join(output_dir, new_filename)

            shutil.copy(src_file, destination)
            global_index += 1

    print("-" * 40)
    print(f"✅ SUCCESS! {global_index - 1} files created.")
    print(f"📂 Output Folder: {os.path.abspath(output_dir)}")

if __name__ == "__main__":
    create_duplicates()
