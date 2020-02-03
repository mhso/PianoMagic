import numpy as np
import cv2
import util

BG_COLOR = 185
VERTICAL_GAP = 50
SPACE_BETWEEN = 25
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

def draw_semitone(img, x, y):
    cv2.ellipse(img, (x, y), (14, SPACE_BETWEEN // 2 - 2), 325, 0, 360, (0, 0, 0), -1)
    cv2.line(img, (x+11, y-SPACE_BETWEEN*3), (x+11, y), (0, 0, 0), 3)

def draw_note(img, key_index, bass, sharp):
    x = 200
    offset = VERTICAL_GAP // 2 if bass else -VERTICAL_GAP // 2
    start_y = img.shape[0] // 2 + offset
    y = int(start_y + (23 - key_index) * (SPACE_BETWEEN / 2))
    if ((bass and (key_index < 10 or key_index > 22))
            or (not bass and (key_index < 25 or key_index > 34))):
        line_y = y + 10 if key_index % 2 == 0 else y
        cv2.line(img, (x-15, line_y), (x+15, line_y), (0, 0, 0), 2)
    draw_semitone(img, x, y)
    if sharp:
        draw_sharp(img, x-30, y)

def overlay_img(img_1, img_2, x, y):
    h, w = img_2.shape[:2]

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

    treb_clef_img = cv2.resize(cv2.imread("../resources/img/treble-clef.png", -1), (72, 172))
    bass_clef_img = cv2.resize(cv2.imread("../resources/img/bass-clef.png", -1), (82, 82))
    img = overlay_img(img, treb_clef_img, PADDING_X + 10, int(h / 2 - SPACE_BETWEEN * 7.25))
    img = overlay_img(img, bass_clef_img, PADDING_X + 5, int(h / 2 + SPACE_BETWEEN * 1.95))

    return img

# Draw notes, maybe with a countdown.
SIZE = (1280, 720)
# Key range = 0-51. (52 keys)
# MID C = 23

KEYS = [6, 42, 44, 48, 60, 34]
BASSES = [True, True, False, True, True]
for KEY, BASS in zip(KEYS, BASSES):
    IMAGE = create_image(SIZE)
    draw_note(IMAGE, to_sheet_key(KEY), BASS, util.is_sharp(KEY))
    cv2.imshow("Test", IMAGE)
    key = cv2.waitKey(0)
    if key == ord('q'):
        break
