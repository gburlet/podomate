eel.expose(update_determinant_loader);
function update_determinant_loader(progress, message="WORKING ...") {
    $("#loading-bar-determinant").width(progress+'%');
    $("#loading-bar-determinant").attr("aria-valuenow", progress);
    $("#loading-text-determinant").text(message);
}
