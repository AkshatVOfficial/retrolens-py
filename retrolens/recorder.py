import time
from pathlib import Path
from typing import Optional, Tuple

import cv2

from .config import PipelineConfig


class SessionRecorder:
    def __init__(self, cfg: PipelineConfig):
        self.cfg = cfg
        self.writer: Optional[cv2.VideoWriter] = None
        self.is_recording = False
        self._start_time = 0.0
        self.last_path: Optional[Path] = None

    def toggle(self, frame_shape: Tuple[int, int, int]) -> None:
        if self.is_recording:
            self.stop()
        else:
            self.start(frame_shape)

    def start(self, frame_shape: Tuple[int, int, int]) -> None:
        self.cfg.recordings_dir.mkdir(parents=True, exist_ok=True)
        path = self.cfg.recordings_dir / f"retrolens_{int(time.time())}.mp4"
        h, w = frame_shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.writer = cv2.VideoWriter(str(path), fourcc, self.cfg.recording_fps, (w, h))
        self.is_recording = True
        self._start_time = time.time()
        self.last_path = path

    def stop(self) -> None:
        if self.writer is not None:
            self.writer.release()
        self.writer = None
        self.is_recording = False

    def write(self, frame) -> None:
        if self.is_recording and self.writer is not None:
            self.writer.write(frame)

    def elapsed(self) -> float:
        return time.time() - self._start_time if self.is_recording else 0.0
