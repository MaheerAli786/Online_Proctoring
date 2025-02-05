import cv2
import dlib
import pyttsx3
import numpy as np
import threading

# Function to compute eye aspect ratio (optional for blinking detection)
def eye_aspect_ratio(eye):
    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])
    C = np.linalg.norm(eye[0] - eye[3])
    return (A + B) / (2.0 * C)

# Function to get the eye region from facial landmarks
def get_eye_region(landmarks, eye_indices):
    return np.array([(landmarks.part(i).x, landmarks.part(i).y) for i in eye_indices], np.int32)

# Function to determine gaze direction
def get_gaze_direction(eye):
    # Compute bounding box
    x_min, y_min = np.min(eye, axis=0)
    x_max, y_max = np.max(eye, axis=0)

    eye_roi = gray[y_min:y_max, x_min:x_max]  # Extract eye region
    _, threshold_eye = cv2.threshold(eye_roi, 55, 255, cv2.THRESH_BINARY_INV)  # Threshold to isolate iris

    # Find contours in threshold image
    contours, _ = cv2.findContours(threshold_eye, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if len(contours) == 0:
        return "Unknown"

    # Get the largest contour (iris)
    contour = max(contours, key=cv2.contourArea)
    M = cv2.moments(contour)
    
    if M["m00"] == 0:
        return "Unknown"
    
    cx = int(M["m10"] / M["m00"])  # Center of the contour
    eye_width = x_max - x_min

    # Determine direction based on iris position
    if cx < eye_width // 3:
        return "Left"
    elif cx > 2 * eye_width // 3:
        return "Right"
    else:
        return "Center"

# Load dlib's face detector and facial landmark predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("/Users/maheeralishaik/Mini Project/Online_Proctoring/shape_predictor_68_face_landmarks.dat")

# Start webcam
cap = cv2.VideoCapture(0)

# Store previous direction to avoid repeated prints
prev_direction = None
engine=pyttsx3.init()
continous_right=0
continous_left=0
continous_eye_left=0
continous_eye_right=0
while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame=cv2.flip(frame,1)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)
    if len(faces)>1:
        engine.say("Warning Multiple faces detected.")
        engine.runAndWait()
    for face in faces:
        landmarks = predictor(gray, face)

        # Extract key landmark points
        nose = (landmarks.part(30).x, landmarks.part(30).y)  # Nose tip
        face_center_x = (face.left() + face.right()) // 2
        face_center_y = (face.top() + face.bottom()) // 2
        # print('(',face_center_x,face_center_y,')',end=" ")

        direction = None  # Default to None
        # print('(',nose[0],nose[1],')')
        
        # Determine left or right movement
        if nose[0] < face_center_x - 30:
            direction = "Turned Left"
            continous_left+=1
        elif nose[0] > face_center_x + 30:
            direction = "Turned Right"
            continous_right+=1      
        else:
            prev_direction=None
            continous_left=0      
            continous_right=0      
        # # Determine up or down movement
        # if nose[1] < face_center_y - 20:
        #     direction = "Turned Up"
        # elif nose[1] > face_center_y + 20:
        #     direction = "Turned Down"

        # Print only if the direction has changed
        if direction and direction != prev_direction:
            print(direction)
            prev_direction = direction  # Update previous direction
        if continous_left>10:
            continous_eye_right=0
            engine.say("Warning turned left")
            engine.runAndWait()
            continue
        if continous_right>10:
            continous_eye_left=0
            engine.say("Warning turned right")
            engine.runAndWait()
            continue
        # Draw face landmarks (optional for visualization)
        # for i in range(68):
        #     x, y = landmarks.part(i).x, landmarks.part(i).y
        #     cv2.circle(frame, (x, y), 1, (0, 255, 255), -1)
        
        # Get left and right eye regions
        left_eye = get_eye_region(landmarks, [36, 37, 38, 39, 40, 41])
        right_eye = get_eye_region(landmarks, [42, 43, 44, 45, 46, 47])

        # Determine gaze direction
        left_gaze = get_gaze_direction(left_eye)
        right_gaze = get_gaze_direction(right_eye)

        # Print gaze direction if both eyes agree
        if left_gaze == right_gaze=='Center':
            continous_eye_left=0
            continous_eye_right=0
            # print(f"Eye Direction: {left_gaze}")
            continue
        elif left_gaze == right_gaze=='Left':
            # print(f"Eye Direction: {left_gaze}")
            continous_eye_right=0
            continous_eye_left+=1
        elif left_gaze == right_gaze=='Right':
            # print(f"Eye Direction: {left_gaze}")
            continous_eye_right+=1
            continous_eye_left=0
        
        if continous_eye_left>10:
            engine.say("Warning looking left")
            engine.runAndWait()
            continue
        if continous_eye_right>10:
            engine.say("Warning looking right")
            engine.runAndWait()
            continue

        # Draw eye landmarks
        # cv2.polylines(frame, [left_eye], True, (0, 255, 0), 1)
        # cv2.polylines(frame, [right_eye], True, (0, 255, 0), 1)

    cv2.imshow("Face Direction Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
