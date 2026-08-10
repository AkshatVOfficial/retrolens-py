from dataclasses import dataclass
from pathlib import Path


@dataclass
class PipelineConfig:
    cam_index: int = 0
    frame_width: int = 960
    frame_height: int = 540
    mirror: bool = True

    max_num_hands: int = 2
    model_complexity: int = 1
    min_detection_confidence: float = 0.8
    min_tracking_confidence: float = 0.8

    pinch_threshold_px: float = 45.0
    filter_cooldown_sec: float = 0.15
    mode_cooldown_sec: float = 1.2
    fist_dist_threshold_px: float = 80.0

    smoothing_alpha: float = 0.55

    intensity_span_px: tuple = (80.0, 520.0)
    intensity_smoothing: float = 0.2

    show_hud: bool = True
    show_fps: bool = True
    captures_dir: Path = Path("captures")
    recordings_dir: Path = Path("recordings")
    session_file: Path = Path(".retrolens_session.json")
    recording_fps: float = 24.0
