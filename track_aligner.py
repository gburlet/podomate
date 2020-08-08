import numpy as np

from utils import read_config_timestamp


class TrackAligner(object):

    def __init__(self, tracks_config=None):
        if tracks_config:
            self._track_offsets = [0.]*len(tracks_config)
            for i_track, track_config in enumerate(tracks_config):
                if "offset" in track_config:
                    self._track_offsets[i_track] = read_config_timestamp(track_config["offset"])

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

    def auto_calc_offset(self, tracks, finetune_local_search_s=1.0):
        """
        Algorithm is:
            loop through each track and try to find optimal offset so it merges into master track with
            least amount of overlap

        Args:
            tracks: list of SpeakerTrack
            finetune_local_search_s (float): number of seconds to grid search around coarse placement to finetune alignment

        Returns:
            offsets: list of time (s) offsets for each track
        """

        """
        # GRID SEARCH +/- 5min for offset
        imaster = [t.master for t in tracks].index(True)
        master_track = tracks[imaster]
        master_silence_ranges = master_track.silence_ranges
        master_activity_ranges = master_track.get_activity_ranges_from_silence_ranges(master_silence_ranges)
        for islave, slave_track in enumerate(tracks):
            if islave == imaster or self._track_offsets[islave] != 0:
                # skip offset calculation if master track or manual offset provided
                continue

            track_overlap_s = self._calc_track_overlap(master_track, slave_track, 0.)
            max_overhang_s = max(master_track.audio_buffer.get_duration_s()-track_overlap_s, slave_track.audio_buffer.get_duration_s()-track_overlap_s)
            search_length_s = max(max_overhang_s, 5*60.)   # search length of max track overhang or 5mins
            offset_candidates = np.linspace(-search_length_s, search_length_s, int(2*search_length_s*10))
            offset_candidate_errors = []
            slave_activity_ranges = slave_track.activity_ranges
            for offset in offset_candidates:
                placement_error = self._calc_activity_overlap(
                    master_track, master_activity_ranges, slave_activity_ranges, offset
                )
                offset_candidate_errors.append(placement_error)

            self._track_offsets[islave] = offset_candidates[np.argmin(offset_candidate_errors)]
        """

        """
        # PLACE LONGEST ACTIVITY IN SILENCES AND FINETUNE AROUND OFFSET WITH MIN ERROR
        imaster = [t.master for t in tracks].index(True)
        master_track = tracks[imaster]
        master_silence_ranges = master_track.silence_ranges
        master_activity_ranges = master_track.get_activity_ranges_from_silence_ranges(master_silence_ranges)
        for islave, slave_track in enumerate(tracks):
            if islave == imaster or self._track_offsets[islave] != 0:
                # skip offset calculation if master track or manual offset provided
                continue

            # locate longest audio_buffer activity near the middle of the slave track
            slave_activity_ranges = slave_track.activity_ranges
            num_slave_activities = len(slave_activity_ranges)
            i_middle_start = max(0, int(num_slave_activities/2.)-int(0.2*num_slave_activities))
            i_middle_end = min(int(num_slave_activities/2.)+int(0.2*num_slave_activities), num_slave_activities)
            middle_slave_activity_ranges = slave_activity_ranges[i_middle_start:i_middle_end]
            slave_longest_activity = sorted(middle_slave_activity_ranges, key=lambda ar: ar[1]-ar[0], reverse=True)[0]
            shortest_track_duration_s = min(master_track.audio_buffer.get_duration_s(), slave_track.audio_buffer.get_duration_s())

            # try to find rough fit in master silence
            silence_ranges_candidates = []
            silence_ranges_errors = []
            silence_ranges_overhang = []
            for master_silent_range in master_silence_ranges:
                placement_error = self._calc_activity_overlap(
                    master_track, master_activity_ranges, slave_activity_ranges,
                    master_silent_range[0]-slave_longest_activity[0]
                )
                track_overlap = self._calc_track_overlap(
                    master_track, slave_track, master_silent_range[0]-slave_longest_activity[0]
                )
                placement_error += shortest_track_duration_s - track_overlap
                silence_ranges_overhang.append(shortest_track_duration_s - track_overlap)
                silence_ranges_candidates.append(master_silent_range)
                silence_ranges_errors.append(placement_error)

            selected_silence_placement = master_silence_ranges[np.argmin(silence_ranges_errors)]

            # fine-tune the alignment by grid searching around the silence start period
            finetune_start_s = selected_silence_placement[0] - finetune_local_search_s
            finetune_end_s = selected_silence_placement[0] + finetune_local_search_s
            finetune_candidates = np.linspace(finetune_start_s, finetune_end_s, 20)
            finetune_errors = []
            for finetune_placement_s in finetune_candidates:
                placement_error = self._calc_activity_overlap(
                    master_track, master_activity_ranges, slave_activity_ranges,
                    finetune_placement_s-slave_longest_activity[0]
                )
                finetune_errors.append(placement_error)

            selected_finetune_placement = finetune_candidates[np.argmin(finetune_errors)]
            slave_offset_s = selected_finetune_placement-slave_longest_activity[0]
            self._track_offsets[islave] = slave_offset_s

        return self._track_offsets
        """

        """
        # PLACE EACH SLAVE ACTIVITY IN EACH SILENCE WITH FINETUNE AROUND EACH SILENCE
        imaster = [t.master for t in tracks].index(True)
        master_track = tracks[imaster]
        master_silence_ranges = master_track.silence_ranges
        master_activity_ranges = master_track.get_activity_ranges_from_silence_ranges(master_silence_ranges)
        for islave, slave_track in enumerate(tracks):
            if islave == imaster or self._track_offsets[islave] != 0:
                # skip offset calculation if master track or manual offset provided
                continue

            # locate longest audio_buffer activity near the middle of the slave track
            slave_activity_ranges = slave_track.activity_ranges

            # try to find rough fit in master silence
            slave_offsets = []
            for slave_activity in slave_activity_ranges:
                master_placement_candidates = []
                master_placement_errors = []
                for master_silent_range in master_silence_ranges:
                    # fine-tune the alignment by grid searching around the silence start period
                    finetune_start_s = master_silent_range[0] - finetune_local_search_s
                    finetune_end_s = master_silent_range[0] + finetune_local_search_s
                    finetune_candidates = np.linspace(finetune_start_s, finetune_end_s, 10)
                    for finetune_placement_s in finetune_candidates:
                        placement_error = self._calc_activity_overlap(
                            master_track, master_activity_ranges, slave_activity_ranges,
                            finetune_placement_s-slave_activity[0]
                        )

                        master_placement_candidates.append(finetune_placement_s)
                        master_placement_errors.append(placement_error)


                selected_master_placement = master_placement_candidates[np.argmin(master_placement_errors)]
                slave_offset_s = selected_master_placement-slave_activity[0]
                slave_offsets.append(s_to_timestamp(slave_offset_s))

        return self._track_offsets
        """

        # PLACE LONGEST ACTIVITY IN SILENCE WITH FINETUNE AROUND EACH SILENCE
        imaster = [t.master for t in tracks].index(True)
        master_track = tracks[imaster]
        master_silence_ranges = master_track.silence_ranges
        master_activity_ranges = master_track.get_activity_ranges_from_silence_ranges(master_silence_ranges)
        for islave, slave_track in enumerate(tracks):
            if islave == imaster or self._track_offsets[islave] != 0:
                # skip offset calculation if master track or manual offset provided
                continue

            # locate longest audio_buffer activity near the middle of the slave track
            slave_activity_ranges = slave_track.activity_ranges
            num_slave_activities = len(slave_activity_ranges)
            i_middle_start = max(0, int(num_slave_activities/2.)-int(0.2*num_slave_activities))
            i_middle_end = min(int(num_slave_activities/2.)+int(0.2*num_slave_activities), num_slave_activities)
            middle_slave_activity_ranges = slave_activity_ranges[i_middle_start:i_middle_end]
            slave_longest_activity = sorted(middle_slave_activity_ranges, key=lambda ar: ar[1]-ar[0], reverse=True)[0]
            shortest_track_duration_s = min(master_track.audio_buffer.get_duration_s(), slave_track.audio_buffer.get_duration_s())

            # try to find rough fit in master silence
            master_placement_candidates = []
            master_placement_errors = []
            for master_silent_range in master_silence_ranges:
                # fine-tune the alignment by grid searching around the silence start period
                finetune_start_s = master_silent_range[0] - finetune_local_search_s
                finetune_end_s = master_silent_range[0] + finetune_local_search_s
                finetune_candidates = np.linspace(finetune_start_s, finetune_end_s, 10)
                for finetune_placement_s in finetune_candidates:
                    slave_offset_s = finetune_placement_s-slave_longest_activity[0]
                    track_overlap = self._calc_track_overlap(master_track, slave_track, slave_offset_s)
                    if track_overlap/float(shortest_track_duration_s) < 0.9:
                        # optimization heuristic: there should be sufficient overlap between tracks
                        continue
                    # error = activity overlap + lost audio
                    # 1. activity overlap
                    placement_error = self._calc_activity_overlap(
                        master_track, master_activity_ranges, slave_activity_ranges, slave_offset_s
                    )
                    # 2. lost audio
                    placement_error += abs(slave_offset_s)

                    master_placement_candidates.append(finetune_placement_s)
                    master_placement_errors.append(placement_error)

            selected_master_placement = master_placement_candidates[np.argmin(master_placement_errors)]
            slave_offset_s = selected_master_placement-slave_longest_activity[0]
            self._track_offsets[islave] = slave_offset_s

        return self._track_offsets

    def _calc_track_overlap(self, master_track, slave_track, slave_offset):
        master_track_start = 0
        master_track_end = master_track.audio_buffer.get_duration_s()
        slave_track_start = slave_offset
        slave_track_end = slave_track.audio_buffer.get_duration_s() + slave_offset
        latest_start = max(master_track_start, slave_track_start)
        earliest_end = min(master_track_end, slave_track_end)
        overlap_s = max(0, earliest_end - latest_start)
        return overlap_s

    def _calc_activity_overlap(self, master_track, master_activity_ranges, slave_activity_ranges, slave_offset):
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

        return activity_overlap
