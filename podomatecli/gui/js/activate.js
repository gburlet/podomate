function validateEmail(email) {
    const re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(email);
}

function validateLicenseKey(licenseKey) {
    const re = /^\w{8}-\w{4}-\w{4}-\w{4}-\w{12}$/;
    return re.test(licenseKey);
}

$("#btn-get-key").click(function() {
    // TODO: figure out how to open default browser with links
    //shell.openExternal("https://podomate.io/buy");
});

$("#btn-activate").click(function() {
    // client-side validation
    $("#activation-email").removeClass("is-invalid");
    $("#activation-key").removeClass("is-invalid");
    let formIsValid = true;
    const email = $("#activation-email").val();
    let validEmail = validateEmail(email);
    if (!validEmail) {
        $("#activation-email").addClass("is-invalid");
    }
    const licenseKey = $("#activation-key").val();
    let validLicenseKey = validateLicenseKey(licenseKey);
    if (!validLicenseKey) {
        $("#activation-key").addClass("is-invalid");
    }
    formIsValid = formIsValid && validEmail && validLicenseKey;

    if (formIsValid) {
        $("#activation-spinner").show();
        $("#btn-activate").attr("disabled", true);
        setTimeout(() => {
            performActivation(email, licenseKey);
        }, 2000);
    }
});

async function performActivation(email, licenseKey) {
    let response = await eel.activate(email, licenseKey)();
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

async function checkActivation() {
    let isActivated = await eel.check_license()();
    if (isActivated) {
        $("#btn-start-activation").hide();
    }
}

$('#activationModal').on('hidden.bs.modal', function (e) {
    $("#activation-start").show();
    $("#activation-success").hide();
    $("#activation-footer").show();
});
