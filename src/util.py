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
            key_events[key_data["key"]].append(key_data["timestamp"])

    return data, key_events

def parse_midi_msg(msg, time_started):
    rec_obj = None
    if msg.type != "clock":
        rec_obj = {
            "down": True,
            "velocity": 0,
            "key": -1
        }
        rec_obj["key"] = msg.note - 21
        is_down = msg.velocity > 0
        rec_obj["down"] = is_down
        rec_obj["timestamp"] = time() - time_started
        if is_down:
            rec_obj["velocity"] = msg.velocity
    return rec_obj
