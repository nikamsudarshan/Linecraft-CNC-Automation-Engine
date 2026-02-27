![Linecraft Automated Workcell](Linecraft_Automated_Workcell.jpg)

# Linecraft CNC Automation Engine ⚙️✍️

### Overview & Context

This system was engineered as the proprietary production backend for **Linecraft Studios**. It is a full-stack hardware orchestration pipeline designed to eliminate manual CNC plotting. The engine seamlessly bridges digital data structures (CSVs, AI-generated text payloads) with physical mechatronic execution, translating variable data into precise, single-stroke paths for a 2-axis CNC machine (AxiDraw).

### 🔬 Applications in Research & Lab Automation

While built for automated handwriting, the core architecture of this system translates directly to **High-Throughput Experimentation** and **Lab Automation (DAQ)**. It demonstrates the ability to:

* Programmatically map variable datasets to physical $X, Y$ coordinate systems.
* Manage hardware state, queues, and continuous operation in a Linux environment.
* Build resilient Python wrappers around existing CLI tools to automate physical hardware without connection drops.

---

### 🏗️ System Architecture & Workflow

The system operates on a continuous software-to-hardware loop:

1. **Data Ingestion (CSV/AI):** A Python backend reads batch data from CSV files. For dynamic content, AI-synthesized text (via external LLM agents) can be routed directly into the data payload.
2. **Vector Template Engine:** Base designs are created as standard Inkscape `.svg` files with embedded variable placeholders (e.g., `{{Name}}`, `{{Address}}`).
3. **Custom Font Processing:** The system parses custom single-stroke Python fonts, calculating exact X and Y offsets to map fixed characters into the SVG placeholders mathematically.
4. **Hardware Orchestration:** A Flask-based API manages the plotting queue. To ensure maximum stability on Linux, the system bypasses native serial libraries and uses Python's `subprocess` to directly execute the AxiDraw Command Line Interface (`axicli`), ensuring zero dropped connections during long batch runs.
5. **Physical Telemetry:** The engine calculates total SVG path lengths using Pythagorean math to actively track and estimate physical pen ink depletion in millimeters.

---

### 📂 Repository Structure

* **`app.py`**: The core API server. Manages the frontend communication, state handling, and issues commands to the physical hardware.
* **`Linecraft_Core/job_generator.py`**: The mathematical heart of the engine. Reads the SVG templates, applies font offsets, handles text-wrapping, and generates the final machine-ready SVGs.
* **`Linecraft_Core/plot_manager.py`**: The hardware state manager. Handles the job queue (Start, Pause, Skip) and safely executes the `axicli` commands.
* **`Linecraft_Core/template_engine.py`**: Contains advanced geometry logic, including `_estimate_path_length` to track physical ink usage.
* **`/dashboard.html`**: The HTML/JS user interface for real-time machine control and batch monitoring.
* **`template_example.svg`**: A sample vector template demonstrating the placeholder format.
* **`sample_data.csv`**: Example data structure for batch processing.

---

### 🛠️ Technical Stack

* **Backend:** Python 3, Flask, Subprocess (for CLI wrapping)
* **Frontend:** HTML5, CSS, vanilla JavaScript
* **Vector Processing:** Native SVG DOM manipulation, custom Python dictionaries
* **Hardware Interface:** AxiDraw CLI (`axicli`)
* **Math/Logic:** Coordinate geometry, Pythagorean path estimation


### 🚀 Installation & Setup

1. **Clone the repository:**
```bash
git clone https://github.com/nikamsudarshan/Linecraft-CNC-Automation-Engine.git
cd Linecraft-CNC-Automation-Engine

```


2. **Install Python Dependencies:**
```bash
pip install -r requirements.txt

```


3. **Hardware Prerequisites:** Ensure that the **AxiDraw software and CLI tools** (EBB firmware) are installed and accessible on your machine's system PATH.
4. **Run the Automation Server:**
```bash
# Navigate to the server directory
cd Linecraft_System/Server

# Start the Flask application
python app.py

```

**Access the control dashboard:** Open your local browser and navigate to `http://localhost:5000`.

Access the control dashboard via your local browser at `http://localhost:5000`.

