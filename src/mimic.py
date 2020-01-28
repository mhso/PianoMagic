from time import time
import cv2
import mido
import util
import draw

def filter_events(key_events, prev_presses):
    filtered = [0 for _ in range(88)]
    for note, events in enumerate(key_events):
        any_pressed = False
        for status, _, _ in events:
            if status == "pressed":
                filtered[note] = 1
                prev_presses[note] = True
                any_pressed = True
        if prev_presses[note] and not any_pressed:
            filtered[note] = -1
            prev_presses[note] = False
    return filtered, prev_presses

INPUT_FILE = util.get_kw_value("in", mandatory=True)
INPUT_NAME = "../resources/recorded/" + INPUT_FILE + ".bin"
DATA, KEY_EVENTS = util.load_key_events(INPUT_NAME)

FPS = float(util.get_kw_value("fps", 30))

SIZE = (1920//2, 1080//2)
KEY_POS = draw.calculate_key_positions(SIZE[0])

TIMESTEP = 1 / FPS
TIMESTAMP = 0

print("Preparing...")

FRAMES = []
FRAME_EVENTS = []
PREV_PRESS = [False for _ in range(88)]

while not draw.end_of_data(TIMESTAMP, DATA):
    KEY_STATUSES, _ = draw.get_key_statuses(TIMESTAMP, KEY_EVENTS)
    FILTERED, PREV_PRESS = filter_events(KEY_STATUSES, PREV_PRESS)

    FRAME_EVENTS.append(FILTERED)

    IMAGE = draw.draw_piano(KEY_STATUSES, KEY_POS, SIZE, draw_presses=False)
    TIMESTAMP += TIMESTEP
    FRAMES.append(IMAGE)

STARTED = time()
KEY_GRACE = [0 for _ in range(88)]
KEYS_HELD = [False] * 88
FRAME_ACC_THRESH = FPS // 8
ONGOING_EVENT = [False] * 88
POINTS_PER_KEY = [0] * 88
TOTAL_POINTS = 0

with mido.open_input() as inport:
    for frame, (img, frame_event) in enumerate(zip(FRAMES, FRAME_EVENTS)):
        for MSG in inport.iter_pending():
            PARSED_OBJ = util.parse_midi_msg(MSG, STARTED)
            if PARSED_OBJ is not None:
                KEYS_HELD[PARSED_OBJ["key"]] = PARSED_OBJ["down"]

        for note_id in range(88):
            if frame_event[note_id]:
                if ONGOING_EVENT[note_id]:
                    if POINTS_PER_KEY[note_id] > 0:
                        draw.draw_correct_note(img, note_id, KEYS_HELD[note_id], KEY_POS)
                        ONGOING_EVENT[note_id] = False
                    elif POINTS_PER_KEY[note_id] < 0:
                        draw.draw_wrong_note(img, note_id, KEYS_HELD[note_id], KEY_POS)
                elif abs(KEY_GRACE[note_id]) < FRAME_ACC_THRESH:
                    if frame_event[note_id] > 0 and KEYS_HELD[note_id]:
                        ONGOING_EVENT[note_id] = True
                        draw.draw_correct_note(img, note_id, KEYS_HELD[note_id], KEY_POS)
                        POINTS_PER_KEY[note_id] = FRAME_ACC_THRESH - KEY_GRACE[note_id]
                        TOTAL_POINTS += POINTS_PER_KEY[note_id]
                        KEY_GRACE[note_id] = 0
                    elif frame_event[note_id] < 0 and not KEYS_HELD[note_id]:
                        ONGOING_EVENT[note_id] = False
                        POINTS_PER_KEY[note_id] = FRAME_ACC_THRESH - abs(KEY_GRACE[note_id])
                        TOTAL_POINTS += POINTS_PER_KEY[note_id]
                        KEY_GRACE[note_id] = 0
                    else:
                        KEY_GRACE[note_id] += frame_event[note_id]
                elif not ONGOING_EVENT[note_id]:
                    ONGOING_EVENT[note_id] = True
                    draw.draw_wrong_note(img, note_id, KEYS_HELD[note_id], KEY_POS)
                    KEY_GRACE[note_id] = 0
                    POINTS_PER_KEY[note_id] = -10
                    TOTAL_POINTS += POINTS_PER_KEY[note_id]
            else:
                POINTS_PER_KEY[note_id] = 0
                ONGOING_EVENT[note_id] = False

        draw.draw_points(img, int(TOTAL_POINTS))

        cv2.imshow("Test", img)
        key = cv2.waitKey(int(TIMESTEP * 1000))
        if key == ord('q'):
            break
