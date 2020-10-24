var selectedRegion = null;
const initZoomPx = 10;
var wavesurfer = null;
var numRegions = 0;
var regionLimit = 0;

/*
 * Sets up an interactive waveform
 * Parameters:
 *  audioFilename (string): filename of the audio file
 *  containerID (string): id for the wavesurfer object
 *  regionLimit (int): 0 = no region selections, x = x region selections. Make x = Infinity for no limit
 */
function setupInteractiveWaveform(audioFilename, containerID, regions=0) {
    if (wavesurfer == null) {
        // one-time setups
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
    }

    regionLimit = regions;
    if (regionLimit > 0) {
        // enable region selection
        wavesurfer = WaveSurfer.create({
            container: '#'+containerID,
            scrollParent: true,
            hideScrollbar: false,
            plugins: [
                WaveSurfer.timeline.create({
                    container: "#"+containerID+"-timeline"
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

        wavesurfer.on('region-created', handleAddRegion);
        wavesurfer.on('region-removed', handleRemoveRegion);
        wavesurfer.on('region-updated', handleUpdateRegion);
        wavesurfer.on('region-click', handleSelectRegion);
        wavesurfer.on('region-dblclick', function(e) {
            e.play();
            $('#playPause').removeClass('fa-play').addClass('fa-pause');
        });

        $("#one-region").click(function() {
            addRegion(0, wavesurfer.getDuration());
        });

        $("#clear-regions").click(function() {
            wavesurfer.clearRegions();
            $("#del-region").hide();
            $("#snap-cursor-region").hide();
        });

        $("#snap-cursor-region").click(function() {
            if (selectedRegion != null && selectedRegion.end < wavesurfer.getCurrentTime()) {
                selectedRegion.onResize(wavesurfer.getCurrentTime() - selectedRegion.end);
            }
        });

        $("#del-region").click(function() {
            deleteSelectedRegion();
        });
    } else {
        // disable region selection
        wavesurfer = WaveSurfer.create({
            container: '#'+containerID,
            scrollParent: true,
            hideScrollbar: false,
            plugins: [
                WaveSurfer.timeline.create({
                    container: "#"+containerID+"-timeline"
                })
            ]
        });
    }

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

    wavesurfer.load("../media/" + audioFilename);
}

function selectRegion(region) {
    selectedRegion = region;
    $("#del-region").show();
    $("#snap-cursor-region").show();
}

function deleteSelectedRegion() {
    if (selectedRegion != null) {
        selectedRegion.remove();
    }
    $("#del-region").hide();
    $("#snap-cursor-region").hide();
}

function handleAddRegion(region) {
    $("#alert").hide();
    numRegions++;
    if (numRegions > regionLimit) {
        setError("<b>Oh Snap!</b> You can only select " + regionLimit + " segment(s) of music for the backtrack");
        region.remove();
    }
}

function handleRemoveRegion(region) {
    numRegions = Math.max(0, numRegions-1);
}

function handleUpdateRegion(region) {
    selectRegion(region);
}

function handleSelectRegion(region) {
    selectedRegion = region;
    $("#del-region").show();
    $("#snap-cursor-region").show();
}

function addRegion(start, end) {
    let region = wavesurfer.addRegion({
        start: start,
        end: end,
        drag: true,
        resize: true,
        color: "rgba(45, 255, 25, 0.1)"
    });
    selectRegion(region);
}
