import argparse
import json

from audio_inserter import AudioInserter
from audio_overlayer import AudioOverlayer
from fx_chain import FXChain
from mixer import Mixer
from audio_buffer import AudioBuffer
from silence_remover import SilenceRemover
from track import Track
from track_aligner import TrackAligner
import librosa

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
        is_master = local_track.get("master", False)
        track = Track(audio=audio_buffer, master=is_master)
        tracks.append(track)

    # auto calculate track alignment (offsets) for non master tracks
    track_aligner = TrackAligner(config["local_tracks"])
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

    # TODO: maybe change to user setting active (live) timestamps instead of dead time?
    # silence global timestamps
    if "silence_timestamps" in config["global_track"]:
        for silence_interval in config["global_track"]["silence_timestamps"]:
            mixed_track.apply_silence_to_interval(silence_interval)

    # Audio Overlays
    # TODO: allow overlays to start before the master track starts
    for overlay_config in config["global_track"]["overlays"]:
        mixed_track = AudioOverlayer.from_config(overlay_config).overlay(mixed_track)
        mixed_track.audio_buffer.normalize()

    # Ad Inserts
    # TODO: multiple inserts bug. Insertions offset subsequent insertion timestamps
    for insert_config in config["global_track"]["inserts"]:
        AudioInserter.from_config(insert_config).insert_into(mixed_track)
    mixed_track.audio_buffer.normalize()

    # TODO: fade in/out on track snipper
    # TODO: if audio overlays put over awkward long silence it won't be removed because there's audio activity
    SilenceRemover(config["global_track"]["min_silence_duration"]).remove(mixed_track, padding_s=0.2)

    # global fX chain
    if "fX" in config["global_track"]:
        FXChain(config["global_track"]["fX"]).apply(mixed_track)

    mixed_track.audio_buffer.normalize()
    mixed_track.audio_buffer.stereofy()

    mixed_track.audio_buffer._path = args.output
    mixed_track.audio_buffer.write()
