class GateFilter(object):
    """
    Makes non-active audio a bit quieter
    """

    def __init__(self, db_reduction=-10.0):
        self._db_reduction = db_reduction
        pass

    def process(self, track):
        silence_intervals = track.silence_ranges
        for silence in silence_intervals:
            track.apply_gain(silence, self._db_reduction)
