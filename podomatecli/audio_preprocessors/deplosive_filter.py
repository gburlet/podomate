import librosa
import numpy as np
from scipy.signal import butter, filtfilt

from utils import time_to_timestamp


class DeplosiveFilter(object):
    """
    Locates, filters and attenuates plosive sounds in a track
    Locate: tag plosives with low zero-crossing rate and of considerable volumes
    Filter: high-pass filter the located plosive regions
    Attenuate: reduce the dB of the plosive regions
    """

    def __init__(self, window_size=1024, hop_size=1024, order=5, cutoff=225, db_attenuation=-3.5, zero_cross_threshold=0.2, rms_threshold=1.5, min_plosive_length_s=0.03, max_plosive_length_s=0.2):
        """
        Parameters
        ----------
        window_size (int): analysis window size in samples
        hop_size (int): hop size in samples
        order (int): filter order
        cutoff (int): high-pass filter cut-off frequency
        db_attenuation (float): dB plosive attenuation after high-pass filtering
        zero_cross_threshold (float): proportion of track's mean 0x to tag plosives
        rms_threshold (float): proportion of track's mean rms to tag plosives
        min_plosive_length_s (float): any region tagged as a plosive shorter than this, skip it
        max_plosive_length_s (float): any region tagged as a plosive longer than this, skip it, prob not a plosive
        """

        self._window_size = window_size
        self._hop_size = hop_size
        self._order = order
        self._cutoff = cutoff
        self._db_attenuation = db_attenuation
        self._zero_cross_threshold = zero_cross_threshold
        self._rms_threshold = rms_threshold
        self._min_plosive_length_s = min_plosive_length_s
        self._max_plosive_length_s = max_plosive_length_s

    def process(self, track):
        """
        Parameters
        ----------
        track (Track): track to remove plosives from

        Algorithm
        - what we're looking for: low zero-crossing and relatively high volume
        ---------
        1. Remove any DC offset
        2. Get sample of 0x speaker activities
        3. Get sample of RMS noise floor
        4. Tag plosives in frames where 0x < 0.5*0x_activity, RMS > 2*RMS_noisefloor
        5. Apply 150Hz cut-off freq high-pass filter to plosive regions

        Note: modifies track AudioBuffer in place!
        """

        """
        # 1. Remove any DC offset
        dc_offset = np.mean(track.audio_buffer.x)
        if abs(dc_offset) > 0.001:
            track.audio_buffer.x += dc_offset
        """

        # low-pass filter to smooth
        # TODO: downsample for analysis
        b, a = butter(5, 800, btype='low', fs=track.audio_buffer.fs)
        x_smoothed = filtfilt(b, a, track.audio_buffer.x)

        # remove any DC offset from low-pass smoothed signal
        dc_offset = np.mean(x_smoothed)
        if abs(dc_offset) > 0.001:
            x_smoothed += dc_offset

        # sample noisefloor RMS
        """
        silent_regions = track.silence_range_cache if track.silence_range_cache else track.silence_ranges
        mean_rms = 0.04
        if len(silent_regions):
            mean_rms = 0.
            for silent_region in silent_regions:
                silent_sample_start = track.audio_buffer.get_sample_from_timestamp(silent_region[0])
                silent_sample_end = track.audio_buffer.get_sample_from_timestamp(silent_region[1])
                region_rms = np.mean(
                    librosa.feature.rms(
                        x_smoothed[silent_sample_start:silent_sample_end],
                        frame_length=self._window_size, hop_length=self._hop_size, center=False
                    )
                )
                mean_rms += region_rms
            mean_rms /= float(len(silent_regions))
        """

        frame_rms = librosa.feature.rms(x_smoothed, frame_length=self._window_size, hop_length=self._hop_size, center=False)
        vad_rms_threshold = np.percentile(frame_rms, 30)
        punchy_rms_threshold = np.percentile(frame_rms, 85)
        #noisefloor_rms = np.mean(frame_rms[frame_rms < vad_rms_threshold])
        print("vad rms thresh: %0.3f" % vad_rms_threshold)
        print("punchy rms thresh: %0.3f" % punchy_rms_threshold)
        zero_x_rate = librosa.feature.zero_crossing_rate(x_smoothed, frame_length=self._window_size, hop_length=self._hop_size, center=False)
        plosive_0x_threshold = np.percentile(zero_x_rate[frame_rms > vad_rms_threshold], 30)
        print("plosive 0x threshold: %0.3f" % plosive_0x_threshold)
        vad_0x_threshold = np.percentile(zero_x_rate[frame_rms > vad_rms_threshold], 70)
        mean_0x_rate = np.mean(zero_x_rate[zero_x_rate > vad_0x_threshold])
        print("mean active 0x rate: %0.3f" % mean_0x_rate)

        """
        # 2. Sample zero crossing profile
        # mean_zero_crossings = int(np.sum(librosa.zero_crossings(track.audio_buffer.x))) / float(len(track.audio_buffer.x)/self._window_size)
        activity_ranges = track.activity_range_cache if track.activity_range_cache else track.activity_ranges
        print("activity ranges: ", activity_ranges)
        mean_zero_crossings = 30 * self._window_size / 1024.  # default value set by looking at some tracks
        mean_zero_crossing_rate = 0.02
        if len(activity_ranges):
            mean_zero_crossings = 0.
            mean_zero_crossing_rate = 0.
            for activity_range in activity_ranges:
                activity_sample_start = track.audio_buffer.get_sample_from_timestamp(activity_range[0])
                activity_sample_end = track.audio_buffer.get_sample_from_timestamp(activity_range[1])
                activity_num_samples = activity_sample_end - activity_sample_start
                region_zero_crossings = int(
                    np.sum(librosa.zero_crossings(x_smoothed[activity_sample_start:activity_sample_end])))
                mean_zero_crossings += (region_zero_crossings / (activity_num_samples / float(self._window_size)))
                mean_zero_crossing_rate += region_zero_crossings / float(activity_num_samples)
            mean_zero_crossings /= float(len(activity_ranges))
            mean_zero_crossing_rate /= float(len(activity_ranges))

        # mean_zero_crossings = 15 * self._window_size/512.
        # mean_zero_crossings = 15. / self._zero_cross_threshold
        print("mean 0x: %0.3f" % mean_zero_crossings)
        print("mean 0x rate: %0.3f" % mean_zero_crossing_rate)
        """

        # 3. Sample RMS profile
        # mean_rms = np.mean(librosa.feature.rms(track.audio_buffer.x))
        """
        silent_regions = track.silence_range_cache if track.silence_range_cache else track.silence_ranges
        mean_rms = 0.04
        if len(silent_regions):
            mean_rms = 0.
            for silent_region in silent_regions:
                silent_sample_start = track.audio_buffer.get_sample_from_timestamp(silent_region[0])
                silent_sample_end = track.audio_buffer.get_sample_from_timestamp(silent_region[1])
                region_rms = np.mean(
                    librosa.feature.rms(
                        x_smoothed[silent_sample_start:silent_sample_end],
                        frame_length=self._window_size, hop_length=self._hop_size, center=False
                    )
                )
                mean_rms += region_rms
            mean_rms /= float(len(silent_regions))
        """
        #mean_rms = 0.04
        #print("mean rms noisefloor: %0.3f" % mean_rms)

        # tag plosive frames
        frames = librosa.util.frame(
            x_smoothed, frame_length=self._window_size, hop_length=self._hop_size
        )
        num_frames = np.shape(frames)[1]
        is_plosive = np.zeros(num_frames, dtype=np.bool)
        prev_0x_rate = 0.
        for i_frame in range(num_frames):
            zero_crossings = int(np.sum(librosa.zero_crossings(frames[:, i_frame])))
            zero_crossing_rate = zero_crossings / float(np.shape(frames[:, i_frame])[0])
            prev_frames_rms_mean = float(np.mean(
                np.sqrt(np.mean(np.abs(frames[:, max(0,i_frame-5):i_frame]) ** 2, axis=0, keepdims=True)), axis=1
            )) if i_frame > 0 else 0.04
            #print("prev_frames_rms_mean: %0.3f" % prev_frames_rms_mean)
            rms = float(librosa.feature.rms(frames[:, i_frame], frame_length=self._window_size, hop_length=self._hop_size, center=False))
            # debug
            print("Frame: @[%s - %s]: 0x: %d; 0xrate: %0.3f; rms: %0.3f; ma_rms: %0.3f" % (
                time_to_timestamp((i_frame * self._hop_size) / float(track.audio_buffer.fs)),
                time_to_timestamp(((i_frame * self._hop_size) + self._window_size) / float(track.audio_buffer.fs)),
                zero_crossings, zero_crossing_rate, rms, prev_frames_rms_mean
            ))

            if (rms-prev_frames_rms_mean)/prev_frames_rms_mean > 1.0:
                print("BIG BURST")

            # plosive detected
            #is_plosive[i_frame] = zero_crossings <= self._zero_cross_threshold*mean_zero_crossings and rms > self._rms_threshold*mean_rms
            #is_plosive[i_frame] = zero_crossing_rate <= plosive_0x_threshold and rms > punchy_rms_threshold
            prev_is_plosive = is_plosive[i_frame-1] if i_frame-1 >= 0 else False

            rms_percent_diff = (rms-prev_frames_rms_mean)/prev_frames_rms_mean
            is_plosive[i_frame] = zero_crossing_rate <= plosive_0x_threshold and ((rms > punchy_rms_threshold and rms_percent_diff > 1.0) or (rms > 1.75*punchy_rms_threshold and rms_percent_diff > 0.))
            # if is_plosive[i_frame] and not prev_is_plosive:
            #     is_plosive[i_frame] = (zero_crossing_rate-prev_0x_rate)/prev_0x_rate < 0.
            if is_plosive[i_frame]:
                print("\tplosive detected")

            prev_0x_rate = zero_crossing_rate

        # flood fill plosive gaps [Yes, No, Yes] -> [Yes, Yes, Yes]
        for i_frame in range(1, num_frames-1):
            if is_plosive[i_frame-1] and is_plosive[i_frame+1]:
                is_plosive[i_frame] = True

        # convert plosive tags to regions at nearest 0xings (list of sample indices)
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

        # debug
        print("Detected Plosives before 0x snapping:")
        for plosive in plosive_regions:
            print("\t[%s - %s]" % (
                time_to_timestamp(track.audio_buffer.get_timestamp_from_sample(plosive[0])),
                time_to_timestamp(track.audio_buffer.get_timestamp_from_sample(plosive[1]))
            )
        )

        # convert end points of plosive regions to 0xings
        plosive_regions = [
            [
                track.audio_buffer.get_previous_zero_crossing(pr[0], zero_tol=1e-2, sign_change=False),
                track.audio_buffer.get_next_zero_crossing(pr[1], zero_tol=1e-2, sign_change=False),
            ] for pr in plosive_regions
        ]

        # merge any overlapped regions
        for i_plosive in range(len(plosive_regions)-1,0,-1):
            if plosive_regions[i_plosive][0] < plosive_regions[i_plosive-1][1]:
                plosive_regions[i_plosive-1][1] = plosive_regions[i_plosive][1]
                del plosive_regions[i_plosive]

        # debug
        print("Detected Plosives:")
        for plosive in plosive_regions:
            print("\t[%s - %s]" % (
                    time_to_timestamp(track.audio_buffer.get_timestamp_from_sample(plosive[0])),
                    time_to_timestamp(track.audio_buffer.get_timestamp_from_sample(plosive[1]))
                )
            )

        # perform filter: 5 order, 200Hz high-pass filter
        b, a = butter(self._order, self._cutoff, btype='high', fs=track.audio_buffer.fs)
        for plosive in plosive_regions:
            track.audio_buffer.x[plosive[0]:plosive[1]] = filtfilt(
                b, a, track.audio_buffer.x[plosive[0]:plosive[1]]
            )
            track.audio_buffer.x[plosive[0]:plosive[1]] *= np.power(10, self._db_attenuation/20.)
        #track.audio_buffer.x = x_smoothed


if __name__ == "__main__":
    from track import Track

    # plosives @: 1.856, 2.409, 6.258, 11.029, 15.325, 19.656, 21.233, 22.808, 25.247, 27.526
    # audio_path = "/Users/gburlet/Podomate/plosives_example3.mp3"
    # track = Track.from_audio_file(audio_path, master=True)
    # track.audio_buffer.normalize()
    # w = 1536
    # h = 512
    #
    # df = DeplosiveFilter(w, h)
    # df.process(track)
    #
    # audio_out_path = "/Users/gburlet/Podomate/plosives_example3_clean.flac"
    # track.audio_buffer._path = audio_out_path
    # track.audio_buffer.write(normalize=False)

    for i in range(1,7):
        audio_path = "/Users/gburlet/Podomate/plosives_example%d.mp3" % i
        print("\n\n\n", audio_path)
        track = Track.from_audio_file(audio_path, master=True)
        track.audio_buffer.normalize()
        w = 1536
        h = 512

        df = DeplosiveFilter(w, h)
        df.process(track)

        audio_out_path = "/Users/gburlet/Podomate/plosives_example%d_clean.flac" % i
        track.audio_buffer._path = audio_out_path
        track.audio_buffer.write(normalize=False)
