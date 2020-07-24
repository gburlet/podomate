import argparse

from silence_detector import SilenceDetector
from speaker_audio import SpeakerAudio


parser = argparse.ArgumentParser(description='Edit a podcast')
parser.add_argument('-s', '--speakers', type=str, nargs='+', default=[], help='Raw speaker audio files (.wav, .mp3)')
parser.add_argument('-o', '--output', type=str, help='Audio output file')


if __name__ == "__main__":
    args = parser.parse_args()

    speaker_tracks = []
    for spath in args.speakers:
        sa = SpeakerAudio(spath)
        sa.read(normalize=True)
        speaker_tracks.append(sa)

        silent_ranges = SilenceDetector(threshold=0.35, min_silence_len_s=0.3).detect_silences(sa)
        print(silent_ranges)
        print("\n")

