from silence_detector import SilenceDetector


class Track(object):
    """
    Data structure containing data and metadata for each track
    """

    def __init__(self, audio):
        self.audio_buffer = audio

    @property
    def silence_ranges(self):
        return SilenceDetector(threshold=0.35, min_silence_len_s=0.3).detect_silences(self.audio_buffer)

    @property
    def activity_ranges(self):
        silence_ranges = self.silence_ranges
        if silence_ranges is None or len(silence_ranges) == 0:
            return [0., self.audio_buffer.get_duration_s()]
        else:
            activity_ranges = []
            time_cursor = 0.
            for silence in silence_ranges:
                if time_cursor < silence[0]:
                    activity_ranges.append((time_cursor, silence[0]))
                time_cursor = silence[1]
            # End of track
            if time_cursor < self.audio_buffer.get_duration_s():
                activity_ranges.append((time_cursor, self.audio_buffer.get_duration_s()))
            return activity_ranges

    def apply_offset(self, offset_s):
        self.audio_buffer.apply_offset(offset_s)

    def apply_silence_to_interval(self, interval):
        """
        Silence out an interval of the track

        Args:
            interval: (tuple), (interval_start_s, interval_end_s)
        """
        self.audio_buffer.apply_silence_to_interval(interval)
