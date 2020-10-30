from abc import ABCMeta, abstractmethod
import numpy as np

from audio_buffer import AudioBuffer


class NoiseReducer(object):
    """
    An abstract class representing a noise reduction algorithm
    """

    __metaclass__ = ABCMeta

    def __init__(self, window_size=1024, hop_size=512):
        """
        Parameters
        ----------
        window_size (int): analysis window size in samples
        hop_size (int): hop size in samples
        """

        self._window_size = window_size
        self._hop_size = hop_size

    def auto_reduce_noise(self, track):
        """
        Parameters
        ----------
        track (Track)
        """

        silence_ranges = track.silence_range_cache if track.silence_range_cache else track.silence_ranges
        max_silence_range = self._get_sample_of_silence(silence_ranges, method="max")
        if max_silence_range is not None:
            silence_start_sample = track.audio_buffer.get_sample_from_timestamp(max_silence_range[0])
            silence_end_sample = track.audio_buffer.get_sample_from_timestamp(max_silence_range[1])
            audio_buffer_sample = AudioBuffer(
                x=np.copy(track.audio_buffer.x[silence_start_sample:silence_end_sample]),
                fs=track.audio_buffer.fs
            )
            # analyze noise profile
            self.analyze_silence(audio_buffer_sample)
            # reduce noise
            self.reduce_noise(track)

    def _get_sample_of_silence(self, silent_ranges_s, method="max"):
        """
        Helper function to return a silent portion of audio from the waveform using the provided method
        Parameters
        ----------
        silent_ranges_s (list of float timestamp pairs)
        method (string): selection method for silence range in {max, first, last, maxfirstlast}

        Returns
        -------
        max_silence_range (pair of floats) or None if no found silent ranges
        """

        if method not in {"max", "first", "last", "maxfirstlast"}:
            raise NotImplementedError("Unknown silence selector method: %s" % method)

        if len(silent_ranges_s):
            if method == "max":
                return silent_ranges_s[np.argmax(map(lambda r: r[1]-r[0], silent_ranges_s))]
            elif method == "first":
                return silent_ranges_s[0]
            elif method == "last":
                return silent_ranges_s[-1]
            elif method == "maxfirstlast":
                first_silence_duration = silent_ranges_s[0][1] - silent_ranges_s[0][0]
                last_silence_duration = silent_ranges_s[-1][1] - silent_ranges_s[-1][0]
                i_selected_silence = 0 if first_silence_duration > last_silence_duration else -1
                return silent_ranges_s[i_selected_silence]

    @abstractmethod
    def analyze_silence(self, audio_buffer_sample):
        """
        Analyze an audio_buffer waveform to form a silence profile to use for noise reduction.
        Sets instance member variables with state.

        Parameters
        ----------
        audio_buffer_sample (AudioBuffer): audio buffer sample of silence
        """
        pass

    @abstractmethod
    def reduce_noise(self, track):
        """
        Performs the noise reduction
        Note: auto_analyze_silence or analyze_silence must be called prior to calling this function

        Parameters
        ----------
        track (Track) to reduce noise on

        Note: modifies track AudioBuffer in place!
        """
        pass
