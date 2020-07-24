class SpeakerTrack(object):
    """
    Data structure containing data and metadata for each speaker track
    """

    def __init__(self, audio=None, silence_ranges=None):
        self.audio = audio
        self.__activity_ranges = []
        self.silence_ranges = silence_ranges

    @property
    def silence_ranges(self):
        return self.__silence_ranges

    @silence_ranges.setter
    def silence_ranges(self, silence_ranges):
        self.__silence_ranges = silence_ranges

        # calculate activity ranges
        if len(self.silence_ranges) == 0:
            self.__activity_ranges = [0., self.audio.get_duration_s()]
        self.__activity_ranges = []
        time_cursor = 0.
        for silence in self.silence_ranges:
            if time_cursor < silence[0]:
                self.__activity_ranges.append((time_cursor, silence[0]))
            time_cursor = silence[1]
        # End of track
        if time_cursor < self.audio.get_duration_s():
            self.__activity_ranges.append((time_cursor, self.audio.get_duration_s()))

    @property
    def activity_ranges(self):
        return self.__activity_ranges

    def apply_offset(self, offset_s):
        self.audio.apply_offset(offset_s)
        new_silence_ranges = []
        for silent_range in self.__silence_ranges:
            new_silent_range_start = silent_range[0] + offset_s
            new_silent_range_end = silent_range[1] + offset_s
            if new_silent_range_end <= 0:
                continue
            new_silence_ranges.append((max(new_silent_range_start, 0), new_silent_range_end))
        self.silence_ranges = new_silence_ranges
