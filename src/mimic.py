from time import time, sleep
from multiprocessing import Process, Queue
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

def render_buffered(data, key_events, key_pos, size, timestep, queue):
    timestamp = 0

    prev_press = [False for _ in range(88)]

    try:
        while not draw.end_of_data(timestamp, data):
            key_statuses, _ = draw.get_key_statuses(timestamp, key_events)
            filtered, prev_press = filter_events(key_statuses, prev_press)

            image = draw.draw_piano(key_statuses, key_pos, size, draw_presses=False)
            timestamp += timestep
            queue.put((image, filtered), timeout=3)
    except Exception:
        print("Queue 'put' timed out.")
        exit(0)

if __name__ == "__main__":
    INPUT_FILE = util.get_kw_value("in", mandatory=True)
    INPUT_NAME = "../resources/recorded/" + INPUT_FILE + ".bin"
    DATA, KEY_EVENTS = util.load_key_events(INPUT_NAME)

    FPS = float(util.get_kw_value("fps", 30))
    SIZE = (1920, 1080)
    KEY_POS = draw.calculate_key_positions(SIZE[0])
    TIMESTEP = 1 / FPS

    BUFFER_SIZE = 400 * ((1920 * 1080) / (SIZE[0] * SIZE[1]))
    QUEUE = Queue(int(BUFFER_SIZE))

    print("Preparing...")

    p = Process(target=render_buffered, args=(DATA, KEY_EVENTS, KEY_POS, SIZE, TIMESTEP, QUEUE))
    p.start()

    while QUEUE.qsize() < BUFFER_SIZE * 0.8: # Wait for buffer to be at least 80% full.
        sleep(0.1)

    STARTED = time()
    KEY_GRACE = [0 for _ in range(88)]
    KEYS_HELD = [False] * 88
    FRAME_ACC_THRESH = FPS // 6
    ONGOING_EVENT = [False] * 88
    POINTS_PER_KEY = [0] * 88
    TOTAL_POINTS = 0
    MS_PER_FRAME = int(TIMESTEP * 1000)

    with mido.open_input() as inport:
        FRAME = 0
        while not QUEUE.empty():
            FRAME_BEFORE = time()
            (img, frame_event) = QUEUE.get()
            for MSG in inport.iter_pending():
                PARSED_OBJ = util.parse_midi_msg(MSG, STARTED)
                if PARSED_OBJ is not None:
                    KEYS_HELD[PARSED_OBJ["key"]] = PARSED_OBJ["down"]

            for note_id in range(88):
                if frame_event[note_id]:
                    if ONGOING_EVENT[note_id]:
                        if POINTS_PER_KEY[note_id] > 0:
                            draw.draw_correct_note(img, note_id, KEY_POS)
                            ONGOING_EVENT[note_id] = False
                        elif POINTS_PER_KEY[note_id] < 0:
                            draw.draw_wrong_note(img, note_id, KEY_POS)
                    elif abs(KEY_GRACE[note_id]) < FRAME_ACC_THRESH:
                        if frame_event[note_id] > 0 and KEYS_HELD[note_id]:
                            ONGOING_EVENT[note_id] = True
                            draw.draw_correct_note(img, note_id, KEY_POS)
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
                        draw.draw_wrong_note(img, note_id, KEY_POS)
                        KEY_GRACE[note_id] = 0
                        POINTS_PER_KEY[note_id] = -10
                        TOTAL_POINTS += POINTS_PER_KEY[note_id]
                else:
                    POINTS_PER_KEY[note_id] = 0
                    ONGOING_EVENT[note_id] = False

            draw.draw_points(img, int(TOTAL_POINTS))

            cv2.imshow("Test", img)

            FRAME_TIME = (time() - FRAME_BEFORE) * 1000

            SLEEP = 1
            if FRAME_TIME < MS_PER_FRAME:
                SLEEP = MS_PER_FRAME - FRAME_TIME

            KEY = cv2.waitKey(int(SLEEP))
            if KEY == ord('q'):
                cv2.destroyAllWindows()
                p.terminate()
                break

            FRAME += 1
