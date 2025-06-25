import cv2
import mediapipe as mp
import numpy as np
import time
import math
from collections import deque
import threading
import pygame

class BodySafetyMonitor:
    def __init__(self):
        # Initialize MediaPipe components
        self.mp_pose = mp.solutions.pose
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Initialize pose estimation
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,
            enable_segmentation=True,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        
        # Initialize face mesh for detailed facial analysis
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        
        # Initialize face detection for stress analysis
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1,
            min_detection_confidence=0.7
        )
        
        # Movement tracking variables
        self.position_history = deque(maxlen=30)  # Store last 30 frames
        self.velocity_history = deque(maxlen=10)
        self.acceleration_history = deque(maxlen=5)
        
        # Fall detection parameters
        self.fall_threshold_angle = 45  # degrees from vertical
        self.fall_velocity_threshold = 150  # pixels per frame
        self.fall_detected = False
        self.fall_timer = 0
        
        # Stress detection parameters
        self.stress_indicators = {
            'eye_blink_rate': deque(maxlen=30),
            'mouth_tension': deque(maxlen=30),
            'head_movement': deque(maxlen=30),
            'facial_asymmetry': deque(maxlen=30)
        }
        # Panic and distress detection parameters
        self.panic_indicators = {
            'chest_clutching': deque(maxlen=20),
            'throat_touching': deque(maxlen=20),
            'restless_movement': deque(maxlen=30),
            'breathing_rate': deque(maxlen=60),  # Track for 2 seconds at 30fps
            'hand_to_chest_frequency': deque(maxlen=30),
            'erratic_movement_score': deque(maxlen=20)
        }

