import numpy as np
import cv2

BG_COLOR = 185

def draw_note(img, note_index):
    pass

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

    vertical_gap = 50
    space_between = 25
    padding_x = 50
    for sign in range(-1, 2, 2):
        for y_offset in range(5):
            y = int(h / 2 + (y_offset * space_between + vertical_gap) * sign)
            cv2.line(img, (padding_x, y), (w-padding_x, y), (0, 0, 0), 2)

    split_lines = 6
    left = int((w - padding_x * 2) / (split_lines-1))
    for x_offset in range(split_lines):
        x = padding_x + int(left * x_offset)
        cv2.line(img, (x, int(h / 2 - (4 * space_between + vertical_gap))),
                 (x, int(h / 2 + (4 * space_between + vertical_gap))), (0, 0, 0), 2)

    treb_clef_img = cv2.resize(cv2.imread("../resources/img/treble-clef.png", -1), (72, 172))
    bass_clef_img = cv2.resize(cv2.imread("../resources/img/bass-clef.png", -1), (82, 82))
    img = overlay_img(img, treb_clef_img, padding_x + 10, int(h / 2 - space_between * 7.25))
    img = overlay_img(img, bass_clef_img, padding_x + 5, int(h / 2 + space_between * 1.95))

    return img

# Draw notes, maybe with a countdown.
SIZE = (1920, 1080)
IMAGE = create_image(SIZE)
cv2.imshow("Test", IMAGE)
cv2.waitKey(0)
