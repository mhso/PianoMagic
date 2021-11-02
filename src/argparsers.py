from glob import glob
import argparse

import util

def parse_size(value):
    stripped = value
    if value[0] == "(":
        stripped = stripped[1:]
    if value[-1] == ")":
        stripped = stripped[:-1]
    
    split = stripped.split(",")

    if len(split) != 2:
        raise argparse.ArgumentTypeError("Tuple value expected.")

    try:
        tup = int(split[0].strip()), int(split[1].strip())
        return tup
    except ValueError:
        raise argparse.ArgumentTypeError("Tuple values should be integers.")

def parser_visual():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--size", type=parse_size, default=(1920, 1080))

    return parser

def args_render():
    parser = parser_visual()

    parser.add_argument("--in_file", type=str, required=True)

    num_files = len(glob(util.RENDER_PATH + "/*.avi"))

    parser.add_argument("--out_file", type=str, default=f"rendered_{num_files}")

    return parser.parse_args()

def args_mimic():
    parser = parser_visual()

    parser.add_argument("--in_file", type=str, required=True)
    parser.add_argument("--speed", type=float, default=1)
    parser.add_argument("--freeze", action="store_true")

    return parser.parse_args()

def args_training():
    parser = parser_visual()

    parser.add_argument("--difficulty", type=int, default=2) # Difficulty ranges from 1-5

    return parser.parse_args()

def args_visual():
    return parser_visual().parse_args()
