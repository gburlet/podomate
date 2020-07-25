import numpy as np

from audio_buffer import AudioBuffer


class Mixer(object):

    def __init__(self):
        pass

    def mix_tracks(self, tracks):
        num_tracks = len(tracks)
        mixed_buffer = np.zeros_like(tracks[0].audio_buffer.x)
        for t in tracks:
            mixed_buffer += 1./num_tracks * t.audio_buffer.x

        return AudioBuffer(x=mixed_buffer, fs=tracks[0].audio_buffer.fs)

