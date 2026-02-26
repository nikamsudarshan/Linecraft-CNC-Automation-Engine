from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import sys
import os
import shutil
import json
import datetime
import subprocess
import time
import importlib

# --- PATH CONFIG ---
current_dir = os.path.dirname(os.path.abspath(__file__))
SYSTEM_ROOT = os.path.join(current_dir, '..')
CORE_PATH = os.path.join(SYSTEM_ROOT, 'Linecraft_Core')
PROJECTS_ROOT = os.path.join(SYSTEM_ROOT, 'Projects')
ARCHIVES_ROOT = os.path.join(SYSTEM_ROOT, 'Archives')

sys.path.append(CORE_PATH)
from job_generator import generate_batch_api
from plot_manager import manager as plot_manager

FONT_LIB_PATH = os.path.join(CORE_PATH, 'font_library')
AXICLI_PATH = "/path/to/your/env/bin/axicli"

app = Flask(__name__)
CORS(app)

# --- 1. FONTS ---
@app.route('/fonts', methods=['GET'])
def list_fonts():
    fonts = []
    # Scan Variable Folder
    var_path = os.path.join(FONT_LIB_PATH, "variable")
    if os.path.exists(var_path):
        for f in sorted(os.listdir(var_path)):
            if f.endswith(".py") and f != "__init__.py":
                fonts.append({"name": f.replace(".py", ""), "type": "Variable"})

    # Scan Standard Folder
    std_path = os.path.join(FONT_LIB_PATH, "standard")
    if os.path.exists(std_path):
        for f in sorted(os.listdir(std_path)):
            if f.endswith(".py") and f != "__init__.py":
                fonts.append({"name": f.replace(".py", ""), "type": "Standard"})

    return jsonify({"fonts": fonts})

# --- 2. PEN MANAGEMENT ---
@app.route('/pens', methods=['GET'])
def list_pens():
    return jsonify({
        "pens": plot_manager.pens,
        "active_id": plot_manager.current_pen_id
    })

@app.route('/pens/create', methods=['POST'])
def create_pen():
    data = request.json
    name = data.get('name', 'Unnamed Pen')
    capacity = data.get('capacity', 200)
    pen_id = plot_manager.add_pen(name, capacity)
    return jsonify({"success": True, "pen_id": pen_id})

@app.route('/pens/select', methods=['POST'])
def select_pen():
    pen_id = request.json.get('pen_id')
    if plot_manager.set_active_pen(pen_id):
        return jsonify({"success": True})
    return jsonify({"error": "Pen not found"}), 404

# --- 3. QUEUE & STATUS ---
@app.route('/queue/load', methods=['POST'])
def load_queue():
    name = request.json.get('project')
    project_path = os.path.join(PROJECTS_ROOT, name)
    success, msg = plot_manager.load_batch(project_path)
    return jsonify({"success": success, "message": msg})

@app.route('/queue/start', methods=['POST'])
def start_queue():
    success, msg = plot_manager.start_queue()
    return jsonify({"success": success, "message": msg})

@app.route('/queue/continue', methods=['POST'])
def continue_queue():
    if plot_manager.user_continue(): return jsonify({"success": True})
    return jsonify({"error": "Not waiting"}), 400

@app.route('/queue/skip/forward', methods=['POST'])
def skip_forward():
    success, msg = plot_manager.skip_forward()
    return jsonify({"success": success, "message": msg})

@app.route('/queue/skip/backward', methods=['POST'])
def skip_backward():
    success, msg = plot_manager.skip_backward()
    return jsonify({"success": success, "message": msg})

@app.route('/queue/pause', methods=['POST'])
def toggle_pause():
    status = plot_manager.toggle_pause()
    return jsonify({"success": True, "status": status})

@app.route('/queue/status', methods=['GET'])
def queue_status():
    duration = int(time.time() - plot_manager.start_time) if plot_manager.start_time > 0 else 0
    active_pen = plot_manager.pens.get(plot_manager.current_pen_id, {})

    return jsonify({
        "state": plot_manager.state,
        "current_file": plot_manager.current_file,
        "next_file": plot_manager.next_file,
        "current_index": plot_manager.current_index + 1,
        "total_files": len(plot_manager.queue),
        "message": plot_manager.status_message,
        "stats": {
            "duration_str": str(datetime.timedelta(seconds=duration)),
            "pen_name": active_pen.get('name', 'Unknown'),
            "pen_capacity": active_pen.get('capacity', 200),
            "pen_used": active_pen.get('used', 0)
            # REMOVED: "current_speed" to fix the crash
        }
    })

@app.route('/preview/<project_name>/<filename>')
def serve_preview(project_name, filename):
    path = os.path.join(PROJECTS_ROOT, project_name, "generated_batch", filename)
    if os.path.exists(path): return send_file(path)
    return "Not Found", 404

