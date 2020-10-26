from utils import s_to_timestamp


class SpeakerTrackRecipe(object):
    DEFAULT_FX = [
        {
            "effect": "contrast",
            "parameters": {
                "amount": 80
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
        self.fX = kwargs.get("fX", [])

    def to_json(self):
        recipe_data = {
            "silence_timestamps": self.silence_timestamps,
            "master": self.master,
            "path": self.path,
            "fX": self.fX
        }
        if self.offset:
            recipe_data["offset"] = s_to_timestamp(self.offset) if isinstance(self.offset, float) else self.offset
        if self.gate_filter:
            recipe_data["gate_filter"] = self.gate_filter
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
        if len(new_recipe.fX):
            self.fX.extend(new_recipe.fX)
