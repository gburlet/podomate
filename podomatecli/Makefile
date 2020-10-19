VERSION=$(shell cat version.txt)

app:
	pyinstaller podomate.spec

dmg: app
	VERSION=$(file < version.txt)
	create-dmg \
		--volname "Podomate Installer" \
		--volicon "podomate.icns" \
		--background "podomate_dmg_background.png" \
		--window-pos 200 120 \
		--window-size 600 400 \
		--icon-size 100 \
		--icon "Podomate.app" 150 130 \
		--hide-extension "Podomate.app" \
		--app-drop-link 450 125 \
		dist/Podomate_v$(VERSION).dmg dist/Podomate.app

clean:
	rm -rf build dist
