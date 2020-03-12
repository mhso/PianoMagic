from time import time
from glob import glob
from pickle import dump
import mido
import util

PATH = "../resources/recorded/"
NUM_FILES = len(glob(PATH + "*.bin"))
OUTPUT_FILE = f"{PATH}" + util.get_kw_value("out", f"rec_{NUM_FILES}") + ".bin"
RECORDED_NOTES = []

STARTED = time()
try:
    with mido.open_input() as inport:
        while True:
            MSG = inport.receive(True)
            PARSED_OBJ = util.parse_midi_msg(MSG, STARTED)
            if PARSED_OBJ is not None:
                RECORDED_NOTES.append(PARSED_OBJ)

                NOTE = util.get_note_desc(MSG.note)
                if MSG.velocity > 0:
                    print(f"{NOTE} up")
                else:
                    print(f"{NOTE} down")
except OSError:
    print("Error: No digital piano detected, please connect one.")
    exit(0)
except KeyboardInterrupt:
    pass
finally:
    with open(OUTPUT_FILE, "wb") as r_out:
        dump(RECORDED_NOTES, r_out)
        print(f"Saved recording to file '{OUTPUT_FILE}'")
