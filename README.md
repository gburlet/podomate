# poddit
Edit, postprocess, and master podcasts and interviews automatically

## Setup Client
```
cd <gitrepo>/podditcli
pyenv local 3.8.5
mkvirtualenv poddit
workon poddit
brew install sox
pip install -r requirements.txt
poddit episode_template.json podcast.mp3
```

`episode_template.json` contains input paths and processing parameters for the episode

## Setup Server
```
cd <gitrepo>/podditweb
pyenv local 3.8.5
mkvirtualenv podditweb
workon podditweb
pip install -r requirements.txt
python manage.py runserver localhost:8000
```

