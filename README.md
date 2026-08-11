# RetroLens

RetroLens turns your webcam into a hand-controlled portal: hold up your hands, and the space between your fingers becomes a window into a live video filter — glitch, thermal, sketch, neon, VHS, and a dozen others. No mouse, no keyboard required (though both still work) — everything is driven by hand gestures read through MediaPipe.

This is a rebuild of the original single-file `retro_lens.py` prototype: same core idea (fingertip polygon → filtered ROI → composited back into frame), restructured into a small package, with the render pipeline optimized and a batch of new features layered on top.

---

## How it works

```
Camera frame
   │
   ├─ flip + resize                               (app.py)
   ├─ MediaPipe hand detection                    (tracker.py)
   │     → up to 2 hands × 21 landmarks each
   ├─ per-hand gesture checks                     (geometry.py)
   │     • thumb-index pinch  → cycle filter
   │     • closed fist × 2    → toggle 2D/3D mode
   │     • wrist-to-wrist gap → filter intensity
   ├─ build a portal polygon from fingertips       (app.py)
   │     • 1 hand   → small quad from 4 fingertips
   │     • 2 hands  → quad (or "bowtie" if hands are rotated)
   │     • 3D mode  → two overlapping hex portals, two filters
   ├─ run the active filter(s) on that ROI         (filters.py)
   ├─ feather-blend the result back into the frame (portal.py)
   ├─ draw HUD / help / recording indicator        (hud.py)
   └─ optionally write the frame to disk           (recorder.py)
```

### Module map

| File | Responsibility |
| :--- | :--- |
| `retrolens/config.py` | Every tunable constant (thresholds, sizes, smoothing) |
| `retrolens/geometry.py` | Pure math on landmark points — no OpenCV/MediaPipe calls |
| `retrolens/filters.py` | The 18 visual effects, each `fn(roi, intensity) -> roi` |
| `retrolens/portal.py` | Composites a filtered ROI into the frame through a polygon mask |
| `retrolens/tracker.py` | Wraps MediaPipe Hands, adds fingertip smoothing |
| `retrolens/capture.py` | Optional background-thread camera reader |
| `retrolens/recorder.py` | Start/stop MP4 recording of the output stream |
| `retrolens/hud.py` | Status bar, filter carousel, intensity bar, help panel |
| `retrolens/app.py` | `RetroLensApp` — wires all of the above into one per-frame pipeline |
| `run.py` | CLI entry point: opens the camera, runs the loop, handles keys |

---

## Controls

| Input | Effect |
| :--- | :--- |
| Pinch thumb + index finger | Cycle to the next filter |
| `N` / `P` | Next / previous filter |
| `1`–`9` | Jump straight to filter #1–#9 |
| Close both hands into fists | Toggle 2D ↔ 3D portal mode |
| `C` | Toggle 2D ↔ 3D mode manually |
| Spread two hands apart / bring together | Raise / lower filter intensity |
| `S` | Save a screenshot to `captures/` |
| `R` | Start / stop recording to `recordings/` |
| `H` | Toggle the in-app help overlay |
| `Q` | Quit |

**Portal shapes:** one hand draws a small quad from four of your fingertips. Two hands draw a larger quad between them — rotate one hand and it twists into a crossed "bowtie" shape instead. In 3D mode, two hands draw two overlapping hexagonal portals, each running a different filter (the current one and the next one in the list).

---

## Installation

### Requirements & Prerequisites
* **Python 3.9–3.11** (MediaPipe binaries require Python 3.9–3.11).
* **Webcam**.
* **Git** (to clone the repository).

---

### Step-by-Step Setup

#### 1. Clone the repository
```bash
git clone https://github.com/AkshatVOfficial/RetroLens.git
cd RetroLens
```

---

#### 2. Environment Setup by Operating System

<details>
<summary><b>Windows Setup</b></summary>

1. **Verify Python Installation:**
   ```cmd
   python --version
   ```
   *Ensure the version output is between `3.9.x` and `3.11.x`.*

2. **Create and Activate Virtual Environment:**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```
   *(If you encounter execution policy errors in PowerShell, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` first).*

3. **Install Dependencies:**
   ```cmd
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
</details>

<details>
<summary><b>macOS Setup</b></summary>

1. **Verify Python Installation:**
   ```bash
   python3 --version
   ```
   *If you do not have Python 3.9–3.11, install it via Homebrew (`brew install python@3.11`) or download it from [python.org](https://www.python.org/).*

2. **Create and Activate Virtual Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Camera Permissions:**
   * Open **System Settings > Privacy & Security > Camera**.
   * Grant permission to **Terminal** (or **iTerm2** / **VS Code**, depending on where you execute the script).
</details>

<details>
<summary><b>Linux Setup (Ubuntu / Debian / Arch / Fedora)</b></summary>

1. **Install System Dependencies & Python:**
   OpenCV and MediaPipe require basic system OpenGL and GTK libraries to open windows.

   * **Ubuntu/Debian:**
     ```bash
     sudo apt update
     sudo apt install python3.11 python3.11-venv python3-pip libgl1-mesa-glx libgtk-3-dev libglib2.0-0
     ```
   * **Arch Linux:**
     ```bash
     sudo pacman -S python opencv hdf5
     ```
   * **Fedora:**
     ```bash
     sudo dnf install python3.11 mesa-libGL gtk3
     ```

2. **Create and Activate Virtual Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
</details>

---

## Running

```bash
python run.py                  # default camera, GUI window, HUD on
python run.py --camera 1       # use a different camera index
python run.py --threaded       # background-thread camera reads (lower latency)
python run.py --no-hud         # clean output, no overlay
python run.py --no-mirror      # disable the selfie-mirror flip
python run.py --width 1280 --height 720
python run.py --list-filters   # print all filter names and exit
```

Screenshots land in `captures/`, recordings in `recordings/`, both created next to `run.py` on first use.

---

## Troubleshooting

* **`No matching distribution found for mediapipe`**: You are likely using Python 3.12 or newer. Create your virtual environment using an explicit Python 3.11 path (e.g., `python3.11 -m venv venv`).
* **Black screen / Camera initialization error**: Try passing a different camera index (`python run.py --camera 1`) or ensure no other app (Zoom, Teams, etc.) is locking the webcam.
* **`qt.qpa.plugin: Could not load the Qt platform plugin` (Linux)**: Run `pip install opencv-python-headless` or ensure `libgl1-mesa-glx` is installed on your system.

---

## Follow On

```
Instagram   -->    @ezphemous         https://www.instagram.com/ezphemous/
GitHub      -->    @AkshatVOfficial   https://github.com/AkshatVOfficial
Youtube     -->    @ezphemous         https://www.youtube.com/@ezphemouse
X           -->    @ezphemous         https://x.com/ezphemous
```
