from functools import cache

import cv2
import numpy as np


class KalmanFilter:
    kf = cv2.KalmanFilter(4, 2)
    kf.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
    kf.transitionMatrix = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32)

    @cache
    def predict(self, coord_x, coord_y):
        """ This function estimates the position of the MIDDLE_FINGER_PIP """
        measured = np.array([[np.float32(coord_x)], [np.float32(coord_y)]])
        self.kf.correct(measured)
        predicted = self.kf.predict()
        x, y = (predicted[0]), (predicted[1])
        return x, y


class PedsFilter:
    finger_input = []

    @cache
    def confidence(self, motion_value):
        """ This function assures the motion of the tip fingers """
        last_value = []
        self.finger_input.append(motion_value)
        if len(self.finger_input) == 4:
            self.finger_input.pop(0)
            self.finger_input.pop()
            if 1 in self.finger_input:
                last_value.append(1)
            else:
                last_value.append(0)
            self.finger_input.clear()
            return last_value[0]
