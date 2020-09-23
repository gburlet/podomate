VERSION=0.1.21

app:
	pyinstaller poddit.spec

dmg: app
	create-dmg \
		--volname "Poddit Installer" \
		--volicon "poddit.icns" \
		--background "gui/img/main.jpg" \
		--window-pos 200 120 \
		--window-size 800 400 \
		--icon-size 100 \
		--icon "Poddit.app" 200 190 \
		--hide-extension "Poddit.app" \
		--app-drop-link 600 185 \
		dist/poddit_v$(VERSION).dmg dist/poddit.app

clean:
	rm -rf build dist
