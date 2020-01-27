from time import time
import cv2
import mido
import util
import draw

def filter_events(key_events):
    filtered = [0 for _ in range(88)]
    for note, events in enumerate(key_events):
        for index, (status, start, end) in enumerate(events):
            if status == "pressed":
                filtered[note] = 1
            elif index > 0 and events[index-1] == "pressed":
                filtered[note] = -1
    return filtered

INPUT_FILE = util.get_kw_value("in", mandatory=True)
INPUT_NAME = "../resources/recorded/" + INPUT_FILE + ".bin"
DATA, KEY_EVENTS = util.load_key_events(INPUT_NAME)

FPS = float(util.get_kw_value("fps", 30))

SIZE = (1920, 1080)
KEY_POS = draw.calculate_key_positions(SIZE[0])

TIMESTEP = 1 / FPS
TIMESTAMP = 0

print("Preparing...")

FRAMES = []
FRAME_EVENTS = []

while not draw.end_of_data(TIMESTAMP, DATA):
    KEY_STATUSES, _ = draw.get_key_statuses(TIMESTAMP, KEY_EVENTS)
    FILTERED = filter_events(KEY_STATUSES)

    FRAME_EVENTS.append(FILTERED)

    IMAGE = draw.draw_piano(KEY_STATUSES, KEY_POS, SIZE)
    TIMESTAMP += TIMESTEP
    FRAMES.append(IMAGE)

STARTED = time()
KEY_GRACE = [0 for _ in range(88)]
KEYS_HELD = [False] * 88
FRAME_ACC_THRESH = FPS // 5

with mido.open_input() as inport:
    for frame, (img, frame_event) in enumerate(zip(FRAMES, FRAME_EVENTS)):
        for MSG in inport.iter_pending():
            PARSED_OBJ = util.parse_midi_msg(MSG, STARTED)
            if PARSED_OBJ is not None:
                KEYS_HELD[PARSED_OBJ["key"]] = PARSED_OBJ["down"]

        for note_id in range(88):
            if frame_event[note_id]:
                if abs(KEY_GRACE[note_id]) < FRAME_ACC_THRESH:
                    if KEY_GRACE[note_id] > 0 and KEYS_HELD[note_id]:
                        draw.draw_correct_note(img, note_id, KEYS_HELD[note_id], KEY_POS)
                        KEY_GRACE[note_id] = 0
                    elif KEY_GRACE[note_id] < 0 and not KEYS_HELD[note_id]:
                        KEY_GRACE[note_id] = 0
                    else:
                        KEY_GRACE[note_id] += frame_event[note_id]
                else:
                    draw.draw_wrong_note(img, note_id, KEYS_HELD[note_id], KEY_POS)

        cv2.imshow("Test", img)
        key = cv2.waitKey(int(TIMESTEP * 1000))
        if key == ord('q'):
            break
