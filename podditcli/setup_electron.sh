#!/usr/bin/env bash

ELECTRON_VER="v10.1.2"
VERSION=`cat version.txt`
DL_DIR=$HOME/Downloads

wget https://github.com/electron/electron/releases/download/$ELECTRON_VER/electron-$ELECTRON_VER-darwin-x64.zip -P $DL_DIR
unzip -uo $DL_DIR/electron-$ELECTRON_VER-darwin-x64.zip Electron.app/*
unlink Electron.app/Contents/Frameworks/Electron\ Framework.framework/Electron\ Framework
unlink Electron.app/Contents/Frameworks/Electron\ Framework.framework/Helpers
unlink Electron.app/Contents/Frameworks/Electron\ Framework.framework/Libraries
unlink Electron.app/Contents/Frameworks/Electron\ Framework.framework/Resources
unlink Electron.app/Contents/Frameworks/Electron\ Framework.framework/Versions/Current
mv Electron.app/Contents/Frameworks/Electron\ Framework.framework/Versions/A/* Electron.app/Contents/Frameworks/Electron\ Framework.framework/
rm -rf Electron.app/Contents/Frameworks/Electron\ Framework.framework/Versions
cp poddit.icns Electron.app/Contents/Resources
rm Electron.app/Contents/Resources/electron.icns
plutil -replace CFBundleDisplayName -string Poddit Electron.app/Contents/Info.plist
plutil -replace CFBundleIconFile -string poddit.icns Electron.app/Contents/Info.plist
plutil -replace CFBundleIdentifier -string io.poddit Electron.app/Contents/Info.plist
plutil -replace CFBundleName -string Poddit Electron.app/Contents/Info.plist
plutil -replace CFBundleShortVersionString -string $VERSION Electron.app/Contents/Info.plist
plutil -replace CFBundleVersion -string $VERSION Electron.app/Contents/Info.plist