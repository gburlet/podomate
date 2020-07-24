from scipy.fftpack import fft, ifft
import scipy.signal as sg
import numpy as np
import librosa

from mir.mir.transcription.audio_preprocessors.noise_reducer import NoiseReducer


class TwoStepWeinerNoiseReducer(NoiseReducer):
    """
    Performs two-step weiner filter noise reduction on an input audio waveform

    References:
    [1] Cyril Plapous, Claude Marro, Pascal Scalart. Improved Signal-to-Noise Ratio Estimation for Speech
        Enhancement. IEEE Transactions on Audio, Speech and Language Processing, Institute of Electrical
        and Electronics Engineers, 2006.
    """

    ID = "twostepweiner"

    def __init__(self, window_size, hop_size, beta=0.98):
        super(TwoStepWeinerNoiseReducer, self).__init__(window_size, hop_size)

        # Typical constant used to determine SNR_dd_prio
        self._beta = beta
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
        sa (SongAudio): audio waveform to reduce noise on

        Note: modifies SongAudio waveform in place!
        """

        if np.count_nonzero(self._Sbb) == 0:
            # if no silence has been analyzed, or silence is truly silence, escape
            return

        # Initialising output estimated signal
        s_est_tsnr = np.zeros_like(sa.x)

        window = sg.hann(self._window_size)
        ew = np.sum(window)

        # Initialising matrix to store previous values.
        # For readability purposes, -1 represents past frame values and 0 represents actual frame values.
        S = np.zeros((2, self._window_size), dtype='cfloat')
        for i_frame, frame in enumerate(librosa.util.frame(sa.x, frame_length=self._window_size, hop_length=self._hop_size).T):
            X_frame = fft(frame*window, self._window_size)

            # Weiner filter: Computation of spectral gain G using SNR a posteriori
            SNR_post = np.abs(X_frame)**2/ew/self._Sbb
            S[0, :] = SNR_post/(SNR_post+1) * X_frame

            # Directed decision: Computation of spectral gain G_dd using output S of Wiener Filter
            SNR_dd_prio = self._beta*np.abs(S[-1, :])**2/self._Sbb + (1 - self._beta)*self._halfwave_rectification(SNR_post - 1)
            S_dd = SNR_dd_prio/(SNR_dd_prio+1) * X_frame

            # Two-step noise reduction: Computation of spectral gain G_tsnr using output S_dd of Directed Decision
            SNR_tsnr_prio = np.abs(S_dd)**2/self._Sbb
            S_tsnr = SNR_tsnr_prio/(SNR_tsnr_prio+1) * X_frame

            # Estimated temporal signal at frame normalized by the shift value
            temp_s_est_tsnr = np.real(ifft(S_tsnr)) * self._hop_size/self._window_size
            frame_start_sample = int(i_frame*self._hop_size)
            frame_end_sample = min(int(i_frame*self._hop_size + self._window_size), len(sa.x))
            signal_duration = frame_end_sample - frame_start_sample
            # truncate zero padding
            s_est_tsnr[frame_start_sample:frame_end_sample] += temp_s_est_tsnr[:min(self._window_size, signal_duration)]

            # Rolling matrix to update old values (Circshift in Matlab)
            S = np.roll(S, 1, axis=0)

        sa.x = s_est_tsnr

    def _halfwave_rectification(self, x):
        """
        Function that computes the half wave rectification with a threshold of 0.
            Input :
                array : 1D np.array, Temporal frame
            Output :
                halfwave : 1D np.array, Half wave temporal rectification
        """
        halfwave = np.zeros(x.size)
        halfwave[np.argwhere(x > 0)] = 1
        return halfwave
