"""
SHolo: Holographic 3D Interaction System

Main script that initializes the 3D viewer and manages eye and hand tracking.
"""

import cv2
from threading import Thread
import pyglet
import trimesh
from threading import Thread

import config
from eyes_tracking import track_eyes, compute_gaze_rotation
from hands_tracking import track_hands
from view_3d import HoloViewer

class StimuliRetrieverThread(Thread):
    """Thread for capturing video and tracking eyes and hands."""
    def __init__(self, viewer: HoloViewer, debug: bool = False):
        super().__init__(daemon=True)
        self.viewer = viewer
        self.debug = debug
        self.cap = cv2.VideoCapture(0)

    def run(self):
        """The main loop for video capture and processing."""
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break

            # Flip the frame horizontally for a mirror effect
            frame = cv2.flip(frame, 1)

            # Track eyes and hands
            frame = track_eyes(frame, self.update_eyes)
            frame = track_hands(frame, self.viewer.swipe, self.viewer.stop_rotation)

            if self.debug:
                cv2.imshow("SHolo Detection", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        self.stop()

    def stop(self):
        """Release resources and close windows."""
        self.cap.release()
        if self.debug:
            cv2.destroyAllWindows()
        pyglet.app.exit()

    def update_eyes(self, screen_x: int, screen_y: int, distance_cm: float):
        """Callback to update the camera angle based on gaze."""
        angle, direction = compute_gaze_rotation(screen_x, screen_y, distance_cm)
        self.viewer.set_camera_angle(angle, direction)


if __name__ == '__main__':
    # Load 3D model and create scene
    mesh = trimesh.load(config.GLB_PATH, force='mesh')
    scene = trimesh.Scene(mesh)

    # Create Hologram viewer
    viewer = HoloViewer(scene, fullscreen=False, background=(0, 0, 0, 1))
    viewer.set_fullscreen(True)

    # Create and start the stimuli retriever thread
    stimuli_thread = StimuliRetrieverThread(viewer, debug=True)
    stimuli_thread.start()

    # Start the pyglet event loop
    pyglet.app.run()
