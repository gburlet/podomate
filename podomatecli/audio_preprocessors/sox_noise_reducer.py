from __future__ import division

import os
import tempfile

import sox

from audio_preprocessors.noise_reducer import NoiseReducer


class SoxNoiseReducer(NoiseReducer):
    """
    Performs noise reduction on an input audio_buffer waveform using sox's algorithm
    """

    ID = "sox"

    def __init__(self, window_size, hop_size, noise_threshold=0.3):
        super(SoxNoiseReducer, self).__init__(window_size, hop_size)

        self._noise_threshold = noise_threshold
        self._noise_profile_path = None

    def analyze_silence(self, audio_buffer_sample):
        tfm = sox.Transformer()

        """
        # get noise profile as string
        _, self._profile, err = tfm.build(
            input_array=x_silence, sample_rate_in=44100, output_filepath='-n', return_output=True,
            extra_args=['noiseprof']
        )
        """

        # write noise profile to file
        with tempfile.NamedTemporaryFile(suffix='.profile', delete=False) as fp:
            tfm.build(
                input_array=audio_buffer_sample.x, sample_rate_in=audio_buffer_sample.fs, output_filepath='-n',
                extra_args=['noiseprof', fp.name]
            )
            self._noise_profile_path = fp.name

    def reduce_noise(self, track):
        """
        Performs the noise reduction
        Note: auto_analyze_silence or analyze_silence must be called prior to calling this function

        Parameters
        ----------
        track: (Track) to reduce noise on

        Note: modifies track AudioBuffer in place!
        """

        if not os.path.isfile(self._noise_profile_path):
            raise IOError("Can not find calculated noise profile")

        tfm = sox.Transformer()
        tfm.noisered(self._noise_profile_path, self._noise_threshold)
        track.audio_buffer.x = tfm.build_array(
            input_array=track.audio_buffer.x, sample_rate_in=track.audio_buffer.fs
        ).copy()
        # copy required to make output array mutable

        os.remove(self._noise_profile_path)


if __name__ == "__main__":
    from track import Track

    dirty_path = "/Users/gburlet/Podomate/crapmictest.mp3"
    clean_path = "/Users/gburlet/Podomate/crapmictest_clean.flac"
    track = Track.from_audio_file(dirty_path, master=True)
    nr = SoxNoiseReducer(2048, 1024, 0.3)
    nr.auto_reduce_noise(track)
    track.audio_buffer._path = clean_path
    track.audio_buffer.write()

