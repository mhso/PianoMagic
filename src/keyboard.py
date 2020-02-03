from time import sleep
import mido
import win32api as win
import win32con as con
import util

def press_key(note_index):
    key = 0
    if note_index == 44:
        key = 0x51
    elif note_index == 46:
        key = 0x57
    elif note_index == 48:
        key = 0x45
    elif note_index == 50:
        key = 0x52
    win.keybd_event(key, 0, con.KEYEVENTF_EXTENDEDKEY, 0)

while True:
    with mido.open_input() as inport:
        for MSG in inport:
            PARSED_OBJ = util.parse_midi_msg(MSG, 0)
            if PARSED_OBJ is not None:
                KEY = PARSED_OBJ["key"]
                print(KEY)
                if PARSED_OBJ["down"] and KEY in (44, 46, 48, 50):
                    press_key(KEY)
