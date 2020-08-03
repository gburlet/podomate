from audio_buffer import AudioBuffer
from mixer import Mixer
from track import Track
from track_aligner import TrackAligner
from utils import read_config_time


class AudioOverlayer(object):

    def __init__(self, overlay_path, overlay_slice, sync_point, volume_automations):
        self._overlay_path = overlay_path
        self._overlay_slice = [read_config_time(i) for i in overlay_slice] if overlay_slice else None
        self._sync_point_overlay = read_config_time(sync_point["overlay"])
        self._sync_point_master = read_config_time(sync_point["master"])
        if volume_automations:
            for va in volume_automations:
                va["timestamp"] = read_config_time(va["timestamp"])
        self._volume_automations = volume_automations

    @staticmethod
    def from_config(config):
        return AudioOverlayer(
            config["path"], config.get("slice"), config["sync_point"], config["volume_automations"]
        )

    def overlay(self, track):
        overlay_audio_buffer = AudioBuffer(self._overlay_path)
        overlay_audio_buffer.read(normalize=False)
        if self._overlay_slice:
            overlay_audio_buffer.slice(self._overlay_slice)
        if self._volume_automations and len(self._volume_automations) > 0:
            overlay_audio_buffer.apply_volume_automation(self._volume_automations)
        overlay_track = Track(audio=overlay_audio_buffer, master=False)

        tracks = [track, overlay_track]
        offset = self._sync_point_master-self._sync_point_overlay
        track_offsets = [abs(offset) if offset < 0 else 0., max(offset, 0.)]
        TrackAligner().align(tracks, track_offsets).pad(tracks)
        return Mixer().mix_tracks(tracks), track_offsets[0]
