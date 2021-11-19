from time import time, sleep
from multiprocessing import Process, Queue

import mido
import cv2

import util
import draw
import argparsers

def filter_events(key_events, prev_presses):
    filtered = [0 for _ in range(88)]
    for note, events in enumerate(key_events):
        for status, _, _ in events:
            if status == "pressed":
                if not prev_presses[note]:
                    filtered[note] = 1
                prev_presses[note] = True
            elif status == "passed" and prev_presses[note]:
                filtered[note] = -1
                prev_presses[note] = False
    return filtered, prev_presses

def render_buffered(data, key_events, key_pos, size, timestep, queue, tolerance, total_frames):
    timestamp = 0

    prev_press = [False for _ in range(88)]

    headstart = 5
    frames = 0
    offset = []
    images = []

    try:
        while not draw.end_of_data(timestamp, data):
            key_statuses, _ = util.get_key_statuses(timestamp, key_events)
            filtered, prev_press = filter_events(key_statuses, prev_press)
            offset.append(filtered)
            if len(offset) > tolerance:
                offset.pop(0)

            image = draw.draw_piano(key_statuses, key_pos, size,
                                    frames / total_frames, draw_presses=False)
            if len(images) < headstart:
                images.append(image)
                image = images.pop(0)
            timestamp += timestep
            queue.put((image, [x for x in offset]), timeout=3)
            frames += 1
    except Exception as e:
        print(e)
        print("Queue 'put' timed out.")
        exit(0)

