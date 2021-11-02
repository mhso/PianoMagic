from time import time, sleep
from glob import glob
from pickle import dump

from mss import mss
import numpy as np
import win32api as win

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

def space_pressed(space_state):
    key_space = win.GetKeyState(SPACE_KEY_HEX)
    return key_space != space_state and key_space < 0

def main():
    path = "../resources/recorded/"
    num_files = len(glob(path + "*.bin"))
    filename = f"{path}rec_{num_files}.bin"
    recorded_notes = []

    space_state = win.GetKeyState(SPACE_KEY_HEX)

    while not space_pressed(space_state):
        sleep(0.01)

    space_state = win.GetKeyState(SPACE_KEY_HEX)

    sleep(0.5)

    try:
        with mss() as sct:
            monitor = sct.monitors[1]

            height = 110
            x_offset = 100

            bbox = (monitor["left"], monitor["top"] + monitor["height"] - height - 3, monitor["width"] - x_offset, monitor["top"] + monitor["height"] - height + 3)
            key_pos = draw.calculate_key_positions((monitor["width"] - x_offset) + 5)

            started = time()
            y_pos = 3

            while not space_pressed(space_state):
                sc = np.array(sct.grab(bbox))

                parsed_objects = get_key_statuses(sc, key_pos, y_pos, started)
                if parsed_objects != []:
                    recorded_notes.extend(parsed_objects)
    except KeyboardInterrupt:
        pass
    finally:
        for frame_data in reversed(recorded_notes):
            for key in range(88):
                if frame_data["key"] == key:
                    if frame_data["down"]:
                        recorded_notes.append(util.create_record_obj(False, 0, frame_data["key"], time() - started))
                        break
        with open(filename, "wb") as r_out:
            dump(recorded_notes, r_out)
            print(f"Saved recording to file '{filename}'")

if __name__ == "__main__":
    main()
