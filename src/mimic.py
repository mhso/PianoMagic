from time import time, sleep
from multiprocessing import Process, Queue
import mido
import cv2
import util
import draw

def filter_events(key_events, prev_presses):
    filtered = [0 for _ in range(88)]
    for note, events in enumerate(key_events):
        for status, _, _ in events:
            if status == "pressed":
                if not prev_presses[note]:
                    filtered[note] = 1
                prev_presses[note] = True
            elif status == "passed" and prev_presses[note]:
                filtered[note] = -1
                prev_presses[note] = False
    return filtered, prev_presses

def render_buffered(data, key_events, key_pos, size, timestep, queue, tolerance, total_frames):
    timestamp = 0

    prev_press = [False for _ in range(88)]

    headstart = 5
    frames = 0
    offset = []
    images = []

    try:
        while not draw.end_of_data(timestamp, data):
            key_statuses, _ = draw.get_key_statuses(timestamp, key_events)
            filtered, prev_press = filter_events(key_statuses, prev_press)
            offset.append(filtered)
            if len(offset) > tolerance:
                offset.pop(0)

            image = draw.draw_piano(key_statuses, key_pos, size,
                                    frames / total_frames, draw_presses=False)
            if len(images) < headstart:
                images.append(image)
                image = images.pop(0)
            timestamp += timestep
            queue.put((image, [x for x in offset]), timeout=3)
            frames += 1
    except Exception as e:
        print(e)
        print("Queue 'put' timed out.")
        exit(0)

