"""
Hand Tracking Module

Detects hand gestures and interprets them as swipe or stop commands.
"""

import cv2
from cv2.typing import MatLike
import mediapipe as mp
import numpy as np
import time
from typing import Callable

import config

class HandTracker:
    """Encapsulates hand tracking logic using MediaPipe."""

    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
        self.mp_draw = mp.solutions.drawing_utils

        # Parameters for movement tracking
        self.prev_x = None
        self.hand_visible = False
        self.last_seen_time = time.time()
        self.last_gesture_time = 0

    def track(self, frame: MatLike, swipe_callback: Callable[[float], None], stop_callback: Callable[[], None]) -> MatLike:
        """Tracks hand movements for gestures like swipe and stop."""
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb_frame)
        current_time = time.time()

        if result.multi_hand_landmarks: # type: ignore
            self.hand_visible = True
            self.last_seen_time = current_time

            for hand_landmarks in result.multi_hand_landmarks: # type: ignore
                self.handle_swipe(frame, hand_landmarks, current_time, swipe_callback)
                self.handle_stop_gesture(frame, hand_landmarks, current_time, stop_callback)
                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS) # type: ignore
        else:
            if self.hand_visible and (current_time - self.last_seen_time > config.VISIBILITY_RESET_TIME):
                self.prev_x = None
                self.hand_visible = False

        return frame

    def handle_swipe(self, frame: MatLike, hand_landmarks, current_time: float, swipe_callback: Callable[[float], None]):
        """Detects and handles swipe gestures."""
        h, w, _ = frame.shape
        x = hand_landmarks.landmark[0].x

        if self.prev_x is not None:
            movement = x - self.prev_x
            if abs(movement) > config.SWIPE_THRESHOLD and (current_time - self.last_gesture_time > config.GESTURE_COOLDOWN):
                swipe_magnitude = round(abs(movement) * 10, 2)
                direction = "Right" if movement > 0 else "Left"
                self.last_gesture_time = current_time

                cv2.arrowedLine(frame, (int(w * x), h // 2), (int(w * (x + movement * 5)), h // 2), (255, 0, 0), 5, tipLength=0.5)
                cv2.putText(frame, f"Swipe {direction} - Magnitude: {swipe_magnitude}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
                
                swipe_callback((1 if movement > 0 else -1) * swipe_magnitude)
        
        self.prev_x = x

    def handle_stop_gesture(self, frame: MatLike, hand_landmarks, current_time: float, stop_callback: Callable[[], None]):
        """Detects and handles the open palm (stop) gesture."""
        h, w, _ = frame.shape
        finger_tips = [hand_landmarks.landmark[i].y for i in [4, 8, 12, 16, 20]]
        palm_center = hand_landmarks.landmark[0].y
        openness = abs(np.mean([tip - palm_center for tip in finger_tips]))

        if openness > config.STOP_THRESHOLD and (current_time - self.last_gesture_time > config.GESTURE_COOLDOWN):
            self.last_gesture_time = current_time
            cv2.putText(frame, "STOP!", (w // 2 - 50, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4)
            stop_callback()

# --- Backward compatibility / Singleton instance ---
_tracker = HandTracker()

def track_hands(frame: MatLike, swipe_function: Callable[[float], None], stop_function: Callable[[], None]) -> MatLike:
    """Tracks hand movements for gestures like swipe and stop. To be called from other modules."""
    return _tracker.track(frame, swipe_function, stop_function)


if __name__ == '__main__':
    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = track_hands(frame, lambda m: print(f"Swipe {'Right' if m > 0 else 'Left'}, magnitude: {abs(m)}"), lambda: print("Stop"))

        cv2.imshow("Hand Gesture Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
