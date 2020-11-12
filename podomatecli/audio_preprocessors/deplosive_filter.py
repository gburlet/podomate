import librosa
import numpy as np
from scipy.signal import butter, filtfilt


class DeplosiveFilter(object):
    """
    Locates, filters and attenuates plosive sounds in a track
    Locate: tag plosives with low zero-crossing rate and of considerable volumes
    Filter: high-pass filter the located plosive regions
    Attenuate: reduce the dB of the plosive regions
    """

    PRE_LPFILTER_CUTOFF = 800
    PRE_LPFILTER_ORDER = 5
    VAD_RMS_PERCENTILE = 30         # %ile to set threshold for voice activity RMS
    PUNCHY_RMS_PERCENTILE = 85      # %ile to set threshold for intense (punchy) voice activity
    PLOSIVE_0X_PERCENTILE = 30      # %ile to set threshold for plosive
    DEFAULT_RMS_MEAN = 0.04
    RMS_MOVING_AVG_FRAME_LAG = 5    # number of frames to calculate in RMS moving average
    PLOSIVE_HPFILTER_ORDER = 5
    HIGH_ENERGY_RMS_MULTIPLIER = 1.75
    ENERGY_BURST_RMS_PERCENT_DIFF = 1.0

    def __init__(self, window_size=1024, hop_size=1024, cutoff=225, db_attenuation=-3.5, min_plosive_length_s=0.03, max_plosive_length_s=0.2):
        """
        Parameters
        ----------
        window_size (int): analysis window size in samples
        hop_size (int): hop size in samples
        cutoff (int): plosive high-pass filter cut-off frequency
        db_attenuation (float): dB plosive attenuation after high-pass filtering
        min_plosive_length_s (float): any region tagged as a plosive shorter than this, skip it
        max_plosive_length_s (float): any region tagged as a plosive longer than this, skip it, prob not a plosive
        """

        self._window_size = window_size
        self._hop_size = hop_size
        self._plosive_cutoff_freq = cutoff
        self._db_attenuation = db_attenuation
        self._min_plosive_length_s = min_plosive_length_s
        self._max_plosive_length_s = max_plosive_length_s

    def process(self, track):
        """
        Parameters
        ----------
        track (Track): track to remove plosives from

        Algorithm: we're looking for short areas with low zero-crossing and relatively high volume
        ---------
        1. Low-pass filter @800Hz to remove excessive 0x in time domain interfering with analysis
        2. Remove any DC offset
        3. Calculate 0x and RMS thresholds for windowed signal
        4. Tag frames where plosive detected:
            low 0x & sudden burst in signal energy over moving average or just high signal energy
        # 5. Flood fill plosive tag gaps [Yes, No, Yes] -> [Yes, Yes, Yes]
        # 6. Convert plosive tags to regions at nearest 0xings
            Note: Operating on audio within 0xings removes clicks when applying filters
        # 7. Merge any overlapped regions resulting from analysis window hopping
        # 8. Perform high-pass filter & dB reduction on plosive to remove high impact breath hitting mic

        Note: modifies track AudioBuffer in place!
        """

        # 1. Low-pass filter to smooth
        b, a = butter(
            DeplosiveFilter.PRE_LPFILTER_ORDER, DeplosiveFilter.PRE_LPFILTER_CUTOFF, btype='low', fs=track.audio_buffer.fs
        )
        x_smoothed = filtfilt(b, a, track.audio_buffer.x)

        # 2. Remove any DC offset from low-pass smoothed signal
        dc_offset = np.mean(x_smoothed)
        if abs(dc_offset) > 0.001:
            x_smoothed += dc_offset

        # 3. Calculate 0x and RMS thresholds for windowed signal
        frame_rms = np.squeeze(librosa.feature.rms(
            x_smoothed, frame_length=self._window_size, hop_length=self._hop_size, center=False
        ))
        vad_rms_threshold = np.percentile(frame_rms, DeplosiveFilter.VAD_RMS_PERCENTILE)
        punchy_rms_threshold = np.percentile(frame_rms, DeplosiveFilter.PUNCHY_RMS_PERCENTILE)
        zero_x_rate = np.squeeze(librosa.feature.zero_crossing_rate(
            x_smoothed, frame_length=self._window_size, hop_length=self._hop_size, center=False
        ))
        plosive_0x_threshold = np.percentile(
            zero_x_rate[frame_rms > vad_rms_threshold], DeplosiveFilter.PLOSIVE_0X_PERCENTILE
        )

        # 4. Tag plosive frames
        frames = librosa.util.frame(
            x_smoothed, frame_length=self._window_size, hop_length=self._hop_size
        )
        num_frames = np.shape(frames)[1]
        is_plosive = np.zeros(num_frames, dtype=np.bool)
        for i_frame in range(num_frames):
            zero_crossing_rate = zero_x_rate[i_frame]
            rms = frame_rms[i_frame]
            moving_avg_rms_mean = float(np.mean(
                frame_rms[max(0,i_frame-DeplosiveFilter.RMS_MOVING_AVG_FRAME_LAG):i_frame]
            )) if i_frame > 0 else DeplosiveFilter.DEFAULT_RMS_MEAN

            rms_percent_diff = (rms-moving_avg_rms_mean) / moving_avg_rms_mean
            is_low_0x = zero_crossing_rate <= plosive_0x_threshold
            is_energy_burst = rms > punchy_rms_threshold and rms_percent_diff > DeplosiveFilter.ENERGY_BURST_RMS_PERCENT_DIFF
            is_high_energy = rms > DeplosiveFilter.HIGH_ENERGY_RMS_MULTIPLIER*punchy_rms_threshold and rms_percent_diff > 0.
            is_plosive[i_frame] = is_low_0x and (is_energy_burst or is_high_energy)

        # 5. Flood fill plosive gaps [Yes, No, Yes] -> [Yes, Yes, Yes]
        for i_frame in range(1, num_frames-1):
            if is_plosive[i_frame-1] and is_plosive[i_frame+1]:
                is_plosive[i_frame] = True

        # 6. Convert plosive tags to sample regions at nearest 0xings (list of sample indices)
        plosive_regions = []
        current_plosive = None
        for i_frame in range(num_frames):
            if is_plosive[i_frame]:
                if current_plosive is None:
                    # plosive OFF -> ON
                    current_plosive = [i_frame * self._hop_size, None]
                # track plosive end point
                current_plosive[1] = (i_frame * self._hop_size) + self._window_size
            else:
                if current_plosive:
                    # plosive ON -> OFF
                    plosive_duration_s = track.audio_buffer.get_timestamp_from_sample(current_plosive[1]) - track.audio_buffer.get_timestamp_from_sample(current_plosive[0])
                    if self._min_plosive_length_s <= plosive_duration_s <= self._max_plosive_length_s:
                        plosive_regions.append(current_plosive)
                current_plosive = None
        if current_plosive:
            current_plosive[1] = track.audio_buffer.get_num_samples()-1
            # plosive ON -> OFF
            plosive_duration_s = track.audio_buffer.get_timestamp_from_sample(current_plosive[1]) - track.audio_buffer.get_timestamp_from_sample(current_plosive[0])
            if self._min_plosive_length_s <= plosive_duration_s <= self._max_plosive_length_s:
                plosive_regions.append(current_plosive)

        # convert sample end points of plosive regions to 0xings
        plosive_regions = [
            [
                track.audio_buffer.get_previous_zero_crossing(pr[0], zero_tol=1e-2, sign_change=False),
                track.audio_buffer.get_next_zero_crossing(pr[1], zero_tol=1e-2, sign_change=False),
            ] for pr in plosive_regions
        ]

        # 7. Merge any overlapped regions
        for i_plosive in range(len(plosive_regions)-1,0,-1):
            if plosive_regions[i_plosive][0] < plosive_regions[i_plosive-1][1]:
                plosive_regions[i_plosive-1][1] = plosive_regions[i_plosive][1]
                del plosive_regions[i_plosive]

        # 8. Perform high-pass filter & dB reduction on plosive to remove high impact breath hitting mic
        b, a = butter(
            DeplosiveFilter.PLOSIVE_HPFILTER_ORDER, self._plosive_cutoff_freq, btype='high', fs=track.audio_buffer.fs
        )
        for plosive in plosive_regions:
            track.audio_buffer.x[plosive[0]:plosive[1]] = filtfilt(
                b, a, track.audio_buffer.x[plosive[0]:plosive[1]]
            )
            track.audio_buffer.x[plosive[0]:plosive[1]] *= np.power(10, self._db_attenuation/20.)
