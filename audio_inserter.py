from audio_buffer import AudioBuffer


class AudioInserter(object):

    def __init__(self, path, slice, timestamp, volume_automations):
        self._path = path
        self._slice = slice
        self._timestamp = timestamp
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
