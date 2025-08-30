"""
Configuration file for SHolo project.
"""

import numpy as np

# Path to the 3D model
GLB_PATH = '3D_objects/trex.glb'

# -- Eye Tracking Configuration --

# Screen and camera setup
SCREEN_WIDTH_CM = 52  # Screen width in cm
SCREEN_HEIGHT_CM = 29.5  # Screen height in cm
SCREEN_RESOLUTION = (1920, 1080)  # Screen resolution (px)
CAMERA_OFFSET_CM = 4  # Camera offset from the top of the screen (cm)

# Camera info
FOV_DEGREES = 110  # Camera horizontal FOV
FOV_RADIANS = np.radians(FOV_DEGREES)
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
FOCAL_LENGTH_MM = 3.92
SENSOR_WIDTH_MM = (1 / 2.9) * 2.54 * 10
FOCAL_LENGTH_PX = (FOCAL_LENGTH_MM / SENSOR_WIDTH_MM) * (2 * CAMERA_WIDTH)

# Estimated distance of the scene from the screen (in cm)
SCENE_SCREEN_DISTANCE_CM = 200

IPD_REAL_CM = 6.5 # Real interpupillary distance in cm

# -- Hand Tracking Configuration --

# Swipe gesture detection area (as a fraction of the screen width)
SWIPE_LEFT_THRESHOLD_X = 0.25
SWIPE_RIGHT_THRESHOLD_X = 0.75

# Fist gesture detection threshold (sum of distances from fingertips to palm)
FIST_DETECTION_THRESHOLD = 100

SWIPE_THRESHOLD = 0.15  # Minimum movement to trigger a swipe
STOP_THRESHOLD = 0.6  # Threshold for recognizing an open palm
GESTURE_COOLDOWN = 0.5  # Cooldown time (seconds) between gestures
VISIBILITY_RESET_TIME = 1.5 # Time in seconds to reset tracking after disappearance