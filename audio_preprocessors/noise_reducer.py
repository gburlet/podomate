from abc import ABCMeta, abstractmethod

from mir.mir.transcription.audio_preprocessors.silence_detector import SilenceDetector


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

    def auto_analyze_silence(self, sa):
        """
        Automatically detects largest portion of silence in raw signal waveform and analyzes it,
        setting relevant state variables on the class

        Parameters
        ----------
        sa (SongAudio): the audio waveform to analyze

        Returns
        -------
        max_silent_range (pair of float timestamps): indicating beginning and end timestamp of max duration silence
        """

        silence_detector = SilenceDetector(window_size=self._window_size, hop_size=self._hop_size)
        selected_silence = silence_detector.get_sample_of_silence(sa, method='first')
        if selected_silence is not None:
            silence_start_sample = max(0, int(selected_silence[0] * sa.fs))
            silence_end_sample = min(int(selected_silence[1] * sa.fs), len(sa.x))
            self.analyze_silence(sa.x[silence_start_sample:silence_end_sample])

        return selected_silence

    def auto_reduce_noise(self, sa):
        """
        Automatically detects silence, analyzes silence, and performs noise reduction

        Parameters
        ----------
        sa (SongAudio): audio waveform to reduce noise on

        Note: modifies SongAudio waveform in place!
        """

        self.auto_analyze_silence(sa)
        self.reduce_noise(sa)

    @abstractmethod
    def analyze_silence(self, x_silence):
        """
        Analyze an audio waveform to form a silence profile to use for noise reduction.
        Sets instance member variables with state.

        Parameters
        ----------
        x_silence (np.array): audio waveform
        """
        pass

    @abstractmethod
    def reduce_noise(self, sa):
        """
        Performs the noise reduction
        Note: auto_analyze_silence or analyze_silence must be called prior to calling this function

        Parameters
        ----------
        sa (SongAudio): audio waveform to reduce noise on

        Note: modifies SongAudio waveform in place!
        """
        pass
