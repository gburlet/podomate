import os
import numpy as np

from audio_inserter import AudioInserter
from audio_overlayer import AudioOverlayer
from audio_preprocessors.gate_filter import GateFilter
from audio_preprocessors.noise_reducer_factory import NoiseReducerFactory
from episode_recipe import EpisodeRecipe
from fx_chain import FXChain
from mixer import Mixer
from silence_remover import SilenceRemover
from speaker_track_recipe import SpeakerTrackRecipe
from track import Track
from track_aligner import TrackAligner


class Episode(object):
    """
    Metadata and Data for an episode
    """

    def __init__(self, recipe=None):
        if recipe is None:
            recipe = EpisodeRecipe()
        self.recipe = recipe

        # internal data structures
        self.speaker_tracks = []
        self.mixed_track = None

    @staticmethod
    def from_recipe_file(path):
        episode = Episode(recipe=EpisodeRecipe.from_file(path))

        # load speaker tracks
        for speaker_track_recipe in episode.recipe.speaker_track_recipes:
            if speaker_track_recipe.path:
                if not os.path.isfile(speaker_track_recipe.path):
                    raise IOError("Can't find audio file for speaker track")
                episode.speaker_tracks.append(
                    Track.from_audio_file(speaker_track_recipe.path, master=speaker_track_recipe.master)
                )

        return episode

    def reset(self):
        self.recipe = EpisodeRecipe()
        self.speaker_tracks.clear()
        self.mixed_track = None

    def add_speaker_track(self, track, recipe=None):
        self.speaker_tracks.append(track)
        if recipe is None:
            recipe = SpeakerTrackRecipe(path=track.audio_buffer._path, master=track.master)
        self.recipe.add_speaker_track(recipe)

    def update_speaker_track(self, i_speaker, track, recipe=None):
        if 0 <= i_speaker < len(self.speaker_tracks):
            self.speaker_tracks[i_speaker] = track
            if recipe is None:
                recipe = SpeakerTrackRecipe(path=track.audio_buffer._path, master=track.master)
            self.recipe.update_speaker_track(i_speaker, recipe)

    def del_speaker_track(self, i_speaker):
        if 0 <= i_speaker < len(self.speaker_tracks):
            del self.speaker_tracks[i_speaker]
            self.recipe.del_speaker_track(i_speaker)

    def set_master_speaker_track(self, i_speaker):
        if 0 <= i_speaker < len(self.speaker_tracks):
            self.speaker_tracks[i_speaker].master = True
            self.recipe.speaker_track_recipes[i_speaker].master = True

    def mix_speaker_tracks(self):
        # set master track if it has not already been set
        if not any([t.master for t in self.speaker_tracks]):
            i_master_track = np.argmax([t.audio_buffer.get_duration_s() for t in self.speaker_tracks])
            self.set_master_speaker_track(i_master_track)

        # auto calculate track alignment (offsets) for non master tracks
        track_aligner = TrackAligner(track_offsets=[trecipe.offset for trecipe in self.recipe.speaker_track_recipes])
        track_offsets = track_aligner.auto_calc_offset(self.speaker_tracks)

        for i_track in range(len(self.speaker_tracks)):
            # apply noise reducer
            noise_reducer = self.recipe.speaker_track_recipes[i_track].noise_reducer
            if noise_reducer:
                NoiseReducerFactory.construct_noise_reducer(
                    noise_reducer["id"], noise_reducer.get("params", {})
                ).auto_reduce_noise(self.speaker_tracks[i_track])

            # apply gate filter
            gate_filter_db = self.recipe.speaker_track_recipes[i_track].gate_filter
            if gate_filter_db:
                GateFilter(gate_filter_db).process(self.speaker_tracks[i_track])

            # silence timestamps
            silence_timestamps = self.recipe.speaker_track_recipes[i_track].silence_timestamps
            for silence_interval in silence_timestamps:
                self.speaker_tracks[i_track].apply_silence_to_interval(silence_interval)

        # perform alignment
        track_aligner.align(self.speaker_tracks, track_offsets).pad(self.speaker_tracks)

        # apply fX chain
        for i_track in range(len(self.speaker_tracks)):
            fX_chain = self.recipe.speaker_track_recipes[i_track].fX
            if len(fX_chain):
                FXChain(fX_chain).apply(self.speaker_tracks[i_track])
                self.speaker_tracks[i_track].audio_buffer.normalize()

        # mix global track
        self.mixed_track = Mixer().mix_tracks(self.speaker_tracks)
        self.mixed_track.audio_buffer.normalize()
        _ = self.mixed_track.silence_ranges  # cache VAD for future operations

    def add_intro_overlay(self, filename, slice, overlay_sync_point):
        if self.mixed_track.activity_range_cache is None or len(self.mixed_track.activity_range_cache) == 0:
            raise ValueError("We ran into an issue applying the intro backtrack. Is your mixed track of speakers silent?")

        # find first voice timestamp
        first_voice_timestamp = None
        for lt in self.recipe.mixed_track_recipe.live_timestamps:
            for va in self.mixed_track.activity_range_cache:
                if va[0] <= lt[0] <= va[1]:
                    first_voice_timestamp = lt[0]
                    break
                elif lt[0] <= va[0] <= lt[1]:
                    first_voice_timestamp = va[0]
                    break
                elif va[0] > lt[1]:
                    # search optimization
                    break
            if first_voice_timestamp is not None:
                break

        if first_voice_timestamp is None:
            raise ValueError("We ran into an issue applying the intro backtrack. Are your selected live segments silent?")

        duration_until_sync_point_s = overlay_sync_point - slice[0]
        backtrack_duration_s = slice[1] - slice[0]
        if not 0 < duration_until_sync_point_s < backtrack_duration_s:
            raise ValueError("We ran into an issue applying the intro backtrack. The talking start point should be within the segment of selected music.")

        overlay_config = AudioOverlayer.automated_intro(
            filename, slice, overlay_sync_point, first_voice_timestamp
        ).to_json(str_timestamps=False)

        self.recipe.mixed_track_recipe.add_overlay(overlay_config, allow_duplicate_tags=False)

    def add_outro_overlay(self, filename, slice, overlay_sync_point):
        if self.mixed_track.activity_range_cache is None or len(self.mixed_track.activity_range_cache) == 0:
            raise ValueError("We ran into an issue applying the outro backtrack. Is your mixed track of speakers silent?")

        # find last voice timestamp
        last_voice_timestamp = None
        for lt in self.recipe.mixed_track_recipe.live_timestamps:
            for va in self.mixed_track.activity_range_cache:
                if va[0] <= lt[0] <= va[1] or lt[0] <= va[0] <= lt[1]:
                    last_voice_timestamp = va[1] if va[1] < lt[1] else lt[1]
                    break
                elif va[0] > lt[1]:
                    # search optimization
                    break
            if last_voice_timestamp is not None:
                break

        if last_voice_timestamp is None:
            raise ValueError("We ran into an issue applying the intro backtrack. Are your selected live segments silent?")

        last_voice_timestamp = self.mixed_track.activity_range_cache[-1][1]
        duration_until_sync_point_s = overlay_sync_point - slice[0]
        backtrack_duration_s = slice[1] - slice[0]
        if not 0 < duration_until_sync_point_s < backtrack_duration_s:
            raise ValueError("We ran into an issue applying the outro backtrack. The talking end point should be within the segment of selected music.")

        overlay_config = AudioOverlayer.automated_outro(
            filename, slice, overlay_sync_point, last_voice_timestamp
        ).to_json(str_timestamps=False)
        self.recipe.mixed_track_recipe.add_overlay(overlay_config, allow_duplicate_tags=False)

    def add_insert(self, filename, slice, timestamp):
        self.recipe.mixed_track_recipe.inserts.append(
            AudioInserter(filename, slice, timestamp).to_json(str_timestamps=False)
        )

    def update_insert(self, i_insert, filename, slice, timestamp):
        if 0 <= i_insert < len(self.recipe.mixed_track_recipe.inserts):
            insert_options = AudioInserter(filename, slice, timestamp).to_json(str_timestamps=False)
            self.recipe.mixed_track_recipe.inserts[i_insert] = insert_options

    def del_insert(self, i_insert):
        if 0 <= i_insert < len(self.recipe.mixed_track_recipe.inserts):
            del self.recipe.mixed_track_recipe.inserts[i_insert]

    def process(self):
        silence_intervals = []
        if len(self.recipe.mixed_track_recipe.live_timestamps):
            silence_intervals.extend(
                self.mixed_track.get_silence_ranges_from_activity_ranges(self.recipe.mixed_track_recipe.live_timestamps)
            )
        if len(self.recipe.mixed_track_recipe.silence_timestamps):
            silence_intervals.extend(self.recipe.mixed_track_recipe.silence_timestamps)
        for silence_interval in silence_intervals:
            self.mixed_track.apply_silence_to_interval(silence_interval)

        SilenceRemover(self.recipe.mixed_track_recipe.min_silence_duration).remove(self.mixed_track, padding_s=0.2)

        # Audio Overlays
        for overlay_config in self.recipe.mixed_track_recipe.overlays:
            self.mixed_track = AudioOverlayer.from_config(overlay_config).overlay(self.mixed_track)
            self.mixed_track.audio_buffer.normalize()

        # Ad Inserts
        for insert_config in self.recipe.mixed_track_recipe.inserts:
            AudioInserter.from_config(insert_config).insert_into(self.mixed_track)
        self.mixed_track.audio_buffer.normalize()

        # global fX chain
        if len(self.recipe.mixed_track_recipe.fX):
            FXChain(self.recipe.mixed_track_recipe.fX).apply(self.mixed_track)

        self.mixed_track.audio_buffer.normalize()
        self.mixed_track.audio_buffer.stereofy()

    def write_audio(self, path):
        self.mixed_track.audio_buffer._path = path
        self.mixed_track.audio_buffer.write()

    def write_recipe(self, path):
        self.recipe.to_file(path)
