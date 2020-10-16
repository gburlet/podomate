import numpy as np

from audio_buffer import AudioBuffer
from track import Track


class Mixer(object):

    def __init__(self):
        pass

    def mix_tracks(self, tracks):
        num_tracks = len(tracks)
        master_track = next(t for t in tracks if t.master)
        mixed_buffer = np.zeros_like(master_track.audio_buffer.x)
        for t in tracks:
            mixed_buffer += 1./num_tracks * t.audio_buffer.x

        mixed_track = Track(
            audio=AudioBuffer(x=mixed_buffer, fs=master_track.audio_buffer.fs), master=True
        )
        mixed_track.timeline = master_track.timeline
        return mixed_track
