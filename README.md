# RetroLens

RetroLens turns your webcam into a hand-controlled portal: hold up your
hands, and the space between your fingers becomes a window into a live
video filter — glitch, thermal, sketch, neon, VHS, and a dozen others.
No mouse, no keyboard required (though both still work) — everything
is driven by hand gestures read through MediaPipe.

This is a rebuild of the original single-file `retro_lens.py` prototype:
same core idea (fingertip polygon → filtered ROI → composited back into
frame), restructured into a small package, with the render pipeline
optimized and a batch of new features layered on top.

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

| File                    | Responsibility                                                      |
| ----------------------- | ------------------------------------------------------------------- |
| `retrolens/config.py`   | Every tunable constant (thresholds, sizes, smoothing)               |
| `retrolens/geometry.py` | Pure math on landmark points — no OpenCV/MediaPipe calls            |
| `retrolens/filters.py`  | The 18 visual effects, each `fn(roi, intensity) -> roi`             |
| `retrolens/portal.py`   | Composites a filtered ROI into the frame through a polygon mask     |
| `retrolens/tracker.py`  | Wraps MediaPipe Hands, adds fingertip smoothing                     |
| `retrolens/capture.py`  | Optional background-thread camera reader                            |
| `retrolens/recorder.py` | Start/stop MP4 recording of the output stream                       |
| `retrolens/hud.py`      | Status bar, filter carousel, intensity bar, help panel              |
| `retrolens/app.py`      | `RetroLensApp` — wires all of the above into one per-frame pipeline |
| `run.py`                | CLI entry point: opens the camera, runs the loop, handles keys      |

---

## Controls

| Input                                   | Effect                                  |
| --------------------------------------- | --------------------------------------- |
| Pinch thumb + index finger              | Cycle to the next filter                |
| `N` / `P`                               | Next / previous filter                  |
| `1`–`9`                                 | Jump straight to filter #1–#9           |
| Close both hands into fists             | Toggle 2D ↔ 3D portal mode              |
| `C`                                     | Toggle 2D ↔ 3D mode manually            |
| Spread two hands apart / bring together | Raise / lower filter intensity          |
| `S`                                     | Save a screenshot to `captures/`        |
| `R`                                     | Start / stop recording to `recordings/` |
| `H`                                     | Toggle the in-app help overlay          |
| `Q`                                     | Quit                                    |

**Portal shapes:** one hand draws a small quad from four of your
fingertips. Two hands draw a larger quad between them — rotate one
hand and it twists into a crossed "bowtie" shape instead. In 3D mode,
two hands draw two overlapping hexagonal portals, each running a
different filter (the current one and the next one in the list).

---

## Installation

<!-- (window and linux) -->

Requires Python 3.9–3.11 (see the [troubleshooting](#troubleshooting)
note below on why not 3.12+) and a webcam.

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

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

<!-- for mac idk man just figure it out or just GPT may be its python3 run.py (hope it works) -->
<!-- for shortcut read shortcut.sh after setup-->

Screenshots land in `captures/`, recordings in `recordings/`, both
created next to `run.py` on first use.

---

## Follow On

```
Instagram   -->    @ezphemous         https://www.instagram.com/ezphemous/
GitHub      -->    @AkshatVOfficial   https://github.com/AkshatVOfficial
Youtube     -->    @ezphemous         https://www.youtube.com/@ezphemouse
X           -->    @ezphemous         https://x.com/ezphemous
```