# --- 4. PROJECT & ARCHIVE ---
@app.route('/projects/<name>/archive', methods=['POST'])
def archive_project(name):
    project_path = os.path.join(PROJECTS_ROOT, name)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    archive_path = os.path.join(ARCHIVES_ROOT, name, timestamp)
    os.makedirs(archive_path, exist_ok=True)

    # Create Report
    report = {
        "archived_at": timestamp,
        "session_ink_meters": plot_manager.session_ink_meters,
        "total_time_seconds": int(time.time() - plot_manager.start_time) if plot_manager.start_time else 0,
        "pen_used_id": plot_manager.current_pen_id
    }
    with open(os.path.join(archive_path, "run_report.json"), "w") as f:
        json.dump(report, f, indent=4)

    # Move/Copy Files
    if os.path.exists(os.path.join(project_path, "input.csv")):
        shutil.move(os.path.join(project_path, "input.csv"), os.path.join(archive_path, f"input_{timestamp}.csv"))
    batch_dir = os.path.join(project_path, "generated_batch")
    if os.path.exists(batch_dir):
        shutil.move(batch_dir, os.path.join(archive_path, "plots"))
    if os.path.exists(os.path.join(project_path, "project_settings.json")):
        shutil.copy(os.path.join(project_path, "project_settings.json"), os.path.join(archive_path, "settings_snapshot.json"))
    if os.path.exists(os.path.join(project_path, "template.svg")):
        shutil.copy(os.path.join(project_path, "template.svg"), os.path.join(archive_path, "layout_snapshot.svg"))

    return jsonify({"success": True})

# --- STANDARD CRUD ---
@app.route('/projects', methods=['GET'])
def list_projects():
    if not os.path.exists(PROJECTS_ROOT): os.makedirs(PROJECTS_ROOT)
    return jsonify({"projects": sorted(os.listdir(PROJECTS_ROOT))})

@app.route('/projects/create', methods=['POST'])
def create_project():
    name = request.json.get('name')
    if not name: return jsonify({"error": "No name"}), 400
    safe_name = "".join(x for x in name if x.isalnum() or x == "_")
    if not safe_name: return jsonify({"error": "Invalid name"}), 400

    path = os.path.join(PROJECTS_ROOT, safe_name)
    if os.path.exists(path): return jsonify({"error": "Exists"}), 400
    os.makedirs(path)
    with open(os.path.join(path, "project_settings.json"), "w") as f: json.dump({}, f)
    return jsonify({"success": True})

@app.route('/projects/<name>/details', methods=['GET'])
def get_project_details(name):
    path = os.path.join(PROJECTS_ROOT, name)
    if not os.path.exists(path): return jsonify({"error": "Not found"}), 404
    settings = {}
    if os.path.exists(os.path.join(path, "project_settings.json")):
        with open(os.path.join(path, "project_settings.json")) as f: settings = json.load(f)
    has_csv = os.path.exists(os.path.join(path, "input.csv"))
    has_template = os.path.exists(os.path.join(path, "template.svg"))
    batch_path = os.path.join(path, "generated_batch")
    svg_count = len([f for f in os.listdir(batch_path) if f.endswith('.svg')]) if os.path.exists(batch_path) else 0
    return jsonify({"settings": settings, "has_csv": has_csv, "has_template": has_template, "svg_count": svg_count})

@app.route('/projects/<name>/generate', methods=['POST'])
def generate_project(name):
    data = request.json
    project_path = os.path.join(PROJECTS_ROOT, name)
    with open(os.path.join(project_path, "project_settings.json"), "w") as f: json.dump(data, f)
    result = generate_batch_api(
        project_path=project_path,
        font_name=data.get('font'),
        body_template=data.get('template'),
        offset_x=float(data.get('offset_x', 0)),
        offset_y=float(data.get('offset_y', 0))
    )
    return jsonify(result)

@app.route('/projects/<name>/save', methods=['POST'])
def save_settings(name):
    with open(os.path.join(PROJECTS_ROOT, name, "project_settings.json"), "w") as f: json.dump(request.json, f)
    return jsonify({"success": True})

@app.route('/status', methods=['GET'])
def status(): return jsonify({"status": "online"})

@app.route('/machine', methods=['POST'])
def machine_control():
    action = request.json.get('command')
    if action == "pen_up":
        subprocess.run([AXICLI_PATH, '--mode', 'manual', '--manual_cmd', 'raise_pen'])
        subprocess.run([AXICLI_PATH, '--mode', 'manual', '--manual_cmd', 'disable_xy'])
    elif action == "pen_down":
        subprocess.run([AXICLI_PATH, '--mode', 'manual', '--manual_cmd', 'lower_pen'])
        subprocess.run([AXICLI_PATH, '--mode', 'manual', '--manual_cmd', 'disable_xy'])
    elif action == "motors_off":
        subprocess.run([AXICLI_PATH, '--mode', 'manual', '--manual_cmd', 'disable_xy'])
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    print("🔒 Linecraft OS (Secured Localhost) Running...")
    app.run(host='127.0.0.1', port=5000, debug=False)
