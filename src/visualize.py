from time import time

import mido
import cv2

import argparsers
import draw
import util

def get_pressed_keys(port):
    notes = []
    for msg in port.iter_pending():
        parsed_obj = util.parse_midi_msg(msg, time())
        if parsed_obj is not None:
            notes.append(parsed_obj)
    return notes

def main(args):
    img = draw.create_sheet_image(args.size)

    try:
        with mido.open_input() as inport:
            active_keys = [None] * 88
            while True:
                pressed_keys = get_pressed_keys(inport)

                for key_index, obj in enumerate(pressed_keys):
                    if obj["down"]:
                        active_keys[obj["key"]] = (obj, key_index)
                    else:
                        active_keys[obj["key"]] = None
                if pressed_keys != []:
                    img = draw.create_sheet_image(args.size)

                for i in range(88):
                    if active_keys[i] is not None:
                        note_obj, key_index = active_keys[i]
                        draw.draw_note(
                            img, key_index, util.to_sheet_key(note_obj["key"]),
                            True, util.is_sharp(note_obj["key"])
                        )

                cv2.imshow("Piano Quiz", img)
                key = cv2.waitKey(10)
                if key == ord('q'):
                    break
    except OSError:
        print("WARNING: No digital piano detected, please connect one.")

if __name__ == "__main__":
    ARGS = argparsers.args_visual()

    main(ARGS)
