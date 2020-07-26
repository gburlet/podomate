import numpy as np


class TrackAligner(object):

    def __init__(self):
        pass

    def align(self, tracks, track_offsets=None):
        if track_offsets is None:
            track_offsets = self.auto_calc_offset(tracks)
        for offset, track in zip(track_offsets, tracks):
            if offset != 0:
                track.apply_offset(offset)

        return self

    def pad(self, tracks):
        max_samples = max(map(lambda t: len(t.audio_buffer.x), tracks))
        for t in tracks:
            t.audio_buffer.pad(max_samples)

    def auto_calc_offset(self, tracks):
        """
        Algorithm is:
            loop through each track and try to find optimal offset so it merges into master track with
            least amount of overlap

        Args:
            tracks: list of SpeakerTrack

        Returns:
            offsets: list of time (s) offsets for each track
        """

        imaster = [t.master for t in tracks].index(True)
        track_offsets = [0.]*len(tracks)
        master_silence_ranges = tracks[imaster].silence_ranges
        for islave, slave_track in enumerate(tracks):
            if islave == imaster:
                continue

            # locate longest audio_buffer activity
            slave_longest_activity = sorted(slave_track.activity_ranges, key=lambda ar: ar[1]-ar[0], reverse=True)[0]

            # try to find fit in master silence
            silence_ranges_errors = []
            for master_silent_range in master_silence_ranges:
                placement_error = self._calc_activity_overlap(
                    tracks[0], slave_track, master_silent_range[0]-slave_longest_activity[0]
                )
                silence_ranges_errors.append(placement_error)
            selected_silence_placement = master_silence_ranges[np.argmin(silence_ranges_errors)]
            slave_offset_s = selected_silence_placement[0]-slave_longest_activity[0]
            track_offsets[islave] = slave_offset_s

        return track_offsets

    def _calc_activity_overlap(self, master_track, slave_track, slave_offset):
        master_activity_ranges = master_track.activity_ranges
        slave_activity_ranges = slave_track.activity_ranges

        activity_overlap = 0.
        for master_activity in master_activity_ranges:
            master_activity_start = master_activity[0]
            master_activity_end = master_activity[1]
            for slave_activity in slave_activity_ranges:
                slave_activity_start = slave_activity[0] + slave_offset
                slave_activity_end = slave_activity[1] + slave_offset
                if slave_activity_start >= master_activity_end:
                    break
                elif slave_activity_end <= master_activity_start:
                    continue
                elif slave_activity_start < master_activity_start and slave_activity_end < master_activity_end:
                    activity_overlap += slave_activity_end - master_activity_start
                elif slave_activity_start > master_activity_start and slave_activity_end < master_activity_end:
                    activity_overlap += slave_activity_end - slave_activity_start
                elif slave_activity_start < master_activity_end < slave_activity_end:
                    activity_overlap += master_activity_end - slave_activity_start

        # add overhang error
        master_track_duration = master_track.audio_buffer.get_duration_s()
        for slave_activity in slave_activity_ranges:
            slave_activity_start = slave_activity[0] + slave_offset
            slave_activity_end = slave_activity[1] + slave_offset
            if slave_activity_start < 0:
                activity_overlap += min(slave_activity_end, 0) - slave_activity_start
            if slave_activity_end > master_track_duration:
                activity_overlap += slave_activity_end - master_track_duration

        return activity_overlap
