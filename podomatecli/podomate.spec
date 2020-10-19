# -*- mode: python ; coding: utf-8 -*-
import platform

block_cipher = None
with open("version.txt", "r") as vfile:
    version = vfile.readline().strip().lower()
os_id = platform.system().lower()

if os_id == "darwin":
    a = Analysis(['podomate.py'],
                 pathex=['/Users/gburlet/Podomate/podomate/podomatecli'],
                 binaries=[
                    ('/usr/local/lib/libsox.dylib', '.'),
                    ('/usr/local/opt/libvorbis/lib/libvorbis.dylib', '.'),
                    ('/usr/local/opt/libvorbis/lib/libvorbisenc.dylib', '.'),
                    ('/usr/local/opt/libvorbis/lib/libvorbisfile.dylib', '.'),
                    ('/usr/local/opt/lame/lib/libmp3lame.dylib', '.'),
                    ('/usr/local/opt/mad/lib/libmad.dylib', '.'),
                    ('/usr/lib/libz.dylib', '.'),
                    ('/usr/local/opt/flac/lib/libFLAC.dylib', '.'),
                    ('/usr/lib/libSystem.dylib', '.'),
                    ('/usr/local/opt/libogg/lib/libogg.dylib', '.'),
                    ('/usr/local/opt/libsndfile/lib/libsndfile.dylib', '.'),
                    ('/usr/local/opt/libpng/lib/libpng.dylib', '.'),
                    ('/usr/local/opt/opusfile/lib/libopusfile.dylib', '.'),
                    ('/usr/local/lib/libtbb.dylib', '.')
                 ],
                 datas=[
                    ('/Users/gburlet/virtualenvs/podomatecli/lib/python3.8/site-packages/eel/eel.js', 'eel'), ('gui', 'gui'),
                    ('Electron.app', 'Electron.app'),
                    ('main.js', 'Electron.app/Contents/Resources/app'),
                    ('package.json', 'Electron.app/Contents/Resources/app'),
                    ('podomate_public.pem', '.'),
                    ('version.txt', '.'),
                    ('/Users/gburlet/virtualenvs/podomatecli/lib/python3.8/site-packages/librosa', 'librosa'),
                    ('/usr/local/bin/sox', '.'),
                    ('/usr/local/lib/libsox.a', '.'),
                    ('/usr/local/include/sox.h', '.')
                 ],
                 hiddenimports=[
                    'bottle_websocket', 'sklearn.utils._cython_blas', 'sklearn.neighbors._typedefs', 'sklearn.neighbors._quad_tree',
                    'sklearn.tree._criterion', 'sklearn.tree._utils'
                 ],
                 hookspath=[],
                 runtime_hooks=[],
                 excludes=[],
                 win_no_prefer_redirects=False,
                 win_private_assemblies=False,
                 cipher=block_cipher,
                 noarchive=False)
    pyz = PYZ(a.pure, a.zipped_data,
                 cipher=block_cipher)

    """
    # this generates the one directory
    exe = EXE(pyz,
              a.scripts,
              [],
              exclude_binaries=True,
              name='podomate',
              debug=False,
              bootloader_ignore_signals=False,
              strip=False,
              upx=True,
              console=False, icon='podomate.icns')

    coll = COLLECT(exe,
                   a.binaries,
                   a.zipfiles,
                   a.datas,
                   strip=False,
                   upx=True,
                   upx_exclude=[],
                   name='podomate')
    """

    # this generates the one file
    exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='podomate',
          debug=True,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True, icon='podomate.icns')

    app = BUNDLE(exe,
                 name='Podomate.app',
                 icon='podomate.icns',
                 bundle_identifier='com.podomate.io',
                 version=version)
