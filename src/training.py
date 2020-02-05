import random
from time import time
import mido
import numpy as np
import cv2
import util

BG_COLOR = 185
VERTICAL_GAP = 40
SPACE_BETWEEN = 20
PADDING_X = 50

def convert_key(key_index, up):
    sharp_distances = [1, 2, 1, 2, 1]
    abs_index = key_index
    sharp_index = 0
    last_sharp = 0
    index = 0
    while index <= key_index:
        if last_sharp == sharp_distances[sharp_index % 5]:
            sharp_index += 1
            abs_index += 1 if up else -1
            last_sharp = 0
        else:
            last_sharp += 1
        index += 1
    return abs_index

def to_absolute_key(key_index):
    return convert_key(key_index, True)

def to_sheet_key(key_index):
    return convert_key(key_index, False)

def draw_sharp(img, x, y):
    hori_offset_x = 12
    hori_offset_y = 12
    vert_offset_x = 6
    vert_offset_y = hori_offset_x * 2
    hori_offset = 6
    vert_offset = 12
    cv2.line(img, (x - hori_offset_x, y - hori_offset_y + hori_offset),
             (x + hori_offset_x, y - hori_offset_y - hori_offset), (0, 0, 0), 6)
    cv2.line(img, (x - hori_offset_x, y + hori_offset_y + hori_offset),
             (x + hori_offset_x, y + hori_offset_y - hori_offset), (0, 0, 0), 6)
    cv2.line(img, (x - vert_offset_x, y - vert_offset_y),
             (x - vert_offset_x, y + vert_offset_y + vert_offset), (0, 0, 0), 2)
    cv2.line(img, (x + vert_offset_x, y - vert_offset_y - vert_offset),
             (x + vert_offset_x, y + vert_offset_y), (0, 0, 0), 2)

def draw_semitone(img, x, y, treble, index, color):
    note_color = (0, 0, 0) if color is None else color
    y_radius = SPACE_BETWEEN // 2
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
    cv2.line(img, (x+offset_x, y-(SPACE_BETWEEN * 3 * offset_y)), (x+offset_x, y), color, 3)

def draw_note(img, key_index, treble, sharp, color=None):
    x = 200
    offset = -VERTICAL_GAP // 2 if treble else VERTICAL_GAP // 2
    start_y = img.shape[0] // 2 + offset
    y = int(start_y + (23 - key_index) * (SPACE_BETWEEN / 2))
    if ((treble and (key_index < 25 or key_index > 34))
            or (not treble and (key_index < 10 or key_index > 22))):
        line_y = y + 10 if key_index % 2 == 0 else y
        cv2.line(img, (x-15, line_y), (x+15, line_y), (0, 0, 0), 2)
    draw_semitone(img, x, y, treble, key_index, color)
    if sharp:
        draw_sharp(img, x-30, y)
    # name = "Treble clef" if treble else "Bass clef"
    # text_x = (img.shape[1] // 2 - 100)
    # text_y = 150
    # cv2.putText(img, f"Note is {name}", (text_x, text_y), cv2.QT_FONT_NORMAL, 1, (0, 0, 0), 2)

def overlay_img(img_1, img_2, x, y):
    y1, y2 = y, y + img_2.shape[0]
    x1, x2 = x, x + img_2.shape[1]

    alpha_s = img_2[:, :, 3] / 255.0
    alpha_l = 1.0 - alpha_s

    for c in range(0, 3):
        img_1[y1:y2, x1:x2, c] = (alpha_s * img_2[:, :, c] +
                                  alpha_l * img_1[y1:y2, x1:x2, c])
    return img_1

def create_image(size):
    img = np.full((size[1], size[0], 3), BG_COLOR, dtype="uint8")
    h, w = img.shape[:2]

    for sign in range(-1, 2, 2):
        for y_offset in range(5):
            y = int(h / 2 + (y_offset * SPACE_BETWEEN + VERTICAL_GAP) * sign)
            cv2.line(img, (PADDING_X, y), (w-PADDING_X, y), (60, 60, 60), 2)

    split_lines = 6
    left = int((w - PADDING_X * 2) / (split_lines-1))
    for x_offset in range(split_lines):
        x = PADDING_X + int(left * x_offset)
        cv2.line(img, (x, int(h / 2 - (4 * SPACE_BETWEEN + VERTICAL_GAP))),
                 (x, int(h / 2 + (4 * SPACE_BETWEEN + VERTICAL_GAP))), (0, 0, 0), 2)

    treb_clef_img = cv2.imread("../resources/img/treble-clef.png", -1)
    treb_clef_img = cv2.resize(treb_clef_img, (62, int(SPACE_BETWEEN*6.8)))
    bass_clef_img = cv2.imread("../resources/img/bass-clef.png", -1)
    bass_clef_img = cv2.resize(bass_clef_img, (62, int(SPACE_BETWEEN*3.1)))
    img = overlay_img(img, treb_clef_img, PADDING_X + 10, int(h / 2 - SPACE_BETWEEN * 7.25))
    img = overlay_img(img, bass_clef_img, PADDING_X + 10, int(h / 2 + SPACE_BETWEEN * 2))

    return img

