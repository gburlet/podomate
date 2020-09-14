from audio_buffer import AudioBuffer
from track import Track
from utils import read_config_timestamp


class AudioInserter(object):

    def __init__(self, path, slice, timestamp, volume_automations):
        self._path = path
        self._slice = [read_config_timestamp(i) for i in slice] if slice else None
        self._timestamp = read_config_timestamp(timestamp)
        self._volume_automations = volume_automations

    @staticmethod
    def from_config(config):
        return AudioInserter(
            config["path"], config.get("slice"), config["timestamp"], volume_automations=config.get("volume_automations")
        )

    def insert_into(self, track):
        insert_audio_buffer = AudioBuffer(self._path)
        insert_audio_buffer.read(normalize=False)
        insert_track = Track(audio=insert_audio_buffer, master=False)
        if self._slice:
            insert_track.slice(self._slice)
        if self._volume_automations and len(self._volume_automations) > 0:
            insert_track.apply_volume_automation(self._volume_automations)
        track.insert(insert_track.audio_buffer, self._timestamp)

        return self._timestamp, insert_audio_buffer.get_duration_s()
