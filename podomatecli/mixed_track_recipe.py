class MixedTrackRecipe(object):

    def __init__(self, **kwargs):
        self.min_silence_duration = kwargs.get("min_silence_duration", 1.0)
        self.silence_timestamps = kwargs.get("silence_timestamps", [])
        self.live_timestamps = kwargs.get("live_timestamps", [])
        self.fX = kwargs.get("fX", [])
        self.inserts = kwargs.get("inserts", [])
        self.overlays = kwargs.get("overlays", [])

    def to_json(self):
        return {
            "min_silence_duration": self.min_silence_duration,
            "silence_timestamps": self.silence_timestamps,
            "live_timestamps": self.live_timestamps,
            "fX": self.fX,
            "inserts": self.inserts,
            "overlays": self.overlays
        }

    def remove_overlays_with_tag(self, tag):
        for i_overlay in range(len(self.overlays)-1,-1,-1):
            if self.overlays[i_overlay]["tag"] == tag:
                del self.overlays[i_overlay]
