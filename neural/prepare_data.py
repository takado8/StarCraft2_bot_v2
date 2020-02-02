import numpy as np
import cv2
import random
import string


def random_name():
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(12))


def input_from_game_state(state_arr):
    img = np.array(state_arr)
    img = img.reshape(-1, 6, 6, 1)
    img = img/10
    return img

