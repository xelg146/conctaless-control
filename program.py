import os
import time
from math import hypot

import cv2
import mediapipe as mp
import numpy
import pyautogui
import win32con
import win32gui
from win32api import GetSystemMetrics

import piestimate

cap = cv2.VideoCapture(0 + cv2.CAP_DSHOW)
window_width, window_height = 640, 480
cap.set(3, window_width)
cap.set(4, window_height)

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
hands_num = mp_hands.Hands(max_num_hands=1, model_complexity=0)

os.popen('osk')
current_window = win32gui.GetForegroundWindow()
win32gui.ShowWindow(current_window, win32con.SW_MINIMIZE)

near_x, near_y = 0, 0
while True:
    success, image = cap.read()
    image = cv2.flip(image, 1)
    results = hands_num.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

    landmarks_info = []
    if results.multi_hand_landmarks:
        for hand_landmarks, xyz in enumerate(results.multi_hand_landmarks[0].landmark):
            image_height, image_width, image_channel = image.shape
            height_y, width_x = (xyz.y * image_height), (xyz.x * image_width)
            landmarks_info.append([hand_landmarks, width_x, height_y])

        # Draw the hand annotations on the image.
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                                      mp_drawing_styles.get_default_hand_landmarks_style(),
                                      mp_drawing_styles.get_default_hand_connections_style())

    hand_type = []
    if results.multi_handedness:
        for idx, classification in enumerate(results.multi_handedness):
            label = classification.classification[0].label
            hand_type.append(label)

    finger_motion = []
    fingertips = [4, 8, 12, 16, 20]
    if landmarks_info:
        if hand_type[0] == 'Right':
            if landmarks_info[fingertips[0]][1] >= landmarks_info[fingertips[0] - 3][1]:
                finger_motion.append(1)
            else:
                finger_motion.append(0)

        if hand_type[0] == 'Left':
            if landmarks_info[fingertips[0]][1] <= landmarks_info[fingertips[0] - 3][1]:
                finger_motion.append(1)
            else:
                finger_motion.append(0)

        for hand_landmarks in range(1, 5):
            if landmarks_info[fingertips[hand_landmarks]][2] >= landmarks_info[fingertips[hand_landmarks] - 1][2]:
                finger_motion.append(1)
            else:
                finger_motion.append(0)

        screen_width, screen_height = GetSystemMetrics(win32con.SM_CXSCREEN), GetSystemMetrics(win32con.SM_CYSCREEN)
        xy_limiter = 200
        x = numpy.interp(landmarks_info[10][1], (xy_limiter, window_width - xy_limiter), (0, screen_width))
        y = numpy.interp(landmarks_info[10][2], (xy_limiter, window_height - xy_limiter), (0, screen_height))

        (x2, y2) = piestimate.KalmanFilter().predict(x, y)

        close_value = 10
        near_x, near_y = near_x + (x2 - near_x) / close_value, near_y + (y2 - near_y) / close_value

        pyautogui.FAILSAFE = False
        if pyautogui.onScreen(near_x, near_y):
            pyautogui.moveTo(near_x, near_y)

        if finger_motion.count(1) > 1:
            time.sleep(3)

        flags, h, *point = win32gui.GetCursorInfo()

        if finger_motion[0]:
            if piestimate.PedsFilter().confidence(finger_motion[0]) == 1:
                pyautogui.click()

        if h == 65545:
            if finger_motion[1] == 1:
                pyautogui.mouseDown(button='left')

        if h == 65541:
            if finger_motion[1] == 1:
                with pyautogui.hold('win'):
                    pyautogui.press('h')

        if finger_motion[2]:
            if piestimate.PedsFilter().confidence(finger_motion[2]) == 1:
                pyautogui.click(button='right')

        if finger_motion[3] == 1:
            pyautogui.scroll(70)

        if finger_motion[4] == 1:
            pyautogui.scroll(-70)

        palm_distance = hypot(landmarks_info[9][1] - landmarks_info[10][1],
                              landmarks_info[9][2] - landmarks_info[10][2])
        osk = win32gui.FindWindow(None, "On-Screen Keyboard")
        if palm_distance < 35:
            win32gui.ShowWindow(osk, win32con.SW_SHOWNORMAL)
        else:
            win32gui.ShowWindow(osk, win32con.SW_MINIMIZE)

    cv2.imshow('image', image)
    if cv2.waitKey(5) & 0xFF == 27:
        os.system("taskkill /im osk.exe")
        break

cap.release()
