import copy

import eel
import eel.browsers
import os
import numpy as np
from tempfile import NamedTemporaryFile

from audio_buffer import AudioBuffer
from audio_preprocessors.gate_filter import GateFilter
from fx_chain import FXChain
from mixer import Mixer
from track import Track
from track_aligner import TrackAligner

eel.browsers.set_path('electron', 'node_modules/electron/dist/Electron.app/Contents/MacOS/Electron')
eel.init('gui')

tracks = []
mixed_track = None

default_local_track_options = {
    "fX": [
        {
            "effect": "contrast",
            "parameters": {
                "amount": 80
            }
        },
        {
            "effect": "equalizer",
            "parameters": {
                "frequency": 100,
                "width_q": 1,
                "gain_db": 0
            }
        },
        {
            "effect": "equalizer",
            "parameters": {
                "frequency": 296.1,
                "width_q": 1,
                "gain_db": -1.6
            }
        },
        {
            "effect": "equalizer",
            "parameters": {
                "frequency": 3511,
                "width_q": 1,
                "gain_db": 1.8
            }
        },
        {
            "effect": "equalizer",
            "parameters": {
                "frequency": 10000,
                "width_q": 1,
                "gain_db": 2.2
            }
        }
    ]
}


@eel.expose
def set_speaker_track(audio_path, i_speaker):
    # read
    audio_buffer = AudioBuffer(audio_path)
    audio_buffer.read(normalize=True)
    track = Track(audio=audio_buffer)
    if len(tracks) == 0 or i_speaker >= len(tracks):
        tracks.append(track)
    else:
        tracks[i_speaker] = track

    print(audio_path, i_speaker, tracks)


@eel.expose
def del_speaker_track(i_speaker):
    if 0 <= i_speaker < len(tracks):
        del tracks[i_speaker]


@eel.expose
def mix_speaker_tracks(user_tracks_options):
    # set master track to be longest track
    tracks[np.argmax([t.audio_buffer.get_duration_s() for t in tracks])].master = True

    # set default track options and override with user-selected options
    tracks_options = []
    for user_track_options in user_tracks_options:
        track_options = copy.copy(default_local_track_options)
        track_options.update(user_track_options)
        tracks_options.append(track_options)

    print(tracks_options)

    """
    # gate filter
    for track, track_options in zip(tracks, tracks_options):
        if "gate_filter" in track_options:
            GateFilter(track_options["gate_filter"]).process(track)

    # auto calculate track alignment (offsets) for non master tracks
    track_aligner = TrackAligner(tracks_options)
    track_offsets = track_aligner.auto_calc_offset(tracks)

    # silence local timestamps
    for track, track_options in zip(tracks, tracks_options):
        if "silence_timestamps" in track_options:
            for silence_interval in track_options["silence_timestamps"]:
                track.apply_silence_to_interval(silence_interval)

    # perform alignment
    track_aligner.align(tracks, track_offsets).pad(tracks)

    # local fX chain
    for track, track_options in zip(tracks, tracks_options):
        if "fX" in track_options:
            FXChain(track_options["fX"]).apply(track)
        track.audio_buffer.normalize()

    # mix global track
    mixed_track = Mixer().mix_tracks(tracks)
    mixed_track.audio_buffer.normalize()
    with open(NamedTemporaryFile(suffix='.flac'), 'w') as f:
        mixed_track.audio_buffer._path = f.name
        mixed_track.audio_buffer.write()
    """


eel.start('templates/main.html', mode="electron", jinja_templates="templates")
