$("#btn-get-key").click(function() {
    // TODO: figure out how to open default browser with links
    //shell.openExternal("https://poddit.io/buy");
});

$("#btn-activate").click(function() {
    const email = $("#activation-email").val();
    const licenseKey = $("#activation-key").val();
    // TODO: perform client-side validation

    performActivation(email, licenseKey);
});

async function performActivation(email, licenseKey) {
    let response = await eel.activate(email, licenseKey)();
    const activated = response[0];
    const activations_remaining = response[1];
    const msg = response[2];
}
