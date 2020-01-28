from pickle import load

with open("../resources/recorded/rec_3.bin", "rb") as f_in:
    data = load(f_in)
    for frame_data in data:
        if frame_data["key"] == 41:#38:
            print(frame_data)