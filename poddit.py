import argparse
import json

from fx_chain import FXChain
from mixer import Mixer
from audio_buffer import AudioBuffer
from track import Track
from track_aligner import TrackAligner

parser = argparse.ArgumentParser(description='Edit a podcast')
parser.add_argument('config', type=str, help='Parameter JSON file')
parser.add_argument('output', type=str, help='Audio output file')


if __name__ == "__main__":
    args = parser.parse_args()

    # read config JSON file
    with open(args.config, 'r') as f_json:
        config = json.load(f_json)

    tracks = []
    for local_track in config["local_tracks"]:
        audio_buffer = AudioBuffer(local_track["path"])
        audio_buffer.read(normalize=True)
        tracks.append(Track(audio=audio_buffer))

    # auto calculate track alignment (offsets): sort 1st track is master track
    tracks.sort(key=lambda t: t.audio_buffer.get_duration_s(), reverse=True)
    track_aligner = TrackAligner()
    track_offsets = track_aligner.auto_calc_offset(tracks)

    # silence local timestamps
    for track_config, track in zip(config["local_tracks"], tracks):
        if "silence_timestamps" in track_config:
            for silence_interval in track_config["silence_timestamps"]:
                track.apply_silence_to_interval(silence_interval)

    track_aligner.align(tracks, track_offsets).pad(tracks)

    # local fX chain
    for track_config, track in zip(config["local_tracks"], tracks):
        if "fX" in track_config:
            FXChain(track_config["fX"]).apply(track)
        track.audio_buffer.normalize()

    # mix global track
    mixed_track = Mixer().mix_tracks(tracks)
    mixed_track.audio_buffer.normalize()

    mixed_track.audio_buffer._path = args.output
    mixed_track.audio_buffer.write()
