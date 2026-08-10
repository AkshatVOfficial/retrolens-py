import threading
from typing import Optional, Tuple

import numpy as np

try:
    import cv2
except ImportError: 
    cv2 = None


class ThreadedCamera:
    def __init__(self, index: int):
        self.cap = cv2.VideoCapture(index)
        self._ret, self._frame = self.cap.read()
        self._stopped = False
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._update, daemon=True)

    def start(self) -> "ThreadedCamera":
        self._thread.start()
        return self

    def _update(self) -> None:
        while not self._stopped:
            ret, frame = self.cap.read()
            with self._lock:
                self._ret, self._frame = ret, frame

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        with self._lock:
            if self._frame is None:
                return self._ret, None
            return self._ret, self._frame.copy()

    def isOpened(self) -> bool:
        return self.cap.isOpened()

    def stop(self) -> None:
        self._stopped = True
        self._thread.join(timeout=1.0)
        self.cap.release()
