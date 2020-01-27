import numpy as np
import cv2
from util import BAR_SPEED

BG_COLOR = 75
KEY_HEIGHT = 200
KEY_FRAC = 52
BAR_COLOR_FULL = (60, 175, 30)
BAR_COLOR_SHARP = (50, 130, 30)

def get_key_statuses(timestamp, keys):
    key_statuses = [[("upcoming", 3, 100)] for i in range(88)]
    processed = 0
    for key_index, event_list in enumerate(keys):
        i = 0
        while i < len(event_list) and event_list[i] < timestamp + BAR_SPEED:
            if event_list[i] < timestamp:
                if i % 2 == 1:
                    key_statuses[key_index].pop()
                    processed += 1
                else:
                    key_statuses[key_index].append(("pressed", 0, event_list[i+1] - timestamp))
                    processed += 1
            elif i % 2 == 0:
                key_statuses[key_index].append(("onscreen", event_list[i] - timestamp, event_list[i+1] - timestamp))
            i += 1
    return key_statuses, processed

def calculate_key_positions(width):
    sharp_distances = [1, 2, 1, 2, 1]
    last_sharp = 0
    sharp_index = 0
    key_index = 0
    key_thickness = width / KEY_FRAC
    keys = []
    sharps = []
    for i in range(88):
        x = int(key_index * key_thickness) - 1
        if last_sharp == sharp_distances[sharp_index]:
            sharp_index += 1
            sharp_offset = 0
            if sharp_index == 5:
                sharp_offset = 0
                sharp_index = 0
            elif last_sharp == 2:
                sharp_offset = -3
            else:
                sharp_offset = 3
            last_sharp = 0
            sharps.append((x + sharp_offset, i, True))
        else:
            key_index += 1
            last_sharp += 1
            keys.append((x, i, False))
    return keys + sharps

def draw_bar(img, x_1, x_2, is_sharp, status):
    height = img.shape[0]
    any_pressed = False
    view_height = height - KEY_HEIGHT
    for key_status, key_start, key_end in status:
        if key_status in ("onscreen", "pressed"):
            if key_status == "pressed":
                any_pressed = True
            bar_bot = view_height - int(view_height * (key_start / BAR_SPEED))
            bar_top = view_height - int(view_height * (key_end / BAR_SPEED))
            if bar_top < 0:
                bar_top = 0
            if bar_bot > height - KEY_HEIGHT:
                bar_bot = height - KEY_HEIGHT
            color = BAR_COLOR_FULL
            if is_sharp:
                color = BAR_COLOR_SHARP

            cv2.rectangle(img, (x_1, bar_top), (x_2, bar_bot), (0, 0, 0), 2)
            cv2.rectangle(img, (x_1, bar_top), (x_2, bar_bot), color, -1)
    return any_pressed

def draw_key(img, x, x_1, x_2, any_pressed, is_sharp, press_color=(205, 120, 70)):
    height = img.shape[0]
    view_height = height - KEY_HEIGHT
    y_unp = height - 10
    y_sharp = height - int(KEY_HEIGHT * 0.4)
    y_2 = y_unp if not is_sharp else y_sharp
    key_color = (255, 255, 255) if not is_sharp else (0, 0, 0)
    color = press_color if any_pressed else key_color
    if not is_sharp:
        y_2 = height if any_pressed else y_2
    cv2.rectangle(img, (x_1, view_height), (x_2, y_2), color, -1)
    if not is_sharp:
        cv2.line(img, (x, view_height), (x, y_unp), (0, 0, 0))

def draw_piano(statuses, key_pos, size):
    img = np.full((size[1], size[0], 3), BG_COLOR, dtype="uint8")
    h, w = img.shape[:2]
    key_thickness = w // KEY_FRAC
    sharp_thickness = key_thickness - 16
    view_height = h - KEY_HEIGHT

    for (x, key, is_sharp) in key_pos:
        any_pressed = False
        x_1 = x if not is_sharp else x - 5
        x_2 = x + key_thickness if not is_sharp else x-5+sharp_thickness

        any_pressed = draw_bar(img, x_1, x_2, is_sharp, statuses[key])

        draw_key(img, x, x_1, x_2, any_pressed, is_sharp)

    cv2.line(img, (0, view_height-2), (w, view_height-2), (0, 0, 0), 2)
    return img

def find_key(key, key_pos):
    for tupl in key_pos:
        if tupl[1] == key:
            return tupl
    return None

def draw_correct_note(img, note_id, pressed, key_pos):
    h, w = img.shape[:2]
    x, _, is_sharp = find_key(note_id, key_pos)
    key_thickness = w // KEY_FRAC
    sharp_thickness = key_thickness - 16
    x_1 = x if not is_sharp else x - 5
    x_2 = x + key_thickness if not is_sharp else x-5 + sharp_thickness
    draw_key(img, x, x_1, x_2, pressed, is_sharp, press_color=(0, 255, 0))

def draw_wrong_note(img, note_id, pressed, key_pos):
    h, w = img.shape[:2]
    x, _, is_sharp = find_key(note_id, key_pos)
    key_thickness = w // KEY_FRAC
    sharp_thickness = key_thickness - 16
    x_1 = x if not is_sharp else x - 5
    x_2 = x + key_thickness if not is_sharp else x-5 + sharp_thickness
    draw_key(img, x, x_1, x_2, pressed, is_sharp, press_color=(0, 0, 255))

def end_of_data(timestamp, key_data):
    return timestamp > key_data[-1]["timestamp"]
