from time import time, sleep
from queue import Queue
from threading import Thread

import cv2

import argparsers
import util
import draw

def writer_loop(writer, queue):
    while True:
        frame, prev_frame = queue.get(True)
        if frame is None:
            break
        frame_time = time() - prev_frame
        if frame_time < args.fps:
            sleep(args.fps - frame_time)
        writer.write(frame)

def main(args):
    input_name = "../resources/recorded/" + args.in_file + ".bin"
    output_name = f"{util.RENDER_PATH}/{args.out_file}.avi"

    fcc = cv2.VideoWriter_fourcc(*"XVID")

    writer = cv2.VideoWriter(output_name, fcc, args.fps, args.size, True)

    data, key_events = util.load_key_events(input_name)

    key_pos = draw.calculate_key_positions(args.size[0])

    timestep = 1 / args.fps
    timestamp = 0
    events = 0
    progress_indicators = 50
    progress = 0
    time_left = (
        (data[-1]["timestamp"] - data[0]["timestamp"]) * 0.08
        * ((args.size[0] * args.size[1]) / (1920*1080)) * args.fps
    )

    print(f"Rendering '{input_name}' in '{args.size[0]}x{args.size[1]}p' at '{args.fps}' fps", flush=True)

    buffer_size = min(300 * ((1920 * 1080) / (args.size[0] * args.size[1])), len(data))
    queue = Queue(int(buffer_size))
    t = Thread(target=writer_loop, args=(writer, queue))
    t.start()
    total_frames = int(data[-1]["timestamp"] * args.fps)
    frames = 0
    started = time()
    render_time = time()

    try:
        while not draw.end_of_data(timestamp, data):
            frame_time = time()
            active_keys, events = util.get_key_statuses(timestamp, key_events)

            frame = draw.draw_piano(active_keys, key_pos, args.size, frames / total_frames)
            queue.put((frame, time() - frame_time), True)

            timestamp += timestep
            indicators = 0
            if int(events / len(data) * 100) > progress:
                progress = int(events / len(data) * 100)
                indicators = int(progress / (100 / progress_indicators))
                new_time_left = ((time() - started) / events) * (len(data) - events)
                if new_time_left <= time_left:
                    time_left = new_time_left
                prog_str = "#" * indicators
                remain_str = "_" * (progress_indicators - indicators)
                print("[" + prog_str + remain_str + "] (" +
                      str(progress) +
                      "%) " + str(int(time_left)) + " s.", end=" ", flush=True)
                print("\r", end="", flush=True)

            frames += 1

        print("[" + ("#" * indicators) + "] (100%) 0s")
    finally:
        queue.put((None, None))
        t.join()
        print(f"Rendered video to file '{output_name}'")
        print(f"Rendering took {(time() - render_time):.2f} seconds.")
        writer.release()

if __name__ == "__main__":
    args = argparsers.args_render()

    main(args)
