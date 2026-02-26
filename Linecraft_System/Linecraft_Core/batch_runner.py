import os
import time
from plotter import AxiPlotter
from pyaxidraw import axidraw

def run_batch_job():
    # 1. SETUP
    job_folder = "batch_input"  # Put your 5 templates here
    if not os.path.exists(job_folder):
        os.makedirs(job_folder)
        print(f"📂 Created folder '{job_folder}'. Put your SVG templates inside!")
        return

    # Get list of SVGs
    files = [f for f in os.listdir(job_folder) if f.endswith(".svg")]
    files.sort()

    if not files:
        print(f"❌ No SVG files found in '{job_folder}'.")
        return

    # 2. CONFIGURATION
    print(f"--- BATCH JOB DETECTED ---")
    print(f"Found {len(files)} templates: {files}")

    try:
        copies_per_file = int(input("How many copies per template? (e.g., 10): "))
    except ValueError:
        print("Invalid number.")
        return

    total_plots = len(files) * copies_per_file
    print(f"\n📊 TOTAL JOB: {total_plots} Cards")
    print(f"   ({len(files)} templates x {copies_per_file} copies each)")

    confirm = input("Type 'start' to begin the batch: ")
    if confirm.lower() != 'start':
        print("Aborted.")
        return

    # 3. INITIALIZE ROBOT
    plotter = AxiPlotter()
    current_count = 0

    # 4. EXECUTION LOOP
    for svg_file in files:
        full_path = os.path.join(job_folder, svg_file)

        print(f"\nvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv")
        print(f"🔵 SWITCHING TO TEMPLATE: {svg_file}")
        print(f"^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")

        for i in range(copies_per_file):
            current_count += 1
            print(f"\n[Card {current_count} of {total_plots}] | Template: {svg_file} ({i+1}/{copies_per_file})")

            # Wait for user to load paper
            while True:
                ready = input("   Load Paper & Press ENTER to plot (or 's' to skip, 'q' to quit): ")
                if ready.lower() == 'q':
                    print("🛑 Batch cancelled.")
                    plotter.disable_motors()
                    return
                if ready.lower() == 's':
                    print("   Skipping this copy...")
                    break # Breaks the while loop, moves to next copy logic (but we usually just continue)

                # PLOT!
                plotter.plot_file(full_path)

                # After plotting, the pen is raised automatically by plot_file
                # We disable motors so you can swap paper easily
                plotter.disable_motors()
                break

    print("\n✅✅✅ BATCH JOB COMPLETE! ✅✅✅")

if __name__ == "__main__":
    run_batch_job()
