import cv2
import numpy as np
import dlib
from imutils import face_utils
import pygame
import time

#  AUDIO SETUP 
pygame.mixer.init()
pygame.mixer.music.load("alarm.wav")
alarm_on = False

# yawn sound 
try:
    yawn_sound = pygame.mixer.Sound("yawn.wav")
except:
    yawn_sound = None

cap = cv2.VideoCapture(0)

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

status = ""
color = (0, 0, 0)

eye_close_start = None

# YAWN VARIABLES
yawn_active = False
yawn_start_time = None
YAWN_MAR_THRESH = 0.75
YAWN_DISPLAY_TIME = 3   # seconds

def compute(ptA, ptB):
    return np.linalg.norm(ptA - ptB)

#EAR (eye aspect ratio)
def blinked(a, b, c, d, e, f):
    up = compute(b, d) + compute(c, e)
    down = compute(a, f)
    ratio = up / (2.0 * down)
    if ratio > 0.25:
        return 2
    elif ratio > 0.21:
        return 1
    else:
        return 0

#MAR (mouth aspect ratio)
def mouth_aspect_ratio(mouth):
    A = compute(mouth[2], mouth[10])
    B = compute(mouth[4], mouth[8])
    C = compute(mouth[0], mouth[6])
    return (A + B) / (2.0 * C)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)

    for face in faces:

        # Green  rectangle
        x1 = face.left()
        y1 = face.top()
        x2 = face.right()
        y2 = face.bottom()

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        cv2.putText(frame, "DRIVER", (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)


        landmarks = predictor(gray, face)
        landmarks = face_utils.shape_to_np(landmarks)

        current_time = time.time()

        right_blink = blinked(landmarks[36], landmarks[37],
                              landmarks[38], landmarks[41],
                              landmarks[40], landmarks[39])
        left_blink = blinked(landmarks[42], landmarks[43],
                             landmarks[44], landmarks[47],
                             landmarks[46], landmarks[45])

#alarm condition
        if left_blink == 0 and right_blink == 0:
            if eye_close_start is None:
                eye_close_start = current_time

            closed_duration = current_time - eye_close_start

            if 2 <= closed_duration < 3:
                status = "WARNING! EYE CLOSED"
                color = (0, 0, 255)

            elif closed_duration >= 3:
                status = "ALERT! SLEEPING"
                color = (0, 0, 255)

                if not alarm_on:
                    pygame.mixer.music.play(-1)
                    alarm_on = True
        else:
            eye_close_start = None
            if alarm_on:
                pygame.mixer.music.stop()
                alarm_on = False

            status = "ACTIVE"
            color = (0, 255, 0)

        
        mouth = landmarks[48:68]
        mar = mouth_aspect_ratio(mouth)

        if mar > YAWN_MAR_THRESH and not yawn_active:
            yawn_active = True
            yawn_start_time = current_time

            if yawn_sound:
                yawn_sound.play()

        # yawn notification for 3 seconds
        if yawn_active:
            status = "TAKE BREAK !!"
            color = (255, 0, 255)
        
            if yawn_active and (current_time - yawn_start_time >= YAWN_DISPLAY_TIME):
                yawn_active = False
         
        
        cv2.putText(frame, status, (100, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)

        for (x, y) in landmarks:
            cv2.circle(frame, (x, y), 1, (255, 255, 255), -1)

    cv2.imshow("Driver Drowsiness Detector", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
pygame.mixer.music.stop()
cv2.destroyAllWindows()
