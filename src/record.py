from time import time
from glob import glob
from pickle import dump
from sys import argv
import mido

def create_note_list():
    notes = []
    sharp_distances = [1, 2, 1, 2, 1]
    last_sharp = 0
    sharp_index = 0
    key_index = 0
    for i in range(88):
        if last_sharp == sharp_distances[sharp_index % 5]:
            letter = notes[-1] + "#"
            sharp_index += 1
            last_sharp = 0
        else:
            key_numerical = key_index % 7
            letter = chr(key_numerical+65) + str(key_index // 7 + 1)
            key_index += 1
            last_sharp += 1
        notes.append(letter)
    return notes

NOTES = create_note_list()

def get_note(note_id):
    return NOTES[note_id - 21]

create_note_list()

RECORD = "-r" in argv
PATH = "../resources/recorded/"
NUM_FILES = len(glob(PATH + "*.bin"))
FILE = f"{PATH}rec_{NUM_FILES}.bin"
RECORDED_NOTES = []

STARTED = time()
try:
    with mido.open_input() as inport:
        while True:
            MSG = inport.receive(True)
            PARSED_OBJ = util.parse_midi_msg(MSG, STARTED)
            if PARSED_OBJ is not None and RECORD:
                RECORDED_NOTES.append(PARSED_OBJ)

            NOTE = get_note(MSG.note)
            if NOTE.velocity > 0:
                print(f"{NOTE} up")
            else:
                print(f"{NOTE} down")
except KeyboardInterrupt:
    pass
finally:
    with open(FILE, "wb") as r_out:
        dump(RECORDED_NOTES, r_out)
        print(f"Saved recording to file '{FILE}'")
