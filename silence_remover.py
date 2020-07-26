class SilenceRemover(object):

    def __init__(self, min_silence_duration=0.75):
        self.min_silence_duration = min_silence_duration

    def remove(self, track, silence_ranges=None, padding_s=0.1):
        """
        Args:
            track: (Track)
            silence_ranges: (list of tuple intervals)
            padding_s: (float) amount of silent padding to leave in (seconds)
        """
        if silence_ranges is None:
            silence_ranges = track.silence_ranges
        for silent_range in reversed(silence_ranges):
            silence_duration = silent_range[1] - silent_range[0]
            if silence_duration > self.min_silence_duration:
                # pad the snipped audio a bit
                padded_silent_range = [
                    min(silent_range[0]+padding_s, silent_range[1]),
                    max(silent_range[1]-padding_s, silent_range[0])
                ]
                track.snip(padded_silent_range)
