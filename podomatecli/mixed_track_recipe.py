from audio_inserter import AudioInserter
from audio_overlayer import AudioOverlayer
from utils import time_interval_to_timestamp, time_interval_to_s


class MixedTrackRecipe(object):

    def __init__(self, **kwargs):
        self.min_silence_duration = kwargs.get("min_silence_duration", 1.0)
        self.silence_timestamps = kwargs.get("silence_timestamps", [])
        self.live_timestamps = kwargs.get("live_timestamps", [])
        self.fX = kwargs.get("fX", [])
        self.inserts = kwargs.get("inserts", [])
        self.overlays = kwargs.get("overlays", [])

    def clear(self):
        self.silence_timestamps = []
        self.live_timestamps = []
        self.fX = []
        self.inserts = []
        self.overlays = []

    def clear_inserts(self):
        self.inserts = []

    def clear_overlays(self):
        self.overlays = []

    def to_json(self, str_timestamps=False):
        formatted_silence_timestamps = [
            time_interval_to_timestamp(sinterval) for sinterval in self.silence_timestamps
        ] if str_timestamps else [
            time_interval_to_s(sinterval) for sinterval in self.silence_timestamps
        ]
        formatted_live_timestamps = [
            time_interval_to_timestamp(linterval) for linterval in self.live_timestamps
        ] if str_timestamps else [
            time_interval_to_s(linterval) for linterval in self.live_timestamps
        ]

        return {
            "min_silence_duration": self.min_silence_duration,
            "silence_timestamps": formatted_silence_timestamps,
            "live_timestamps": formatted_live_timestamps,
            "fX": self.fX,
            "inserts": [AudioInserter.from_config(insert).to_json(str_timestamps) for insert in self.inserts],
            "overlays": [AudioOverlayer.from_config(overlay).to_json(str_timestamps) for overlay in self.overlays]
        }

    def add_overlay(self, overlay, allow_duplicate_tags=False):
        """
        Args:
            overlay: overlay recipe
            allow_duplicate_tags: if False, replace any overlay recipe matching tag with the overlay
        """
        if not allow_duplicate_tags:
            self.remove_overlays_with_tag(overlay["tag"])
        self.overlays.append(overlay)

    def remove_overlays_with_tag(self, tag):
        for i_overlay in range(len(self.overlays)-1,-1,-1):
            if self.overlays[i_overlay]["tag"] == tag:
                del self.overlays[i_overlay]

    def processing_steps(self):
        """
        Returns: int number of operations to be run on the track
        """

        operations = [
            self.silence_timestamps or self.live_timestamps, self.inserts, self.overlays, self.fX
        ]
        num_steps = sum([((isinstance(o, list) and len(o) > 0) or o is not None) for o in operations])
        return num_steps
