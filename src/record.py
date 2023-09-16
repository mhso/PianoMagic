from time import time
from pickle import dump

import mido

import util
import argparsers

def main(args):
    recorded_notes = []
    started = time()
    try:
        with mido.open_input() as inport:
            while True:
                parsed_obj = util.get_input_key(inport, started)
                if parsed_obj is not None:
                    recorded_notes.append(parsed_obj)

                    note = util.get_note_desc(parsed_obj["key"])
                    if parsed_obj["velocity"] > 0:
                        print(f"{note} up")
                    else:
                        print(f"{note} down")
    except OSError:
        print("Error: No digital piano detected, please connect one.")
        exit(0)
    except KeyboardInterrupt:
        pass
    finally:
        if recorded_notes != []:
            with open(args.out_file, "wb") as r_out:
                dump(recorded_notes, r_out)
                print(f"Saved recording to file '{args.out_file}'")

if __name__ == "__main__":
    ARGS = argparsers.args_record()

    main(ARGS)
