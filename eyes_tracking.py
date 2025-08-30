"""
Eyes Tracking Module

Tracks the user's gaze and estimates their distance from the screen.
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import Callable

import config

class EyeTracker:
    """Encapsulates eye tracking logic using MediaPipe Face Mesh."""

    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        
        # Eye landmarks indices
        self.left_eye_indices = [33, 133, 159, 145]
        self.right_eye_indices = [362, 263, 386, 374]

    def get_eye_center(self, landmarks, eye_indices: list[int]) -> np.ndarray:
        """Compute the center of the eye from landmark points."""
        eye_points = np.array([(landmarks[i].x, landmarks[i].y) for i in eye_indices])
        return np.mean(eye_points, axis=0)

    def estimate_distance(self, ipd_px: float) -> float:
        """Estimate distance from the screen using the inter-pupillary distance."""
        return (config.IPD_REAL_CM * config.FOCAL_LENGTH_PX) / ipd_px

    def track(self, frame: np.ndarray, update_eyes_callback: Callable[[int, int, float], None]) -> np.ndarray:
        """Detects eye position and estimates gaze direction."""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(frame_rgb)

        if results.multi_face_landmarks: # type: ignore
            for face_landmarks in results.multi_face_landmarks: # type: ignore
                landmarks = face_landmarks.landmark

                # Compute eye centers
                left_eye_center = self.get_eye_center(landmarks, self.left_eye_indices)
                right_eye_center = self.get_eye_center(landmarks, self.right_eye_indices)
                
                # Convert to pixel coordinates
                left_x, left_y = int(left_eye_center[0] * config.CAMERA_WIDTH), int(left_eye_center[1] * config.CAMERA_HEIGHT)
                right_x, right_y = int(right_eye_center[0] * config.CAMERA_WIDTH), int(right_eye_center[1] * config.CAMERA_HEIGHT)
                
                # Draw circles on eyes
                cv2.circle(frame, (left_x, left_y), 5, (0, 0, 255), -1)
                cv2.circle(frame, (right_x, right_y), 5, (0, 0, 255), -1)
                
                # Compute eye distance in pixels
                ipd_px = np.linalg.norm(np.array([left_x, left_y]) - np.array([right_x, right_y]))
                distance_cm = self.estimate_distance(ipd_px) # type: ignore
                
                # Compute relative gaze direction
                eye_avg_x = (left_x + right_x) / 2
                eye_avg_y = (left_y + right_y) / 2
                relative_x = (eye_avg_x - config.CAMERA_WIDTH / 2) / (config.CAMERA_WIDTH / 2)
                relative_y = (eye_avg_y - config.CAMERA_HEIGHT / 2) / (config.CAMERA_HEIGHT / 2)
                
                # Convert to screen coordinates
                screen_x = int((relative_x + 1) / 2 * config.SCREEN_RESOLUTION[0])
                screen_y = int((relative_y + 1) / 2 * config.SCREEN_RESOLUTION[1])
                
                # Display gaze estimation and distance
                text = f"Gaze: ({screen_x}, {screen_y}) | Distance: {distance_cm:.1f} cm"
                cv2.putText(frame, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (89, 123, 0), 2)

                # Callback
                update_eyes_callback(screen_x, screen_y, distance_cm)

        return frame

def compute_gaze_rotation(screen_x: int, screen_y: int, distance_cm: float) -> tuple[float, list[float]]:
    """Calculates camera rotation based on eye tracking and perspective."""
    center_x = config.SCREEN_RESOLUTION[0] / 2
    center_y = config.SCREEN_RESOLUTION[1] / 2

    dx = screen_x - center_x
    dy = screen_y - center_y

    dx_cm = (dx / config.SCREEN_RESOLUTION[0]) * config.SCREEN_WIDTH_CM
    dy_cm = (dy / config.SCREEN_RESOLUTION[1]) * config.SCREEN_HEIGHT_CM
    
    scene_distance_cm = config.SCENE_SCREEN_DISTANCE_CM + distance_cm
    yaw_angle = np.arctan2(dx_cm, scene_distance_cm)  
    pitch_angle = np.arctan2(dy_cm, scene_distance_cm)  
    
    angle = np.sqrt(yaw_angle**2 + pitch_angle**2)
    direction = np.array([pitch_angle, yaw_angle, 0])
    
    norm = np.linalg.norm(direction)
    if norm > 0:
        direction /= norm  
    
    return -float(angle), direction.tolist()

# --- Backward compatibility / Singleton instance ---
_tracker = EyeTracker()

def track_eyes(frame: np.ndarray, update_eyes_function: Callable[[int, int, float], None]) -> np.ndarray:
    """Public function to be called from other modules."""
    return _tracker.track(frame, update_eyes_function)


if __name__ == '__main__':

    # Open webcam
    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
        
        frame = track_eyes(frame, lambda x, y, d: print(end='' if d > 20 else f'Too close to the screen! (x: {x}, y: {y})\n'))
        
        # Show frame
        cv2.imshow("Eye Tracking", frame)
        
        # Exit with 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
