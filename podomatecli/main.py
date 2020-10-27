import argparse
import json
from tqdm import tqdm

from audio_inserter import AudioInserter
from audio_overlayer import AudioOverlayer
from audio_preprocessors.gate_filter import GateFilter
from episode import Episode
from episode_recipe import EpisodeRecipe
from fx_chain import FXChain
from mixer import Mixer
from audio_buffer import AudioBuffer
from silence_remover import SilenceRemover
from track import Track
from track_aligner import TrackAligner
from utils import time_to_s, time_interval_to_s

parser = argparse.ArgumentParser(description='Edit a podcast')
parser.add_argument('config', type=str, help='Parameter JSON file')
parser.add_argument('output', type=str, help='Audio output file')

# read, gate, silence, fX
local_processing_steps = 4
# calc align, align, mix, silence, overlays, inserts, silence removal, fX, normalize, stereofy, write
global_processing_steps = 11


if __name__ == "__main__":
    args = parser.parse_args()

    #total_steps = local_processing_steps * len(config["local_tracks"]) + global_processing_steps
    #pbar = tqdm(total=total_steps)

    episode = Episode.from_recipe_file(args.config)
    episode.mix_speaker_tracks()
    episode.process()
    episode.write_audio(args.output)

    # pbar.close()
