function secondsToTimestamp(s) {
    /*
    Takes in number of seconds and converts to a timestamp

    Args:
        s (float or int): seconds

    Returns:
        timestamp (string): format HH:MM:SS.MSS
    */

    let sign = s < 0 ? '-' : '';
    let remainder = Math.abs(s);
    let hours = Math.floor(remainder/3600.);
    remainder -= 3600*hours;
    let minutes = Math.floor(remainder/60.)
    remainder -= 60*minutes
    let seconds = Math.floor(remainder)
    remainder -= seconds
    let milliseconds = Math.floor(1000*remainder)

    return `${sign}${zeroPad(hours,2)}:${zeroPad(minutes,2)}:${zeroPad(seconds,2)}.${zeroPad(milliseconds,3)}`;
}

function checkValidTimestamp(timestamp) {
    // checks that a given timestamp is in format HH:MM:SS.MSS
    let re = /\d{2}:\d{2}:\d{2}\.\d{3}/;
    return re.test(timestamp);
}

function zeroPad(num, numZeros) {
    var n = Math.abs(num);
    var zeros = Math.max(0, numZeros - Math.floor(n).toString().length );
    var zeroString = Math.pow(10,zeros).toString().substr(1);
    if( num < 0 ) {
        zeroString = '-' + zeroString;
    }

    return zeroString+n;
}
