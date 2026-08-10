import time
from functools import lru_cache
from typing import Callable, Dict, Tuple

import cv2
import numpy as np


@lru_cache(maxsize=16)
def _meshgrid(w: int, h: int) -> Tuple[np.ndarray, np.ndarray]:
    """Cached coordinate grid - rebuilding this every frame was the single
    most expensive part of the original rainbow-wave filter."""
    return np.meshgrid(np.arange(w), np.arange(h))


def _odd(n: int) -> int:
    n = int(n)
    return n if n % 2 == 1 else n + 1


class FilterBank:
    @staticmethod
    def dual_tone(roi: np.ndarray, intensity: float = 1.0) -> np.ndarray:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 110, 255, cv2.THRESH_BINARY)
        out = np.empty_like(roi)
        out[mask == 255] = (10, 140, 255)
        out[mask == 0] = (180, 30, 220)
        return out
        
    @staticmethod
    def thermal(roi: np.ndarray, intensity: float = 1.0) -> np.ndarray:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        return cv2.applyColorMap(gray, cv2.COLORMAP_JET)

    @staticmethod
    def sketch(roi: np.ndarray, intensity: float = 1.0) -> np.ndarray:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        inv = 255 - gray
        blur = cv2.GaussianBlur(inv, (21, 21), 0)
        sketch = cv2.divide(gray, 255 - blur, scale=256)
        return cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)

    @staticmethod
    def pixelate(roi: np.ndarray, intensity: float = 1.0) -> np.ndarray:
        h, w = roi.shape[:2]
        if h < 2 or w < 2:
            return roi
        block = max(2, int(np.interp(intensity, [0, 1], [4, 30])))
        small = cv2.resize(roi, (max(1, w // block), max(1, h // block)), interpolation=cv2.INTER_LINEAR)
        return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)

    @staticmethod
    def glitch(roi: np.ndarray, intensity: float = 1.0) -> np.ndarray:
        h, w = roi.shape[:2]
        if h < 2 or w < 2:
            return roi
        shift = int(np.interp(intensity, [0, 1], [4, 24]))
        b, g, r = cv2.split(roi)
        r = np.roll(r, shift, axis=1)
        b = np.roll(b, -shift, axis=1)
        out = cv2.merge([b, g, r])
        lines = 1 + int(intensity * 4)
        for _ in range(lines):
            y = np.random.randint(0, h)
            out[y : y + 1, :] = np.random.randint(0, 255, (1, w, 3), dtype=np.uint8)
        return out

    @staticmethod
    def invert(roi: np.ndarray, intensity: float = 1.0) -> np.ndarray:
        return 255 - roi

    @staticmethod
    def red_channel(roi: np.ndarray, intensity: float = 1.0) -> np.ndarray:
        b, g, r = cv2.split(roi)
        zeros = np.zeros_like(b)
        return cv2.merge([zeros, zeros, r])

    @staticmethod
    def edge(roi: np.ndarray, intensity: float = 1.0) -> np.ndarray:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 60, 150)
        colored = cv2.applyColorMap(edges, cv2.COLORMAP_SUMMER)
        return cv2.bitwise_and(colored, colored, mask=edges)

    @staticmethod
    def blur(roi: np.ndarray, intensity: float = 1.0) -> np.ndarray:
        k = _odd(np.interp(intensity, [0, 1], [5, 45]))
        return cv2.GaussianBlur(roi, (k, k), 0)

    @staticmethod
    def cartoon(roi: np.ndarray, intensity: float = 1.0) -> np.ndarray:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        gray_blur = cv2.medianBlur(gray, 5)
        edges = cv2.adaptiveThreshold(gray_blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
        color = cv2.bilateralFilter(roi, 9, 250, 250)
        return cv2.bitwise_and(color, cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR))

    @staticmethod
    def rainbow_wave(roi: np.ndarray, intensity: float = 1.0) -> np.ndarray:
        h, w = roi.shape[:2]
        x_coords, y_coords = _meshgrid(w, h)
        t = time.time() * 5.0
        pattern = np.sin((x_coords + y_coords) * 0.05 + t) * 127 + 128
        rainbow = cv2.applyColorMap(pattern.astype(np.uint8), cv2.COLORMAP_HSV)
        weight = np.interp(intensity, [0, 1], [0.35, 0.85])
        return cv2.addWeighted(roi, 1 - weight, rainbow, weight, 0)

    # -- new effects ----------------------------------------------------------

    @staticmethod
    def neon(roi: np.ndarray, intensity: float = 1.0) -> np.ndarray:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 40, 130)
        edges = cv2.dilate(edges, np.ones((2, 2), np.uint8), iterations=1)
        colored = cv2.applyColorMap(edges, cv2.COLORMAP_RAINBOW)
        glow = cv2.GaussianBlur(colored, (9, 9), 0)
        glow_weight = np.interp(intensity, [0, 1], [0.2, 0.9])
        return cv2.addWeighted(colored, 0.7, glow, glow_weight, 0)

    @staticmethod
    def vhs(roi: np.ndarray, intensity: float = 1.0) -> np.ndarray:
        h, w = roi.shape[:2]
        if h < 4 or w < 4:
            return roi
        shift = 1 + int(intensity * 6)
        b, g, r = cv2.split(roi)
        r = np.roll(r, shift, axis=1)
        b = np.roll(b, -shift, axis=1)
        out = cv2.merge([b, g, r]).astype(np.float32)
        scan = np.tile(np.array([1.0, 0.7], dtype=np.float32), h // 2 + 1)[:h].reshape(-1, 1, 1)
        out *= scan
        noise_std = np.interp(intensity, [0, 1], [2.0, 14.0])
        noise = np.random.normal(0, noise_std, out.shape).astype(np.float32)
        return np.clip(out + noise, 0, 255).astype(np.uint8)

    @staticmethod
    def night_vision(roi: np.ndarray, intensity: float = 1.0) -> np.ndarray:
        h, w = roi.shape[:2]
        gray = cv2.equalizeHist(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY))
        out = np.zeros_like(roi)
        out[:, :, 1] = gray
        yy, xx = np.mgrid[0:h, 0:w]
        dist = np.sqrt((xx - w / 2) ** 2 + (yy - h / 2) ** 2)
        max_dist = dist.max() or 1.0
        vignette = 1 - (dist / max_dist) * 0.6
        out = (out * vignette[..., None]).astype(np.uint8)
        noise_amount = int(np.interp(intensity, [0, 1], [4, 35]))
        noise = np.random.randint(0, max(1, noise_amount), (h, w), dtype=np.uint8)
        out[:, :, 1] = cv2.add(out[:, :, 1], noise)
        return out

    @staticmethod
    def posterize(roi: np.ndarray, intensity: float = 1.0) -> np.ndarray:
        levels = max(2, int(np.interp(intensity, [0, 1], [8, 2])))
        step = 256 // levels
        return (roi // step * step + step // 2).astype(np.uint8)

    @staticmethod
    def kaleidoscope(roi: np.ndarray, intensity: float = 1.0) -> np.ndarray:
        h, w = roi.shape[:2]
        if h < 4 or w < 4:
            return roi
        half_h, half_w = max(1, h // 2), max(1, w // 2)
        tile = cv2.resize(roi, (half_w, half_h))
        top = np.hstack([tile, cv2.flip(tile, 1)])
        bottom = cv2.flip(top, 0)
        mosaic = np.vstack([top, bottom])
        return cv2.resize(mosaic, (w, h))

    @staticmethod
    def watercolor(roi: np.ndarray, intensity: float = 1.0) -> np.ndarray:
        passes = 1 + int(intensity * 3)
        smooth = roi
        for _ in range(passes):
            smooth = cv2.bilateralFilter(smooth, 7, 60, 60)
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.adaptiveThreshold(cv2.medianBlur(gray, 7), 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 4)
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        return cv2.bitwise_and(smooth, edges)

    @staticmethod
    def ascii_art(roi: np.ndarray, intensity: float = 1.0) -> np.ndarray:
        h, w = roi.shape[:2]
        cell = int(np.interp(intensity, [0, 1], [7, 18]))
        if h < cell or w < cell:
            return roi
        ramp = "@%#*+=-:. "
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        small = cv2.resize(gray, (max(1, w // cell), max(1, h // cell)), interpolation=cv2.INTER_AREA)
        color_small = cv2.resize(roi, (small.shape[1], small.shape[0]), interpolation=cv2.INTER_AREA)
        out = np.zeros_like(roi)
        sh, sw = small.shape
        ramp_len = len(ramp)
        font_scale = max(0.3, cell / 14.0)
        for gy in range(sh):
            row_y = gy * cell + cell - 2
            for gx in range(sw):
                brightness = int(small[gy, gx])
                ch = ramp[min(ramp_len - 1, (255 - brightness) * ramp_len // 256)]
                color = tuple(int(c) for c in color_small[gy, gx])
                cv2.putText(out, ch, (gx * cell, row_y), cv2.FONT_HERSHEY_PLAIN, font_scale, color, 1, cv2.LINE_AA)
        return out


FILTERS: Dict[str, Callable[[np.ndarray, float], np.ndarray]] = {
    "dual-tone": FilterBank.dual_tone,
    "thermal": FilterBank.thermal,
    "sketch": FilterBank.sketch,
    "pixelate": FilterBank.pixelate,
    "glitch": FilterBank.glitch,
    "invert": FilterBank.invert,
    "red-channel": FilterBank.red_channel,
    "edge": FilterBank.edge,
    "blur": FilterBank.blur,
    "cartoon": FilterBank.cartoon,
    "rainbow-wave": FilterBank.rainbow_wave,
    "neon": FilterBank.neon,
    "vhs": FilterBank.vhs,
    "night-vision": FilterBank.night_vision,
    "posterize": FilterBank.posterize,
    "kaleidoscope": FilterBank.kaleidoscope,
    "watercolor": FilterBank.watercolor,
    "ascii": FilterBank.ascii_art,
}
