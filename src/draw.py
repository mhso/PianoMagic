import numpy as np
import cv2
from util import BAR_SPEED, get_note_desc

SYNTHESIA_BG_COLOR = 65
KEY_HEIGHT_FRAC = 6
KEY_WIDTH_FRAC = 52
KEY_WIDTH_FRAC_SHARP = 160
BAR_COLOR_FULL = (60, 175, 30)
BAR_COLOR_SHARP = (50, 130, 30)
SHARP_OFFSET = 3
SHEET_BG_COLOR = 185
SHEET_VERT_GAP = 40
SHEET_SPACE_BETWEEN = 20
SHEET_PADDING_X = 50

def get_view_height(height):
    return height - (height // KEY_HEIGHT_FRAC)

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

def draw_rounded_rect(img, p1, p2, color, thickness, radius):
    x_1 = p1[0] + radius
    x_2 = p2[0] - radius
    y_1 = p1[1] + radius
    y_2 = p2[1] - radius

    view_height = get_view_height(img.shape[0])

    black = (0, 0, 0)

    cv2.line(img, (x_1, p1[1]), (x_2, p1[1]), black, thickness)
    cv2.line(img, (x_1, p2[1]), (x_2, p2[1]), black, thickness)
    cv2.line(img, (p1[0], y_1), (p1[0], y_2), black, thickness)
    cv2.line(img, (p2[0], y_1), (p2[0], y_2), black, thickness)

    # Corners.
    cv2.line(img, (p1[0], y_1), (x_1, p1[1]), black, thickness)
    cv2.line(img, (p1[0], y_2), (x_1, p2[1]), black, thickness)
    cv2.line(img, (x_2, p1[1]), (p2[0], y_1), black, thickness)
    cv2.line(img, (x_2, p2[1]), (p2[0], y_2), black, thickness)

    if p2[1] > radius + 3 and p1[1] < view_height - radius - 3:
        cv2.floodFill(img, None, (x_1 + 5, y_2 - 1), color)

def draw_bar(img, x_1, x_2, is_sharp, status):
    height = img.shape[0]
    any_pressed = False
    view_height = get_view_height(height)
    for key_status, key_start, key_end in status:
        if key_status in ("onscreen", "pressed"):
            if key_status == "pressed":
                any_pressed = True
            bar_bot = view_height - int(view_height * (key_start / BAR_SPEED)) - 1
            bar_top = (view_height - int(view_height * (key_end / BAR_SPEED)) + 1
                       if key_end > -1 else 0)
            if bar_top < view_height:
                if bar_top < 0:
                    bar_top = 0
                if bar_bot > view_height:
                    bar_bot = view_height
                color = BAR_COLOR_FULL
                if is_sharp:
                    color = BAR_COLOR_SHARP

                draw_rounded_rect(img, (x_1, bar_top), (x_2, bar_bot), color, 2, 4)
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

def draw_progress(img, progress):
    length = int(img.shape[1] * progress)
    y = 5
    thickness = y * 2
    cv2.line(img, (0, y), (length, y), (0, 0, 255), thickness)
    cv2.line(img, (0, thickness), (length, thickness), (0, 0, 0), 1)

def draw_piano(statuses, key_pos, size, progress, draw_presses=True):
    img = np.full((size[1], size[0], 3), SYNTHESIA_BG_COLOR, dtype="uint8")
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
    draw_progress(img, progress)
    return img

def find_key(key, key_pos):
    for tupl in key_pos:
        if tupl[1] == key:
            return tupl
    return None

def draw_altered_note(img, note_id, key_pos, color):
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

def draw_correct_note(img, note_id, key_pos):
    draw_altered_note(img, note_id, key_pos, (30, 200, 30))

def draw_wrong_note(img, note_id, key_pos):
    draw_altered_note(img, note_id, key_pos, (0, 0, 225))

def end_of_data(timestamp, key_data):
    return timestamp > key_data[-1]["timestamp"]

def draw_str(img, x, y, text, color=(255, 255, 255), size=1.5):
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_COMPLEX, size, (0, 0, 0), 8)
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_COMPLEX, size, color, 2)

def draw_points(img, points):
    w = img.shape[1]
    pt_str = "Score: " + str(points)
    x = w - len(pt_str) * 27 - 20
    draw_str(img, x, 50, pt_str)

def draw_streak(img, streak):
    as_str = "Streak: " + str(streak)
    draw_str(img, 20, 50, as_str)

def draw_accuracy(img, accuracy):
    as_str = "Acc: " + str(accuracy) + "%"
    draw_str(img, 20, 100, as_str, size=1.2)

def draw_hits(img, hits, total):
    str_1 = str(hits)
    str_2 = "/"
    str_3 = str(total)
    w = img.shape[1]
    space_per_char = 25
    x_1 = w - len(str_1 + str_2 + str_3) * space_per_char - 20
    x_2 = w - len(str_1 + str_2) * space_per_char - 20
    x_3 = w - len(str_1) * space_per_char - 20

    draw_str(img, x_1, 100, str_1, color=(0, 190, 0), size=1.2)
    draw_str(img, x_2, 100, str_2, size=1.2)
    draw_str(img, x_3, 100, str_3, size=1.2)

    if total > 0:
        draw_accuracy(img, int((hits / total) * 100))

