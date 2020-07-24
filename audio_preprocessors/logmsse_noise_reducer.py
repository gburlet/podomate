from __future__ import division

import math
import numpy as np
from scipy.special import expn
import librosa

from mir.mir.transcription.audio_preprocessors.noise_reducer import NoiseReducer


class LogMSSENoiseReducer(NoiseReducer):
    """
    Performs logMMSE noise reduction on an input audio waveform

    References:
    [1] Ephraim, Y. and Malah, D. (1985). Speech enhancement using a minimum
        mean-square error log-spectral amplitude estimator. IEEE Trans. Acoust.,
        Speech, Signal Process., ASSP-23(2), 443-445. 1984
    """

    ID = "logmsse"

    def __init__(self, window_size, hop_size, noise_threshold=0.15):
        super(LogMSSENoiseReducer, self).__init__(window_size, hop_size)

        self._noise_threshold = noise_threshold

        # noise reduction state (analyzed from silent audio)
        self._noise_mu2 = np.zeros(2*self._window_size)
        self._Xk_prev = np.zeros(self._hop_size)
        self._x_old = np.zeros(self._hop_size)

    def analyze_silence(self, x_silence):
        if len(x_silence) < self._window_size:
            x_silence = np.pad(x_silence, self._window_size, mode="constant", constant_values=0)
        len2 = self._window_size - self._hop_size
        win = np.hanning(self._window_size)
        win = win * len2 / float(np.sum(win))
        nFFT = 2 * self._window_size

        silence_frames = librosa.util.frame(x_silence, frame_length=self._window_size, hop_length=self._hop_size)
        num_silence_frames = np.shape(silence_frames)[1]

        noise_mean = np.zeros(nFFT)
        for i_frame in xrange(num_silence_frames):
            noise_mean = noise_mean + np.absolute(np.fft.fft(win * silence_frames[:,i_frame], nFFT, axis=0))
        self._noise_mu2 = (noise_mean / float(num_silence_frames)) ** 2

    def reduce_noise(self, sa):
        """
        Performs the noise reduction
        Note: auto_analyze_silence or analyze_silence must be called prior to calling this function

        Parameters
        ----------
        sa (SongAudio): audio waveform to reduce noise on

        Note: modifies SongAudio waveform in place!
        """

        if np.count_nonzero(self._noise_mu2) == 0:
            # if no silence has been analyzed, or silence is truly silence, escape
            return

        len2 = int(self._window_size - self._hop_size)

        win = np.hanning(self._window_size)
        win = win * len2 / np.sum(win)
        nFFT = 2 * self._window_size

        Nframes = int(math.floor(len(sa.x) / len2) - math.floor(self._window_size / len2))
        xfinal = np.zeros(Nframes * len2)

        aa = 0.98
        mu = 0.98
        ksi_min = 10 ** (-25 / 10)

        for k in range(0, Nframes*len2, len2):
            insign = win * sa.x[k:k + self._window_size]

            spec = np.fft.fft(insign, nFFT, axis=0)
            sig = np.absolute(spec)
            sig2 = sig ** 2

            gammak = np.minimum(sig2 / self._noise_mu2, 40)

            if self._Xk_prev.all() == 0:
                ksi = aa + (1 - aa) * np.maximum(gammak - 1, 0)
            else:
                ksi = aa * self._Xk_prev / self._noise_mu2 + (1 - aa) * np.maximum(gammak - 1, 0)
                ksi = np.maximum(ksi_min, ksi)

            log_sigma_k = gammak * ksi/(1 + ksi) - np.log(1 + ksi)
            vad_decision = np.sum(log_sigma_k)/float(self._window_size)
            if vad_decision < self._noise_threshold:
                self._noise_mu2 = mu * self._noise_mu2 + (1 - mu) * sig2

            A = ksi / (1 + ksi)
            vk = A * gammak
            ei_vk = 0.5 * expn(1, vk)
            hw = A * np.exp(ei_vk)
            # exponential integral returns inf if vk is zero and then hw is nan
            hw[np.isinf(hw)] = 1.0
            sig = sig * hw
            self._Xk_prev = sig ** 2
            xi_w = np.fft.ifft(hw * spec, nFFT, axis=0)
            xi_w = np.real(xi_w)

            xfinal[k:k + len2] = self._x_old + xi_w[0:self._hop_size]
            self._x_old = xi_w[self._hop_size:self._window_size]

        sa.x = xfinal
