from silence_detector import SilenceDetector


class Track(object):
    """
    Data structure containing data and metadata for each track
    """

    def __init__(self, audio, master=False):
        self.audio_buffer = audio
        self.master = master

    @property
    def silence_ranges(self):
        # TODO: make min_silence_len_s parameterable, maybe to match config param min_silence_duration?
        return SilenceDetector(threshold=0.3, min_silence_len_s=0.5).detect_silences(self.audio_buffer)

    @property
    def activity_ranges(self):
        silence_ranges = self.silence_ranges
        return self.get_activity_ranges_from_silence_ranges(silence_ranges)

    def get_activity_ranges_from_silence_ranges(self, silence_ranges):
        if silence_ranges is None or len(silence_ranges) == 0:
            return [(0., self.audio_buffer.get_duration_s())]
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

    def apply_silence_to_interval(self, interval, fade_in_s=0.025, fade_out_s=0.025):
        """
        Silence out an interval of the track

        Args:
            interval: (tuple), (interval_start_s, interval_end_s)
            fade_in_s (float): fade in time
            fade_out_s (float): fade out time
        """
        self.audio_buffer.apply_silence_to_interval(interval, fade_in_s, fade_out_s)

    def snip(self, interval, fade_in_s=0.025, fade_out_s=0.025):
        """
        Snip out a segment of audio
        Args:
            interval: (tuple), (interval_start_s, interval_end_s)
            fade_in_s (float): fade in time
            fade_out_s (float): fade out time
        """
        self.audio_buffer.snip(interval, fade_in_s, fade_out_s)

    def slice(self, interval):
        """
        Slice out a segment of audio
        Args:
            interval: (tuple), (interval_start_s, interval_end_s)
        """
        self.audio_buffer.slice(interval)

    def apply_volume_automation(self, automation):
        self.audio_buffer.apply_volume_automation(automation)
