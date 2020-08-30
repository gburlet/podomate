import copy
import shutil
import uuid
import eel
import eel.browsers
import os
import numpy as np

from audio_buffer import AudioBuffer
from audio_overlayer import AudioOverlayer
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

global_track_overlays = {
    "intro": None,
    "outro": None,
    "others": []
}
global_track_options = {
    "live_timestamps": [],
    "silence_timestamps": [],
    "min_silence_duration": 1.25,
    "overlays": [],
    "inserts": [],
    "fX": []
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


@eel.expose
def del_speaker_track(i_speaker):
    if 0 <= i_speaker < len(tracks):
        del tracks[i_speaker]


@eel.expose
def mix_speaker_tracks(user_tracks_options):
    global mixed_track

    # set master track to be longest track
    tracks[np.argmax([t.audio_buffer.get_duration_s() for t in tracks])].master = True

    # set default track options and override with user-selected options
    tracks_options = []
    for user_track_options in user_tracks_options:
        track_options = copy.copy(default_local_track_options)
        track_options.update(user_track_options)
        tracks_options.append(track_options)

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
    _ = mixed_track.silence_ranges  # cache VAD for future operations

    filename = "%s.flac" % str(uuid.uuid4())
    mixed_track.audio_buffer._path = 'gui/media/%s' % filename
    mixed_track.audio_buffer.write()

    return filename


@eel.expose
def get_mixed_track_filename():
    if mixed_track is not None:
        filename = os.path.split(mixed_track.audio_buffer._path)[-1]
        return filename


@eel.expose
def get_global_track_options():
    global global_track_options
    return global_track_options


@eel.expose
def set_live_timestamps(live_timestamps):
    global global_track_options
    global_track_options["live_timestamps"] = live_timestamps


@eel.expose
def upload_audio(filepath):
    filename = os.path.split(filepath)[-1]
    shutil.copy(filepath, 'gui/media/%s' % filename)
    return filename


@eel.expose
def add_intro_backtrack(filename, slice, overlay_sync_point):
    global mixed_track, global_track_overlays

    if mixed_track.activity_range_cache is None or len(mixed_track.activity_range_cache) == 0:
        raise ValueError("We ran into an issue applying the intro backtrack. Is your mixed track of speakers silent?")

    # find first voice timestamp
    first_voice_timestamp = None
    for lt in global_track_options["live_timestamps"]:
        for va in mixed_track.activity_range_cache:
            if va[0] <= lt[0] <= va[1]:
                first_voice_timestamp = lt[0]
                break
            elif lt[0] <= va[0] <= lt[1]:
                first_voice_timestamp = va[0]
                break
            elif va[0] > lt[1]:
                # search optimization
                break
        if first_voice_timestamp is not None:
            break

    if first_voice_timestamp is None:
        raise ValueError("We ran into an issue applying the intro backtrack. Are your selected live segments silent?")

    duration_until_sync_point_s = overlay_sync_point - slice[0]
    backtrack_duration_s = slice[1] - slice[0]
    if not 0 < duration_until_sync_point_s < backtrack_duration_s:
        raise ValueError("We ran into an issue applying the intro backtrack. The talking start point should be within the segment of selected music.")

    overlay_path = os.path.join("gui/media/%s" % filename)
    overlay_config = AudioOverlayer.automated_intro(
        overlay_path, slice, overlay_sync_point, first_voice_timestamp
    ).to_config()
    global_track_overlays["intro"] = overlay_config


@eel.expose
def remove_intro_backtrack():
    global global_track_overlays
    del global_track_overlays["intro"]


@eel.expose
def add_outro_backtrack(filename, slice, overlay_sync_point):
    global mixed_track, global_track_overlays

    if mixed_track.activity_range_cache is None or len(mixed_track.activity_range_cache) == 0:
        raise ValueError("We ran into an issue applying the outro backtrack. Is your mixed track of speakers silent?")

    # find last voice timestamp
    last_voice_timestamp = None
    for lt in global_track_options["live_timestamps"]:
        for va in mixed_track.activity_range_cache:
            if va[0] <= lt[0] <= va[1] or lt[0] <= va[0] <= lt[1]:
                last_voice_timestamp = va[1] if va[1] < lt[1] else lt[1]
                break
            elif va[0] > lt[1]:
                # search optimization
                break
        if last_voice_timestamp is not None:
            break

    if last_voice_timestamp is None:
        raise ValueError("We ran into an issue applying the intro backtrack. Are your selected live segments silent?")

    last_voice_timestamp = mixed_track.activity_range_cache[-1][1]
    duration_until_sync_point_s = overlay_sync_point - slice[0]
    backtrack_duration_s = slice[1] - slice[0]
    if not 0 < duration_until_sync_point_s < backtrack_duration_s:
        raise ValueError("We ran into an issue applying the outro backtrack. The talking end point should be within the segment of selected music.")

    overlay_path = os.path.join("gui/media/%s" % filename)
    overlay_config = AudioOverlayer.automated_outro(
        overlay_path, slice, overlay_sync_point, last_voice_timestamp
    ).to_config()
    global_track_overlays["outro"] = overlay_config


@eel.expose
def remove_outro_backtrack():
    global global_track_overlays
    del global_track_overlays["outro"]


@eel.expose
def get_global_track_overlays():
    global global_track_overlays
    return global_track_overlays


@eel.expose
def add_insert(filename, slice, timestamp):
    global global_track_options
    insert_path = os.path.join("gui/media/%s" % filename)
    global_track_options["inserts"].append({
        "path": insert_path,
        "slice": slice,
        "timestamp": timestamp
    })


@eel.expose
def remove_insert(i):
    global global_track_options
    if 0 <= i < len(global_track_options["inserts"]):
        del global_track_options["inserts"][i]


def cleanup(page, sockets):
    pass


eel.start(
    'templates/main.html', mode="electron", jinja_templates="templates",
    close_callback=cleanup
)
