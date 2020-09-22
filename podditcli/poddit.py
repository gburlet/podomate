import base64
import copy
import shutil
import sys
import uuid
import eel
import eel.browsers
import os
import numpy as np
import requests
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from getmac import get_mac_address

from audio_buffer import AudioBuffer
from audio_inserter import AudioInserter
from audio_overlayer import AudioOverlayer
from audio_preprocessors.gate_filter import GateFilter
from fx_chain import FXChain
from mixer import Mixer
from silence_remover import SilenceRemover
from track import Track
from track_aligner import TrackAligner



################################
#            GLOBALS           #
################################
bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
exe_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else bundle_dir
electron_path = os.path.join(bundle_dir, "Electron.app/Contents/MacOS/Electron")
API_ROOT = "http://localhost:8001/api"
license_path = os.path.join(exe_path, "license.lic")
publickey_path = os.path.join(bundle_dir, "poddit_public.pem")
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


################################
#            Startup           #
################################
eel.browsers.set_path('electron', electron_path)
eel.init('gui')

################################
#            GLOBALS           #
################################
@eel.expose
def activate(email, license_key):
    mac_address = get_mac_address()

    # contact licensing server
    api_endpoint = "%s/activate" % API_ROOT
    response = requests.post(
        url=api_endpoint,
        data={
            'email': email, 'license_key': license_key, 'mac_address': mac_address
        }
    )
    response_data = response.json()
    if response.status_code == 200:
        # server activation OK, analyze response
        signature = response_data.get("signature")
        decoded_signature = base64.decodebytes(signature.encode('utf-8'))
        activations_remaining = response_data.get("activations_remaining")

        with open(publickey_path, "rb") as key_file:
            public_key = serialization.load_pem_public_key(
                key_file.read(),
                backend=default_backend()
            )

        message = mac_address
        try:
            public_key.verify(
                decoded_signature, bytes(message, encoding='utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        except InvalidSignature:
            return {
                "activated": False,
                "activations_remaining": 0,
                "msg": "There was an error activating the license key"
            }

        # save signed response on HDD for bootup checks
        with open(license_path, 'w') as f:
            f.write(email+'\n')
            f.write(license_key+'\n')
            f.write(signature)

        return {
            "activated": True,
            "activations_remaining": activations_remaining,
            "msg": "activated"
        }
    elif response.status_code == 403:
        return {
            "activated": False,
            "activations_remaining": 0,
            "msg": response_data.get("general")
        }


@eel.expose
def check_license():
    # reads the license file on disk and checks signature authenticity
    if os.path.isfile(license_path) and os.path.isfile(publickey_path):
        with open(license_path, 'r') as f:
            license_data = f.readlines()
            email = license_data[0]
            license_key = license_data[1]
            signature = license_data[2]

            with open(publickey_path, "rb") as key_file:
                public_key = serialization.load_pem_public_key(
                    key_file.read(),
                    backend=default_backend()
                )

                try:
                    message = get_mac_address()
                    decoded_signature = base64.decodebytes(signature.encode('utf-8'))
                    public_key.verify(
                        decoded_signature, bytes(message, encoding='utf-8'),
                        padding.PSS(
                            mgf=padding.MGF1(hashes.SHA256()),
                            salt_length=padding.PSS.MAX_LENGTH
                        ),
                        hashes.SHA256()
                    )
                except InvalidSignature:
                    return False

                return True
    return False


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
    mixed_track_path = os.path.abspath(os.path.join(bundle_dir, 'gui/media/%s' % filename))
    mixed_track.audio_buffer._path = mixed_track_path
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
    audio_sink_path = os.path.abspath(os.path.join(bundle_dir, 'gui/media/%s' % filename))
    shutil.copy(filepath, audio_sink_path)
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
def edit_insert(i_insert, filename, slice, timestamp):
    global global_track_options
    if 0 <= i_insert < len(global_track_options["inserts"]):
        insert_path = os.path.join("gui/media/%s" % filename)
        global_track_options["inserts"][i_insert] = {
            "path": insert_path,
            "slice": slice,
            "timestamp": timestamp
        }


@eel.expose
def remove_insert(i):
    global global_track_options
    if 0 <= i < len(global_track_options["inserts"]):
        del global_track_options["inserts"][i]


@eel.expose
def process():
    global global_track_overlays, global_track_options, mixed_track

    global_track_options["overlays"].clear()
    if global_track_overlays["intro"]:
        global_track_options["overlays"].append(global_track_overlays["intro"])
    if global_track_overlays["outro"]:
        global_track_options["overlays"].append(global_track_overlays["outro"])
    global_track_options["overlays"].extend(global_track_overlays["others"])

    silence_intervals = []
    if "live_timestamps" in global_track_options:
        silence_intervals.extend(mixed_track.get_silence_ranges_from_activity_ranges(global_track_options["live_timestamps"]))
    if "silence_timestamps" in global_track_options:
        silence_intervals.extend(global_track_options["silence_timestamps"])
    for silence_interval in silence_intervals:
        mixed_track.apply_silence_to_interval(silence_interval)

    SilenceRemover(global_track_options["min_silence_duration"]).remove(mixed_track, padding_s=0.2)

    # Audio Overlays
    cache_mixed_track_path = mixed_track.audio_buffer._path
    for overlay_config in global_track_options["overlays"]:
        mixed_track = AudioOverlayer.from_config(overlay_config).overlay(mixed_track)
        mixed_track.audio_buffer.normalize()

    # Ad Inserts
    for insert_config in global_track_options["inserts"]:
        AudioInserter.from_config(insert_config).insert_into(mixed_track)
    mixed_track.audio_buffer.normalize()

    # global fX chain
    if "fX" in global_track_options:
        FXChain(global_track_options["fX"]).apply(mixed_track)

    mixed_track.audio_buffer.normalize()
    mixed_track.audio_buffer.stereofy()
    filename = "%s_mastered.flac" % os.path.split(cache_mixed_track_path)[-1]
    mixed_track_path = os.path.abspath(os.path.join(bundle_dir, 'gui/media/%s' % filename))
    mixed_track.audio_buffer._path = mixed_track_path
    mixed_track.audio_buffer.write()


eel.start(
    'templates/main.html', mode="electron", jinja_templates="templates"
)