# Breathing detection thresholds
        self.breathing_baseline = 0.02  # Normal chest movement range
        self.rapid_breathing_threshold = 25  # breaths per minute
        self.panic_movement_threshold = 0.05
        self.chest_area_touch_threshold = 0.08
        
        self.baseline_established = False
        self.baseline_blink_rate = 15  # blinks per minute
        self.stress_score = 0
        
        # Alert system
        self.alert_active = False
        self.last_alert_time = 0
        self.alert_cooldown = 3  # seconds
        
        # Initialize pygame for audio alerts
        try:
            pygame.mixer.init()
            self.audio_enabled = True
        except:
            self.audio_enabled = False
            print("Audio alerts disabled - pygame mixer not available")
    
    def calculate_angle(self, p1, p2, p3):
        """Calculate angle between three points"""
        try:
            # Convert landmarks to arrays
            a = np.array([p1.x, p1.y])
            b = np.array([p2.x, p2.y])
            c = np.array([p3.x, p3.y])
            
            # Calculate vectors
            ba = a - b
            bc = c - b
            
            # Calculate angle
            cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
            angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
            
            return np.degrees(angle)
        except:
            return 0
    
    def detect_fall(self, landmarks, frame_height, frame_width):
        """Detect potential falls based on body orientation and movement"""
        if not landmarks:
            return False
        
        try:
            # Key body landmarks
            head = landmarks[self.mp_pose.PoseLandmark.NOSE]
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
            left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP]
            right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP]
            
            # Calculate body center and orientation
            shoulder_center = ((left_shoulder.x + right_shoulder.x) / 2, 
                             (left_shoulder.y + right_shoulder.y) / 2)
            hip_center = ((left_hip.x + right_hip.x) / 2, 
                         (left_hip.y + right_hip.y) / 2)
            
            # Calculate body angle from vertical
            body_vector = (hip_center[0] - shoulder_center[0], 
                          hip_center[1] - shoulder_center[1])
            vertical_vector = (0, 1)
            
            # Calculate angle from vertical
            dot_product = body_vector[1]  # Only y component for vertical comparison
            magnitude = math.sqrt(body_vector[0]**2 + body_vector[1]**2)
            
            if magnitude > 0:
                cos_angle = dot_product / magnitude
                angle_from_vertical = math.degrees(math.acos(abs(cos_angle)))
            else:
                angle_from_vertical = 0
            
            # Track position for velocity calculation
            current_pos = (head.x * frame_width, head.y * frame_height)
            self.position_history.append(current_pos)
            
            # Calculate velocity if we have enough history
            velocity = 0
            if len(self.position_history) >= 2:
                prev_pos = self.position_history[-2]
                velocity = math.sqrt((current_pos[0] - prev_pos[0])**2 + 
                                   (current_pos[1] - prev_pos[1])**2)
                self.velocity_history.append(velocity)
            
            # Calculate acceleration
            acceleration = 0
            if len(self.velocity_history) >= 2:
                acceleration = abs(self.velocity_history[-1] - self.velocity_history[-2])
                self.acceleration_history.append(acceleration)
            
            # Fall detection logic
            fall_conditions = [
                angle_from_vertical > self.fall_threshold_angle,  # Body tilted
                velocity > self.fall_velocity_threshold,          # Fast movement
                head.y > hip_center[1],                          # Head below hips
                acceleration > 50                                 # Sudden acceleration
            ]
            
            # Fall detected if multiple conditions are met
            fall_score = sum(fall_conditions)
            
            if fall_score >= 2:
                if not self.fall_detected:
                    self.fall_detected = True
                    self.fall_timer = time.time()
                return True
            else:
                # Reset fall detection if person recovers quickly
                if self.fall_detected and time.time() - self.fall_timer > 2:
                    self.fall_detected = False
            
            return False
            
        except Exception as e:
            print(f"Fall detection error: {e}")
            return False
    
    def analyze_facial_stress(self, face_landmarks, frame):
        """Analyze facial features for stress indicators"""
        if not face_landmarks:
            return 0
        
        try:
            landmarks = face_landmarks.landmark
            stress_score = 0
            
            # Eye landmarks for blink detection
            left_eye_top = landmarks[159]
            left_eye_bottom = landmarks[145]
            right_eye_top = landmarks[386]
            right_eye_bottom = landmarks[374]
            
            # Calculate eye openness ratio
            left_eye_ratio = abs(left_eye_top.y - left_eye_bottom.y)
            right_eye_ratio = abs(right_eye_top.y - right_eye_bottom.y)
            eye_openness = (left_eye_ratio + right_eye_ratio) / 2
            
            # Blink detection (simplified)
            if eye_openness < 0.01:  # Eyes closed
                self.stress_indicators['eye_blink_rate'].append(1)
            else:
                self.stress_indicators['eye_blink_rate'].append(0)
            
            # Calculate blink rate (blinks per 30 frames)
            recent_blinks = sum(list(self.stress_indicators['eye_blink_rate'])[-30:])
            
            # Mouth tension analysis
            mouth_left = landmarks[61]
            mouth_right = landmarks[291]
            mouth_top = landmarks[13]
            mouth_bottom = landmarks[14]
            
            mouth_width = abs(mouth_left.x - mouth_right.x)
            mouth_height = abs(mouth_top.y - mouth_bottom.y)
            mouth_ratio = mouth_height / mouth_width if mouth_width > 0 else 0
            
            self.stress_indicators['mouth_tension'].append(mouth_ratio)
            
            # Head movement analysis
            nose_tip = landmarks[1]
            head_pos = (nose_tip.x, nose_tip.y)
            
            if len(self.stress_indicators['head_movement']) > 0:
                prev_head_pos = self.stress_indicators['head_movement'][-1]
                head_movement = math.sqrt((head_pos[0] - prev_head_pos[0])**2 + 
                                        (head_pos[1] - prev_head_pos[1])**2)
            else:
                head_movement = 0
            
            self.stress_indicators['head_movement'].append(head_movement)
            
            # Facial asymmetry (simplified)
            left_cheek = landmarks[116]
            right_cheek = landmarks[345]
            nose_bridge = landmarks[6]
            
            left_distance = math.sqrt((left_cheek.x - nose_bridge.x)**2 + 
                                    (left_cheek.y - nose_bridge.y)**2)
            right_distance = math.sqrt((right_cheek.x - nose_bridge.x)**2 + 
                                     (right_cheek.y - nose_bridge.y)**2)
            
            asymmetry = abs(left_distance - right_distance)
            self.stress_indicators['facial_asymmetry'].append(asymmetry)
            
            # Calculate stress score
            if len(self.stress_indicators['eye_blink_rate']) >= 10:
                avg_blink_rate = np.mean(list(self.stress_indicators['eye_blink_rate'])[-10:]) * 30
                avg_mouth_tension = np.mean(list(self.stress_indicators['mouth_tension'])[-10:])
                avg_head_movement = np.mean(list(self.stress_indicators['head_movement'])[-10:])
                avg_asymmetry = np.mean(list(self.stress_indicators['facial_asymmetry'])[-10:])
                
                # Normalize and weight stress indicators
                blink_stress = max(0, (avg_blink_rate - 20) / 10)  # Above 20 blinks/30frames
                tension_stress = min(1, avg_mouth_tension * 10)     # Mouth tension
                movement_stress = min(1, avg_head_movement * 100)   # Head movement
                asymmetry_stress = min(1, avg_asymmetry * 100)     # Facial asymmetry
                
                stress_score = (blink_stress * 0.3 + tension_stress * 0.3 + 
                              movement_stress * 0.2 + asymmetry_stress * 0.2)
            
            return min(1.0, stress_score)
            
        except Exception as e:
            return 0
        
    def detect_panic_distress(self, landmarks, frame_height, frame_width):
        """Detect panic, breathlessness, and distress indicators"""
        if not landmarks:
            return 0, {}
    
        try:
        # Key landmarks for detection
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
            left_elbow = landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW]
            right_elbow = landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW]
            left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST]
            right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST]
            left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP]
            right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP]
            nose = landmarks[self.mp_pose.PoseLandmark.NOSE]
        
            # Calculate chest center
            chest_center_x = (left_shoulder.x + right_shoulder.x) / 2
            chest_center_y = (left_shoulder.y + right_shoulder.y + left_hip.y + right_hip.y) / 4
            
            # Throat area (between nose and chest)
            throat_center_x = chest_center_x
            throat_center_y = (nose.y + chest_center_y) / 2
            
            # Detect chest clutching
            left_hand_to_chest = math.sqrt((left_wrist.x - chest_center_x)**2 + (left_wrist.y - chest_center_y)**2)
            right_hand_to_chest = math.sqrt((right_wrist.x - chest_center_x)**2 + (right_wrist.y - chest_center_y)**2)
            
            chest_clutching = min(left_hand_to_chest, right_hand_to_chest) < self.chest_area_touch_threshold
            self.panic_indicators['chest_clutching'].append(1 if chest_clutching else 0)
            
            # Detect throat touching
            left_hand_to_throat = math.sqrt((left_wrist.x - throat_center_x)**2 + (left_wrist.y - throat_center_y)**2)
            right_hand_to_throat = math.sqrt((right_wrist.x - throat_center_x)**2 + (right_wrist.y - throat_center_y)**2)
            
            throat_touching = min(left_hand_to_throat, right_hand_to_throat) < 0.06
            self.panic_indicators['throat_touching'].append(1 if throat_touching else 0)
            
            # Detect rapid/erratic movement
            current_body_center = ((left_shoulder.x + right_shoulder.x + left_hip.x + right_hip.x) / 4,
                                (left_shoulder.y + right_shoulder.y + left_hip.y + right_hip.y) / 4)
            
            if len(self.panic_indicators['restless_movement']) > 0:
                prev_center = self.panic_indicators['restless_movement'][-1]
                movement_magnitude = math.sqrt((current_body_center[0] - prev_center[0])**2 + 
                                            (current_body_center[1] - prev_center[1])**2)
            else:
                movement_magnitude = 0
            
            self.panic_indicators['restless_movement'].append(current_body_center)
            
            # Calculate erratic movement score
            if len(self.panic_indicators['restless_movement']) >= 5:
                recent_movements = list(self.panic_indicators['restless_movement'])[-5:]
                movement_variations = []
                for i in range(1, len(recent_movements)):
                    var = math.sqrt((recent_movements[i][0] - recent_movements[i-1][0])**2 + 
                                (recent_movements[i][1] - recent_movements[i-1][1])**2)
                    movement_variations.append(var)
                
                erratic_score = np.std(movement_variations) if movement_variations else 0
                self.panic_indicators['erratic_movement_score'].append(erratic_score)
            
            # Breathing rate estimation (simplified - based on shoulder movement)
            shoulder_distance = abs(left_shoulder.y - right_shoulder.y)
            self.panic_indicators['breathing_rate'].append(shoulder_distance)
            
            # Hand-to-chest frequency
            hand_chest_contact = 1 if (chest_clutching or throat_touching) else 0
            self.panic_indicators['hand_to_chest_frequency'].append(hand_chest_contact)
            
            # Calculate overall panic/distress score
            panic_score = 0
            detection_details = {}
            
            if len(self.panic_indicators['chest_clutching']) >= 10:
                # Chest clutching frequency (last 10 frames)
                chest_clutch_rate = np.mean(list(self.panic_indicators['chest_clutching'])[-10:])
                detection_details['chest_clutching'] = chest_clutch_rate > 0.3
                
                # Throat touching frequency
                throat_touch_rate = np.mean(list(self.panic_indicators['throat_touching'])[-10:])
                detection_details['throat_touching'] = throat_touch_rate > 0.2
                
                # Hand-to-chest contact frequency
                hand_contact_rate = np.mean(list(self.panic_indicators['hand_to_chest_frequency'])[-15:])
                detection_details['frequent_chest_contact'] = hand_contact_rate > 0.4
                
                # Erratic movement detection
                if len(self.panic_indicators['erratic_movement_score']) >= 3:
                    avg_erratic = np.mean(list(self.panic_indicators['erratic_movement_score'])[-3:])
                    detection_details['erratic_movement'] = avg_erratic > 0.03
                
                # Rapid breathing detection
                if len(self.panic_indicators['breathing_rate']) >= 30:
                    breathing_data = list(self.panic_indicators['breathing_rate'])[-30:]
                    breathing_variance = np.var(breathing_data)
                    detection_details['rapid_breathing'] = breathing_variance > 0.0005
                
                # Calculate weighted panic score
                panic_score = (
                    chest_clutch_rate * 0.25 +
                    throat_touch_rate * 0.25 +
                    hand_contact_rate * 0.2 +
                    (avg_erratic if 'erratic_movement' in detection_details else 0) * 15 +
                    (breathing_variance if 'rapid_breathing' in detection_details else 0) * 200
                )
        
                return min(1.0, panic_score), detection_details
        
        except Exception as e:
            print(f"Panic detection error: {e}")
            return 0, {}
    
    def trigger_alert(self, alert_type, severity="medium"):
        """Trigger appropriate alert based on detection type"""
        current_time = time.time()
        
        # Prevent alert spam
        if current_time - self.last_alert_time < self.alert_cooldown:
            return
        
        self.alert_active = True
        self.last_alert_time = current_time
        
        print(f"\n🚨 ALERT: {alert_type.upper()} DETECTED! Severity: {severity}")
        
        # Audio alert (if available)
        if self.audio_enabled:
            try:
                # Generate a simple beep sound
                frequency = 800 if alert_type == "fall" else 600
                duration = 500  # milliseconds
                # Note: This would need actual sound file or sound generation
                print(f"🔊 Audio alert triggered: {frequency}Hz for {duration}ms")
            except:
                pass
    
    def draw_pose_landmarks(self, frame, landmarks):
        """Draw pose landmarks on frame"""
        if landmarks:
            self.mp_drawing.draw_landmarks(
                frame, landmarks, self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style())
    
    def draw_face_landmarks(self, frame, landmarks):
        """Draw face landmarks on frame"""
        if landmarks:
            self.mp_drawing.draw_landmarks(
                frame, landmarks, self.mp_face_mesh.FACEMESH_CONTOURS,
                landmark_drawing_spec=None,
                connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_contours_style())
    
    def draw_ui_overlay(self, frame, pose_landmarks, stress_score, fall_detected, panic_score=0, panic_details={}):
        """Draw UI overlay with monitoring information"""
        height, width = frame.shape[:2]
        
        # Status panel background
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (400, 200), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # System status
        cv2.putText(frame, "Body Safety Monitor", (20, 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Pose detection status
        pose_status = "DETECTED" if pose_landmarks else "NOT DETECTED"
        pose_color = (0, 255, 0) if pose_landmarks else (0, 0, 255)
        cv2.putText(frame, f"Body Pose: {pose_status}", (20, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, pose_color, 1)
        
        # Stress level
        stress_level = "LOW" if stress_score < 0.3 else "MEDIUM" if stress_score < 0.7 else "HIGH"
        stress_color = (0, 255, 0) if stress_score < 0.3 else (0, 255, 255) if stress_score < 0.7 else (0, 0, 255)
        cv2.putText(frame, f"Stress Level: {stress_level} ({stress_score:.2f})", (20, 85), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, stress_color, 1)
        
        # Fall detection status
        fall_status = "FALL DETECTED!" if fall_detected else "NORMAL"
        fall_color = (0, 0, 255) if fall_detected else (0, 255, 0)
        cv2.putText(frame, f"Fall Status: {fall_status}", (20, 110), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, fall_color, 1)
        
        # Panic/distress indicators
        if panic_score > 0.3:
            panic_level = "HIGH DISTRESS" if panic_score > 0.6 else "DISTRESS DETECTED"
            panic_color = (0, 0, 255) if panic_score > 0.6 else (0, 165, 255)
            cv2.putText(frame, f"Distress: {panic_level} ({panic_score:.2f})", (20, 135), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, panic_color, 1)
            
            # Show specific indicators
            y_offset = 160
            if panic_details.get('chest_clutching'):
                cv2.putText(frame, "⚠ Chest clutching detected", (20, y_offset), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                y_offset += 20
            if panic_details.get('throat_touching'):
                cv2.putText(frame, "⚠ Throat contact detected", (20, y_offset), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                y_offset += 20
            if panic_details.get('rapid_breathing'):
                cv2.putText(frame, "⚠ Irregular breathing", (20, y_offset), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                y_offset += 20
            if panic_details.get('erratic_movement'):
                cv2.putText(frame, "⚠ Restless movement", (20, y_offset), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

        # Alert indicator
        if self.alert_active:
            cv2.rectangle(frame, (width-150, 10), (width-10, 60), (0, 0, 255), -1)
            cv2.putText(frame, "ALERT!", (width-130, 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Reset alert after display
        if time.time() - self.last_alert_time > 2:
            self.alert_active = False
    
    def process_frame(self, frame):
        """Process a single frame for all detections"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width = frame.shape[:2]
        
        # Pose detection
        pose_results = self.pose.process(rgb_frame)
        
        # Face detection for stress analysis
        face_results = self.face_mesh.process(rgb_frame)
        
        # Initialize detection results
        fall_detected = False
        stress_score = 0
        
        # Analyze pose for fall detection
        if pose_results.pose_landmarks:
            fall_detected = self.detect_fall(pose_results.pose_landmarks.landmark, height, width)
            self.draw_pose_landmarks(frame, pose_results.pose_landmarks)
        
        # Analyze face for stress
        if face_results.multi_face_landmarks:
            for face_landmarks in face_results.multi_face_landmarks:
                stress_score = self.analyze_facial_stress(face_landmarks, frame)
                self.draw_face_landmarks(frame, face_landmarks)
                break  # Only process first face

        # Analyze for panic and distress indicators
        # Analyze for panic and distress indicators
        panic_score = 0
        panic_details = {}
        if pose_results.pose_landmarks:
            result = self.detect_panic_distress(pose_results.pose_landmarks.landmark, height, width)
            if result is not None:
                panic_score, panic_details = result
            else:
                panic_score, panic_details = 0, {}
        # Trigger alerts
        if fall_detected:
            self.trigger_alert("fall", "high")
        elif panic_score > 0.6:
            alert_msg = "panic_distress"
            if panic_details.get('chest_clutching') or panic_details.get('throat_touching'):
                alert_msg = "breathing_difficulty"
            elif panic_details.get('erratic_movement'):
                alert_msg = "panic_movement"
            self.trigger_alert(alert_msg, "high")
        elif stress_score > 0.7:
            self.trigger_alert("high_stress", "medium")

        # Draw UI overlay
        self.draw_ui_overlay(frame, pose_results.pose_landmarks, stress_score, fall_detected, panic_score, panic_details)
        
        return frame
    
    def run_camera_monitor(self, camera_index=0):
        """Run the monitoring system with camera input"""
        cap = cv2.VideoCapture(camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        print("Starting Body Safety Monitor...")
        print("Press 'q' to quit, 's' to save screenshot")
        
        frame_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to read from camera")
                    break
                
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Process frame
                processed_frame = self.process_frame(frame)
                
                # Display frame
                cv2.imshow('Body Safety Monitor', processed_frame)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    screenshot_name = f"safety_monitor_screenshot_{int(time.time())}.jpg"
                    cv2.imwrite(screenshot_name, processed_frame)
                    print(f"Screenshot saved: {screenshot_name}")
                
                frame_count += 1
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("Body Safety Monitor stopped")
    
    def run_video_monitor(self, video_path):
        """Run the monitoring system on a video file"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"Error: Could not open video file {video_path}")
            return
        
        print(f"Processing video: {video_path}")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("End of video reached")
                    break
                
                # Process frame
                processed_frame = self.process_frame(frame)
                
                # Display frame
                cv2.imshow('Body Safety Monitor - Video', processed_frame)
                
                # Control playback speed
                if cv2.waitKey(30) & 0xFF == ord('q'):
                    break
                
        except KeyboardInterrupt:
            print("\nVideo processing stopped by user")
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("Video processing completed")

def main():
    """Main function to run the Body Safety Monitor"""
    monitor = BodySafetyMonitor()
    
    print("Body Safety Monitor System")
    print("=" * 40)
    print("Features:")
    print("- Full body pose detection")
    print("- Facial stress analysis")
    print("- Fall detection")
    print("- Real-time alerts")
    print("=" * 40)
    
    choice = input("Choose input source:\n1. Camera (default)\n2. Video file\nEnter choice (1-2): ").strip()
    
    if choice == '2':
        video_path = input("Enter video file path: ").strip()
        monitor.run_video_monitor(video_path)
    else:
        camera_index = input("Enter camera index (0 for default): ").strip()
        camera_index = int(camera_index) if camera_index.isdigit() else 0
        monitor.run_camera_monitor(camera_index)

if __name__ == "__main__":
    monitor = BodySafetyMonitor()
    monitor.run_camera_monitor(camera_index=0)
