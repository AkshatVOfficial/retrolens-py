#!/usr/bin/env python3
"""RetroLens entry point.

    python run.py                  # default camera, GUI window, HUD on
    python run.py --camera 1       # pick a different camera
    python run.py --threaded       # background-thread camera reads
    python run.py --no-hud         # clean output, no overlay
    python run.py --list-filters   # print available filter names and exit
"""

import argparse
import logging

import cv2

from retrolens.app import RetroLensApp
from retrolens.capture import ThreadedCamera
from retrolens.config import PipelineConfig
from retrolens.filters import FILTERS

WINDOW_NAME = "RetroLens Engine"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RetroLens - gesture-controlled AR filter portals")
    parser.add_argument("--camera", type=int, default=0, help="camera index (default: 0)")
    parser.add_argument("--width", type=int, default=960, help="capture/processing width")
    parser.add_argument("--height", type=int, default=540, help="capture/processing height")
    parser.add_argument("--no-hud", action="store_true", help="disable the on-screen overlay")
    parser.add_argument("--no-mirror", action="store_true", help="disable the selfie-mirror flip")
    parser.add_argument("--threaded", action="store_true", help="read the camera on a background thread (lower latency)")
    parser.add_argument("--list-filters", action="store_true", help="print available filter names and exit")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    args = parse_args()

    if args.list_filters:
        for name in FILTERS:
            print(name)
        return

    cfg = PipelineConfig(
        cam_index=args.camera,
        frame_width=args.width,
        frame_height=args.height,
        show_hud=not args.no_hud,
        mirror=not args.no_mirror,
    )
    app = RetroLensApp(cfg)

    cap = ThreadedCamera(cfg.cam_index).start() if args.threaded else cv2.VideoCapture(cfg.cam_index)
    if not cap.isOpened():
        logging.error("Could not open camera index %s", cfg.cam_index)
        return

    logging.info("RetroLens started - press H in the window for controls, Q to quit")
    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                logging.warning("Failed to read a frame from the camera; stopping")
                break

            out = app.process_frame(frame)
            cv2.imshow(WINDOW_NAME, out)

            key = cv2.waitKey(1) & 0xFF
            if key != 255 and not app.handle_key(key, out):
                break
    finally:
        app.close()
        if isinstance(cap, ThreadedCamera):
            cap.stop()
        else:
            cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
