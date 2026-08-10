import json
import time
from typing import List

import cv2
import numpy as np

from .config import PipelineConfig
from .filters import FILTERS
from .geometry import GeometryUtils
from .hud import Hud
from .portal import PortalRenderer
from .recorder import SessionRecorder
from .tracker import HandTracker

# Landmark indices for thumb, index, middle, ring, pinky tips.
FINGERTIP_IDS = (4, 8, 12, 16, 20)


class RetroLensApp:
    def __init__(self, cfg: PipelineConfig):
        self.cfg = cfg
        self.tracker = HandTracker(cfg)
        self.recorder = SessionRecorder(cfg)

        self.filter_keys: List[str] = list(FILTERS.keys())
        self.active_idx = 0
        self.is_3d_mode = False
        self.show_hud = cfg.show_hud
        self.show_help = False
        self.intensity = 0.5

        self.last_switch_time = 0.0
        self.last_mode_toggle = 0.0
        self._fps_ema = 0.0
        self._last_tick = time.time()

        self._load_session()

    # persistence 
    def _load_session(self) -> None:
        try:
            if self.cfg.session_file.exists():
                data = json.loads(self.cfg.session_file.read_text())
                self.active_idx = data.get("filter_idx", 0) % len(self.filter_keys)
                self.is_3d_mode = bool(data.get("is_3d_mode", False))
        except (OSError, ValueError, json.JSONDecodeError):
            pass  

    def _save_session(self) -> None:
        try:
            self.cfg.session_file.write_text(
                json.dumps({"filter_idx": self.active_idx, "is_3d_mode": self.is_3d_mode})
            )
        except OSError:
            pass

    # filter
    @property
    def current_filter(self) -> str:
        return self.filter_keys[self.active_idx]

    @property
    def secondary_filter(self) -> str:
        return self.filter_keys[(self.active_idx + 1) % len(self.filter_keys)]

    def cycle_filter(self, step: int = 1) -> None:
        self.active_idx = (self.active_idx + step) % len(self.filter_keys)

    def jump_to_filter(self, n: int) -> None:
        if 0 <= n < len(self.filter_keys):
            self.active_idx = n

    def _update_fps(self) -> float:
        now = time.time()
        dt = now - self._last_tick
        self._last_tick = now
        if dt > 0:
            inst = 1.0 / dt
            self._fps_ema = inst if self._fps_ema == 0 else 0.9 * self._fps_ema + 0.1 * inst
        return self._fps_ema

# frames
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        if self.cfg.mirror:
            frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (self.cfg.frame_width, self.cfg.frame_height))
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False  
        results = self.tracker.process(rgb)
        now = time.time()

        all_tips: List[List[tuple]] = []
        wrists: List[tuple] = []
        fist_count = 0
        is_bowtie = False

        if results.multi_hand_landmarks:
            for idx, hand_lm in enumerate(results.multi_hand_landmarks):
                self.tracker.draw(frame, hand_lm)
                lm = hand_lm.landmark

                raw_tips = np.array(
                    [(lm[i].x * self.cfg.frame_width, lm[i].y * self.cfg.frame_height) for i in FINGERTIP_IDS],
                    dtype=np.float32,
                )
                smoothed = self.tracker.smooth_tips(idx, raw_tips)
                tip_pts = [(int(px), int(py)) for px, py in smoothed]
                all_tips.append(tip_pts)
                wrists.append((lm[0].x * self.cfg.frame_width, lm[0].y * self.cfg.frame_height))

                # thumb-index pinch -> cycle to the next filter
                if GeometryUtils.euclidean_dist(tip_pts[0], tip_pts[1]) < self.cfg.pinch_threshold_px:
                    if now - self.last_switch_time > self.cfg.filter_cooldown_sec:
                        self.cycle_filter(1)
                        self.last_switch_time = now

                if GeometryUtils.is_fist_closed(lm, self.cfg.frame_width, self.cfg.frame_height, self.cfg.fist_dist_threshold_px):
                    fist_count += 1

            self.tracker.reset_smoothing(len(all_tips))

        # 3d toggle
            if fist_count == 2 and now - self.last_mode_toggle > self.cfg.mode_cooldown_sec:
                self.is_3d_mode = not self.is_3d_mode
                self.last_mode_toggle = now

