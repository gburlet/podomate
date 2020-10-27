import copy

import os

from audio_buffer import AudioBuffer
from track import Track
from utils import time_to_s, time_to_timestamp, time_interval_to_timestamp, time_interval_to_s


class AudioInserter(object):

    def __init__(self, path, slice, timestamp, volume_automations=None):
        self._path = path
        self._slice = [time_to_s(i) for i in slice] if slice else None
        self._timestamp = time_to_s(timestamp)
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

    def to_json(self, str_timestamps=False):
        insert_options = {
            "path": self._path,
            "filename": os.path.split(self._path)[-1],
            "timestamp": time_to_timestamp(self._timestamp) if str_timestamps else time_to_s(self._timestamp),
        }
        if self._slice:
            insert_options["slice"] = time_interval_to_timestamp(self._slice) if str_timestamps else time_interval_to_s(self._slice)
        if self._volume_automations:
            formatted_volume_automations = copy.copy(self._volume_automations)
            for va in formatted_volume_automations:
                va["timestamp"] = time_to_timestamp(va["timestamp"]) if str_timestamps else time_to_s(va["timestamp"])
                insert_options["volume_automations"] = formatted_volume_automations

        return insert_options
