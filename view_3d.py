"""
3D Scene Viewer

Handles rendering and interactions with the 3D holographic scene.
"""

import trimesh
from trimesh.viewer.windowed import SceneViewer
import trimesh.transformations as t
import pyglet
import numpy as np
import threading
import time

import config

class HoloViewer(SceneViewer):
    def __init__(self, scene, **kwargs):
        self.fps = kwargs.get('fps', 24)
        self.current_speed = kwargs.get('speed', 0)  # Initial speed
        self.base_speed = kwargs.get('base_speed', 0.125)  # Constant rotation speed
        self.target_speed = self.current_speed  # Desired speed
        self.base_deceleration = 0.0125  # Regular deceleration rate
        self.stop_deceleration = 0.25  # Fast deceleration for stopping
        self.deceleration = 0  # Active deceleration value
        self.rotation_direction = 1  # 1: right, -1: left

        # eyes view
        self.camera_current_angle = 0
        self.camera_current_direction = [0, 1, 0]
        
        super().__init__(scene, start_loop=False, callback=self._auto_motor, callback_period=1/self.fps, **kwargs)
    
    def _auto_motor(self, dt):
        """Handles auto-rotation and interaction updates"""
        self._auto_rotate()
    
    def _auto_rotate(self):
        """Apply rotation with inertia"""
        delta_time = 1 / self.fps
        
        # Apply gradual deceleration
        if self.current_speed > self.target_speed:
            if (self.current_speed - self.target_speed) > max(self.target_speed, self.deceleration):
                # Exponential decay for high excess speed
                self.current_speed = self.current_speed * (1 - delta_time) + self.target_speed * delta_time
            else:
                # Normal linear deceleration
                self.current_speed = max(self.current_speed - self.deceleration * delta_time, self.target_speed)
        
        # Apply rotation transformation
        transform = t.rotation_matrix(self.rotation_direction * self.current_speed * 2 * np.pi * delta_time, [0, 1, 0])
        self.scene.apply_transform(transform)
        self._update_view()
    
    def _update_view(self):
        """Force a redraw (workaround for proper rendering)"""
        self.on_mouse_scroll(None, None, None, 0)

    def set_camera_angle(self, angle, direction):
        """Set a new pov angle and direction to see the scene"""
        # remove previous camera view
        self.scene.apply_transform(t.rotation_matrix(-self.camera_current_angle, self.camera_current_direction))
        # new view
        self.camera_current_angle = angle
        self.camera_current_direction = direction
        self.scene.apply_transform(t.rotation_matrix(self.camera_current_angle, self.camera_current_direction))
    
    def swipe(self, swipe_magnitude):
        """Increase speed based on gesture intensity"""
        # for now: all the same; TODO: distinguish left swipe from right swipe
        swipe_magnitude = swipe_magnitude / 5

        # update with swipe stimuli
        self.current_speed = swipe_magnitude + self.current_speed * self.rotation_direction
        self.rotation_direction = 1 if (self.current_speed >= 0) else -1
        self.current_speed *= self.rotation_direction

        self.target_speed = self.base_speed
        self.deceleration = self.base_deceleration
    
    def stop_rotation(self):
        """Initiate a stop by setting the target speed to zero"""
        self.target_speed = 0
        self.deceleration = self.stop_deceleration


if __name__ == '__main__':

    def simulate_external_stimuli(viewer):
        time.sleep(2)
        viewer.set_speed_from_gesture(1)
        time.sleep(1)
        viewer.set_speed_from_gesture(1)
        time.sleep(1)
        viewer.set_speed_from_gesture(1)
        time.sleep(6)
        viewer.stop_rotation()

    # Load 3D model and create scene
    mesh = trimesh.load(config.GLB_PATH, force='mesh')
    scene = trimesh.Scene(mesh)
    viewer = HoloViewer(scene, fullscreen=False, background=(0, 0, 0, 1))
    viewer.set_fullscreen(True)

    # Simulate external input after some delay
    stimuli_thread = threading.Thread(target=simulate_external_stimuli, args=(viewer,), daemon=True)
    stimuli_thread.start()

    pyglet.app.run()
