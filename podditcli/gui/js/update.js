eel.expose(update_progress_tick);
function update_progress_tick(progress) {
    // update download bar here
    console.log(progress);
}

async function performUpdate() {
    let response = await eel.update(email, licenseKey)();
    const activated = response["activated"];
    const activations_remaining = response["activations_remaining"];
    const msg = response["msg"];

    if (activated) {
        $("#activation-start").hide();
        $("#activation-success").show();
        $("#activation-footer").hide();
        $("#btn-start-activation").hide();
    } else {
        $("#activation-key").addClass("is-invalid");
    }
    $("#activation-spinner").hide();
    $("#btn-activate").attr("disabled", false);
}

async function checkUpdate() {
    let updateAvailable = await eel.check_update()();
    if (updateAvailable) {
        $("#update-notification-toast").show();
    }
}

$("#btn-update").click(function() {
    performUpdate();
});
