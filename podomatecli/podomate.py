import base64
import shutil
import sys
import uuid
import eel
import eel.browsers
import os
import requests
import subprocess
from tempfile import NamedTemporaryFile
from zipfile import ZipFile
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from getmac import get_mac_address

from episode import Episode
from speaker_track_recipe import SpeakerTrackRecipe
from track import Track
from utils import parse_version_string


################################
#            GLOBALS           #
################################
bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
exe_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else bundle_dir
electron_path = os.path.join(bundle_dir, "Electron.app/Contents/MacOS/Electron")
API_ROOT = "http://localhost:8001/api"
license_path = os.path.join(exe_path, "license.lic")
publickey_path = os.path.join(bundle_dir, "podomate_public.pem")
product_sku = "podomate-desktop"
with open(os.path.join(bundle_dir, "version.txt"), "r") as vfile:
    version = vfile.readline().strip().lower()
latest_version = None
latest_mac_version_link = None
episode = Episode()


################################
#            Startup           #
################################
eel.browsers.set_path('electron', electron_path)
eel.init('gui')

################################
#            GLOBALS           #
################################
@eel.expose
def get_version():
    return version


@eel.expose
def check_version_active():
    api_endpoint = "%s/version" % API_ROOT
    response = requests.get(url=api_endpoint, params={"sku": product_sku, "version": version})
    return response.status_code == 200


@eel.expose
def check_update():
    global latest_version, latest_mac_version_link
    api_endpoint = "%s/update" % API_ROOT
    response = requests.get(url=api_endpoint, params={"sku": product_sku})
    response_data = response.json()
    if response.status_code == 200:
        latest_version = response_data.get("version")
        latest_mac_version_link = response_data.get("mac_link")
        return _can_update()
    return False


@eel.expose
def update():
    global latest_version, latest_mac_version_link
    if _can_update():
        response = requests.get(latest_mac_version_link, stream=True)
        total_size_in_bytes = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1 kibibyte
        app_zip_path = None
        with NamedTemporaryFile(mode='wb', suffix='.app.zip', delete=False) as app_update_file:
            bytes_downloaded = 0
            for data in response.iter_content(block_size):
                bytes_downloaded += len(data)
                download_progress = float(bytes_downloaded) / total_size_in_bytes
                eel.update_progress_tick(int(download_progress*100))
                app_update_file.write(data)
            app_zip_path = app_update_file.name

        # we're done downloading, unpack and move
        mac_app_path = exe_path
        if getattr(sys, 'frozen', False):
            mac_app_path = os.path.abspath(os.path.join(exe_path, "../../../"))
        if os.path.isfile(app_zip_path):
            with ZipFile(app_update_file.name, 'r') as app_zip_file:
                app_zip_file.extractall(mac_app_path)
            os.remove(app_zip_path)
        app_path = os.path.join(mac_app_path, "Podomate.app/Contents/MacOS/podomate")
        subprocess.Popen([app_path])
        eel.close_window_for_restart()


def _can_update():
    global latest_version, latest_mac_version_link
    if latest_version is None or latest_mac_version_link is None:
        return False
    cmajor, cminor, cpatch = parse_version_string(version)
    lmajor, lminor, lpatch = parse_version_string(latest_version)
    return lmajor > cmajor or (lmajor == cmajor and lminor > cminor) or (lmajor == cmajor and lminor == cminor and lpatch > cpatch)


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
def load_episode_recipe(path):
    global episode

    if os.path.isfile(path):
        episode = Episode.from_recipe_file(path)

        # load audio assets into media directory for the web app
        for speaker_track in episode.speaker_tracks:
            upload_audio(speaker_track.audio_buffer._path)
        for overlay in episode.recipe.mixed_track_recipe.overlays:
            upload_audio(overlay["path"])
        for insert in episode.recipe.mixed_track_recipe.inserts:
            upload_audio(insert["path"])

        mix_speaker_tracks([])


@eel.expose
def get_episode_recipe():
    global episode
    return episode.recipe.to_json(str_timestamps=False)


@eel.expose
def get_speaker_track_recipe(i_track):
    global episode
    if 0 <= i_track < len(episode.speaker_tracks):
        return episode.recipe.speaker_track_recipes[i_track].to_json(str_timestamps=False)


@eel.expose
def get_speaker_track_recipes():
    global episode
    return [trecipe.to_json(str_timestamps=False) for trecipe in episode.recipe.speaker_track_recipes]


@eel.expose
def get_mixed_track_recipe():
    global episode
    return episode.recipe.mixed_track_recipe.to_json(str_timestamps=False)


@eel.expose
def get_music_overlays():
    return get_mixed_track_recipe()["overlays"]


@eel.expose
def get_snippet_inserts():
    return get_mixed_track_recipe()["inserts"]


@eel.expose
def get_speaker_track_filename(i_track):
    return get_speaker_track_recipe(i_track)["filename"]


