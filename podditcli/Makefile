VERSION=0.1.21

app:
	pyinstaller poddit.spec

dmg: app
	create-dmg \
		--volname "Poddit Installer" \
		--volicon "poddit.icns" \
		--background "poddit_dmg_background.png" \
		--window-pos 200 120 \
		--window-size 600 400 \
		--icon-size 100 \
		--icon "Poddit.app" 150 130 \
		--hide-extension "Poddit.app" \
		--app-drop-link 450 125 \
		dist/Poddit_v$(VERSION).dmg dist/Poddit.app

clean:
	rm -rf build dist
