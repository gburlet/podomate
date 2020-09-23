# poddit
Edit, postprocess, and master podcasts and interviews automatically

## Setup Client

#### Electron.js Browser

We use Electron.js as the chromium browser for the GUI frontend for Python-Eel. Download Electron.js app and fiddle with some internals.
```
wget https://github.com/electron/electron/releases/download/v10.1.2/electron-v10.1.2-darwin-x64.zip
unzip -e electron-v10.1.2-darwin-x64.zip
cp electron-v10.1.2-darwin-x64/Electron.app <gitrepo>/podditcli
cd <gitrepo>/podditcli
mv Electron.app/Contents/Frameworks/Electron\ Framework.framework/Versions/A Electron.app/Contents/Frameworks/Electron\ Framework.framework
rm -rf Electron.app/Contents/Frameworks/Electron\ Framework.framework/Versions
```

#### Development Environment

**Install Python3**: Poddit uses Python3. We recommend installing Python3 using [pyenv](https://github.com/pyenv/pyenv).
Here's a couple good tutorial blog posts on pyenv: [[1](https://medium.com/faun/pyenv-multi-version-python-development-on-mac-578736fb91aa)] [[2](https://alysivji.github.io/setting-up-pyenv-virtualenvwrapper.html)].

**Install VirtualEnv**: It's also recommended that you install all the dependencies in a virtual environment. If using pyenv, we recommend [pyenv-virtualenvwrapper](https://github.com/pyenv/pyenv-virtualenvwrapper) to easily create virtual environments hooked up to your pyenv Python installations.
Here's a good tutorial blog post on pyenv & pyenv-virtualenvwrapper: [[1]](https://alysivji.github.io/setting-up-pyenv-virtualenvwrapper.html).

**Setup Client Environment**
```
mkvirtualenv podditcli
workon podditcli
cd <gitrepo>/podditcli
brew install libsndfile libvorbis libogg libpng opusfile lame mad flac ffmpeg sox tbb
pip install -r requirements.txt
python poddit.py
```

**Poddit Command Line**

`python main.py episode_config.json path/to/output.flac`

Note: `podditcli/episode_template.json` in the git repo is an example template JSON file where you can plug in your own parameters to create an episode.

**Poddit GUI**

`python poddit.py`

## Setup Server

```
mkvirtualenv podditweb
workon podditweb
cd <gitrepo>/podditweb
brew install postgresql
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver localhost:8001
```

You can now access the server in your web browser at `http://localhost:8001` and login to the admin at `http://localhost:8001/admin`. The API is available at `http://localhost:8001/api`.

## Bundle Executables

Instructions to bundle a Mac OS .app & Windows .exe

#### Mac OS

To bundle the GUI app into a standalone .app using [pyinstaller](https://github.com/pyinstaller/pyinstaller)
```
pip install pyinstaller
make app
```

Will create a .app in `/podditcli/dist/poddit.app` that you can double click to open and distribute to different macs.

To bundle the .app into a .dmg file using [create-dmg](https://github.com/create-dmg/create-dmg):
```
make dmg
```

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