def get_countdown_color(progress):
    r_lo = 30
    g_lo = 80
    b_lo = 200
    r_hi = 220
    g_hi = 20
    b_hi = 30
    red = r_lo + (r_hi - r_lo) * progress
    green = g_lo + (g_hi - g_lo) * progress
    blue = b_lo + (b_hi - b_lo) * progress
    return (blue, green, red)

def draw_countdown(img, progress):
    offset_x = PADDING_X
    max_width = img.shape[1] - (PADDING_X * 2)
    width = int(progress * max_width)
    y = int(img.shape[0] - PADDING_X)
    color = get_countdown_color(progress)
    cv2.line(img, (offset_x, y), (img.shape[1] - offset_x, y), (0, 0, 0), 12)
    cv2.line(img, (offset_x, y), (offset_x + width, y), color, 10)

def draw_score(img, correct, total):
    point_str = "Score: " + str(correct) + "/" + str(total)
    x = img.shape[1] // 2 - (len(point_str) * 17)
    y = img.shape[0] // 6
    cv2.putText(img, point_str, (x, y), cv2.QT_FONT_NORMAL, 2, (0, 0, 0), 4)

SIZE = (1280, 720)
QUESTIONS = 200

def generate_questions(q_number):
    data = []
    duration = 6 - (q_number / QUESTIONS) * 4
    amount = 5
    for _ in range(amount):
        is_treble = random.random() > 0.5
        if is_treble:
            choices = [x for x in range(30, 88)]
            weights = np.array([2 if x > 60 else 1 for x in choices])
        else:
            choices = [x for x in range(0, 59)]
            weights = np.array([2 if x > 30 else 1 for x in choices])
        weights = weights / sum(weights)
        note = np.random.choice(choices, size=1, p=weights)[0]
        data.append((note, is_treble))
    return data, duration

def get_input(port):
    if port is not None:
        msg = port.receive(False)
        parsed_msg = util.parse_midi_msg(msg, 0)
        if parsed_msg is not None and parsed_msg["down"]:
            return parsed_msg["key"]
    return None

def animate_questions(img, notes, timelimit, port):
    curr_note = 0
    elapsed_time = 0
    sleep_time = 10
    correct = 0
    statuses = [0 for _ in notes]
    changed = [True for _ in notes]
    while elapsed_time < timelimit and curr_note < len(notes):
        before = time()
        pressed_note = get_input(port)
        if elapsed_time < 300:
            pressed_note = None
        for i, (note, is_treble) in enumerate(notes[curr_note:]):
            is_sharp = util.is_sharp(note)
            sheet_note = to_sheet_key(note)
            color = None
            if statuses[i] == 1:
                color = (0, 255, 0)
            elif statuses[i] == -1:
                color = (0, 0, 255)
            if changed[i]:
                draw_note(img, sheet_note, is_treble, is_sharp, color)
                changed[i] = False
            if pressed_note is not None:
                if pressed_note == note and i == curr_note:
                    statuses[i] = 1
                    correct += 1
                    curr_note += 1
                else:
                    statuses[i] = -1
                    curr_note += 1
                changed[i] = True
        draw_countdown(img, elapsed_time / timelimit)
        cv2.imshow("Piano Quiz", img)
        key = cv2.waitKey(sleep_time)
        if key == ord('q'):
            return correct, -1
        elapsed_time += sleep_time
    for note, is_treble in notes[curr_note:]:
        is_sharp = util.is_sharp(note)
        sheet_note = to_sheet_key(note)
        draw_note(img, sheet_note, is_treble, is_sharp, (0, 0, 255))
    return correct, 0

def training_loop(port):
    correct = 0
    for question in range(QUESTIONS):
        image = create_image(SIZE)
        draw_score(image, correct, question+1)
        notes, duration = generate_questions(question)
        notes_correct, status = animate_questions(image, notes, duration*1000, port)
        correct += notes_correct
        if status == -1:
            break
        cv2.imshow("Piano Quiz", image)
        key = cv2.waitKey(1500)
        if key == ord('q'):
            break

try:
    with mido.open_input() as inport:
        training_loop(inport)
except OSError:
    print("WARNING: No digital piano detected, please connect one.")
    training_loop(None)
