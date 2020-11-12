import os

from utils import time_interval_to_s, time_interval_to_timestamp, time_to_timestamp, time_to_s


class SpeakerTrackRecipe(object):
    DEFAULT_FX = [
        {
            "effect": "contrast",
            "parameters": {
                "amount": 33
            }
        },
        {
            "effect": "equalizer",
            "parameters": {
                "frequency": 100,
                "width_q": 1,
                "gain_db": 0
            }
        },
        {
            "effect": "equalizer",
            "parameters": {
                "frequency": 296.1,
                "width_q": 1,
                "gain_db": -1.6
            }
        },
        {
            "effect": "equalizer",
            "parameters": {
                "frequency": 3511,
                "width_q": 1,
                "gain_db": 1.8
            }
        },
        {
            "effect": "equalizer",
            "parameters": {
                "frequency": 10000,
                "width_q": 1,
                "gain_db": 2.2
            }
        }
    ]

    def __init__(self, **kwargs):
        self.silence_timestamps = kwargs.get("silence_timestamps", [])
        self.master = kwargs.get("master", False)
        self.path = kwargs.get("path")
        self.offset = kwargs.get("offset")
        self.gate_filter = kwargs.get("gate_filter")
        self.deplosive_filter = kwargs.get("deplosive_filter")
        self.noise_reducer = kwargs.get("noise_reducer")
        self.fX = kwargs.get("fX", [])

    def to_json(self, str_timestamps=False):
        formatted_silence_timestamps = [
            time_interval_to_timestamp(sinterval) for sinterval in self.silence_timestamps
        ] if str_timestamps else [
            time_interval_to_s(sinterval) for sinterval in self.silence_timestamps
        ]

        recipe_data = {
            "silence_timestamps": formatted_silence_timestamps,
            "master": self.master,
            "path": self.path,
            "filename": os.path.split(self.path)[-1],
            "fX": self.fX
        }
        if self.offset:
            recipe_data["offset"] = time_to_timestamp(self.offset) if str_timestamps else time_to_s(self.offset)
        if self.gate_filter:
            recipe_data["gate_filter"] = self.gate_filter
        if self.deplosive_filter:
            recipe_data["deplosive_filter"] = self.deplosive_filter
        if self.noise_reducer:
            recipe_data["noise_reducer"] = self.noise_reducer
        return recipe_data

    def update(self, new_recipe):
        if len(new_recipe.silence_timestamps):
            self.silence_timestamps.extend(new_recipe.silence_timestamps)
        new_recipe.master = new_recipe
        if new_recipe.path:
            self.path = new_recipe.path
        if new_recipe.offset:
            self.offset = new_recipe.offset
        if new_recipe.gate_filter:
            self.gate_filter = new_recipe.gate_filter
        if new_recipe.deplosive_filter:
            self.deplosive_filter = new_recipe.deplosive_filter
        if new_recipe.noise_reducer:
            self.noise_reducer = new_recipe.noise_reducer
        if len(new_recipe.fX):
            self.fX.extend(new_recipe.fX)

    def set_silence_timestamps(self, silence_timestamps):
        self.silence_timestamps = silence_timestamps

