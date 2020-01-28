from pickle import load

with open("../resources/recorded/rec_3.bin", "rb") as f_in:
    data = load(f_in)
    for i, frame_data in enumerate(data[:len(data)//2]):
        STATES[frame_data["key"]] = frame_data["down"]
