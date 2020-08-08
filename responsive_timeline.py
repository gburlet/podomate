from utils import read_config_timestamp, s_to_timestamp


class ResponsiveTimeline(object):

    def __init__(self):
        # [[timestamp_s, offset], ...]
        # when inserting audio, timestamp_s is insertion beginning and (+) offset is duration of audio insert
        # when snipping out audio, timestamp_s is snip beginning and (-) offset is duration of audio snipped
        self._edits = []

    def perform_edit(self, timestamp, duration_s):
        """
        Amend the timeline

        Args:
            timestamp (string or float): timestamp when edit starts on original track (not considering other edits)
            duration_s (float): duration of edit (+) if insert (-) if deletion

        Returns:

        """
        self._edits.append([read_config_timestamp(timestamp), duration_s])

    def transform_timestamp(self, timestamp):
        """
        Args:
            timestamp (float or string): timestamp to transform

        Returns:
            transformed_timestamp (float): timestamp that is responsive to previous edits on track in order to place
                at the correct location
        """
        timestamp_s = read_config_timestamp(timestamp)
        offset_s = 0.
        for edit in self._edits:
            if edit[1] < 0 and edit[0] < timestamp_s < edit[0] - edit[1]:
                # this segment of audio was snipped, place at beginning of snip event
                return self.transform_timestamp(edit[0])
            elif edit[0] < timestamp_s:
                # an edit point occurs before the timestamp
                offset_s += edit[1]

        return timestamp_s + offset_s

    def untransform_timestamp(self, timestamp):
        """
        Args:
            timestamp (float or string): timestamp to transform

        Returns:
            untransformed_timestamp (float): timestamp in original file (before any track edits)
        """
        timestamp_s = read_config_timestamp(timestamp)
        transformed_timestamp_s = self.transform_timestamp(timestamp_s)
        offset_s = transformed_timestamp_s - timestamp_s
        return timestamp_s - offset_s

    def transform_interval(self, interval):
        """
        Args:
            interval (pair of timestamps):

        Returns:
            transformed_interval (pair of transformed timestamps)
        """
        return [self.transform_timestamp(interval[0]), self.transform_timestamp(interval[1])]

    def untransform_interval(self, interval):
        """
        Args:
            interval (pair of timestamps):

        Returns:
            untransformed_interval (pair of transformed timestamps)
        """
        return [self.untransform_timestamp(interval[0]), self.untransform_timestamp(interval[1])]

    def __str__(self):
        if len(self._edits) == 0:
            return "<Timeline/>"
        timeline_str = "<Timeline>\n"
        for edit in self._edits:
            timeline_str += "\t%s: %0.3f\n" % (s_to_timestamp(edit[0]), edit[1])
        timeline_str += "<Timeline/>"
        return timeline_str
