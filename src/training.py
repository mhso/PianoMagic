import random
from time import time
import mido
import numpy as np
import cv2
import util
import draw

DIFFICULTY = util.get_kw_value("diff", 2) # Difficulty ranges from 1-5

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
    offset_x = draw.SHEET_PADDING_X
    max_width = img.shape[1] - (draw.SHEET_PADDING_X * 2)
    width = int(progress * max_width)
    y = int(img.shape[0] - draw.SHEET_PADDING_X)
    color = get_countdown_color(progress)
    cv2.line(img, (offset_x, y), (img.shape[1] - offset_x, y), (0, 0, 0), 12)
    cv2.line(img, (offset_x, y), (offset_x + width, y), color, 10)

def draw_score(img, correct, total):
    point_str = "Score: " + str(correct) + "/" + str(total)
    x = img.shape[1] // 2 - (len(point_str) * 17)
    y = img.shape[0] // 6
    cv2.putText(img, point_str, (x, y), cv2.QT_FONT_NORMAL, 2, (0, 0, 0), 4)

def draw_out_of_time(img):
    h, w = img.shape[:2]
    cv2.putText(img, "Out of time!", (w // 2 - 300, h // 2 + 30),
                cv2.QT_FONT_NORMAL, 3, (0, 0, 255), 5)

QUESTIONS = 200

def generate_questions(q_number):
    data = []
    duration_init = 12 - DIFFICULTY
    duration_end = 7 - (DIFFICULTY // 2)
    duration = duration_init - (q_number / QUESTIONS) * (duration_init - duration_end)
    amount_init = DIFFICULTY
    amount_end = 6 + DIFFICULTY
    amount = int(amount_end * (q_number / QUESTIONS)) + amount_init
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

def draw_pressed_notes(img, sheet_note, is_treble, is_sharp, status, pressed, index):
    note_draw, treble_draw, sharp_draw = sheet_note, is_treble, is_sharp
    color = None
    if status == 1:
        color = (0, 255, 0)
    elif status == -1:
        color = (0, 0, 255)
        note_draw, treble_draw = pressed
        sharp_draw = util.is_sharp(note_draw)
        sheet_note = util.to_sheet_key(note_draw)
    draw.draw_note(img, index, sheet_note, treble_draw, sharp_draw, color)

def animate_questions(img, notes, timelimit, port):
    curr_note = 0
    elapsed_time = 0
    sleep_time = 10
    correct = 0
    statuses = [0 for _ in notes]
    changed = [True for _ in notes]
    pressed_notes = [None for _ in notes]
    last_note = time()
    while elapsed_time < timelimit and curr_note < len(notes):
        before = time()
        pressed_note = util.get_input_key(port, blocking=False)
        if pressed_note and pressed_note["down"]:
            pressed_note = pressed_note["key"]
        else:
            pressed_note = None
        if before - last_note < 0.5:
            pressed_note = None
        for i, (note, is_treble) in enumerate(notes):
            is_sharp = util.is_sharp(note)
            sheet_note = util.to_sheet_key(note)
            if changed[i]:
                draw_pressed_notes(img, sheet_note, is_treble,
                                   is_sharp, statuses[i], pressed_notes[i], i)
                changed[i] = False
            if pressed_note is not None and i == curr_note:
                last_note = time()
                if pressed_note == note:
                    statuses[i] = 1
                    correct += 1
                else:
                    statuses[i] = -1
                curr_note += 1
                changed[i] = True
                pressed_notes[i] = (pressed_note, is_treble)
                pressed_note = None
        draw_countdown(img, elapsed_time / timelimit)

        cv2.imshow("Piano Quiz", img)
        real_time = (time() - before) * 1000
        time_to_sleep = int(sleep_time - real_time) if real_time < sleep_time else sleep_time
        key = cv2.waitKey(time_to_sleep)
        if key == ord('q'):
            return correct, -1
        elapsed_time += time_to_sleep
    for i, (note, is_treble) in enumerate(notes):
        is_sharp = util.is_sharp(note)
        sheet_note = util.to_sheet_key(note)
        draw_pressed_notes(img, sheet_note, is_treble, is_sharp, statuses[i], pressed_notes[i], i)
    return correct, 1 if curr_note == len(notes) else 0

def training_loop(port):
    correct = 0
    for question in range(QUESTIONS):
        image = draw.create_sheet_image(util.SIZE)
        notes, duration = generate_questions(question)
        draw_score(image, correct, question+len(notes))
        notes_correct, status = animate_questions(image, notes, duration*1000, port)
        correct += notes_correct
        if status == -1: # Quit.
            break
        elif status == 0: # Out of time.
            draw_out_of_time(image)
        cv2.imshow("Piano Quiz", image)
        key = cv2.waitKey(1500)
        if key == ord('q'):
            break
    print(f"Training over! You hit '{correct}' correct notes out of a total of '{QUESTIONS}'.")

try:
    with mido.open_input() as inport:
        training_loop(inport)
except OSError:
    print("WARNING: No digital piano detected, please connect one.")
    training_loop(None)