def draw_sharp(img, x, y):
    hori_offset_x = 12
    hori_offset_y = 12
    vert_offset_x = 6
    vert_offset_y = hori_offset_x * 2
    hori_offset = 6
    vert_offset = 12
    cv2.line(
        img, (x - hori_offset_x, y - hori_offset_y + hori_offset),
        (x + hori_offset_x, y - hori_offset_y - hori_offset), (0, 0, 0), 6
    )
    cv2.line(
        img, (x - hori_offset_x, y + hori_offset_y + hori_offset),
        (x + hori_offset_x, y + hori_offset_y - hori_offset), (0, 0, 0), 6
    )
    cv2.line(
        img, (x - vert_offset_x, y - vert_offset_y),
        (x - vert_offset_x, y + vert_offset_y + vert_offset), (0, 0, 0), 2
    )
    cv2.line(
        img, (x + vert_offset_x, y - vert_offset_y - vert_offset),
        (x + vert_offset_x, y + vert_offset_y), (0, 0, 0), 2
    )

def draw_semitone(img, x, y, treble, index, color):
    note_color = (0, 0, 0) if color is None else color
    y_radius = SHEET_SPACE_BETWEEN // 2
    cv2.ellipse(img, (x, y), (int(y_radius * 1.4), y_radius), 325, 0, 360, note_color, -1)
    offset_x, offset_y = 1, 11

    if treble:
        threshold = 31
        offset_y = -1 if index > threshold else 1
        offset_x = -11 if index > threshold else 10
    else:
        threshold = 16
        offset_y = 1 if index < threshold else -1
        offset_x = 11 if index < threshold else -10

    cv2.line(img, (x+offset_x, y-(SHEET_SPACE_BETWEEN * 3 * offset_y)), (x+offset_x, y), color, 3)

def draw_note(img, offset, key_index, treble, sharp, color=None):
    x = 200 + 70 * offset
    offset = -SHEET_VERT_GAP // 2 if treble else SHEET_VERT_GAP // 2
    start_y = img.shape[0] // 2 + offset
    y = int(start_y + (23 - key_index) * (SHEET_SPACE_BETWEEN / 2))
    if ((treble and (key_index < 25 or key_index > 34))
            or (not treble and (key_index < 10 or key_index > 22))):
        line_y = y + 10 if key_index % 2 == 0 else y
        cv2.line(img, (x-15, line_y), (x+15, line_y), (0, 0, 0), 2)

    draw_semitone(img, x, y, treble, key_index, color)

    if sharp:
        draw_sharp(img, x-30, y)

def draw_key_name(img, offset, start_x, y, key_index, color=None):
    key_name = get_note_desc(key_index)

    text_scale = 1.75
    gap = 10
    text_width = int(10 + len(key_name) * 28 * text_scale)
    text_height = int(50 * text_scale)

    offset_x = gap + text_width * offset
    if start_x > img.shape[1] // 2:
        offset_x = -offset_x

    x = start_x + offset_x

    cv2.rectangle(
        img, (x - 3, y - text_height), (x + text_width, y + 3),
        (SHEET_BG_COLOR,) * 3, cv2.FILLED
    )

    note_color = (0, 0, 0) if color is None else color

    cv2.putText(img, key_name, (x, y), cv2.QT_FONT_NORMAL, text_scale, note_color, 2)

def overlay_img(img_1, img_2, x, y):
    y1, y2 = y, y + img_2.shape[0]
    x1, x2 = x, x + img_2.shape[1]

    alpha_s = img_2[:, :, 3] / 255.0
    alpha_l = 1.0 - alpha_s

    for c in range(0, 3):
        img_1[y1:y2, x1:x2, c] = (alpha_s * img_2[:, :, c] +
                                  alpha_l * img_1[y1:y2, x1:x2, c])
    return img_1

def create_sheet_image(size):
    img = np.full((size[1], size[0], 3), SHEET_BG_COLOR, dtype="uint8")
    h, w = img.shape[:2]

    for sign in range(-1, 2, 2):
        for y_offset in range(5):
            y = int(h / 2 + (y_offset * SHEET_SPACE_BETWEEN + SHEET_VERT_GAP) * sign)
            cv2.line(img, (SHEET_PADDING_X, y), (w-SHEET_PADDING_X, y), (60, 60, 60), 2)

    split_lines = 6
    left = int((w - SHEET_PADDING_X * 2) / (split_lines-1))
    for x_offset in range(split_lines):
        x = SHEET_PADDING_X + int(left * x_offset)
        cv2.line(img, (x, int(h / 2 - (4 * SHEET_SPACE_BETWEEN + SHEET_VERT_GAP))),
                 (x, int(h / 2 + (4 * SHEET_SPACE_BETWEEN + SHEET_VERT_GAP))), (0, 0, 0), 2)

    treb_clef_img = cv2.imread("../resources/img/treble-clef.png", -1)
    treb_clef_img = cv2.resize(treb_clef_img, (62, int(SHEET_SPACE_BETWEEN*6.8)))
    bass_clef_img = cv2.imread("../resources/img/bass-clef.png", -1)
    bass_clef_img = cv2.resize(bass_clef_img, (62, int(SHEET_SPACE_BETWEEN*3.1)))
    img = overlay_img(img, treb_clef_img, SHEET_PADDING_X + 10, int(h / 2 - SHEET_SPACE_BETWEEN * 7.25))
    img = overlay_img(img, bass_clef_img, SHEET_PADDING_X + 10, int(h / 2 + SHEET_SPACE_BETWEEN * 2))

    return img
