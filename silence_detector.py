import librosa
import numpy as np
from hmmlearn import hmm
from scipy import signal


class SilenceDetector(object):
    """
    Detect silent portions in an audio waveform
    """

    THRESHOLD_METHOD_RMSPROP = "rmsprop"
    THRESHOLD_METHOD_DB = "db"
    THRESHOLD_METHOD_LOGMEAN = "losgmean"
    THRESHOLD_METHOD_ADAPTIVERMSPROP = "adaptivermsprop"
    INTERMEDIARY_SILENCE_BUFFER_S = 0.1
    FRAMING_METHOD_TIME = "time"
    FRAMING_METHOD_SPECTRUM = "spectrum"
    FRAMING_METHOD_ENERGY = "energy"

    def __init__(self, window_size=1024, hop_size=512, framing_method=FRAMING_METHOD_ENERGY,
                 threshold_method=THRESHOLD_METHOD_LOGMEAN,
                 threshold=0.1, min_silence_len_s=0.3):
        """
        Parameters
        ----------
        window_size (int): analysis window size in samples
        hop_size (int): hop size in samples
        framing_method (string):
            "time": uses raw audio samples for a given frame
            "spectrum": uses average energy spectrum for a given frame
        threshold_method (string):
            rmsprop: threshold proportion of RMS from noise floor to signal max
            db: static db SPL threshold
            adaptivermsprop: threshold proportion of RMS from local noise floor to local signal max
        threshold (float):
            rmsprop: relative % between min RMSE and max RMSE
            db: negative decibel level below max signal amplitude to place silence threshold
            logmean: the "a bit"
        min_silence_len_s (float): minimum length of silent portions to tag
        """

        self._window_size = window_size
        self._hop_size = hop_size
        self._framing_method = framing_method
        self._threshold_method = threshold_method
        self._threshold = threshold
        self._min_silence_len_s = min_silence_len_s
        self._viterbi_decoding = True

    def detect_silences(self, sa):
        """
        Detects silent portions of audio in the given audio waveform

        Parameters
        ----------
        sa (SongAudio): audio to analyze

        Returns
        -------
        silent_ranges (list) of tuples of floats
        """

        if sa.get_duration_s() < self._min_silence_len_s:
            return []

        if self._threshold_method not in {SilenceDetector.THRESHOLD_METHOD_RMSPROP, SilenceDetector.THRESHOLD_METHOD_DB,
                                          SilenceDetector.THRESHOLD_METHOD_ADAPTIVERMSPROP,
                                          SilenceDetector.THRESHOLD_METHOD_LOGMEAN}:
            raise NotImplementedError("Unknown thresholding method: %s" % self._threshold_method)

        if self._framing_method not in {SilenceDetector.FRAMING_METHOD_TIME, 
                                        SilenceDetector.FRAMING_METHOD_SPECTRUM, 
                                        SilenceDetector.FRAMING_METHOD_ENERGY}:
            raise NotImplementedError("Unknown framing method: %s" % self._framing_method)

        if self._framing_method == SilenceDetector.FRAMING_METHOD_TIME:
            frame_rms = np.sqrt(np.max(np.abs(
                librosa.util.frame(sa.x, frame_length=self._window_size, hop_length=self._hop_size)
            )**2, axis=0))
            frame_rms = signal.medfilt(frame_rms, kernel_size=5)
        elif self._framing_method == SilenceDetector.FRAMING_METHOD_SPECTRUM:
            stft_matrix = librosa.core.stft(
                sa.x, n_fft=self._window_size, hop_length=self._hop_size, 
                win_length=self._window_size, center=False,
                window=signal.hamming)
            mag, phase = librosa.core.magphase(stft_matrix, power=2)
            frame_rms = librosa.power_to_db(mag).mean(axis=0)
            frame_rms = signal.medfilt(frame_rms, kernel_size=5)
        elif self._framing_method == SilenceDetector.FRAMING_METHOD_ENERGY:
            frame = SilenceDetector.pre_emphasis(
                librosa.util.frame(sa.x, frame_length=self._window_size, hop_length=self._hop_size).T, pre=0.97)
            frame_energy = (frame**2).sum(axis=-1)
            frame_energy[frame_energy == 0] = 1
            frame_rms = np.log(frame_energy)

        silence_threshold_rms = 1.
        if self._threshold_method == SilenceDetector.THRESHOLD_METHOD_RMSPROP:
            silence_threshold_rms = self.threshold_method_rmsprop(frame_rms)
        elif self._threshold_method == SilenceDetector.THRESHOLD_METHOD_DB:
            silence_threshold_rms = self.threshold_method_db()
        elif self._threshold_method == SilenceDetector.THRESHOLD_METHOD_ADAPTIVERMSPROP:
            silence_threshold_rms = self.threshold_method_adaptivermsprop(frame_rms)
        elif self._threshold_method == SilenceDetector.THRESHOLD_METHOD_LOGMEAN:
            silence_threshold_rms = self.threshold_method_log_mean(frame_rms)

        # create silence frame mask (1 if silence, 0 if signal above threshold amplitude)
        silent_frames = np.zeros(len(frame_rms)+2, dtype=np.int8)  # pad each end with an extra 0 for processing
        silent_frames[1:-1] = frame_rms < silence_threshold_rms

        if self._viterbi_decoding:
            silent_frames[1:-1] = SilenceDetector._viterbi_decoding(silent_frames[1:-1])

        absdiff = np.abs(np.diff(silent_frames))
        # Runs start and end where absdiff is 1.
        silent_frame_runs = np.where(absdiff == 1)[0].reshape(-1, 2)

        silent_ranges_s = []
        for i_range in range(np.shape(silent_frame_runs)[0]):
            range_start_s = (silent_frame_runs[i_range][0] * self._hop_size) / float(sa.fs)
            range_end_s = (max(silent_frame_runs[i_range][1]-1, 0) * self._hop_size + self._window_size) / float(sa.fs)

            # add 0.05s buffer time on silence boundaries for intermediary piece silences
            if range_start_s != 0. and range_start_s + SilenceDetector.INTERMEDIARY_SILENCE_BUFFER_S < range_end_s:
                range_start_s += SilenceDetector.INTERMEDIARY_SILENCE_BUFFER_S
            if (abs(range_end_s - sa.get_duration_s()) > SilenceDetector.INTERMEDIARY_SILENCE_BUFFER_S and
                    range_end_s-SilenceDetector.INTERMEDIARY_SILENCE_BUFFER_S > range_start_s):
                range_end_s -= 0.25*SilenceDetector.INTERMEDIARY_SILENCE_BUFFER_S

            range_duration_s = range_end_s - range_start_s
            if range_duration_s >= self._min_silence_len_s:
                silent_ranges_s.append((range_start_s, range_end_s))

        return silent_ranges_s

    def get_sample_of_silence(self, sa, method="maxfirstlast"):
        """
        Helper function to return a silent portion of audio from the waveform using the provided method

        Parameters
        ----------
        sa (SongAudio): audio to analyze
        method (string): selection method for silence range in {max, first, last, maxfirstlast}

        Returns
        -------
        max_silence_range (pair of floats) or None if no found silent ranges
        """

        if method not in {"max", "first", "last", "maxfirstlast"}:
            raise NotImplementedError("Unknown silence selector method: %s" % method)

        silent_ranges_s = self.detect_silences(sa)
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
            
    def threshold_method_db(self):
        """
        Helper function to return threshold using static method

        Returns
        -------
        silence_threshold_rms (float): threshold for signal to noise
        """
        silence_threshold_rms = 10 ** (self._threshold / 20.)
        return silence_threshold_rms
    
    def threshold_method_rmsprop(self, frame_rms):
        """
        Helper function to return threshold using interpolation between max and min rms

        Parameters
        ----------
        frame_rms (np.array(n,)): array to analyze

        Returns
        -------
        silence_threshold_rms (float): threshold for signal to noise
        """
        min_rms = np.min(frame_rms)
        max_rms = np.max(frame_rms)
        silence_threshold_rms = min_rms + self._threshold * (max_rms - min_rms)
        return silence_threshold_rms
    
    def threshold_method_adaptivermsprop(self, frame_rms):
        """
        Helper function to return threshold local min and max value

        Parameters
        ----------
        frame_rms (np.array(n,)): array to analyze

        Returns
        -------
        silence_threshold_rms (np.array(n,): threshold for signal to noise
        """
        peak_points = signal.find_peaks(frame_rms)[0]
        silence_threshold_rms = np.zeros((len(frame_rms)))
        peak_points = np.concatenate([peak_points, [len(frame_rms) - 1]])
        for point in range(len(peak_points)):
            if point == 0:
                start_point = 0
            else:
                start_point = peak_points[point - 1] + 1
            min_rms = np.min(frame_rms[start_point:peak_points[point]+1])
            max_rms = np.max(frame_rms[start_point:peak_points[point]+1])
            silence_threshold_rms[start_point:peak_points[point]+1] = min_rms + self._threshold * (max_rms - min_rms)
        return silence_threshold_rms

    def threshold_method_log_mean(self, frame_rms):
        """
        Helper function to return threshold using log mean RMS minus a bit

        Parameters
        ----------
        frame_rms (np.array(n,)): array to analze

        Returns
        -------
        silence_threshold_rms (float): threshold for signal to noise
        """
        return np.mean(frame_rms) + np.log(self._threshold)

    @staticmethod
    def pre_emphasis(input_sig, pre):
        """
        pre emphasis filter increases the SNR for higher frequencies with a first-order auto-regressive filter:

        y[n] -> y[n] - coef * y[n-1]

        Parameters
        ----------
        input_sig (np.array([n,d] or np.array([n,]) : framed audio
        pre [0,1] (float): coefficient the pre-emphasis filter

        Returns
        -------
        filtered frame (np.array([n,d] or np.array([n,]): emphasised framed audio
        """
        if input_sig.ndim == 1:
            return (input_sig - np.c_[input_sig[np.newaxis, :][..., :1],
                                      input_sig[np.newaxis, :][..., :-1]].squeeze() * pre)
        else:
            return input_sig - np.c_[input_sig[..., :1], input_sig[..., :-1]] * pre

    @staticmethod
    def _viterbi_decoding(raw_activity):
        """
        HMM to output most probable sequence

        References:
        [1] Doukhan, D., Lechapt, E., Evrad, M. and Carrive, J., (2018) INA'S MIREX 2018 MUSIC AND
            SPEECH DETECTION SYSTEM Music Information Retrieval Evaluation eXchange (MIREX).

        Parameters
        ----------
        raw_activity (np.array([n,])): discrete sequence

        Returns
        -------
        final_sequence (np.array([n,])): smoothed sequence after viterbi decoding
        """
        def trans_exp(exp, cost0=0, cost1=0):
            """
            transition matrix for viterbi

            Parameters
            ----------
            exp (int): cost taken as 10**(-exp)
            cost0 (int): transitioning from state 0 to state 0
            cost1 (int): transitioning from state 1 to state 1

            Returns
            -------
            transition_matrix (np.array([2,2])): transition matrix
            """
            cost = -exp * np.log(10)
            trans_matrix = np.ones((2, 2)) * cost
            trans_matrix[0, 0] = cost0
            trans_matrix[1, 1] = cost1
            return np.exp(trans_matrix) / np.exp(trans_matrix).sum(axis=-1, keepdims=True)

        model = hmm.MultinomialHMM(n_components=2)
        model.transmat_ = trans_exp(100, cost0=-5)
        model.startprob_ = np.ones((2,)) / 2.
        model.emissionprob_ = np.array([[1-1e-10, 1e-10], [1e-10, 1-1e-10]])
        log_prob, final_sequence = model.decode(np.asarray(raw_activity, dtype=np.int8).reshape(-1, 1))
        return final_sequence
