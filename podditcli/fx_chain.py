import sox


class FXChain(object):

    def __init__(self, fx_chain):
        self._tfm = sox.Transformer()
        for fx in fx_chain:
            # custom parameter tweaks
            if fx["effect"] == "mcompand" and "tf_points" in fx["parameters"]:
                for i in range(len(fx["parameters"]["tf_points"][0])):
                    fx["parameters"]["tf_points"][0][i] = tuple(fx["parameters"]["tf_points"][0][i])
            getattr(self._tfm, fx["effect"])(**fx["parameters"])

    def apply(self, track):
        track.audio_buffer.x = self._tfm.build_array(
            input_array=track.audio_buffer.x, sample_rate_in=track.audio_buffer.fs
        )
