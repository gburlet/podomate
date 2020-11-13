import argparse
from tqdm import tqdm

from episode import Episode

parser = argparse.ArgumentParser(description='Edit a podcast')
parser.add_argument('config', type=str, help='Parameter JSON file')
parser.add_argument('output', type=str, help='Audio output file')


if __name__ == "__main__":
    args = parser.parse_args()

    episode = Episode.from_recipe_file(args.config)
    processing_steps = episode.recipe.processing_steps()
    pbar = tqdm(total=processing_steps)

    def log_progress(step, steps, message):
        pbar.update()

    episode.mix_speaker_tracks(progress_callback=log_progress)
    episode.process(progress_callback=log_progress)
    episode.write_audio(args.output)

    pbar.close()
