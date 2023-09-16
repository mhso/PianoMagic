from time import time
import board
import neopixel

import mido

import util

NUM_LEDS = 74
PIXELS = neopixel.NeoPixel(board.D18, NUM_LEDS, brightness=0.7)

def get_pixel_index(key):
    # len_row_1_max = 37
    # gap = 1
    row_2_max = 75

    if key % 2 == 0:
        return row_2_max - (key // 2)

    return key // 2

def get_pixel_color(pos):
    if pos < 0 or pos > 255:
        r = g = b = 0

    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0

    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)

    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)

    return (r, g, b)


def main():
    started = time()

    try:
        with mido.open_input() as inport:
            while True:
                parsed_obj = util.get_input_key(inport, started)
                if parsed_obj is not None:
                    note = util.get_note_desc(parsed_obj["key"])
                    index = get_pixel_index(parsed_obj["key"])
                    if parsed_obj["velocity"] > 0:
                        PIXELS[index] = get_pixel_color(parsed_obj["key"] // len(util.NOTES))
                        print(f"{note} up")
                    else:
                        PIXELS[index] = 0
                        print(f"{note} down")
    except OSError:
        print("Error: No digital piano detected, please connect one.")
        exit(0)
    except KeyboardInterrupt:
        pass
    finally:
        PIXELS.deinit()

if __name__ == "__main__":
    main()
