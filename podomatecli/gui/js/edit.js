function hideError() {
    $("#alert").hide();
}

function showError(message) {
    hideSpinners();
    $("#alert").text("Oh Snap! " + message);
    $("#alert").show();
    window.scrollTo(0, 0);
}

function showSpinner(isDeterminant) {
    if (isDeterminant) {
        $("#overlay-determinant").fadeIn();
    } else {
        $("#overlay-indeterminant").fadeIn();
    }
}

function hideSpinners() {
    $("#overlay-determinant").fadeOut();
    $("#overlay-indeterminant").fadeOut();
}

eel.expose(update_determinant_loader);
function update_determinant_loader(progress, message="WORKING ...") {
    $("#loading-bar-determinant").width(progress+'%');
    $("#loading-bar-determinant").attr("aria-valuenow", progress);
    $("#loading-text-determinant").text(message);
}
