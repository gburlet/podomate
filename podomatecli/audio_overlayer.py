from audio_buffer import AudioBuffer
from mixer import Mixer
from track import Track
from track_aligner import TrackAligner
from utils import read_config_timestamp, s_to_timestamp


class AudioOverlayer(object):

    def __init__(self, overlay_path, overlay_slice, sync_point, volume_automations=None):
        self._overlay_path = overlay_path
        self._overlay_slice = [read_config_timestamp(i) for i in overlay_slice] if overlay_slice else None
        self._sync_point_overlay = read_config_timestamp(sync_point["overlay"])
        self._sync_point_master = read_config_timestamp(sync_point["master"])
        self._volume_automations = volume_automations

    @staticmethod
    def from_config(config):
        return AudioOverlayer(
            config["path"], config.get("slice"), config["sync_point"], config["volume_automations"]
        )

    @staticmethod
    def automated_intro(overlay_path, overlay_slice, overlay_sync_point, master_sync_point, min_automation_segment_length_s=1.5):
        """
        Creates an audio overlay with a volume automation suitable for a hype intro

        Args:
            overlay_path (string): path to the audio file overlay
            overlay_slice (pair): overlay timestamp tap-in and tap-out
            overlay_sync_point (float): timestamp of sync point in audio overlay
            master_sync_point (float): timestamp of sync point in master track
            min_automation_segment_length_s (float): minimum length required for an automation segment to do fancy things

        Returns:
            configured AudioOverlay
        """

        volume_automations = []

        # handle automation critical points before the vox begins
        if overlay_slice[0] + 2*min_automation_segment_length_s > overlay_sync_point:
            # not enough room at beginning to do a proper fade out automation, just keep er' quiet for the vox
            volume_automations.append({"timestamp": overlay_slice[0], "volume": 0.33})
        else:
            volume_automations.append({"timestamp": overlay_slice[0], "volume": 0.9})
            volume_automations.append({"timestamp": overlay_sync_point-min_automation_segment_length_s, "volume": 0.9})

        # handle automation critical points after the vox comes in
        if overlay_sync_point + 2*min_automation_segment_length_s < overlay_slice[1]:
            # we have enough room for a smoother fade-out automation
            volume_automations.append({"timestamp": overlay_sync_point+min_automation_segment_length_s, "volume": 0.25})

        # end the automation
        volume_automations.append({"timestamp": overlay_slice[1], "volume": 0.})

        backtrack_options = {
            "path": overlay_path,
            "slice": overlay_slice,
            "sync_point": {
                "overlay": overlay_sync_point,
                "master": master_sync_point
            },
            "volume_automations": volume_automations
        }

        return AudioOverlayer.from_config(backtrack_options)

    @staticmethod
    def automated_outro(overlay_path, overlay_slice, overlay_sync_point, master_sync_point, min_automation_segment_length_s=1.5):
        """
        Creates an audio overlay with a volume automation suitable for a hype outro

        Args:
            overlay_path (string): path to the audio file overlay
            overlay_slice (pair): overlay timestamp tap-in and tap-out
            overlay_sync_point (float): timestamp of sync point in audio overlay
            master_sync_point (float): timestamp of sync point in master track
            min_automation_segment_length_s (float): minimum length required for an automation segment to do fancy things

        Returns:
            configured AudioOverlay
        """

        volume_automations = []

        # handle automation critical points before the vox begins
        volume_automations.append({"timestamp": overlay_slice[0], "volume": 0.0})
        if overlay_slice[0] + 2*min_automation_segment_length_s < overlay_sync_point:
            # we have enough room at the beginning to do a longer fade-in automation
            volume_automations.append({"timestamp": overlay_slice[0]+min_automation_segment_length_s, "volume": 0.2})
        volume_automations.append({"timestamp": overlay_sync_point, "volume": 0.2})

        # handle automation critical points after the vox ends
        automation_ramp_s = min_automation_segment_length_s/3.
        if overlay_sync_point + min_automation_segment_length_s + 2*automation_ramp_s < overlay_slice[1]:
            # we have enough room to play the outro audio for a bit before winding downs
            volume_automations.append({"timestamp": overlay_sync_point+automation_ramp_s, "volume": 0.9})
            volume_automations.append({"timestamp": overlay_slice[1]-automation_ramp_s, "volume": 0.9})

        # end the automation
        volume_automations.append({"timestamp": overlay_slice[1], "volume": 0.})

        backtrack_options = {
            "path": overlay_path,
            "slice": overlay_slice,
            "sync_point": {
                "overlay": overlay_sync_point,
                "master": master_sync_point
            },
            "volume_automations": volume_automations
        }

        return AudioOverlayer.from_config(backtrack_options)

    def overlay(self, track):
        overlay_audio_buffer = AudioBuffer(self._overlay_path)
        overlay_audio_buffer.read(normalize=False)
        overlay_track = Track(audio=overlay_audio_buffer, master=False)
        if self._overlay_slice:
            overlay_track.slice(self._overlay_slice)
        if self._volume_automations and len(self._volume_automations) > 0:
            overlay_track.apply_volume_automation(self._volume_automations)

        tracks = [track, overlay_track]
        offset = track.timeline.transform_timestamp(self._sync_point_master) - overlay_track.timeline.transform_timestamp(self._sync_point_overlay)
        track_offsets = [abs(offset) if offset < 0 else 0., max(offset, 0.)]
        TrackAligner().align(tracks, track_offsets).pad(tracks)

        return Mixer().mix_tracks(tracks)

    def to_config(self):
        backtrack_options = {
            "path": self._overlay_path,
            "slice": [s_to_timestamp(ts) for ts in self._overlay_slice] if self._overlay_slice else None,
            "sync_point": {
                "overlay": s_to_timestamp(self._sync_point_overlay),
                "master": s_to_timestamp(self._sync_point_master)
            },
            "volume_automations": self._volume_automations
        }
        return backtrack_options
