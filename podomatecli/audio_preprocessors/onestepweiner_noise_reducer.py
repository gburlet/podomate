from scipy.fftpack import fft, ifft
import scipy.signal as sg
import numpy as np
import librosa

from mir.mir.transcription.audio_preprocessors.noise_reducer import NoiseReducer


class OneStepWeinerNoiseReducer(NoiseReducer):
    """
    Performs one-step weiner filter noise reduction on an input audio_buffer waveform

    References:
    [1] Cyril Plapous, Claude Marro, Pascal Scalart. Improved Signal-to-Noise Ratio Estimation for Speech
        Enhancement. IEEE Transactions on Audio, Speech and Language Processing, Institute of Electrical
        and Electronics Engineers, 2006.
    """

    ID = "onestepweiner"

    def __init__(self, window_size, hop_size):
        super(OneStepWeinerNoiseReducer, self).__init__(window_size, hop_size)

        self._Sbb = np.zeros(self._window_size)

    def analyze_silence(self, x_silence):
        """
        Estimation of the Power Spectral Density (Sbb) of the stationnary noise
        with Welch's periodogram given prior knowledge of n_noise points where
        speech is absent.
            Output :
                Sbb : 1D np.array, Power Spectral Density of stationnary noise
        """

        if len(x_silence) < self._window_size:
            x_silence = np.pad(x_silence, self._window_size, mode="constant", constant_values=0)

        self._Sbb = np.zeros(self._window_size)
        window = sg.hann(self._window_size)
        for i_frame, frame in enumerate(librosa.util.frame(x_silence, frame_length=self._window_size, hop_length=self._hop_size).T):
            X_frame = fft(frame*window, self._window_size)
            self._Sbb = i_frame * self._Sbb/(i_frame + 1) + np.abs(X_frame)**2/(i_frame + 1)

    def reduce_noise(self, sa):
        """
        Performs the noise reduction
        Note: auto_analyze_silence or analyze_silence must be called prior to calling this function

        Parameters
        ----------
        sa (SongAudio): audio_buffer waveform to reduce noise on

        Note: modifies SongAudio waveform in place!
        """

        if np.count_nonzero(self._Sbb) == 0:
            # if no silence has been analyzed, or silence is truly silence, escape
            return

        window = sg.hann(self._window_size)
        ew = np.sum(window)
        s_est = np.zeros_like(sa.x)
        for i_frame, frame in enumerate(librosa.util.frame(sa.x, frame_length=self._window_size, hop_length=self._hop_size).T):
            X_frame = fft(frame*window, self._window_size)

            # Apply a priori wiener gains G to X_framed to get output S
            SNR_post = (np.abs(X_frame)**2/ew)/self._Sbb
            S = X_frame * SNR_post / (SNR_post + 1)

            # Estimated signals at each frame normalized by the shift value
            temp_s_est = np.real(ifft(S)) * self._hop_size/self._window_size
            frame_start_sample = int(i_frame*self._hop_size)
            frame_end_sample = min(int(i_frame*self._hop_size + self._window_size), len(sa.x))
            signal_duration = frame_end_sample - frame_start_sample
            # truncate zero padding
            s_est[frame_start_sample:frame_end_sample] += temp_s_est[:min(self._window_size, signal_duration)]

        sa.x = s_est