# 
            if len(wrists) == 2:
                spread = GeometryUtils.euclidean_dist(wrists[0], wrists[1])
                lo, hi = self.cfg.intensity_span_px
                target = float(np.clip((spread - lo) / (hi - lo), 0.0, 1.0))
                self.intensity += (target - self.intensity) * self.cfg.intensity_smoothing

            frame, is_bowtie = self._render_portals(frame, all_tips)
        else:
            self.tracker.reset_smoothing(0)

        fps = self._update_fps() if self.cfg.show_fps else 0.0
        if self.show_hud:
            mode_str = "3D Mesh" if self.is_3d_mode else ("2D Bowtie" if is_bowtie else "2D Quad")
            frame = Hud.draw(
                frame,
                mode_str=mode_str,
                filter_names=self.filter_keys,
                active_idx=self.active_idx,
                fps=fps,
                intensity=self.intensity,
                is_recording=self.recorder.is_recording,
                rec_elapsed=self.recorder.elapsed(),
                show_help=self.show_help,
            )

        self.recorder.write(frame)
        return frame

    def _render_portals(self, frame, all_tips):
        """Returns (frame, is_bowtie) - is_bowtie is only ever True in 2D
        two-hand mode and is used purely to label the HUD."""
        is_bowtie = False
        if self.is_3d_mode:
            if len(all_tips) == 2:
                t1, t2 = all_tips[0], all_tips[1]
                frame = PortalRenderer.render(
                    frame, [t1[0], t1[1], t1[2], t2[2], t2[1], t2[0]], FILTERS[self.current_filter], self.intensity
                )
                frame = PortalRenderer.render(
                    frame, [t1[2], t1[3], t1[4], t2[4], t2[3], t2[2]], FILTERS[self.secondary_filter], self.intensity
                )
            elif len(all_tips) == 1:
                frame = PortalRenderer.render(frame, all_tips[0], FILTERS[self.current_filter], self.intensity)
        else:
            if len(all_tips) == 2:
                corners = [all_tips[0][0], all_tips[0][1], all_tips[1][0], all_tips[1][1]]
                if GeometryUtils.is_hand_rotated(corners[0], corners[1]) or GeometryUtils.is_hand_rotated(corners[2], corners[3]):
                    quad = GeometryUtils.sort_quad_bowtie(corners)
                    is_bowtie = True
                else:
                    quad = GeometryUtils.sort_quad_clean(corners)
                frame = PortalRenderer.render(frame, quad, FILTERS[self.current_filter], self.intensity)
            elif len(all_tips) == 1:
                t = all_tips[0]
                frame = PortalRenderer.render(frame, [t[0], t[1], t[2], t[4]], FILTERS[self.current_filter], self.intensity)
        return frame, is_bowtie

        # keyboard      
    def handle_key(self, key: int, frame: np.ndarray) -> bool:
        """Returns False when the app should exit."""
        if key == ord("q"):
            return False
        elif key == ord("c"):
            self.is_3d_mode = not self.is_3d_mode
        elif key == ord("n"):
            self.cycle_filter(1)
        elif key == ord("p"):
            self.cycle_filter(-1)
        elif key == ord("h"):
            self.show_help = not self.show_help
        elif key == ord("r"):
            self.recorder.toggle(frame.shape)
        elif key == ord("s"):
            self._save_screenshot(frame)
        elif ord("1") <= key <= ord("9"):
            self.jump_to_filter(key - ord("1"))
        return True

    def _save_screenshot(self, frame: np.ndarray) -> None:
        self.cfg.captures_dir.mkdir(parents=True, exist_ok=True)
        path = self.cfg.captures_dir / f"cap_{int(time.time())}.png"
        cv2.imwrite(str(path), frame)

    def close(self) -> None:
        self._save_session()
        self.recorder.stop()
        self.tracker.close()