@eel.expose
def get_mixed_track_filename():
    global episode
    if episode.mixed_track is not None:
        filename = os.path.split(episode.mixed_track.audio_buffer._path)[-1]
        return filename


@eel.expose
def get_recipe_filename():
    global episode
    if episode.mixed_track is not None:
        episode_id = os.path.splitext(os.path.split(episode.mixed_track.audio_buffer._path)[-1])[0][:-9]
        return "%s_recipe.json" % episode_id


@eel.expose
def reset():
    global episode
    episode.reset()


@eel.expose
def set_speaker_track(audio_path, i_speaker):
    global episode
    track = Track.from_audio_file(audio_path)
    if 0 <= i_speaker < len(episode.speaker_tracks):
        episode.update_speaker_track(i_speaker, track)
    else:
        episode.add_speaker_track(track)
    upload_audio(audio_path)


@eel.expose
def del_speaker_track(i_speaker):
    global episode
    episode.del_speaker_track(i_speaker)


@eel.expose
def get_speaker_track_silence_timestamps(i_speaker):
    global episode
    if 0 <= i_speaker < len(episode.speaker_tracks):
        return get_speaker_track_recipe(i_speaker)["silence_timestamps"]


@eel.expose
def set_speaker_track_silence_timestamps(silence_timestamps, i_speaker):
    global episode
    if 0 <= i_speaker < len(episode.speaker_tracks):
        episode.recipe.speaker_track_recipes[i_speaker].silence_timestamps = silence_timestamps


@eel.expose
def get_live_timestamps():
    global episode
    return episode.recipe.mixed_track_recipe.live_timestamps


@eel.expose
def set_live_timestamps(live_timestamps):
    global episode
    episode.recipe.mixed_track_recipe.live_timestamps = live_timestamps


@eel.expose
def upload_audio(filepath):
    filename = os.path.split(filepath)[-1]
    audio_sink_path = os.path.abspath(os.path.join(bundle_dir, 'gui/media/%s' % filename))
    shutil.copy(filepath, audio_sink_path)
    return filename


@eel.expose
def add_intro_backtrack(path, slice, overlay_sync_point):
    """
    Creates recipe for intro audio overlay
    """
    global episode
    episode.add_intro_overlay(path, slice, overlay_sync_point)


@eel.expose
def remove_intro_backtrack():
    global episode
    episode.recipe.mixed_track_recipe.remove_overlays_with_tag("intro")


@eel.expose
def add_outro_backtrack(path, slice, overlay_sync_point):
    """
    Creates recipe for outro audio overlay
    """
    global episode
    episode.add_outro_overlay(path, slice, overlay_sync_point)


@eel.expose
def remove_outro_backtrack():
    global episode
    episode.recipe.mixed_track_recipe.remove_overlays_with_tag("outro")


@eel.expose
def add_insert(filename, slice, timestamp):
    """
    Creates recipe for audio insert
    """
    global episode
    episode.add_insert(filename, slice, timestamp)


@eel.expose
def update_insert(i_insert, filename, slice, timestamp):
    global episode
    episode.update_insert(i_insert, filename, slice, timestamp)


@eel.expose
def remove_insert(i_insert):
    global episode
    episode.del_insert(i_insert)


@eel.expose
def mix_speaker_tracks(user_tracks_options):
    global episode

    # set default track options and override with user-selected options
    for i_track, user_track_options in enumerate(user_tracks_options):
        # inject default track fX
        user_track_options["fX"] = SpeakerTrackRecipe.DEFAULT_FX
        episode.recipe.speaker_track_recipes[i_track].update(
            SpeakerTrackRecipe(**user_track_options)
        )

    def update_gui_progress(step, steps, message):
        eel.update_determinant_loader(int(step/float(steps)*100), message)

    episode.mix_speaker_tracks(progress_callback=update_gui_progress)

    filename = "%s.flac" % str(uuid.uuid4())
    mixed_track_path = os.path.abspath(os.path.join(bundle_dir, 'gui/media/%s' % filename))
    episode.mixed_track.audio_buffer._path = mixed_track_path
    episode.mixed_track.audio_buffer.write()
    return filename


@eel.expose
def process():
    global episode

    # figure out where to write recipe file
    cache_mixed_track_path = episode.mixed_track.audio_buffer._path
    episode_id = os.path.splitext(os.path.split(cache_mixed_track_path)[-1])[0]
    recipe_filename = "%s_recipe.json" % episode_id
    recipe_path = os.path.abspath(os.path.join(bundle_dir, 'gui/media/%s' % recipe_filename))

    # figure out where to write audio file
    audio_filename = "%s_mastered.flac" % episode_id
    mixed_track_path = os.path.abspath(os.path.join(bundle_dir, 'gui/media/%s' % audio_filename))

    episode.write_recipe(recipe_path)
    episode.process()
    episode.write_audio(mixed_track_path)


eel.start(
    'templates/main.html', mode="electron", jinja_templates="templates"
)
