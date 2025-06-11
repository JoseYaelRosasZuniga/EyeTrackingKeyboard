# eye_tracker.py (Versión con congelación de puntero reforzada)
import cv2
import mediapipe as mp
import numpy as np
import config
import time

# --- Constantes ---
EYE_LANDMARK_IDS_TO_DRAW = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398, 474, 475, 476, 477, 33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246, 469, 470, 471, 472]
EAR_LEFT_EYE_LANDMARKS_IDS = {"P1": 362, "P4": 263, "P2": 386, "P6": 374, "P3": 385, "P5": 373}
LEFT_IRIS_LANDMARKS_IDS = [474, 475, 476, 477]
LEFT_EYE_LEFT_CORNER_ID, LEFT_EYE_RIGHT_CORNER_ID = 362, 263
LEFT_EYE_TOP_LID_ID, LEFT_EYE_BOTTOM_LID_ID = 386, 374

class EyeTracker:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1, refine_landmarks=True,
            min_detection_confidence=0.5, min_tracking_confidence=0.5)
        
        try:
            self.webcam = cv2.VideoCapture(0)
            if not self.webcam.isOpened(): self.webcam = cv2.VideoCapture(1)
            if not self.webcam.isOpened(): self.webcam = cv2.VideoCapture(-1)
            if not self.webcam.isOpened(): raise IOError("No se puede abrir la webcam.")
        except Exception as e:
            raise IOError(f"Excepción al abrir la webcam: {e}")

        self.frame = None; self.frame_shape = None
        self.smoothed_gaze_coordinates = None; self.raw_gaze_ratio = None
        self.current_face_landmarks = None; self.last_valid_gaze_ratio = None
        
        self.ear_threshold = 0.24
        self.current_ear = 0
        self.blinking_state = "OPEN" 

    def _calculate_ear(self, landmarks):
        try:
            p1 = np.array([landmarks[EAR_LEFT_EYE_LANDMARKS_IDS["P1"]].x, landmarks[EAR_LEFT_EYE_LANDMARKS_IDS["P1"]].y])
            p4 = np.array([landmarks[EAR_LEFT_EYE_LANDMARKS_IDS["P4"]].x, landmarks[EAR_LEFT_EYE_LANDMARKS_IDS["P4"]].y])
            p2 = np.array([landmarks[EAR_LEFT_EYE_LANDMARKS_IDS["P2"]].x, landmarks[EAR_LEFT_EYE_LANDMARKS_IDS["P2"]].y])
            p6 = np.array([landmarks[EAR_LEFT_EYE_LANDMARKS_IDS["P6"]].x, landmarks[EAR_LEFT_EYE_LANDMARKS_IDS["P6"]].y])
            p3 = np.array([landmarks[EAR_LEFT_EYE_LANDMARKS_IDS["P3"]].x, landmarks[EAR_LEFT_EYE_LANDMARKS_IDS["P3"]].y])
            p5 = np.array([landmarks[EAR_LEFT_EYE_LANDMARKS_IDS["P5"]].x, landmarks[EAR_LEFT_EYE_LANDMARKS_IDS["P5"]].y])
            dist_v1 = np.linalg.norm(p2 - p6); dist_v2 = np.linalg.norm(p3 - p5)
            dist_h = np.linalg.norm(p1 - p4)
            if dist_h == 0: return 0.0
            return (dist_v1 + dist_v2) / (2.0 * dist_h)
        except (IndexError, AttributeError): return 0.0

    def is_blinking(self):
        blink_event = False
        is_eye_closed = self.current_ear < self.ear_threshold and self.current_ear > 0
        if is_eye_closed:
            if self.blinking_state == "OPEN":
                blink_event = True
            self.blinking_state = "CLOSED"
        else:
            self.blinking_state = "OPEN"
        return blink_event

    def update_frame(self):
        ret, bgr_frame = self.webcam.read()
        if not ret: self.frame = None; return False
        self.frame = cv2.flip(bgr_frame, 1); self.frame_shape = self.frame.shape
        rgb_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        self.current_face_landmarks = None; self.current_ear = 0
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                self.current_face_landmarks = face_landmarks
                self.current_ear = self._calculate_ear(face_landmarks.landmark)
                break
        
        # Lógica de congelación reforzada
        ratios = self._calculate_gaze_ratios_from_landmarks(self.current_face_landmarks)
        if ratios and self.current_ear > self.ear_threshold:
            self.raw_gaze_ratio = ratios
            self.last_valid_gaze_ratio = ratios
        else:
            self.raw_gaze_ratio = self.last_valid_gaze_ratio
            
        return True

    def _calculate_gaze_ratios_from_landmarks(self, face_landmarks):
        if face_landmarks is None: return None
        landmarks = face_landmarks.landmark
        try:
            left_iris_points = [landmarks[i] for i in LEFT_IRIS_LANDMARKS_IDS]
            left_pupil_center_x = sum(p.x for p in left_iris_points) / len(left_iris_points)
            left_pupil_center_y = sum(p.y for p in left_iris_points) / len(left_iris_points)
            l_eye_left_corner_x = landmarks[LEFT_EYE_LEFT_CORNER_ID].x; l_eye_right_corner_x = landmarks[LEFT_EYE_RIGHT_CORNER_ID].x
            l_eye_top_lid_y = landmarks[LEFT_EYE_TOP_LID_ID].y; l_eye_bottom_lid_y = landmarks[LEFT_EYE_BOTTOM_LID_ID].y
            left_eye_width = abs(l_eye_right_corner_x - l_eye_left_corner_x)
            left_eye_height = abs(l_eye_bottom_lid_y - l_eye_top_lid_y)
            if left_eye_width < 1e-6 or left_eye_height < 1e-6: return None
            h_ratio_left = (left_pupil_center_x - l_eye_left_corner_x) / left_eye_width
            v_ratio_left = (left_pupil_center_y - l_eye_top_lid_y) / left_eye_height
            return (np.clip(h_ratio_left, 0.0, 1.0), np.clip(v_ratio_left, 0.0, 1.0))
        except (IndexError, AttributeError, ZeroDivisionError): return None
        
    def get_annotated_frame(self):
        if self.frame is None: return None
        annotated_frame = self.frame.copy()
        if config.SHOW_DEBUG_FACE_MESH and self.current_face_landmarks:
            landmarks = self.current_face_landmarks.landmark
            (h, w, _) = self.frame.shape
            for index in EYE_LANDMARK_IDS_TO_DRAW:
                point = landmarks[index]
                cv2.circle(annotated_frame, (int(point.x * w), int(point.y * h)), 2, (100, 255, 100), -1)
        return annotated_frame
        
    def get_raw_gaze_ratio(self): return self.raw_gaze_ratio
    def set_gaze_coordinates(self, sxm, sym):
        if sxm is not None and sym is not None:
            if self.smoothed_gaze_coordinates is None: self.smoothed_gaze_coordinates = (sxm, sym)
            else:
                alpha = config.GAZE_SMOOTHING_FACTOR
                sx = alpha * sxm + (1 - alpha) * self.smoothed_gaze_coordinates[0]
                sy = alpha * sym + (1 - alpha) * self.smoothed_gaze_coordinates[1]
                self.smoothed_gaze_coordinates = (int(sx), int(sy))
        else: self.smoothed_gaze_coordinates = None
    def get_gaze_screen_coordinates(self): return self.smoothed_gaze_coordinates
    def release(self):
        if self.webcam and self.webcam.isOpened(): self.webcam.release()
        if hasattr(self, 'face_mesh'): self.face_mesh.close()
        cv2.destroyAllWindows()