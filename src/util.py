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

    if data[0]["timestamp"] < BAR_SPEED:
        shift = BAR_SPEED - data[0]["timestamp"]
        for key_data in data:
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
    if msg.type != "clock":
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
