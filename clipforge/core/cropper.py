"""Computer vision smart face-tracking and 9:16 framing module."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional


@dataclass
class CropWindow:
    """Calculated 9:16 crop window coordinates."""
    crop_x: int  # Horizontal offset from left edge of 16:9 frame
    crop_width: int
    crop_height: int


class SmartCropper:
    """Tracks human face positions in 16:9 video to calculate optimal 9:16 vertical crop."""

    def __init__(self):
        self._face_cascade = None

    def _get_cascade(self):
        if self._face_cascade is None:
            try:
                import cv2
                cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                self._face_cascade = cv2.CascadeClassifier(cascade_path)
            except ImportError:
                raise ImportError(
                    "OpenCV is required for face tracking. Install with: pip install opencv-python-headless"
                )
        return self._face_cascade

    def calculate_optimal_crop(
        self,
        video_path: Path,
        start_time: float,
        end_time: float,
        sample_fps: float = 2.0,
    ) -> CropWindow:
        """
        Samples frames across the clip window, identifies the dominant face centroid,
        and returns a smoothed horizontal crop offset to frame the speaker vertically.
        """
        import cv2
        import numpy as np

        cascade = self._get_cascade()
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise IOError(f"Cannot open video file: {video_path}")

        orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        video_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

        # Target 9:16 width given source height
        target_crop_w = int(orig_h * (9 / 16))
        # Ensure even width
        if target_crop_w % 2 != 0:
            target_crop_w -= 1

        default_center_x = orig_w // 2

        start_frame = int(start_time * video_fps)
        end_frame = int(end_time * video_fps)
        step_frames = max(1, int(video_fps / sample_fps))

        face_centers_x: List[int] = []

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        curr_frame_idx = start_frame

        while curr_frame_idx < end_frame:
            ret, frame = cap.read()
            if not ret:
                break

            if (curr_frame_idx - start_frame) % step_frames == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=4, minSize=(60, 60)
                )

                if len(faces) > 0:
                    # Pick the largest face (assumed primary speaker)
                    largest_face = max(faces, key=lambda f: f[2] * f[3])
                    x, y, w, h = largest_face
                    face_center_x = x + (w // 2)
                    face_centers_x.append(face_center_x)

            curr_frame_idx += 1

        cap.release()

        # Compute smoothed target X coordinate
        if face_centers_x:
            # Use median to resist outliers
            median_face_x = int(np.median(face_centers_x))
            target_center_x = median_face_x
        else:
            # Fall back to centered crop if no face was detected
            target_center_x = default_center_x

        # Calculate left crop_x bounded within video boundaries
        crop_x = target_center_x - (target_crop_w // 2)
        crop_x = max(0, min(crop_x, orig_w - target_crop_w))

        # Ensure even pixel offset for FFmpeg encoders
        if crop_x % 2 != 0:
            crop_x -= 1

        return CropWindow(
            crop_x=crop_x,
            crop_width=target_crop_w,
            crop_height=orig_h,
        )
