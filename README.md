# poddit
Edit, postprocess, and master podcasts and interviews automatically

## Processing Pipeline

### Local Tracks (Individual Speakers)

```
- local_t1 -> VAD -> calc align -> silence local timestamps -> align -> pad -> fxChain:[fx1 -> fx2 -> fx3] -> normalize -> gain
- local_t2 -> VAD -> calc align -> silence local timestamps -> align -> pad -> fxChain:[fx1 -> fx3 -> fx4] -> normalize -> gain
...
- local_tn -> VAD -> calc align -> silence local timestamps -> align -> pad -> fxChain:[fx1 -> fx2 -> fx3] -> normalize -> gain
```

### Global Track (Mixed)

```
local_t1 -
         |
local_t2 - -> Mixer -> silence global timestamps -> Audio Overlays -> Ad Inserts -> VAD -> silence removal -> fxChain:[fx2 -> fx5] -> normalize -0.1dB -> stereofy -> Output
...      |
local_tn -
```

## Setup
```
mkvirtualenv -p python3 poddit
workon poddit
cd <gitrepo>
brew install sox
pip install -r requirements.txt
poddit episode_template.json podcast.mp3
```

`episode_template.json` contains input paths and processing parameters for the episode
