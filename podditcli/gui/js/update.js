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
    $("#btn-start-update").hide();
    $("#update-progress").show();
    await eel.update()();
}

async function checkUpdate() {
    let version = await eel.get_version()();
    $("#version-string").text(version);
    let updateAvailable = await eel.check_update()();
    if (updateAvailable) {
        $("#update-notification-toast").toast('show');
    } else {
        $("#update-prompt").text("Your application is up to date. Hoorah!");
        $("#btn-start-update").hide();
        $("#btn-version-update").hide();
    }
}

$("#btn-start-update").click(function() {
    performUpdate();
});

$('#updateModal').on('show.bs.modal', function (e) {
    $("#update-notification-toast").toast('hide');
});