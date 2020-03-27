## PianoMagic - Visualizing MIDI inputs from digital piano
A collection of small programs for visualizing, and aiding in playing, any digital piano with MIDI input.

![PianoMagic](http://mhooge.com/pianomagic.png)

### Features
- Record and save your piano key strokes to a file
- Visualize and render these to mp4 video files (see an example [here](https://www.youtube.com/watch?v=ydZb75ywT30))
- "Mimic" previously recorded tracks, in the style of Synthesia or Guitar Hero, with tracking of accuracy and points
- Use a visual "quiz" to train your knowledge of musical notes

### Usage
1. Install Anaconda (or Miniconda)
2. Activate the conda environment in the root of the project using `conda env create -f piano_env.yml`
3. Navigate to the src folder

- Run `python record.py [out=name_of_output_file]` to record your key strokes on the piano
- Run `python render.py in=name_of_keystroke_file [out=name_of_output_file] [fps=video_fps] [size=(video_w,video_h)]` to render
a recorded file to mp4 video.
- Run `python mimic.py in=name_of_keystroke_file` [fps=video_fps] [size=(video_w,video_h)]` to mimic a recorded file
- Run `python training.py [diff=desired_difficulty]` to run a program which draws musical notes in sheet music for the user to
press on the piano. Several "rounds" of these visualizations are done, and in each the user has a certain amount of time to hit
the correct note.

Optional arguments in square brackets. All files are saved in the `resources` folder.
