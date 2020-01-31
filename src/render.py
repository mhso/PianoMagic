from time import time
from queue import Queue
from threading import Thread
from glob import glob
from sys import argv
import cv2
import util
import draw

def writer_loop(writer, queue):
    while True:
        frame = queue.get(True)
        if frame is None:
            break
        writer.write(FRAME)

if __name__ == "__main__":
    INPUT_FILE = util.get_kw_value("in", mandatory=True)
    INPUT_NAME = "../resources/recorded/" + INPUT_FILE + ".bin"

    FCC = cv2.VideoWriter_fourcc(*"XVID")
    PATH = "../resources/rendered/"
    NUM_FILES = len(glob(PATH + "*.avi"))
    if "-o" in argv:
        NUM_FILES -= 1
    OUTPUT_FILE = f"{PATH}" + util.get_kw_value("out", f"rendered_{NUM_FILES}") + ".avi"
    FPS = float(util.get_kw_value("fps", 30))
    SIZE_SPLIT = util.get_kw_value("size", "(1920,1080)").split(",")
    SIZE = (int(SIZE_SPLIT[0][1:]), int(SIZE_SPLIT[1][:-1]))

    WRITER = cv2.VideoWriter(OUTPUT_FILE, FCC, FPS, SIZE, True)

    DATA, KEY_EVENTS = util.load_key_events(INPUT_NAME)

    KEY_POS = draw.calculate_key_positions(SIZE[0])

    TIMESTEP = 1 / FPS
    TIMESTAMP = 0
    STARTED = time()
    EVENTS = 0
    INDICATORS = 50
    PROGRESS = 0
    TIME_LEFT = (
        (DATA[-1]["timestamp"] - DATA[0]["timestamp"]) * 0.08
        * ((SIZE[0] * SIZE[1]) / (1920*1080)) * FPS
    )

    print("Rendering...")

    BUFFER_SIZE = min(300 * ((1920 * 1080) / (SIZE[0] * SIZE[1])), len(DATA))
    QUEUE = Queue(int(BUFFER_SIZE))
    t = Thread(target=writer_loop, args=(WRITER, QUEUE))
    t.start()
    FRAMES = 0

    try:
        while not draw.end_of_data(TIMESTAMP, DATA):
            ACTIVE_KEYS, EVENTS = draw.get_key_statuses(TIMESTAMP, KEY_EVENTS)

            FRAME = draw.draw_piano(ACTIVE_KEYS, KEY_POS, SIZE)
            QUEUE.put(FRAME, True)

            TIMESTAMP += TIMESTEP
            if int(EVENTS / len(DATA) * INDICATORS) > PROGRESS:
                PROGRESS = int(EVENTS / len(DATA) * INDICATORS)
                new_time_left = ((time() - STARTED) / EVENTS) * (len(DATA) - EVENTS)
                if new_time_left <= TIME_LEFT:
                    TIME_LEFT = new_time_left
                prog_str = "#" * PROGRESS
                remain_str = "_" * (INDICATORS - PROGRESS)
                print("[" + prog_str + remain_str + "] (" + str(int(PROGRESS * (100 / INDICATORS))) +
                    "%) " + str(int(TIME_LEFT)) + " s.", end=" ", flush=True)
                print("\r", end="")
            FRAMES += 1

        print("[" + ("#" * INDICATORS) + "] (100%) 0s")
        print(f"Rendered video to file '{OUTPUT_FILE}'")
        print(FRAMES / TIMESTAMP)
    finally:
        QUEUE.put(None)
        t.join()
        WRITER.release()
