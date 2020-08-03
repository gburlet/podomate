import argparse
import json
from tqdm import tqdm

from audio_inserter import AudioInserter
from audio_overlayer import AudioOverlayer
from fx_chain import FXChain
from mixer import Mixer
from audio_buffer import AudioBuffer
from silence_remover import SilenceRemover
from track import Track
from track_aligner import TrackAligner
from utils import read_config_time

parser = argparse.ArgumentParser(description='Edit a podcast')
parser.add_argument('config', type=str, help='Parameter JSON file')
parser.add_argument('output', type=str, help='Audio output file')

# read, silence, fX
local_processing_steps = 3
global_processing_steps = 11
# calc align, align, mix, silence, overlays, inserts, silence removal, fX, normalize, stereofy, write

if __name__ == "__main__":
    args = parser.parse_args()

    # read config JSON file
    with open(args.config, 'r') as f_json:
        config = json.load(f_json)

    total_steps = local_processing_steps * len(config["local_tracks"]) + global_processing_steps
    pbar = tqdm(total=total_steps)

    tracks = []
    for local_track in config["local_tracks"]:
        audio_buffer = AudioBuffer(local_track["path"])
        audio_buffer.read(normalize=True)
        is_master = local_track.get("master", False)
        track = Track(audio=audio_buffer, master=is_master)
        tracks.append(track)
        pbar.update(1)

    # auto calculate track alignment (offsets) for non master tracks
    track_aligner = TrackAligner(config["local_tracks"])
    track_offsets = track_aligner.auto_calc_offset(tracks)
    pbar.update(1)

    # silence local timestamps
    for track_config, track in zip(config["local_tracks"], tracks):
        if "silence_timestamps" in track_config:
            for silence_interval in track_config["silence_timestamps"]:
                parsed_interval = [read_config_time(i) for i in silence_interval]
                track.apply_silence_to_interval(parsed_interval)
        pbar.update(1)

    track_aligner.align(tracks, track_offsets).pad(tracks)
    pbar.update(1)

    # local fX chain
    for track_config, track in zip(config["local_tracks"], tracks):
        if "fX" in track_config:
            FXChain(track_config["fX"]).apply(track)
        track.audio_buffer.normalize()
        pbar.update(1)

    # mix global track
    mixed_track = Mixer().mix_tracks(tracks)
    mixed_track.audio_buffer.normalize()
    pbar.update(1)

    # TODO: maybe change to user setting active (live) timestamps instead of dead time?
    # silence global timestamps
    if "silence_timestamps" in config["global_track"]:
        for silence_interval in config["global_track"]["silence_timestamps"]:
            parsed_interval = [read_config_time(i) for i in silence_interval]
            mixed_track.apply_silence_to_interval(parsed_interval)
    pbar.update(1)

    # Audio Overlays
    # TODO: allow overlays to start before the master track starts
    for overlay_config in config["global_track"]["overlays"]:
        mixed_track = AudioOverlayer.from_config(overlay_config).overlay(mixed_track)
        mixed_track.audio_buffer.normalize()
    pbar.update(1)

    # Ad Inserts
    track_inserts = config["global_track"]["inserts"]
    for i_insert, insert_config in enumerate(track_inserts):
        _, insert_duration = AudioInserter.from_config(insert_config).insert_into(mixed_track)
        if i_insert+1 < len(track_inserts):
            for next_insert_config in track_inserts[i_insert+1:]:
                next_insert_config["timestamp"] = read_config_time(next_insert_config["timestamp"])
                next_insert_config["timestamp"] += insert_duration
    mixed_track.audio_buffer.normalize()
    pbar.update(1)

    # TODO: fade in/out on track snipper
    # TODO: if audio overlays put over awkward long silence it won't be removed because there's audio activity
    SilenceRemover(config["global_track"]["min_silence_duration"]).remove(mixed_track, padding_s=0.2)
    pbar.update(1)

    # global fX chain
    if "fX" in config["global_track"]:
        FXChain(config["global_track"]["fX"]).apply(mixed_track)
    pbar.update(1)

    mixed_track.audio_buffer.normalize()
    pbar.update(1)
    mixed_track.audio_buffer.stereofy()
    pbar.update(1)
    mixed_track.audio_buffer._path = args.output
    mixed_track.audio_buffer.write()
    pbar.update(1)
    pbar.close()
