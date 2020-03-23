from time import time, sleep
from queue import Queue
from threading import Thread
from glob import glob
from sys import argv
import cv2
import util
import draw

def writer_loop(writer, queue):
    while True:
        frame, prev_frame = queue.get(True)
        if frame is None:
            break
        frame_time = time() - prev_frame
        if frame_time < util.FPS:
            sleep(util.FPS - frame_time)
        writer.write(frame)

if __name__ == "__main__":
    INPUT_FILE = util.get_kw_value("in", mandatory=True)
    INPUT_NAME = "../resources/recorded/" + INPUT_FILE + ".bin"

    FCC = cv2.VideoWriter_fourcc(*"XVID")
    PATH = "../resources/rendered/"
    NUM_FILES = len(glob(PATH + "*.avi"))
    if "-o" in argv:
        NUM_FILES -= 1
    OUTPUT_FILE = f"{PATH}" + util.get_kw_value("out", f"rendered_{NUM_FILES}") + ".avi"

    WRITER = cv2.VideoWriter(OUTPUT_FILE, FCC, util.FPS, util.SIZE, True)

    DATA, KEY_EVENTS = util.load_key_events(INPUT_NAME)

    KEY_POS = draw.calculate_key_positions(util.SIZE[0])

    TIMESTEP = 1 / util.FPS
    TIMESTAMP = 0
    EVENTS = 0
    PROGRESS_INDICATORS = 50
    PROGRESS = 0
    TIME_LEFT = (
        (DATA[-1]["timestamp"] - DATA[0]["timestamp"]) * 0.08
        * ((util.SIZE[0] * util.SIZE[1]) / (1920*1080)) * util.FPS
    )

    print("Rendering...")

    BUFFER_SIZE = min(300 * ((1920 * 1080) / (util.SIZE[0] * util.SIZE[1])), len(DATA))
    QUEUE = Queue(int(BUFFER_SIZE))
    t = Thread(target=writer_loop, args=(WRITER, QUEUE))
    t.start()
    TOTAL_FRAMES = int(DATA[-1]["timestamp"] * util.FPS)
    FRAMES = 0
    STARTED = time()
    RENDER_TIME = time()

    try:
        while not draw.end_of_data(TIMESTAMP, DATA):
            FRAME_TIME = time()
            ACTIVE_KEYS, EVENTS = util.get_key_statuses(TIMESTAMP, KEY_EVENTS)

            FRAME = draw.draw_piano(ACTIVE_KEYS, KEY_POS, util.SIZE, FRAMES / TOTAL_FRAMES)
            QUEUE.put((FRAME, time() - FRAME_TIME), True)

            TIMESTAMP += TIMESTEP
            if int(EVENTS / len(DATA) * 100) > PROGRESS:
                PROGRESS = int(EVENTS / len(DATA) * 100)
                INDICATORS = int(PROGRESS / (100 / PROGRESS_INDICATORS))
                new_time_left = ((time() - STARTED) / EVENTS) * (len(DATA) - EVENTS)
                if new_time_left <= TIME_LEFT:
                    TIME_LEFT = new_time_left
                prog_str = "#" * INDICATORS
                remain_str = "_" * (PROGRESS_INDICATORS - INDICATORS)
                print("[" + prog_str + remain_str + "] (" +
                      str(PROGRESS) +
                      "%) " + str(int(TIME_LEFT)) + " s.", end=" ", flush=True)
                print("\r", end="")
            FRAMES += 1

        print("[" + ("#" * INDICATORS) + "] (100%) 0s")
    finally:
        QUEUE.put((None, None))
        t.join()
        print(f"Rendered video to file '{OUTPUT_FILE}'")
        print(f"Rendering took {(time() - RENDER_TIME):.2f} seconds.")
        WRITER.release()
