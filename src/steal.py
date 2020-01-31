from time import time, sleep
from glob import glob
from pickle import dump
from mss import mss
import numpy as np
import win32api as win
import cv2
import util
import draw

RGB_GREEN_MIN = (50, 100, 60)
RGB_GREEN_MAX = (200, 255, 200)
RGB_BLUE_MIN = (0, 150, 150)
RGB_BLUE_MAX = (150, 255, 255)
COLORS = [
    (RGB_GREEN_MIN, RGB_GREEN_MAX),
    (RGB_BLUE_MIN, RGB_BLUE_MAX)
]

SPACE_KEY_HEX = 0x20
SPACE_STATE = win.GetKeyState(SPACE_KEY_HEX)
KEYS_PRESSED = [False] * 88

def get_key_statuses(img, key_positions, y, time_started):
    objects = []

    for x, key, is_sharp in key_positions:
        x_pos = x if is_sharp else x + 15
        r = img[y, x_pos, 2]
        g = img[y, x_pos, 1]
        b = img[y, x_pos, 0]
        any_matches = False
        for c_min, c_max in COLORS:
            if (r > c_min[0] and b > c_min[1] and g > c_min[2]
                    and r < c_max[0] and b < c_max[1] and g < c_max[2]):
                any_matches = True
                break
        if any_matches:
            if not KEYS_PRESSED[key]:
                rec_obj = util.create_record_obj(True, 30, key, time() - time_started)
                objects.append(rec_obj)
                KEYS_PRESSED[key] = True
        elif KEYS_PRESSED[key]:
            rec_obj = util.create_record_obj(False, 0, key, time() - time_started)
            objects.append(rec_obj)
            KEYS_PRESSED[key] = False

    return objects

def space_pressed():
    key_space = win.GetKeyState(SPACE_KEY_HEX)
    return key_space != SPACE_STATE and key_space < 0

PATH = "../resources/recorded/"
NUM_FILES = len(glob(PATH + "*.bin"))
FILE = f"{PATH}rec_{NUM_FILES}.bin"
RECORDED_NOTES = []

while not space_pressed():
    sleep(0.01)

SPACE_STATE = win.GetKeyState(SPACE_KEY_HEX)

sleep(0.5)

try:
    with mss() as sct:
        monitor = sct.monitors[1]

        height = 110
        x_offset = 100

        BBOX = (monitor["left"], monitor["top"] + monitor["height"] - height - 3, monitor["width"] - x_offset, monitor["top"] + monitor["height"] - height + 3)
        KEY_POS = draw.calculate_key_positions((monitor["width"] - x_offset) + 5)

        STARTED = time()
        Y_POS = 3

        while not space_pressed():
            SC = np.array(sct.grab(BBOX))

            PARSED_OBJECTS = get_key_statuses(SC, KEY_POS, Y_POS, STARTED)
            if PARSED_OBJECTS != []:
                RECORDED_NOTES.extend(PARSED_OBJECTS)
except KeyboardInterrupt:
    pass
finally:
    for frame_data in reversed(RECORDED_NOTES):
        for key in range(88):
            if frame_data["key"] == key:
                if frame_data["down"]:
                    RECORDED_NOTES.append(util.create_record_obj(False, 0, frame_data["key"], time() - STARTED))
                    break
    with open(FILE, "wb") as r_out:
        dump(RECORDED_NOTES, r_out)
        print(f"Saved recording to file '{FILE}'")
