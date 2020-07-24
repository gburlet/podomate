import os

from librosa import load, to_mono, resample
from librosa.util import normalize as audio_normalize
from scipy.io import wavfile
import numpy as np
import warnings

warnings.simplefilter('ignore', wavfile.WavFileWarning)


class SpeakerAudio(object):
    """
    This class is a data structure for an audio file samples along with its metadata.

    Whenever reading audio samples from disk and passing these
    samples around for processing, you always need the corresponding sampling rate. This allows us to pass
    around this information together and to do smart resampling (only resample when necessary).
    """

    def __init__(self, path):
        self._path = path
        self.fs = None
        self.x = None

    def read(self, fs=None, normalize=True, min_length_s=0.2):
        """
        Reads in audio samples from disk

        Parameters
        ----------
        fs (int): desired sampling rate. None uses native sampling rate
        normalize (bool): whether to normalize the audio samples
        min_length_s (float): ensure audio file is at least x seconds long
            Note: this avoids analysis errors where audio length is less than a single window length

        Returns
        -------
        x [num_samples,]: audio samples
        """

        ext = os.path.splitext(self._path)[-1]
        if ext == ".wav":
            # Scipy wavfile is generally better than librosa, but fails on some wavs, so librosa is a backup
            try:
                self.fs, x_temp = wavfile.read(self._path)
                
                # convert to float in [-1, 1] if int data
                if x_temp.dtype.name in {'int8', 'int16', 'int32'}:
                    num_bits = x_temp.dtype.itemsize * 8
                    max_val = float(2 ** (num_bits - 1))
                    x_temp = np.asarray(x_temp, dtype=np.float32) / max_val

                self.x = to_mono(x_temp.T)
                if fs and fs != self.fs:
                    _ = self.resample_audio(fs)
            except:
                load_params = {"mono": True}
                if fs:
                    load_params["sr"] = fs
                self.x, self.fs = load(self._path, **load_params)
        else:
            load_params = {"mono": True}
            if fs:
                load_params["sr"] = fs
            self.x, self.fs = load(self._path, **load_params)

        if normalize:
            self.x = audio_normalize(self.x, norm=np.inf)

        min_samps = int(np.ceil(min_length_s * self.fs))
        if len(self.x) < min_samps:
            # pad with zeros for length
            self.x = np.pad(self.x, (0, min_samps - len(self.x) % min_samps), 'constant')

        return self.x

    def get_resampled_audio(self, target_fs):
        """
        Calculate resampled audio waveform (don't overwrite)

        Parameters
        ----------
        target_fs (int): sampling rate to resample to

        Returns
        -------
        sa_resampled (SpeakerAudio): resampled audio file
        """

        if target_fs != self.fs:
            sa_resampled = SpeakerAudio(self._path)
            sa_resampled.x = resample(self.x, self.fs, target_fs, res_type="kaiser_fast")
            sa_resampled.fs = target_fs
            return sa_resampled
        return self

    def resample_audio(self, target_fs):
        """
        Resample underlying audio signal to target_fs

        Parameters:
        x [num_samples,]: audio samples
        target_fs (int): sampling rate to resample to

        Returns
        -------
        x [num_samples,]: audio samples
        """

        new_speaker_audio = self.get_resampled_audio(target_fs)
        self.x = new_speaker_audio.x
        self.fs = new_speaker_audio.fs

        return self.x

    def get_duration_s(self):
        """
        Returns
        -------
        duration (float): duration of the audio waveform in seconds
        """
        return np.shape(self.x)[0] / float(self.fs)

    def apply_offset(self, offset_s):
        offset_samples = int(offset_s * float(self.fs))
        if offset_s > 0:
            offset_samples = int(offset_s * float(self.fs))
            self.x = np.hstack((np.zeros(offset_samples), self.x))
        elif offset_s < 0:
            self.x = self.x[offset_samples:]
