from responsive_timeline import ResponsiveTimeline
from silence_detector import SilenceDetector
from utils import read_config_interval


class Track(object):
    """
    Data structure containing data and metadata for each track
    """

    def __init__(self, audio, master=False):
        self.audio_buffer = audio
        self.master = master
        self.timeline = ResponsiveTimeline()
        self.silence_range_cache = None         # could be out of date
        self.activity_range_cache = None        # could be out of date

    @property
    def silence_ranges(self):
        # TODO: make min_silence_len_s parameterable, maybe to match config param min_silence_duration?
        self.silence_range_cache = SilenceDetector(threshold=0.3, min_silence_len_s=0.5).detect_silences(self.audio_buffer)
        self.activity_range_cache = self.get_activity_ranges_from_silence_ranges(self.silence_range_cache)
        return self.silence_range_cache

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
                silence = read_config_interval(silence)
                if time_cursor < silence[0]:
                    activity_ranges.append((time_cursor, silence[0]))
                time_cursor = silence[1]
            # End of track
            if time_cursor < self.audio_buffer.get_duration_s():
                activity_ranges.append((time_cursor, self.audio_buffer.get_duration_s()))
            return activity_ranges

    def get_silence_ranges_from_activity_ranges(self, activity_ranges):
        return self.get_activity_ranges_from_silence_ranges(activity_ranges)

    def apply_offset(self, offset_s):
        self.audio_buffer.apply_offset(offset_s)
        self.timeline.perform_edit(0., offset_s)

    def apply_silence_to_interval(self, interval, fade_in_s=0.025, fade_out_s=0.025):
        """
        Silence out an interval of the track

        Args:
            interval: (tuple), (interval_start_s, interval_end_s)
            fade_in_s (float): fade in time
            fade_out_s (float): fade out time
        """
        transformed_interval = self.timeline.transform_interval(interval)
        self.audio_buffer.apply_silence_to_interval(transformed_interval, fade_in_s, fade_out_s)

    def insert(self, audio_buffer, timestamp):
        """
        Insert an audio buffer at a given timestamp
        Args:
            audio_buffer (AudioBuffer): the buffer to insert
            timestamp: timestamp to insert into track
        """
        self.audio_buffer.insert(audio_buffer, self.timeline.transform_timestamp(timestamp))
        self.timeline.perform_edit(timestamp, audio_buffer.get_duration_s())

    def snip(self, interval, absolute=False, fade_in_s=0.025, fade_out_s=0.025):
        """
        Snip out a segment of audio
        Args:
            interval: (tuple), (interval_start_s, interval_end_s)
            absolute (boolean): whether timestamps are absolute or should be transformed according to previous track edits
            fade_in_s (float): fade in time
            fade_out_s (float): fade out time
        """

        snip_duration_s = interval[1] - interval[0]
        if absolute:
            self.audio_buffer.snip(interval, fade_in_s, fade_out_s)
            untransformed_interval = self.timeline.untransform_interval(interval)
            self.timeline.perform_edit(untransformed_interval[0], -snip_duration_s)    # should be -ve because removing audio
        else:
            self.audio_buffer.snip(self.timeline.transform_interval(interval), fade_in_s, fade_out_s)
            self.timeline.perform_edit(interval[0], -snip_duration_s)    # should be -ve because removing audio

    def slice(self, interval):
        """
        Slice out a segment of audio
        Args:
            interval: (tuple), (interval_start_s, interval_end_s)
        """
        self.audio_buffer.slice(self.timeline.transform_interval(interval))
        self.timeline.perform_edit(0, -interval[0])   # should be -ve because removing audio

    def apply_gain(self, interval, dB):
        """
        Apply gain to a segment of the audio buffer
        Args:
            interval: (tuple), (interval_start_s, interval_end_s)
            dB (float): decibel gain
        """
        transformed_interval = self.timeline.transform_interval(interval)
        self.audio_buffer.apply_gain(transformed_interval, dB)

    def apply_volume_automation(self, automation):
        # transform timestamps
        for va in automation:
            va["timestamp"] = self.timeline.transform_timestamp(va["timestamp"])
        self.audio_buffer.apply_volume_automation(automation)
