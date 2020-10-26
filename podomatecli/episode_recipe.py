import json
import os

from mixed_track_recipe import MixedTrackRecipe
from speaker_track_recipe import SpeakerTrackRecipe


class EpisodeRecipe(object):
    """
    Recipe of input, transformations, & settings to create an output episode
    """

    def __init__(self):
        self.speaker_track_recipes = []
        self.mixed_track_recipe = MixedTrackRecipe()

    @staticmethod
    def from_file(path):
        if not os.path.isfile(path):
            raise IOError("Can't find recipe file to load")

        recipe = EpisodeRecipe()

        # read config JSON file
        with open(path, 'r') as f_json:
            recipe_data = json.load(f_json)

            # read speaker track recipes
            for speaker_track_recipe_data in recipe_data["local_tracks"]:
                recipe.speaker_track_recipes.append(SpeakerTrackRecipe(**speaker_track_recipe_data))

            # read mixed track recipe
            recipe.mixed_track_recipe = MixedTrackRecipe(**recipe_data["global_track"])

        return recipe

    def to_file(self, path):
        recipe_data = {
            "local_tracks": [trecipe.to_json() for trecipe in self.speaker_track_recipes],
            "global_track": self.mixed_track_recipe.to_json()
        }
        with open(path, 'w') as fp:
            json.dump(recipe_data, fp, indent=4, sort_keys=True)

    def add_speaker_track(self, recipe):
        self.speaker_track_recipes.append(recipe)

    def update_speaker_track(self, i_speaker, recipe, clobber=False):
        if 0 <= i_speaker < len(self.speaker_track_recipes):
            if clobber:
                self.speaker_track_recipes[i_speaker] = recipe
            else:
                self.speaker_track_recipes[i_speaker].update(recipe)

    def del_speaker_track(self, i_speaker):
        if 0 <= i_speaker < len(self.speaker_track_recipes):
            del self.speaker_track_recipes[i_speaker]

    def __str__(self):
        return json.dumps({
                "local_tracks": [trecipe.to_json() for trecipe in self.speaker_track_recipes],
                "global_track": self.mixed_track_recipe.to_json()
            }, indent=4, sort_keys=True
        )
