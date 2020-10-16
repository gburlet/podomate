from mir.mir.transcription.audio_preprocessors.logmsse_noise_reducer import LogMSSENoiseReducer
from mir.mir.transcription.audio_preprocessors.onestepweiner_noise_reducer import OneStepWeinerNoiseReducer
from mir.mir.transcription.audio_preprocessors.twostepweiner_noise_reducer import TwoStepWeinerNoiseReducer


class NoiseReducerFactory(object):
    """
    Constructs NoiseReduction algorithms
    """

    ALGORITHMS = {
        LogMSSENoiseReducer.ID: LogMSSENoiseReducer,
        OneStepWeinerNoiseReducer.ID: OneStepWeinerNoiseReducer, TwoStepWeinerNoiseReducer.ID: TwoStepWeinerNoiseReducer
    }

    def __init__(self):
        pass

    def construct_noise_reducer(self, settings):
        if settings.noise_reduction not in NoiseReducerFactory.ALGORITHMS:
            raise NotImplementedError("Unknown noise reduction algorithm: %s" % settings.noise_reducer)
        noise_reducer = NoiseReducerFactory.ALGORITHMS[settings.noise_reduction](
            window_size=2048, hop_size=1024
        )
        return noise_reducer
