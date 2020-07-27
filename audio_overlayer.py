from audio_buffer import AudioBuffer
from mixer import Mixer
from track import Track
from track_aligner import TrackAligner


class AudioOverlayer(object):

    def __init__(self, overlay_path, overlay_slice, sync_point, volume_automations):
        self._overlay_path = overlay_path
        self._overlay_slice = overlay_slice
        self._sync_point_overlay = sync_point["overlay"]
        self._sync_point_master = sync_point["master"]
        self._volume_automations = volume_automations

    @staticmethod
    def from_config(config):
        return AudioOverlayer(
            config["path"], config["slice"], config["sync_point"], config["volume_automations"]
        )

    def overlay(self, track):
        overlay_audio_buffer = AudioBuffer(self._overlay_path)
        overlay_audio_buffer.read(normalize=False)
        overlay_audio_buffer.slice(self._overlay_slice)
        overlay_audio_buffer.apply_volume_automation(self._volume_automations)
        overlay_track = Track(audio=overlay_audio_buffer, master=False)

        tracks = [track, overlay_track]
        track_offsets = [0., self._sync_point_master-self._sync_point_overlay]
        TrackAligner().align(tracks, track_offsets).pad(tracks)
        return Mixer().mix_tracks(tracks)
