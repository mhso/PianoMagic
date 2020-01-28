import numpy as np
import cv2
from util import BAR_SPEED

BG_COLOR = 75
KEY_HEIGHT_FRAC = 6
KEY_WIDTH_FRAC = 52
KEY_WIDTH_FRAC_SHARP = 160
BAR_COLOR_FULL = (60, 175, 30)
BAR_COLOR_SHARP = (50, 130, 30)
SHARP_OFFSET = 3

def get_view_height(height):
    return height - (height // KEY_HEIGHT_FRAC)

def get_key_statuses(timestamp, keys):
    key_statuses = [[("upcoming", 3, 100)] for i in range(88)]
    processed = 0
    for key_index, event_list in enumerate(keys):
        i = 0
        while i < len(event_list)-1 and event_list[i] < timestamp + BAR_SPEED:
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
    key_thickness = width / KEY_WIDTH_FRAC
    keys = []
    sharps = []
    for i in range(88):
        x = int(key_index * key_thickness) - 1
        if last_sharp == sharp_distances[sharp_index]:
            sharp_index += 1
            curr_offset = 0
            if sharp_index == 5:
                curr_offset = 0
                sharp_index = 0
            elif last_sharp == 2:
                curr_offset = -SHARP_OFFSET
            else:
                curr_offset = SHARP_OFFSET
            last_sharp = 0
            sharps.append((x + curr_offset, i, True))
        else:
            key_index += 1
            last_sharp += 1
            keys.append((x, i, False))
    return keys + sharps

def draw_bar(img, x_1, x_2, is_sharp, status):
    height = img.shape[0]
    any_pressed = False
    view_height = get_view_height(height)
    for key_status, key_start, key_end in status:
        if key_status in ("onscreen", "pressed"):
            if key_status == "pressed":
                any_pressed = True
            bar_bot = view_height - int(view_height * (key_start / BAR_SPEED))
            bar_top = view_height - int(view_height * (key_end / BAR_SPEED))
            if bar_top < view_height:
                if bar_top < 0:
                    bar_top = 0
                if bar_bot > view_height:
                    bar_bot = view_height
                color = BAR_COLOR_FULL
                if is_sharp:
                    color = BAR_COLOR_SHARP

                cv2.rectangle(img, (x_1, bar_top), (x_2, bar_bot), (0, 0, 0), 2)
                cv2.rectangle(img, (x_1, bar_top), (x_2, bar_bot), color, -1)
    return any_pressed

def draw_key(img, x, x_1, x_2, any_pressed, is_sharp, press_color=(205, 120, 70)):
    height = img.shape[0]
    view_height = get_view_height(height)
    y_unp = height - 10
    y_sharp = height - int(KEY_HEIGHT_FRAC * 0.4)
    y_2 = y_unp if not is_sharp else y_sharp
    key_color = (255, 255, 255) if not is_sharp else (0, 0, 0)
    color = press_color if any_pressed else key_color
    if not is_sharp:
        y_2 = height if any_pressed else y_2
    cv2.rectangle(img, (x_1, view_height), (x_2, y_2), color, -1)
    if not is_sharp:
        cv2.line(img, (x, view_height), (x, y_unp), (0, 0, 0))

def draw_piano(statuses, key_pos, size, draw_presses=True):
    img = np.full((size[1], size[0], 3), BG_COLOR, dtype="uint8")
    h, w = img.shape[:2]
    key_thickness = w // KEY_WIDTH_FRAC
    sharp_thickness = w // KEY_WIDTH_FRAC_SHARP
    view_height = get_view_height(h)

    for (x, key, is_sharp) in key_pos:
        any_pressed = False
        x_1 = x if not is_sharp else x - 5
        x_2 = x + key_thickness if not is_sharp else x + sharp_thickness

        any_pressed = draw_bar(img, x_1, x_2, is_sharp, statuses[key])

        draw_key(img, x, x_1, x_2, any_pressed and draw_presses, is_sharp)

    cv2.line(img, (0, view_height-2), (w, view_height-2), (0, 0, 0), 2)
    return img

def find_key(key, key_pos):
    for tupl in key_pos:
        if tupl[1] == key:
            return tupl
    return None

def draw_altered_note(img, note_id, pressed, key_pos, color):
    h, w = img.shape[:2]
    curr_key = find_key(note_id, key_pos)
    keys_to_draw = [curr_key]
    prev_key = find_key(note_id-1, key_pos)
    if prev_key is not None and prev_key[2]:
        keys_to_draw.append(prev_key)
    next_key = find_key(note_id+1, key_pos)
    if next_key is not None and next_key[2]:
        keys_to_draw.append(next_key)
    for i, (x, _, is_sharp) in enumerate(keys_to_draw):
        key_thickness = w // KEY_WIDTH_FRAC
        sharp_thickness = w // KEY_WIDTH_FRAC_SHARP
        x_1 = x if not is_sharp else x - 5
        x_2 = x + key_thickness if not is_sharp else x + sharp_thickness
        draw_key(img, x, x_1, x_2, i == 0, is_sharp, press_color=color)
        if i == 0:
            view_height = get_view_height(h)
            cv2.line(img, (x_2, view_height), (x_2, h), (0, 0, 0), 1)

def draw_correct_note(img, note_id, pressed, key_pos):
    draw_altered_note(img, note_id, pressed, key_pos, (30, 200, 30))

def draw_wrong_note(img, note_id, pressed, key_pos):
    draw_altered_note(img, note_id, pressed, key_pos, (0, 0, 225))

def end_of_data(timestamp, key_data):
    return timestamp > key_data[-1]["timestamp"]

def draw_points(img, points):
    h, w = img.shape[:2]
    pt_str = "Score: " + str(points)
    x = len(pt_str) * 30
    cv2.putText(img, pt_str, (w-x, 50), cv2.FONT_HERSHEY_COMPLEX, 1.5, (0, 0, 255), 2)
