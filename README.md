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
local_t2 - -> Mixer -> silence global timestamps -> VAD -> silence removal -> Audio Overlays -> Ad Inserts -> fxChain:[fx2 -> fx5] -> normalize -0.1dB -> -> stereofy -> output
...      |
local_tn -
```

## Setup
```
mkvirtualenv -p python3 poddit
workon poddit
cd <gitrepo>
pip install -r requirements.txt
poddit --speakers path1.mp3 path2.mp3 --output podcast.mp3
```
