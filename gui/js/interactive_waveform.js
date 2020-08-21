var selectedRegion = null;
const initZoomPx = 10;
var wavesurfer = null;

function setupInteractiveWaveform(audioFilename) {
    wavesurfer = WaveSurfer.create({
        container: '#waveform',
        scrollParent: true,
        hideScrollbar: false,
        plugins: [
            WaveSurfer.timeline.create({
                container: "#wave-timeline"
            }),
            WaveSurfer.regions.create({
                regions: []
            })
        ]
    });
    wavesurfer.enableDragSelection({
        drag: true,
        resize: true,
        color: "rgba(45, 255, 25, 0.1)"
    });

    wavesurfer.zoom(initZoomPx);
    $("#zoom-slider").val(initZoomPx);

    function playPause() {
        wavesurfer.playPause();
        if (wavesurfer.isPlaying()) {
            $('#playPause').removeClass('fa-play').addClass('fa-pause');
        } else {
            $('#playPause').removeClass('fa-pause').addClass('fa-play');
        }
    }

    function deleteSelectedRegion() {
        if (selectedRegion != null) {
            selectedRegion.remove();
        }
        $("#del-region").hide();
    }

    function selectRegion(region) {
        selectedRegion = region;
        $("#del-region").show();
    }

    $(document).keydown(function(event) {
        if (event.which == 32) {
            event.preventDefault();
        }
    });

    $(document).keyup(function(event) {
        let key = event.which;
        switch(key) {
            case 32:
                event.preventDefault();
                playPause();
                break;
            case 8:
            case 46:
                deleteSelectedRegion();
                break;
        }
    });

    $("#playPause").click(function() {
        playPause();
    });

    $("#seek-start").click(function() {
        wavesurfer.seekAndCenter(0);
    });

    $("#seek-end").click(function() {
        wavesurfer.seekAndCenter(1);
    });

    $("#zoom-slider").change(function() {
        wavesurfer.zoom(Number(this.value));
    });

    $("#clear-regions").click(function() {
        wavesurfer.clearRegions();
    });

    wavesurfer.on('region-created', selectRegion);
    wavesurfer.on('region-updated', selectRegion);
    wavesurfer.on('region-click', selectRegion);
    wavesurfer.on('region-dblclick', function(e) {
        e.play();
        $('#playPause').removeClass('fa-play').addClass('fa-pause');
    });

    $("#del-region").click(function() {
        deleteSelectedRegion();
    });

    wavesurfer.load("../media/" + audioFilename);
}
