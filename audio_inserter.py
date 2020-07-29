from audio_buffer import AudioBuffer
from utils import read_config_time


class AudioInserter(object):

    def __init__(self, path, slice, timestamp, volume_automations):
        self._path = path
        self._slice = [read_config_time(i) for i in slice] if slice else None
        self._timestamp = read_config_time(timestamp)
        if volume_automations:
            for va in volume_automations:
                va["timestamp"] = read_config_time(va["timestamp"])
        self._volume_automations = volume_automations

    @staticmethod
    def from_config(config):
        return AudioInserter(
            config["path"], config.get("slice"), config["timestamp"], volume_automations=config.get("volume_automations")
        )

    def insert_into(self, track):
        insert_audio_buffer = AudioBuffer(self._path)
        insert_audio_buffer.read(normalize=False)
        if self._slice:
            insert_audio_buffer.slice(self._slice)
        if self._volume_automations and len(self._volume_automations) > 0:
            insert_audio_buffer.apply_volume_automation(self._volume_automations)
        track.audio_buffer.insert(insert_audio_buffer, self._timestamp)

        return self._timestamp, insert_audio_buffer.get_duration_s()