if __name__ == "__main__":
    INPUT_FILE = util.get_kw_value("in", mandatory=True)
    INPUT_NAME = "../resources/recorded/" + INPUT_FILE + ".bin"
    DATA, KEY_EVENTS = util.load_key_events(INPUT_NAME)

    FPS = float(util.get_kw_value("fps", 30))
    SIZE_SPLIT = util.get_kw_value("size", "(1920,1080)").split(",")
    SIZE = (int(SIZE_SPLIT[0][1:]), int(SIZE_SPLIT[1][:-1]))
    SPEED = float(util.get_kw_value("speed", 1))
    KEY_POS = draw.calculate_key_positions(SIZE[0])
    FREEZE_MODE = util.get_kw_value("freeze", False)
    TIMESTEP = 1 / FPS
    TOTAL_FRAMES = int(DATA[-1]["timestamp"] * FPS)

    BUFFER_SIZE = min(300 * ((1920 * 1080) / (SIZE[0] * SIZE[1])), len(DATA))
    QUEUE = Queue(int(BUFFER_SIZE))
    FRAME_TOLERANCE = FPS // 5

    print("Preparing...")

    p = Process(target=render_buffered, args=(DATA, KEY_EVENTS, KEY_POS, SIZE, TIMESTEP, QUEUE, FRAME_TOLERANCE, TOTAL_FRAMES))
    p.start()

    while QUEUE.qsize() < BUFFER_SIZE * 0.8: # Wait for buffer to be at least 80% full.
        sleep(0.1)

    STARTED = time()
    MS_PER_FRAME = int(TIMESTEP * 1000)
    KEY_GRACE = [0 for _ in range(88)]
    KEYS_HELD = [False] * 88
    DRAW_EVENT = [False] * 88
    NOTE_OVER = [False] * 88
    NOTES_RESET = [True] * 88
    POINTS_PER_KEY = [0] * 88
    BASE_REWARD = 5
    HITS = 0
    TOTAL_NOTES = 0
    TOTAL_POINTS = 0
    STREAK = 0

    try:
        with mido.open_input() as inport:
            while not QUEUE.empty():
                FRAME_BEFORE = time()
                (img, frame_events) = QUEUE.get()

                while FREEZE_MODE and frame_events:
                    MSG = inport.receive(True)
                    PARSED_OBJ = util.parse_midi_msg(MSG, STARTED)
                    if PARSED_OBJ is not None and PARSED_OBJ["key"] == frame_events[2][note_id]:
                        break

                for MSG in inport.iter_pending():
                    PARSED_OBJ = util.parse_midi_msg(MSG, STARTED)
                    if PARSED_OBJ is not None:
                        KEYS_HELD[PARSED_OBJ["key"]] = PARSED_OBJ["down"]

                for note_id in range(88):
                    frame_reshaped = [x[note_id] for x in frame_events]
                    if any(frame_reshaped):
                        if NOTES_RESET[note_id]:
                            NOTES_RESET[note_id] = False
                            TOTAL_NOTES += 1
                        press_evnt = 0
                        for evnt in frame_reshaped:
                            if evnt != 0:
                                press_evnt = evnt
                        if POINTS_PER_KEY[note_id] < 0:
                            POINTS_PER_KEY[note_id] = 0
                        if KEY_GRACE[note_id] < FRAME_TOLERANCE:
                            if press_evnt > 0 and KEYS_HELD[note_id]:
                                draw.draw_correct_note(img, note_id, KEY_POS)
                                if POINTS_PER_KEY[note_id] == 0:
                                    POINTS_PER_KEY[note_id] = BASE_REWARD * (FRAME_TOLERANCE - KEY_GRACE[note_id])
                                    HITS += 1
                                    STREAK += 1
                                    TOTAL_POINTS += POINTS_PER_KEY[note_id]
                                DRAW_EVENT[note_id] = True
                                KEY_GRACE[note_id] = 0
                            elif press_evnt < 0 and not KEYS_HELD[note_id] and DRAW_EVENT[note_id]:
                                POINTS_PER_KEY[note_id] = BASE_REWARD * (FRAME_TOLERANCE - KEY_GRACE[note_id])
                                TOTAL_POINTS += POINTS_PER_KEY[note_id]
                                DRAW_EVENT[note_id] = False
                                NOTE_OVER[note_id] = True
                                KEY_GRACE[note_id] = 0
                                STREAK += 1
                                HITS += 1
                        if press_evnt > 0:
                            NOTE_OVER[note_id] = False
                        elif not NOTE_OVER[note_id]:
                            POINTS_PER_KEY[note_id] = -10
                            TOTAL_POINTS += POINTS_PER_KEY[note_id]
                            NOTE_OVER[note_id] = True
                            KEY_GRACE[note_id] = 0
                        if not NOTE_OVER[note_id]:
                            KEY_GRACE[note_id] += 1
                    else:
                        NOTES_RESET[note_id] = True
                    if KEY_GRACE[note_id] >= FRAME_TOLERANCE and not NOTE_OVER[note_id]:
                        draw.draw_wrong_note(img, note_id, KEY_POS)
                        if POINTS_PER_KEY[note_id] == 0:
                            STREAK = 0
                            POINTS_PER_KEY[note_id] = -10
                            TOTAL_POINTS += POINTS_PER_KEY[note_id]
                    elif DRAW_EVENT[note_id]:
                        if DRAW_EVENT[note_id] > 0 and KEYS_HELD[note_id]:
                            KEY_GRACE[note_id] = 0
                            draw.draw_correct_note(img, note_id, KEY_POS)
                        else:
                            KEY_GRACE[note_id] += 1
                            if KEY_GRACE[note_id] >= FRAME_TOLERANCE:
                                draw.draw_wrong_note(img, note_id, KEY_POS)
                                if POINTS_PER_KEY[note_id] == 0:
                                    STREAK = 0
                                    POINTS_PER_KEY[note_id] = -10
                                    TOTAL_POINTS += POINTS_PER_KEY[note_id]
                                    if NOTE_OVER[note_id]:
                                        KEY_GRACE[note_id] = 0
                                        DRAW_EVENT[note_id] = False
                    elif KEYS_HELD[note_id]:
                        draw.draw_wrong_note(img, note_id, KEY_POS)
                        if POINTS_PER_KEY[note_id] == 0:
                            STREAK = 0
                            POINTS_PER_KEY[note_id] = -10
                            TOTAL_POINTS += POINTS_PER_KEY[note_id]

                TOTAL_POINTS = int(TOTAL_POINTS) if TOTAL_POINTS >= 0 else 0
                draw.draw_points(img, TOTAL_POINTS)
                draw.draw_streak(img, STREAK)
                draw.draw_hits(img, HITS, TOTAL_NOTES)

                cv2.imshow("Test", img)

                FRAME_TIME = (time() - FRAME_BEFORE) * 1000

                SLEEP = 1
                if FRAME_TIME < MS_PER_FRAME:
                    SLEEP = (MS_PER_FRAME - FRAME_TIME) / SPEED

                KEY = cv2.waitKey(int(SLEEP))
                if KEY == ord('q'):
                    cv2.destroyAllWindows()
                    break
    except OSError:
        print("Error: No digital piano detected, please connect one.")
    finally:
        p.terminate()
