from sys import argv
from time import time
from pickle import load

BAR_SPEED = 3

def get_kw_value(keyword, default=None, mandatory=False):
    for arg in argv:
        split = arg.split("=")
        if len(split) == 2 and split[0] == keyword:
            return split[1]
    if mandatory:
        raise ValueError(f"Missing argument (and value) of keyword '{keyword}'.")
    return default

def load_key_events(filename):
    data = []
    with open(filename, "rb") as r_in:
        data = load(r_in)

    key_events = [[] for _ in range(88)]

    shift = 0
    if data[0]["timestamp"] < BAR_SPEED:
        shift = BAR_SPEED - data[0]["timestamp"]
    for key_data in data:
        if shift > 0:
            key_data["timestamp"] += shift
        key_events[key_data["key"]].append((key_data["timestamp"], key_data["down"]))

    return data, key_events

def create_record_obj(down, velocity, key, timestamp):
    return {
        "down": down,
        "velocity": velocity,
        "key": key,
        "timestamp": timestamp
    }

def parse_midi_msg(msg, time_started):
    rec_obj = None
    if msg is not None and msg.type != "clock":
        rec_obj = {
            "down": True,
            "velocity": 0,
            "key": -1
        }
        key = msg.note - 21
        is_down = msg.velocity > 0
        timestamp = time() - time_started
        velocity = 0
        if is_down:
            velocity = msg.velocity
        rec_obj = create_record_obj(is_down, velocity, key, timestamp)
    return rec_obj

def create_note_list():
    notes = []
    sharps = []
    sharp_distances = [1, 2, 1, 2, 1]
    last_sharp = 0
    sharp_index = 0
    key_index = 0
    for i in range(88):
        if last_sharp == sharp_distances[sharp_index % 5]:
            letter = notes[-1] + "#"
            sharps.append(i)
            sharp_index += 1
            last_sharp = 0
        else:
            key_numerical = key_index % 7
            letter = chr(key_numerical+65) + str(key_index // 7 + 1)
            key_index += 1
            last_sharp += 1
        notes.append(letter)
    return notes, sharps

NOTES, SHARPS = create_note_list()

def get_note_desc(note_id):
    return NOTES[note_id]

def is_sharp(note_id):
    return note_id in SHARPS
