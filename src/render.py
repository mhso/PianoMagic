from glob import glob
from sys import argv
import cv2
import util
import draw

if __name__ == "__main__":
    INPUT_FILE = util.get_kw_value("in", mandatory=True)
    INPUT_NAME = "../resources/recorded/" + INPUT_FILE + ".bin"

    FCC = cv2.VideoWriter_fourcc(*"XVID")
    PATH = "../resources/rendered/"
    NUM_FILES = len(glob(PATH + "*.avi"))
    if "-o" in argv:
        NUM_FILES -= 1
    FILE = f"{PATH}rendered_{NUM_FILES}.avi"
    FPS = float(util.get_kw_value("fps", 30))
    SIZE = (1920, 1080)

    WRITER = cv2.VideoWriter(FILE, FCC, FPS, SIZE, True)

    DATA, KEY_EVENTS = util.load_key_events(INPUT_NAME)

    KEY_POS = draw.calculate_key_positions(SIZE[0])

    TIMESTEP = 1 / FPS
    TIMESTAMP = 0
    EVENTS = 0
    INDICATORS = 20
    PROGRESS = 0

    print("Rendering...")

    while not draw.end_of_data(TIMESTAMP, DATA):
        active_keys, EVENTS = draw.get_key_statuses(TIMESTAMP, KEY_EVENTS)

        image = draw.draw_piano(active_keys, KEY_POS, SIZE)
        TIMESTAMP += TIMESTEP
        if int(EVENTS / len(DATA) * INDICATORS) > PROGRESS:
            PROGRESS = int(EVENTS / len(DATA) * INDICATORS)
            prog_str = "#" * PROGRESS
            remain_str = "_" * (INDICATORS - PROGRESS)
            print("[" + prog_str + remain_str + "] " + str(int(PROGRESS * (100 / INDICATORS))) + "%", end="", flush=True)
            print("\r", end="")

        WRITER.write(image)

    print("[" + ("#" * INDICATORS) + "] 100%")

    WRITER.release()
