eel.expose(update_progress_tick);
function update_progress_tick(progress) {
    $("#update-progress-bar").width(progress+'%');
    $("#update-progress-bar").attr("aria-valuenow", progress);
}

eel.expose(close_window_for_restart);
function close_window_for_restart() {
    const BrowserWindow = nodeRequire('electron').remote;
	let window = BrowserWindow.getCurrentWindow();
    window.close();
}

async function performUpdate() {
    await eel.update()().then(() => {
        $("#btn-start-update").hide();
        $("#update-progress").show();
    }).catch((err) => {
        $("#btn-start-update").hide();
        $("#update-prompt").text("There was an error updating. Do you have an internet connection? If the problem persists, please send a bug report on our website so we can fix it for you!");
    });
}

async function checkUpdate() {
    let version = await eel.get_version()();
    $("#version-string").text(version);
    await eel.check_update()().then((updateAvailable) => {
        if (updateAvailable) {
            $("#update-notification-toast").toast('show');
        } else {
            $("#update-prompt").text("Your application is up to date. Hoorah!");
            $("#btn-start-update").hide();
            $("#btn-version-update").hide();
        }
    }).catch((err) => {
        showError("There was an error checking for updates. Do you have an internet connection?");
    });
}

async function checkSunset() {
    await eel.check_version_active()().then((isVersionActive) => {
        if (!isVersionActive) {
            $("#btn-start").hide();
            $("#btn-load-episode").hide();
            $("#btn-start-activation").hide();
            showError("This version is too out of date. Please update before using!")
        }
    }).catch((err) => {
        showError("There was an error checking for updates. Do you have an internet connection?");
    });
}

$("#btn-start-update").click(function() {
    performUpdate();
});

$('#updateModal').on('show.bs.modal', function (e) {
    $("#update-notification-toast").toast('hide');
});