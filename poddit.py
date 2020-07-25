import argparse

from mixer import Mixer
from silence_detector import SilenceDetector
from audio_buffer import AudioBuffer
from track import Track
from track_aligner import TrackAligner

parser = argparse.ArgumentParser(description='Edit a podcast')
parser.add_argument('-s', '--speakers', type=str, nargs='+', default=[], help='Raw speaker audio_buffer files (.wav, .mp3)')
parser.add_argument('-o', '--output', type=str, help='Audio output file')


if __name__ == "__main__":
    args = parser.parse_args()

    tracks = []
    for spath in args.speakers:
        sa = AudioBuffer(spath)
        sa.read(normalize=True)
        silence_ranges = SilenceDetector(threshold=0.35, min_silence_len_s=0.3).detect_silences(sa)
        track = Track(audio=sa, silence_ranges=silence_ranges)
        tracks.append(track)

    # sort by duration descending. First track (longest) becomes master track
    tracks.sort(key=lambda t: t.audio_buffer.get_duration_s(), reverse=True)

    TrackAligner().align(tracks).pad(tracks)

    mixed_audio_buffer = Mixer().mix_tracks(tracks)
    mixed_audio_buffer._path = args.output
    mixed_audio_buffer.write()
