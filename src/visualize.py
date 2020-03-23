from time import time
import mido
import cv2
import util
import draw

def get_pressed_keys(port):
    notes = []
    for msg in port.iter_pending():
        parsed_obj = util.parse_midi_msg(msg, time())
        if parsed_obj is not None:
            notes.append(parsed_obj)
    return notes

IMG = draw.create_sheet_image(util.SIZE)

try:
    with mido.open_input() as inport:
        ACTIVE_KEYS = [None] * 88
        while True:
            PRESSED_KEYS = get_pressed_keys(inport)
            for KEY_INDEX, OBJ in enumerate(PRESSED_KEYS):
                if OBJ["down"]:
                    ACTIVE_KEYS[OBJ["key"]] = (OBJ, KEY_INDEX)
                else:
                    ACTIVE_KEYS[OBJ["key"]] = None
            if PRESSED_KEYS != []:
                IMG = draw.create_sheet_image(util.SIZE)
            for i in range(88):
                if ACTIVE_KEYS[i] is not None:
                    NOTE_OBJ, KEY_INDEX = ACTIVE_KEYS[i]
                    draw.draw_note(IMG, KEY_INDEX, util.to_sheet_key(NOTE_OBJ["key"]),
                                   True, util.is_sharp(NOTE_OBJ["key"]))
            cv2.imshow("Piano Quiz", IMG)
            KEY = cv2.waitKey(10)
            if KEY == ord('q'):
                break
except OSError:
    print("WARNING: No digital piano detected, please connect one.")