def main(args):
    input_name = "../resources/recorded/" + args.in_file + ".bin"
    data, key_events = util.load_key_events(input_name)

    key_pos = draw.calculate_key_positions(args.size[0])
    timestep = 1 / args.fps
    total_frames = int(data[-1]["timestamp"] * args.fps)

    buffer_size = min(300 * ((1920 * 1080) / (args.size[0] * args.size[1])), len(data))
    queue = Queue(int(buffer_size))
    frame_tolerance = args.fps // 5

    print("Preparing...")

    p = Process(target=render_buffered, args=(data, key_events, key_pos, args.size, timestep, queue, frame_tolerance, total_frames))
    p.start()

    while queue.qsize() < buffer_size * 0.8: # Wait for buffer to be at least 80% full.
        sleep(0.1)

    started = time()
    ms_per_frame = int(timestep * 1000)
    key_grace = [0 for _ in range(88)]
    keys_held = [False] * 88
    draw_event = [False] * 88
    note_over = [False] * 88
    notes_reset = [True] * 88
    points_per_key = [0] * 88
    base_reward = 5
    hits = 0
    error_deduction = 10
    total_notes = 0
    total_points = 0
    streak = 0

    try:
        with mido.open_input() as inport:
            while not queue.empty():
                frame_before = time()
                (img, frame_events) = queue.get()

                while args.freeze and frame_events:
                    msg = inport.receive(True)
                    parsed_obj = util.parse_midi_msg(msg, started)
                    if parsed_obj is not None and parsed_obj["key"] == frame_events[2][note_id]:
                        break

                for msg in inport.iter_pending():
                    parsed_obj = util.parse_midi_msg(msg, started)
                    if parsed_obj is not None:
                        keys_held[parsed_obj["key"]] = parsed_obj["down"]

                for note_id in range(88):
                    frame_reshaped = [x[note_id] for x in frame_events]
                    # Check if current key should be pressed at this moment.
                    if any(frame_reshaped):
                        # If current key is not held down, mark it as being down.
                        if notes_reset[note_id]:
                            notes_reset[note_id] = False
                            total_notes += 1 # Increment total notes.

                        # Get the press velocity for the currently held key.
                        press_evnt = 0
                        for evnt in frame_reshaped:
                            if evnt != 0:
                                press_evnt = evnt

                        # Ensure points for the current key is not negative.
                        if points_per_key[note_id] < 0:
                            points_per_key[note_id] = 0

                        # Check if current key is pressed sufficiently quickly to award points.
                        if key_grace[note_id] < frame_tolerance:
                            # Check if we pressed down and whether current event requires us to do so.
                            if press_evnt > 0 and keys_held[note_id]:
                                draw.draw_correct_note(img, note_id, key_pos)
                                # Check if we are yet to award points.
                                if points_per_key[note_id] == 0:
                                    # Add points based on how close to perfect timing the press was.
                                    points_per_key[note_id] = base_reward * (frame_tolerance - key_grace[note_id])
                                    hits += 1
                                    streak += 1
                                    total_points += points_per_key[note_id]
                                # Indicate that the current note is currently being drawn.
                                draw_event[note_id] = True
                                key_grace[note_id] = 0
                            # Check if key is not pressed, and current event requires the key to unpressed.
                            elif press_evnt < 0 and not keys_held[note_id] and draw_event[note_id]:
                                # Add points based on how close to perfect timing the release was.
                                points_per_key[note_id] = base_reward * (frame_tolerance - key_grace[note_id])
                                total_points += points_per_key[note_id]
                                draw_event[note_id] = False # No active draw event.
                                note_over[note_id] = True # Note is done (no longer being held).
                                key_grace[note_id] = 0
                                streak += 1
                                hits += 1

                        # Check if we are holding down a key. If so, mark note as being active.
                        if press_evnt > 0:
                            note_over[note_id] = False
                        # Check if we are not holding down a key, but a note is still active
                        # (meaning the key was released too soon).
                        elif not note_over[note_id]:
                            points_per_key[note_id] = -error_deduction # Deduct points.
                            total_points += points_per_key[note_id]
                            note_over[note_id] = True # Mark note as not being active anymore.
                            key_grace[note_id] = 0
                        if not note_over[note_id]:
                            key_grace[note_id] += 1
                    else: # No event is active for current key, mark it as reset.
                        notes_reset[note_id] = True

                    # Check whether a key should be held down, but was pressed too late.
                    if key_grace[note_id] >= frame_tolerance and not note_over[note_id]:
                        draw.draw_wrong_note(img, note_id, key_pos)
                        if points_per_key[note_id] == 0:
                            # Deduct points (but only once per note).
                            streak = 0
                            points_per_key[note_id] = -error_deduction
                            total_points += points_per_key[note_id]
                    # Check whether a note is currently being drawn as pressed.
                    elif draw_event[note_id]:
                        # Check whether the currently drawn key is being held.
                        if draw_event[note_id] > 0 and keys_held[note_id]:
                            key_grace[note_id] = 0
                            draw.draw_correct_note(img, note_id, key_pos)
                        else:
                            key_grace[note_id] += 1
                            if key_grace[note_id] >= frame_tolerance:
                                draw.draw_wrong_note(img, note_id, key_pos)
                                if points_per_key[note_id] == 0:
                                    streak = 0
                                    points_per_key[note_id] = -error_deduction
                                    total_points += points_per_key[note_id]
                                    if note_over[note_id]:
                                        key_grace[note_id] = 0
                                        draw_event[note_id] = False
                    elif keys_held[note_id]:
                        draw.draw_wrong_note(img, note_id, key_pos)
                        if points_per_key[note_id] == 0:
                            streak = 0
                            points_per_key[note_id] = -error_deduction
                            total_points += points_per_key[note_id]

                total_points = int(total_points) if total_points >= 0 else 0
                draw.draw_points(img, total_points)
                draw.draw_streak(img, streak)
                draw.draw_hits(img, hits, total_notes)

                cv2.imshow("Test", img)

                frame_time = (time() - frame_before) * 1000

                time_to_sleep = 1
                if frame_time < ms_per_frame:
                    time_to_sleep = (ms_per_frame - frame_time) / args.speed

                key = cv2.waitKey(int(time_to_sleep))
                if key == ord('q'):
                    cv2.destroyAllWindows()
                    break
    except OSError:
        print("Error: No digital piano detected, please connect one.")
    finally:
        p.terminate()

if __name__ == "__main__":
    ARGS = argparsers.args_mimic()

    main(ARGS)
